# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################

import datetime
import os
from abc import ABC
from collections import OrderedDict
from urllib.parse import unquote_plus, quote_plus

from sqlalchemy import orm
from tornado import gen
from tornado.escape import json_encode
from tornado.httputil import url_concat
from tornado.web import authenticated

import sickrage
from sickrage.clients import get_client_instance
from sickrage.clients.sabnzbd import SabNZBd
from sickrage.core.common import Overview, Quality, cpu_presets, statusStrings, WANTED, FAILED, UNAIRED, IGNORED, \
    SKIPPED
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import AnidbAdbaConnectionException, CantRefreshShowException, NoNFOException, \
    CantUpdateShowException, CantRemoveShowException, EpisodeDeletedException, EpisodeNotFoundException, \
    MultipleEpisodesInDatabaseException
from sickrage.core.helpers import clean_url, clean_host, clean_hosts, get_disk_space_usage, checkbox_to_value, try_int
from sickrage.core.helpers.anidb import get_release_groups_for_anime, short_group_names
from sickrage.core.helpers.srdatetime import SRDateTime
from sickrage.core.helpers.tornado_http import TornadoHTTP
from sickrage.core.queues.search import BacklogQueueItem, FailedQueueItem, ManualSearchQueueItem
from sickrage.core.scene_exceptions import get_scene_exceptions, update_scene_exceptions
from sickrage.core.scene_numbering import get_scene_numbering_for_show, get_xem_numbering_for_show, \
    get_scene_absolute_numbering_for_show, get_xem_absolute_numbering_for_show, xem_refresh, set_scene_numbering, \
    get_scene_absolute_numbering, get_scene_numbering
from sickrage.core.traktapi import TraktAPI
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show.helpers import find_show, get_show_list
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.indexers import IndexerApi
from sickrage.subtitles import Subtitles


@MainDB.with_session
def _get_episode(show, season=None, episode=None, absolute=None, session=None):
    if show is None:
        return _("Invalid show parameters")

    show_obj = find_show(int(show), session=session)

    if show_obj is None:
        return _("Invalid show paramaters")

    try:
        if absolute:
            ep_obj = show_obj.get_episode(absolute_number=int(absolute))
        elif season and episode:
            ep_obj = show_obj.get_episode(int(season), int(episode))
        else:
            return _("Invalid paramaters")
    except (EpisodeNotFoundException, MultipleEpisodesInDatabaseException):
        return _("Episode couldn't be retrieved")

    return ep_obj


class HomeHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        if not get_show_list().count():
            return self.redirect('/home/addShows/')

        showlists = OrderedDict({'Shows': []})
        if sickrage.app.config.anime_split_home:
            for show in get_show_list():
                if show.is_anime:
                    if 'Anime' not in list(showlists.keys()):
                        showlists['Anime'] = []
                    showlists['Anime'] += [show]
                else:
                    showlists['Shows'] += [show]
        else:
            showlists['Shows'] = get_show_list()

        return self.render(
            "/home/index.mako",
            title="Home",
            header="Show List",
            topmenu="home",
            showlists=showlists,
            controller='home',
            action='index'
        )

    def statistics(self):
        show_stat = {}

        overall_stats = {
            'episodes': {
                'downloaded': 0,
                'snatched': 0,
                'total': 0,
            },
            'shows': {
                'active': len([show for show in get_show_list() if show.paused == 0 and show.status.lower() == 'continuing']),
                'total': get_show_list().count(),
            },
            'total_size': 0
        }

        for show in get_show_list(session=self.db_session):
            if sickrage.app.show_queue.is_being_added(show.indexer_id) or sickrage.app.show_queue.is_being_removed(show.indexer_id):
                show_stat[show.indexer_id] = {
                    'ep_airs_next': datetime.date.min,
                    'ep_airs_prev': datetime.date.min,
                    'ep_snatched': 0,
                    'ep_downloaded': 0,
                    'ep_total': 0,
                    'total_size': 0
                }
            else:
                show_stat[show.indexer_id] = {
                    'ep_airs_next': show.airs_next or datetime.date.min,
                    'ep_airs_prev': show.airs_prev or datetime.date.min,
                    'ep_snatched': show.episodes_snatched or 0,
                    'ep_downloaded': show.episodes_downloaded or 0,
                    'ep_total': len(show.episodes),
                    'total_size': show.total_size or 0
                }

            overall_stats['episodes']['snatched'] += show_stat[show.indexer_id]['ep_snatched']
            overall_stats['episodes']['downloaded'] += show_stat[show.indexer_id]['ep_downloaded']
            overall_stats['episodes']['total'] += show_stat[show.indexer_id]['ep_total']
            overall_stats['total_size'] += show_stat[show.indexer_id]['total_size']

        return show_stat, overall_stats


class IsAliveHandler(BaseHandler, ABC):
    def get(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/javascript')

        srcallback = self.get_argument('srcallback')

        if not srcallback:
            return self.write(_("Error: Unsupported Request. Send jsonp request with 'srcallback' variable in the query string."))

        return self.write("{}({})".format(srcallback, {'msg': str(sickrage.app.pid) if sickrage.app.started else 'nope'}))


class TestSABnzbdHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_url(self.get_argument('host'))
        username = self.get_argument('username')
        password = self.get_argument('password')
        apikey = self.get_argument('apikey')

        connection, acces_msg = SabNZBd.get_sab_access_method(host)

        if connection:
            authed, auth_msg = SabNZBd.test_authentication(host, username, password, apikey)
            if authed:
                return self.write(_('Success. Connected and authenticated'))
            return self.write(_('Authentication failed. SABnzbd expects {access!r} as authentication method, {auth}'.format(access=acces_msg, auth=auth_msg)))
        return self.write(_('Unable to connect to host'))


class TestTorrentHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_url(self.get_argument('host'))
        torrent_method = self.get_argument('torrent_method')
        username = self.get_argument('username')
        password = self.get_argument('password')

        client = get_client_instance(torrent_method)
        __, access_msg = client(host, username, password).test_authentication()
        return self.write(access_msg)


class TestFreeMobileHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        freemobile_id = self.get_argument('freemobile_id')
        freemobile_apikey = self.get_argument('freemobile_apikey')

        result, message = sickrage.app.notifier_providers['freemobile'].test_notify(freemobile_id, freemobile_apikey)
        if result:
            return self.write(_('SMS sent successfully'))
        return self.write(_('Problem sending SMS: ') + message)


class TestTelegramHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        telegram_id = self.get_argument('telegram_id')
        telegram_apikey = self.get_argument('telegram_apikey')

        result, message = sickrage.app.notifier_providers['telegram'].test_notify(telegram_id, telegram_apikey)
        if result:
            return self.write(_('Telegram notification succeeded. Check your Telegram clients to make sure it worked'))
        return self.write(_('Error sending Telegram notification: {message}').format(message=message))


class TestJoinHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        join_id = self.get_argument('join_id')
        join_apikey = self.get_argument('join_apikey')

        result, message = sickrage.app.notifier_providers['join'].test_notify(join_id, join_apikey)
        if result:
            return self.write(_('Join notification succeeded. Check your Join clients to make sure it worked'))
        return self.write(_('Error sending Join notification: {message}').format(message=message))


class TestGrowlHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'), default_port=23053)
        password = self.get_argument('password')

        result = sickrage.app.notifier_providers['growl'].test_notify(host, password)
        if password is None or password == '':
            pw_append = ''
        else:
            pw_append = _(' with password: ') + password

        if result:
            return self.write(_('Registered and tested Growl successfully ') + unquote_plus(host) + pw_append)
        return self.write(_('Registration and testing of Growl failed ') + unquote_plus(host) + pw_append)


class TestProwlHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        prowl_api = self.get_argument('prowl_api')
        prowl_priority = self.get_argument('prowl_priority')

        result = sickrage.app.notifier_providers['prowl'].test_notify(prowl_api, prowl_priority)
        if result:
            return self.write(_('Test prowl notice sent successfully'))
        return self.write(_('Test prowl notice failed'))


class TestBoxcar2Handler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        accesstoken = self.get_argument('accesstoken')

        result = sickrage.app.notifier_providers['boxcar2'].test_notify(accesstoken)
        if result:
            return self.write(_('Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked'))
        return self.write(_('Error sending Boxcar2 notification'))


class TestPushoverHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        user_key = self.get_argument('userKey')
        api_key = self.get_argument('apiKey')

        result = sickrage.app.notifier_providers['pushover'].test_notify(user_key, api_key)
        if result:
            return self.write(_('Pushover notification succeeded. Check your Pushover clients to make sure it worked'))
        return self.write(_('Error sending Pushover notification'))


class TwitterStep1Handler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        return self.write(sickrage.app.notifier_providers['twitter']._get_authorization())


class TwitterStep2Handler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        key = self.get_argument('key')

        result = sickrage.app.notifier_providers['twitter']._get_credentials(key)
        sickrage.app.log.info("result: " + str(result))
        if result:
            return self.write(_('Key verification successful'))
        return self.write(_('Unable to verify key'))


class TestTwitterHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        result = sickrage.app.notifier_providers['twitter'].test_notify()
        if result:
            return self.write(_('Tweet successful, check your twitter to make sure it worked'))
        return self.write(_('Error sending tweet'))


class TestTwilioHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        account_sid = self.get_argument('account_sid')
        auth_token = self.get_argument('auth_token')
        phone_sid = self.get_argument('phone_sid')
        to_number = self.get_argument('to_number')

        if not sickrage.app.notifier_providers['twilio'].account_regex.match(account_sid):
            return self.write(_('Please enter a valid account sid'))

        if not sickrage.app.notifier_providers['twilio'].auth_regex.match(auth_token):
            return self.write(_('Please enter a valid auth token'))

        if not sickrage.app.notifier_providers['twilio'].phone_regex.match(phone_sid):
            return self.write(_('Please enter a valid phone sid'))

        if not sickrage.app.notifier_providers['twilio'].number_regex.match(to_number):
            return self.write(_('Please format the phone number as "+1-###-###-####"'))

        result = sickrage.app.notifier_providers['twilio'].test_notify()
        if result:
            return self.write(_('Authorization successful and number ownership verified'))
        return self.write(_('Error sending sms'))


class TestSlackHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        result = sickrage.app.notifier_providers['slack'].test_notify()
        if result:
            return self.write(_('Slack message successful'))
        return self.write(_('Slack message failed'))


class TestDiscordHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        result = sickrage.app.notifier_providers['discord'].test_notify()
        if result:
            return self.write(_('Discord message successful'))
        return self.write(_('Discord message failed'))


class TestKODIHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_hosts(self.get_argument('host'))
        username = self.get_argument('username')
        password = self.get_argument('password')

        final_result = ''
        for curHost in [x.strip() for x in host.split(",")]:
            cur_result = sickrage.app.notifier_providers['kodi'].test_notify(unquote_plus(curHost), username, password)
            if len(cur_result.split(":")) > 2 and 'OK' in cur_result.split(":")[2]:
                final_result += _('Test KODI notice sent successfully to ') + unquote_plus(curHost)
            else:
                final_result += _('Test KODI notice failed to ') + unquote_plus(curHost)
            final_result += "<br>\n"

        return self.write(final_result)


class TestPMCHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_hosts(self.get_argument('host'))
        username = self.get_argument('username')
        password = self.get_argument('password', None)

        if password and set('*') == set(password):
            password = sickrage.app.config.plex_client_password

        final_result = ''
        for curHost in [x.strip() for x in host.split(',')]:
            cur_result = sickrage.app.notifier_providers['plex'].test_notify_pmc(unquote_plus(curHost), username,
                                                                                 password)
            if len(cur_result.split(':')) > 2 and 'OK' in cur_result.split(':')[2]:
                final_result += _('Successful test notice sent to Plex client ... ') + unquote_plus(curHost)
            else:
                final_result += _('Test failed for Plex client ... ') + unquote_plus(curHost)
            final_result += '<br>' + '\n'

        sickrage.app.alerts.message(_('Tested Plex client(s): '),
                                    unquote_plus(host.replace(',', ', ')))

        return self.write(final_result)


class TestPMSHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_hosts(self.get_argument('host'))
        username = self.get_argument('username')
        password = self.get_argument('password', None)
        plex_server_token = self.get_argument('plex_server_token')

        if password and set('*') == set(password):
            password = sickrage.app.config.plex_password

        final_result = ''

        cur_result = sickrage.app.notifier_providers['plex'].test_notify_pms(unquote_plus(host), username, password,
                                                                             plex_server_token)
        if cur_result is None:
            final_result += _('Successful test of Plex server(s) ... ') + \
                            unquote_plus(host.replace(',', ', '))
        elif cur_result is False:
            final_result += _('Test failed, No Plex Media Server host specified')
        else:
            final_result += _('Test failed for Plex server(s) ... ') + \
                            unquote_plus(str(cur_result).replace(',', ', '))
        final_result += '<br>' + '\n'

        sickrage.app.alerts.message(_('Tested Plex Media Server host(s): '),
                                    unquote_plus(host.replace(',', ', ')))

        return self.write(final_result)


class TestLibnotifyHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        if sickrage.app.notifier_providers['libnotify'].notifier.test_notify():
            return self.write(_('Tried sending desktop notification via libnotify'))
        return self.write(sickrage.app.notifier_providers['libnotify'].diagnose())


class TestEMBYHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        emby_apikey = self.get_argument('emby_apikey')

        result = sickrage.app.notifier_providers['emby'].test_notify(unquote_plus(host), emby_apikey)
        if result:
            return self.write(_('Test notice sent successfully to ') + unquote_plus(host))
        return self.write(_('Test notice failed to ') + unquote_plus(host))


class TestNMJHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        database = self.get_argument('database')
        mount = self.get_argument('mount')

        result = sickrage.app.notifier_providers['nmj'].test_notify(unquote_plus(host), database, mount)
        if result:
            return self.write(_('Successfully started the scan update'))
        return self.write(_('Test failed to start the scan update'))


class SettingsNMJHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))

        result = sickrage.app.notifier_providers['nmj'].notify_settings(unquote_plus(host))
        if result:
            return self.write(
                '{"message": "%(message)s %(host)s", "database": "%(database)s", "mount": "%(mount)s"}' % {
                    "message": _('Got settings from'),
                    "host": host, "database": sickrage.app.config.nmj_database,
                    "mount": sickrage.app.config.nmj_mount
                })

        message = _('Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for '
                    'detailed info)')

        return self.write('{"message": {}, "database": "", "mount": ""}'.format(message))


class TestNMJv2Handler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))

        result = sickrage.app.notifier_providers['nmjv2'].test_notify(unquote_plus(host))
        if result:
            return self.write(_('Test notice sent successfully to ') + unquote_plus(host))
        return self.write(_('Test notice failed to ') + unquote_plus(host))


class SettingsNMJv2Handler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        dbloc = self.get_argument('dbloc')
        instance = self.get_argument('instance')

        result = sickrage.app.notifier_providers['nmjv2'].notify_settings(unquote_plus(host), dbloc, instance)
        if result:
            return self.write(
                '{"message": "NMJ Database found at: %(host)s", "database": "%(database)s"}' % {"host": host,
                                                                                                "database": sickrage.app.config.nmjv2_database}
            )
        return self.write(
            '{"message": "Unable to find NMJ Database at location: %(dbloc)s. Is the right location selected and PCH '
            'running?", "database": ""}' % {"dbloc": dbloc}
        )


class GetTraktTokenHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        trakt_pin = self.get_argument('trakt_pin')

        if TraktAPI().authenticate(trakt_pin):
            return self.write(_('Trakt Authorized'))
        return self.write(_('Trakt Not Authorized!'))


class TestTraktHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        username = self.get_argument('username')
        blacklist_name = self.get_argument('blacklist_name')

        return self.write(sickrage.app.notifier_providers['trakt'].test_notify(username, blacklist_name))


class LoadShowNotifyListsHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        data = {'_size': 0}
        for s in sorted(get_show_list(), key=lambda k: k.name):
            data[s.indexer_id] = {'id': s.indexer_id, 'name': s.name, 'list': s.notify_list}
            data['_size'] += 1
        return self.write(json_encode(data))


class SaveShowNotifyListHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        emails = self.get_argument('emails')

        try:
            show = find_show(int(show), session=self.db_session)
            show.notify_list = emails
        except Exception:
            return self.write('ERROR')


class TestEmailHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        port = self.get_argument('port')
        smtp_from = self.get_argument('smtp_from')
        use_tls = self.get_argument('use_tls')
        user = self.get_argument('user')
        pwd = self.get_argument('pwd')
        to = self.get_argument('to')

        if sickrage.app.notifier_providers['email'].test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return self.write(_('Test email sent successfully! Check inbox.'))
        return self.write(_('ERROR: %s') % sickrage.app.notifier_providers['email'].last_err)


class TestNMAHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        nma_api = self.get_argument('nma_api')
        nma_priority = self.get_argument('nma_priority')

        result = sickrage.app.notifier_providers['nma'].test_notify(nma_api, nma_priority)
        if result:
            return self.write(_('Test NMA notice sent successfully'))
        return self.write(_('Test NMA notice failed'))


class TestPushalotHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        authorization_token = self.get_argument('authorizationToken')

        result = sickrage.app.notifier_providers['pushalot'].test_notify(authorization_token)
        if result:
            return self.write(_('Pushalot notification succeeded. Check your Pushalot clients to make sure it worked'))
        return self.write(_('Error sending Pushalot notification'))


class TestPushbulletHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        api = self.get_argument('api')

        result = sickrage.app.notifier_providers['pushbullet'].test_notify(api)
        if result:
            return self.write(_('Pushbullet notification succeeded. Check your device to make sure it worked'))
        return self.write(_('Error sending Pushbullet notification'))


class GetPushbulletDevicesHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        api = self.get_argument('api')

        result = sickrage.app.notifier_providers['pushbullet'].get_devices(api)
        if result:
            return self.write(result)
        return self.write(_('Error getting Pushbullet devices'))


class StatusHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        tvdir_free = get_disk_space_usage(sickrage.app.config.tv_download_dir)
        root_dir = {}
        if sickrage.app.config.root_dirs:
            backend_pieces = sickrage.app.config.root_dirs.split('|')
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if len(backend_dirs):
            for subject in backend_dirs:
                root_dir[subject] = get_disk_space_usage(subject)

        return self.render(
            "/home/status.mako",
            title=_('Status'),
            header=_('Status'),
            topmenu='system',
            tvdirFree=tvdir_free,
            rootDir=root_dir,
            controller='home',
            action='status'
        )


class ShutdownHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')

        if str(pid) != str(sickrage.app.pid):
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        self._genericMessage(_("Shutting down"), _("SiCKRAGE is shutting down"))
        sickrage.app.shutdown()


class RestartHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')
        force = self.get_argument('force', None)

        if str(pid) != str(sickrage.app.pid) and not force:
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        # clear current user to disable header and footer
        self.current_user = None

        sickrage.app.io_loop.add_timeout(datetime.timedelta(seconds=5), sickrage.app.shutdown, restart=True)

        return self.render(
            "/home/restart.mako",
            title="Home",
            header="Restarting SiCKRAGE",
            topmenu="system",
            controller='home',
            action="restart",
        )


class UpdateCheckHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')

        if str(pid) != str(sickrage.app.pid) or sickrage.app.disable_updates:
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        sickrage.app.alerts.message(_("Updater"), _('Checking for updates'))

        # check for new app updates
        if not sickrage.app.version_updater.check_for_new_version(force=True):
            sickrage.app.alerts.message(_("Updater"), _('No new updates available!'))

        return self.redirect(self.previous_url())


class UpdateHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')

        if str(pid) != str(sickrage.app.pid):
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        sickrage.app.alerts.message(_("Updater"), _('Updating SiCKRAGE'))

        self.run_task(sickrage.app.version_updater.update, webui=True)

        return self.redirect(self.previous_url())


class VerifyPathHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        path = self.get_argument('path')

        if os.path.isfile(path):
            return self.write(_('Successfully found {path}'.format(path=path)))
        return self.write(_('Failed to find {path}'.format(path=path)))


class InstallRequirementsHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        sickrage.app.alerts.message(_('Installing SiCKRAGE requirements'))
        if not sickrage.app.version_updater.updater.install_requirements(
                sickrage.app.version_updater.updater.current_branch):
            sickrage.app.alerts.message(_('Failed to install SiCKRAGE requirements'))
        else:
            sickrage.app.alerts.message(_('Installed SiCKRAGE requirements successfully!'))

        return self.redirect(self.previous_url())


class BranchCheckoutHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        branch = self.get_argument('branch')

        if sickrage.app.version_updater.updater.current_branch != branch:
            sickrage.app.alerts.message(_('Checking out branch: '), branch)
            if sickrage.app.version_updater.updater.checkout_branch(branch):
                sickrage.app.alerts.message(_('Branch checkout successful, restarting: '), branch)
                response = await TornadoHTTP().get(
                    url_concat(
                        self.get_url("/home/restart"), {'pid': sickrage.app.pid}
                    )
                )
                return self.write(response.body)
        else:
            sickrage.app.alerts.message(_('Already on branch: '), branch)

        return self.redirect(self.previous_url())


class DisplayShowHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        show = self.get_argument('show')

        submenu = []

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        episode_objects = sorted(show_obj.episodes, key=lambda x: (x.season, x.episode), reverse=True)

        season_results = list({x.season for x in episode_objects})

        submenu.append({
            'title': _('Edit'),
            'path': '/home/editShow?show=%d' % show_obj.indexer_id,
            'icon': 'fas fa-edit'
        })

        show_loc = show_obj.location

        show_message = ''

        if sickrage.app.show_queue.is_being_added(show_obj.indexer_id):
            show_message = _('This show is in the process of being downloaded - the info below is incomplete.')

        elif sickrage.app.show_queue.is_being_updated(show_obj.indexer_id):
            show_message = _('The information on this page is in the process of being updated.')

        elif sickrage.app.show_queue.is_being_refreshed(show_obj.indexer_id):
            show_message = _('The episodes below are currently being refreshed from disk')

        elif sickrage.app.show_queue.is_being_subtitled(show_obj.indexer_id):
            show_message = _('Currently downloading subtitles for this show')

        elif sickrage.app.show_queue.is_being_refreshed(show_obj.indexer_id):
            show_message = _('This show is queued to be refreshed.')

        elif sickrage.app.show_queue.is_being_updated(show_obj.indexer_id):
            show_message = _('This show is queued and awaiting an update.')

        elif sickrage.app.show_queue.is_being_subtitled(show_obj.indexer_id):
            show_message = _('This show is queued and awaiting subtitles download.')

        if not sickrage.app.show_queue.is_being_added(show_obj.indexer_id):
            if not sickrage.app.show_queue.is_being_updated(show_obj.indexer_id):
                if show_obj.paused:
                    submenu.append({
                        'title': _('Resume'),
                        'path': '/home/togglePause?show=%d' % show_obj.indexer_id,
                        'icon': 'fas fa-play'
                    })
                else:
                    submenu.append({
                        'title': _('Pause'),
                        'path': '/home/togglePause?show=%d' % show_obj.indexer_id,
                        'icon': 'fas fa-pause'
                    })

                submenu.append({
                    'title': _('Remove'),
                    'path': '/home/deleteShow?show=%d' % show_obj.indexer_id,
                    'class': 'removeshow',
                    'confirm': True,
                    'icon': 'fas fa-trash'
                })

                submenu.append({
                    'title': _('Re-scan files'),
                    'path': '/home/refreshShow?show=%d' % show_obj.indexer_id,
                    'icon': 'fas fa-compass'
                })

                submenu.append({
                    'title': _('Full Update'),
                    'path': '/home/updateShow?show=%d&amp;force=1' % show_obj.indexer_id,
                    'icon': 'fas fa-sync'
                })

                submenu.append({
                    'title': _('Update show in KODI'),
                    'path': '/home/updateKODI?show=%d' % show_obj.indexer_id,
                    'requires': self.have_kodi(),
                    'icon': 'fas fa-tv'
                })

                submenu.append({
                    'title': _('Update show in Emby'),
                    'path': '/home/updateEMBY?show=%d' % show_obj.indexer_id,
                    'requires': self.have_emby(),
                    'icon': 'fas fa-tv'
                })

                submenu.append({
                    'title': _('Preview Rename'),
                    'path': '/home/testRename?show=%d' % show_obj.indexer_id,
                    'icon': 'fas fa-tag'
                })

                if sickrage.app.config.use_subtitles and show_obj.subtitles:
                    if not sickrage.app.show_queue.is_being_subtitled(show_obj.indexer_id):
                        submenu.append({
                            'title': _('Download Subtitles'),
                            'path': '/home/subtitleShow?show=%d' % show_obj.indexer_id,
                            'icon': 'fas fa-comment'
                        })

        ep_cats = {}
        ep_counts = {
            Overview.SKIPPED: 0,
            Overview.WANTED: 0,
            Overview.QUAL: 0,
            Overview.GOOD: 0,
            Overview.UNAIRED: 0,
            Overview.SNATCHED: 0,
            Overview.SNATCHED_PROPER: 0,
            Overview.SNATCHED_BEST: 0,
            Overview.MISSED: 0,
        }

        for episode_object in episode_objects:
            cur_ep_cat = show_obj.get_overview(int(episode_object.status or -1))

            if episode_object.airdate > datetime.date.min:
                today = datetime.datetime.now().replace(tzinfo=sickrage.app.tz)
                air_date = episode_object.airdate
                if air_date.year >= 1970 or show_obj.network:
                    air_date = SRDateTime(sickrage.app.tz_updater.parse_date_time(episode_object.airdate, show_obj.airs, show_obj.network), convert=True).dt

                if cur_ep_cat == Overview.WANTED and air_date < today:
                    cur_ep_cat = Overview.MISSED

            if cur_ep_cat:
                ep_cats[str(episode_object.season) + "x" + str(episode_object.episode)] = cur_ep_cat
                ep_counts[cur_ep_cat] += 1

        if sickrage.app.config.anime_split_home:
            shows, anime = [], []
            for show in get_show_list():
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)

            sorted_show_lists = {
                "Shows": sorted(shows, key=lambda x: x.name.upper()),
                "Anime": sorted(anime, key=lambda x: x.name.upper())
            }
        else:
            sorted_show_lists = {
                "Shows": sorted(get_show_list(), key=lambda x: x.name.upper())
            }

        bwl = None
        if show_obj.is_anime:
            bwl = show_obj.release_groups

        show_obj.exceptions = await self.run_task(get_scene_exceptions, show_obj.indexer_id)

        indexer_id = int(show_obj.indexer_id)
        indexer = int(show_obj.indexer)

        # Delete any previous occurrances
        for index, recentShow in enumerate(sickrage.app.config.shows_recent):
            if recentShow['indexer_id'] == indexer_id:
                del sickrage.app.config.shows_recent[index]

        # Only track 5 most recent shows
        del sickrage.app.config.shows_recent[4:]

        # Insert most recent show
        sickrage.app.config.shows_recent.insert(0, {
            'indexer_id': indexer_id,
            'name': show_obj.name,
        })

        return self.render(
            "/home/display_show.mako",
            submenu=submenu,
            showLoc=show_loc,
            show_message=show_message,
            show=show_obj,
            episode_objects=episode_objects,
            seasonResults=season_results,
            sortedShowLists=sorted_show_lists,
            bwl=bwl,
            epCounts=ep_counts,
            epCats=ep_cats,
            all_scene_exceptions=show_obj.exceptions,
            scene_numbering=get_scene_numbering_for_show(indexer_id, indexer, session=self.db_session),
            xem_numbering=get_xem_numbering_for_show(indexer_id, indexer, session=self.db_session),
            scene_absolute_numbering=get_scene_absolute_numbering_for_show(indexer_id, indexer, session=self.db_session),
            xem_absolute_numbering=get_xem_absolute_numbering_for_show(indexer_id, indexer, session=self.db_session),
            title=show_obj.name,
            controller='home',
            action="display_show"
        )

    def have_kodi(self):
        return sickrage.app.config.use_kodi and sickrage.app.config.kodi_update_library

    def have_plex(self):
        return sickrage.app.config.use_plex and sickrage.app.config.plex_update_library

    def have_emby(self):
        return sickrage.app.config.use_emby


class EditShowHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        groups = []

        show_obj = find_show(int(show), session=self.db_session)

        if not show_obj:
            err_string = _("Unable to find the specified show: ") + str(show)
            return self._genericMessage(_("Error"), err_string)

        scene_exceptions = get_scene_exceptions(show_obj.indexer_id)

        if show_obj.is_anime:
            whitelist = show_obj.release_groups.whitelist
            blacklist = show_obj.release_groups.blacklist

            try:
                groups = get_release_groups_for_anime(show_obj.name)
            except AnidbAdbaConnectionException as e:
                sickrage.app.log.debug('Unable to get ReleaseGroups: {}'.format(e))

            return self.render(
                "/home/edit_show.mako",
                show=show_obj,
                quality=show_obj.quality,
                scene_exceptions=scene_exceptions,
                groups=groups,
                whitelist=whitelist,
                blacklist=blacklist,
                title=_('Edit Show'),
                header=_('Edit Show'),
                controller='home',
                action="edit_show"
            )
        else:
            return self.render(
                "/home/edit_show.mako",
                show=show_obj,
                quality=show_obj.quality,
                scene_exceptions=scene_exceptions,
                title=_('Edit Show'),
                header=_('Edit Show'),
                controller='home',
                action="edit_show"
            )

    @authenticated
    async def post(self, *args, **kwargs):
        show = self.get_argument('show')
        location = self.get_argument('location', None)
        any_qualities = self.get_arguments('anyQualities')
        best_qualities = self.get_arguments('bestQualities')
        exceptions_list = self.get_arguments('exceptions_list')
        flatten_folders = self.get_argument('flatten_folders', None)
        paused = self.get_argument('paused', None)
        direct_call = bool(self.get_argument('directCall', None))
        air_by_date = self.get_argument('air_by_date', None)
        sports = self.get_argument('sports', None)
        dvdorder = self.get_argument('dvdorder', None)
        indexer_lang = self.get_argument('indexerLang', None)
        subtitles = self.get_argument('subtitles', None)
        sub_use_sr_metadata = self.get_argument('sub_use_sr_metadata', None)
        skip_downloaded = self.get_argument('skip_downloaded', None)
        rls_ignore_words = self.get_argument('rls_ignore_words', None)
        rls_require_words = self.get_argument('rls_require_words', None)
        anime = self.get_argument('anime', None)
        blacklist = self.get_argument('blacklist', None)
        whitelist = self.get_argument('whitelist', None)
        scene = self.get_argument('scene', None)
        default_ep_status = self.get_argument('defaultEpStatus', None)
        quality_preset = self.get_argument('quality_preset', None)
        search_delay = self.get_argument('search_delay', None)

        show_obj = find_show(int(show), session=self.db_session)

        if not show_obj:
            err_string = _("Unable to find the specified show: ") + str(show)
            if direct_call:
                return self.write(err_string)
            return self._genericMessage(_("Error"), err_string)

        show_obj.exceptions = await self.run_task(get_scene_exceptions, show_obj.indexer_id)

        flatten_folders = not checkbox_to_value(flatten_folders)  # UI inverts this value
        dvdorder = checkbox_to_value(dvdorder)
        skip_downloaded = checkbox_to_value(skip_downloaded)
        paused = checkbox_to_value(paused)
        air_by_date = checkbox_to_value(air_by_date)
        scene = checkbox_to_value(scene)
        sports = checkbox_to_value(sports)
        anime = checkbox_to_value(anime)
        subtitles = checkbox_to_value(subtitles)
        sub_use_sr_metadata = checkbox_to_value(sub_use_sr_metadata)

        if indexer_lang and indexer_lang in IndexerApi(show_obj.indexer).indexer().languages.keys():
            indexer_lang = indexer_lang
        else:
            indexer_lang = show_obj.lang

        # if we changed the language then kick off an update
        if indexer_lang == show_obj.lang:
            do_update = False
        else:
            do_update = True

        if scene == show_obj.scene or anime == show_obj.anime:
            do_update_scene_numbering = False
        else:
            do_update_scene_numbering = True

        show_obj.paused = paused
        show_obj.scene = scene
        show_obj.anime = anime
        show_obj.sports = sports
        show_obj.subtitles = subtitles
        show_obj.sub_use_sr_metadata = sub_use_sr_metadata
        show_obj.air_by_date = air_by_date
        show_obj.default_ep_status = int(default_ep_status)
        show_obj.skip_downloaded = skip_downloaded

        # If directCall from mass_edit_update no scene exceptions handling or blackandwhite list handling
        if direct_call:
            do_update_exceptions = False
        else:
            if set(exceptions_list) == set(show_obj.exceptions):
                do_update_exceptions = False
            else:
                do_update_exceptions = True

            if anime:
                if whitelist:
                    shortwhitelist = short_group_names(whitelist)
                    show_obj.release_groups.set_white_keywords(shortwhitelist)
                else:
                    show_obj.release_groups.set_white_keywords([])

                if blacklist:
                    shortblacklist = short_group_names(blacklist)
                    show_obj.release_groups.set_black_keywords(shortblacklist)
                else:
                    show_obj.release_groups.set_black_keywords([])

        warnings, errors = [], []

        new_quality = try_int(quality_preset, None)
        if not new_quality:
            new_quality = Quality.combine_qualities(list(map(int, any_qualities)), list(map(int, best_qualities)))

        show_obj.quality = new_quality

        # reversed for now
        if bool(show_obj.flatten_folders) != bool(flatten_folders):
            show_obj.flatten_folders = flatten_folders
            try:
                sickrage.app.show_queue.refresh_show(show_obj.indexer_id, True)
            except CantRefreshShowException as e:
                errors.append(_("Unable to refresh this show: {}").format(e))

        if not direct_call:
            show_obj.lang = indexer_lang
            show_obj.dvdorder = dvdorder
            show_obj.rls_ignore_words = rls_ignore_words.strip()
            show_obj.rls_require_words = rls_require_words.strip()
            show_obj.search_delay = int(search_delay)

        # if we change location clear the db of episodes, change it, write to db, and rescan
        if os.path.normpath(show_obj.location) != os.path.normpath(location):
            sickrage.app.log.debug(os.path.normpath(show_obj.location) + " != " + os.path.normpath(location))
            if not os.path.isdir(location) and not sickrage.app.config.create_missing_show_dirs:
                warnings.append("New location {} does not exist".format(location))

            # don't bother if we're going to update anyway
            elif not do_update:
                # change it
                try:
                    show_obj.location = location
                    try:
                        sickrage.app.show_queue.refresh_show(show_obj.indexer_id, True)
                    except CantRefreshShowException as e:
                        errors.append(_("Unable to refresh this show:{}").format(e))
                        # grab updated info from TVDB
                        # showObj.loadEpisodesFromIndexer()
                        # rescan the episodes in the new folder
                except NoNFOException:
                    warnings.append(
                        _("The folder at %s doesn't contain a tvshow.nfo - copy your files to that folder before "
                          "you change the directory in SiCKRAGE.") % location)

        # force the update
        if do_update:
            try:
                sickrage.app.show_queue.update_show(show_obj.indexer_id, force=True)
                await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            except CantUpdateShowException as e:
                errors.append(_("Unable to update show: {}").format(e))

        if do_update_exceptions:
            try:
                update_scene_exceptions(show_obj.indexer_id, exceptions_list)
                await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            except CantUpdateShowException:
                warnings.append(_("Unable to force an update on scene exceptions of the show."))

        if do_update_scene_numbering:
            try:
                xem_refresh(show_obj.indexer_id, show_obj.indexer, True)
                await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            except CantUpdateShowException:
                warnings.append(_("Unable to force an update on scene numbering of the show."))

        if direct_call:
            return self.write(json_encode({'warnings': warnings, 'errors': errors}))

        if len(warnings) > 0:
            sickrage.app.alerts.message(
                _('{num_warnings:d} warning{plural} while saving changes:').format(num_warnings=len(warnings),
                                                                                   plural="" if len(
                                                                                       warnings) == 1 else "s"),
                '<ul>' + '\n'.join(['<li>{0}</li>'.format(warning) for warning in warnings]) + "</ul>")

        if len(errors) > 0:
            sickrage.app.alerts.error(
                _('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors),
                                                                               plural="" if len(errors) == 1 else "s"),
                '<ul>' + '\n'.join(['<li>{0}</li>'.format(error) for error in errors]) + "</ul>")

        return self.redirect("/home/displayShow?show=" + show)


class TogglePauseHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        show_obj.paused = not show_obj.paused

        sickrage.app.alerts.message(
            _('%s has been %s') % (show_obj.name, (_('resumed'), _('paused'))[show_obj.paused]))

        return self.redirect("/home/displayShow?show=%i" % show_obj.indexer_id)


class DeleteShowHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        show = self.get_argument('show')
        full = self.get_argument('full', None)

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        try:
            sickrage.app.show_queue.remove_show(show_obj.indexer_id, bool(full))
            sickrage.app.alerts.message(
                _('%s has been %s %s') %
                (
                    show_obj.name,
                    (_('deleted'), _('trashed'))[bool(sickrage.app.config.trash_remove_show)],
                    (_('(media untouched)'), _('(with all related media)'))[bool(full)]
                )
            )
        except CantRemoveShowException as e:
            sickrage.app.alerts.error(_('Unable to delete this show.'), str(e))

        await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')


class RefreshShowHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        try:
            sickrage.app.show_queue.refresh_show(show_obj.indexer_id, True)
        except CantRefreshShowException as e:
            sickrage.app.alerts.error(_('Unable to refresh this show.'), str(e))

        await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexer_id))


class UpdateShowHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        show = self.get_argument('show')
        force = self.get_argument('force', None)

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # force the update
        try:
            sickrage.app.show_queue.update_show(show_obj.indexer_id, force=bool(force))
        except CantUpdateShowException as e:
            sickrage.app.alerts.error(_("Unable to update this show."), str(e))

        # just give it some time
        await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexer_id))


class SubtitleShowHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # search and download subtitles
        sickrage.app.show_queue.download_subtitles(show_obj.indexer_id)

        await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexer_id))


class UpdateKODIHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_name = None

        show_obj = find_show(int(show), session=self.db_session)
        if show_obj:
            show_name = quote_plus(show_obj.name.encode())

        if show_name:
            if sickrage.app.config.kodi_update_onlyfirst:
                host = sickrage.app.config.kodi_host.split(",")[0].strip()
            else:
                host = sickrage.app.config.kodi_host

            if sickrage.app.notifier_providers['kodi'].update_library(showName=show_name):
                sickrage.app.alerts.message(_("Library update command sent to KODI host(s): ") + host)
            else:
                sickrage.app.alerts.error(_("Unable to contact one or more KODI host(s): ") + host)

        if show_obj:
            return self.redirect('/home/displayShow?show=' + str(show_obj.indexer_id))
        else:
            return self.redirect('/home/')


class UpdatePLEXHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        if not sickrage.app.notifier_providers['plex'].update_library():
            sickrage.app.alerts.message(
                _("Library update command sent to Plex Media Server host: ") +
                sickrage.app.config.plex_server_host)
        else:
            sickrage.app.alerts.error(
                _("Unable to contact Plex Media Server host: ") +
                sickrage.app.config.plex_server_host)
        return self.redirect('/home/')


class UpdateEMBYHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj:
            if sickrage.app.notifier_providers['emby'].update_library(show_obj):
                sickrage.app.alerts.message(
                    _("Library update command sent to Emby host: ") + sickrage.app.config.emby_host)
            else:
                sickrage.app.alerts.error(
                    _("Unable to contact Emby host: ") + sickrage.app.config.emby_host)

            return self.redirect('/home/displayShow?show=' + str(show_obj.indexer_id))
        else:
            return self.redirect('/home/')


class SyncTraktHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        if sickrage.app.scheduler.get_job('TRAKTSEARCHER').func():
            sickrage.app.log.info("Syncing Trakt with SiCKRAGE")
            sickrage.app.alerts.message(_('Syncing Trakt with SiCKRAGE'))

        return self.redirect("/home/")


class DeleteEpisodeHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        eps = self.get_argument('eps')
        direct = self.get_argument('direct', None)

        show_obj = find_show(int(show), session=self.db_session)

        if not show_obj:
            err_msg = _("Error", "Show not in show list")
            if direct:
                sickrage.app.alerts.error(_('Error'), err_msg)
                return self.write(json_encode({'result': 'error'}))
            else:
                return self._genericMessage(_("Error"), err_msg)

        if eps:
            for curEp in eps.split('|'):
                if not curEp:
                    sickrage.app.log.debug("curEp was empty when trying to deleteEpisode")

                sickrage.app.log.debug("Attempting to delete episode " + curEp)

                ep_info = curEp.split('x')

                if not all(ep_info):
                    sickrage.app.log.debug(
                        "Something went wrong when trying to deleteEpisode, epInfo[0]: %s, epInfo[1]: %s" % (
                            ep_info[0], ep_info[1]))
                    continue

                try:
                    ep_obj = show_obj.get_episode(int(ep_info[0]), int(ep_info[1]))
                except EpisodeNotFoundException as e:
                    return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))

                try:
                    ep_obj.delete_episode(full=True)
                except EpisodeDeletedException:
                    pass

        if direct:
            return self.write(json_encode({'result': 'success'}))
        else:
            return self.redirect("/home/displayShow?show=" + show)


class SetStatusHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        eps = self.get_argument('eps')
        status = self.get_argument('status')
        direct = bool(self.get_argument('direct', None))

        if int(status) not in statusStrings:
            err_msg = _("Invalid status")
            if direct:
                sickrage.app.alerts.error(_('Error'), err_msg)
                return self.write(json_encode({'result': 'error'}))
            else:
                return self._genericMessage(_("Error"), err_msg)

        show_obj = find_show(int(show), session=self.db_session)

        if not show_obj:
            err_msg = _("Error", "Show not in show list")
            if direct:
                sickrage.app.alerts.error(_('Error'), err_msg)
                return self.write(json_encode({'result': 'error'}))
            else:
                return self._genericMessage(_("Error"), err_msg)

        wanted = []
        trakt_data = []

        if eps:
            for curEp in eps.split('|'):
                if not curEp:
                    sickrage.app.log.debug("curEp was empty when trying to setStatus")

                sickrage.app.log.debug("Attempting to set status on episode " + curEp + " to " + status)

                ep_info = curEp.split('x')

                if not all(ep_info):
                    sickrage.app.log.debug("Something went wrong when trying to setStatus, epInfo[0]: %s, epInfo[1]: %s" % (ep_info[0], ep_info[1]))
                    continue

                try:
                    episode_object = show_obj.get_episode(int(ep_info[0]), int(ep_info[1]))
                except EpisodeNotFoundException as e:
                    return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))

                if int(status) in [WANTED, FAILED]:
                    # figure out what episodes are wanted so we can backlog them
                    wanted += [(episode_object.season, episode_object.episode)]

                # don't let them mess up UNAIRED episodes
                if episode_object.status == UNAIRED:
                    sickrage.app.log.warning("Refusing to change status of " + curEp + " because it is UNAIRED")
                    continue

                if int(status) in Quality.DOWNLOADED and episode_object.status not in Quality.SNATCHED + \
                        Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + [IGNORED] and not os.path.isfile(episode_object.location):
                    sickrage.app.log.warning("Refusing to change status of " + curEp + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED")
                    continue

                if int(status) == FAILED and episode_object.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + \
                        Quality.SNATCHED_BEST + Quality.DOWNLOADED + Quality.ARCHIVED:
                    sickrage.app.log.warning("Refusing to change status of " + curEp + " to FAILED because it's not SNATCHED/DOWNLOADED")
                    continue

                if episode_object.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                    sickrage.app.log.info("Removing release_name for episode as you want to set a downloaded "
                                          "episode back to wanted, so obviously you want it replaced")
                    episode_object.release_name = ""

                episode_object.status = int(status)

                trakt_data += [(episode_object.season, episode_object.episode)]

            data = sickrage.app.notifier_providers['trakt'].trakt_episode_data_generate(trakt_data)
            if data and sickrage.app.config.use_trakt and sickrage.app.config.trakt_sync_watchlist:
                if int(status) in [WANTED, FAILED]:
                    sickrage.app.log.debug(
                        "Add episodes, showid: indexer_id " + str(show_obj.indexer_id) + ", Title " + str(show_obj.name) + " to Watchlist")
                    sickrage.app.notifier_providers['trakt'].update_watchlist(show_obj, data_episode=data, update="add")
                elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                    sickrage.app.log.debug(
                        "Remove episodes, showid: indexer_id " + str(show_obj.indexer_id) + ", Title " + str(show_obj.name) + " from Watchlist")
                    sickrage.app.notifier_providers['trakt'].update_watchlist(show_obj, data_episode=data, update="remove")

        if int(status) == WANTED and not show_obj.paused:
            msg = _("Backlog was automatically started for the following seasons of ") + "<b>" + show_obj.name + "</b>:<br>"
            msg += '<ul>'

            for season, episode in wanted:
                if (show_obj.indexer_id, season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                    sickrage.app.search_queue.SNATCH_HISTORY.remove((show_obj.indexer_id, season, episode))

                sickrage.app.io_loop.add_callback(sickrage.app.search_queue.put, BacklogQueueItem(show_obj.indexer_id, season, episode))
                msg += "<li>" + _("Season ") + str(season) + "</li>"
                sickrage.app.log.info("Sending backlog for " + show_obj.name + " season " + str(season) + " because some eps were set to wanted")

            msg += "</ul>"

            if wanted:
                sickrage.app.alerts.message(_("Backlog started"), msg)
        elif int(status) == WANTED and show_obj.paused:
            sickrage.app.log.info("Some episodes were set to wanted, but {} is paused. Not adding to Backlog until "
                                  "show is unpaused".format(show_obj.name))

        if int(status) == FAILED:
            msg = _(
                "Retrying Search was automatically started for the following season of ") + "<b>" + show_obj.name + "</b>:<br>"
            msg += '<ul>'

            for season, episode in wanted:
                if (show_obj.indexer_id, season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                    sickrage.app.search_queue.SNATCH_HISTORY.remove((show_obj.indexer_id, season, episode))

                sickrage.app.io_loop.add_callback(sickrage.app.search_queue.put, FailedQueueItem(show_obj.indexer_id, season, episode))

                msg += "<li>" + _("Season ") + str(season) + "</li>"
                sickrage.app.log.info("Retrying Search for {} season {} because some eps were set to failed".format(show_obj.name, season))

            msg += "</ul>"

            if wanted:
                sickrage.app.alerts.message(_("Retry Search started"), msg)

        if direct:
            return self.write(json_encode({'result': 'success'}))
        else:
            return self.redirect("/home/displayShow?show=" + show)


class TestRenameHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_object = find_show(int(show), session=self.db_session)

        if show_object is None:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        if not os.path.isdir(show_object.location):
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        episode_objects = []

        for cur_ep_obj in show_object.get_all_episodes(has_location=True):
            if cur_ep_obj.location:
                if cur_ep_obj.related_episodes:
                    for cur_related_ep in cur_ep_obj.related_episodes + [cur_ep_obj]:
                        if cur_related_ep in episode_objects:
                            break
                        episode_objects.append(cur_ep_obj)
                else:
                    episode_objects.append(cur_ep_obj)

        if episode_objects:
            episode_objects.reverse()

        submenu = [
            {'title': _('Edit'), 'path': '/home/editShow?show=%d' % show_object.indexer_id,
             'icon': 'fas fa-edit'}]

        return self.render(
            "/home/test_renaming.mako",
            submenu=submenu,
            episode_objects=episode_objects,
            show=show_object,
            title=_('Preview Rename'),
            header=_('Preview Rename'),
            controller='home',
            action="test_renaming"
        )


class DoRenameHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        eps = self.get_argument('eps')

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj is None:
            err_msg = _("Show not in show list")
            return self._genericMessage(_("Error"), err_msg)

        if not os.path.isdir(show_obj.location):
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        if eps is None:
            return self.redirect("/home/displayShow?show=" + show)

        for curEp in eps.split('|'):
            ep_info = curEp.split('x')

            try:
                ep_result = self.db_session.query(TVEpisode).filter_by(showid=int(show), season=int(ep_info[0]), episode=int(ep_info[1])).one()
            except orm.exc.NoResultFound:
                sickrage.app.log.warning("Unable to find an episode for " + curEp + ", skipping")
                continue

            root_ep_obj = show_obj.get_episode(int(ep_info[0]), int(ep_info[1]))
            root_ep_obj.related_episodes = []

            for cur_related_ep in self.db_session.query(TVEpisode).filter_by(location=ep_result.location).filter(TVEpisode.episode != int(ep_info[1])):
                related_ep_obj = show_obj.get_episode(int(cur_related_ep.season), int(cur_related_ep.episode))
                if related_ep_obj not in root_ep_obj.related_episodes:
                    root_ep_obj.related_episodes.append(related_ep_obj)

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)


class SearchEpisodeHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        season = self.get_argument('season')
        episode = self.get_argument('episode')
        down_cur_quality = self.get_argument('downCurQuality')

        # make a queue item for it and put it on the queue
        ep_queue_item = ManualSearchQueueItem(int(show), int(season), int(episode), bool(int(down_cur_quality)))

        sickrage.app.io_loop.add_callback(sickrage.app.search_queue.put, ep_queue_item)
        if not all([ep_queue_item.started, ep_queue_item.success]):
            return self.write(json_encode({'result': 'success'}))

        return self.write(json_encode({'result': 'failure'}))


class GetManualSearchStatusHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show', None)

        # Queued Searches
        search_status = 'Queued'
        episodes = self.get_episodes(show, sickrage.app.search_queue.get_all_items_from_queue(show), search_status)

        # Running Searches
        search_status = 'Searching'
        if sickrage.app.search_queue.is_manual_search_in_progress():
            for search_thread in sickrage.app.search_queue.processing:
                if search_thread.success:
                    search_status = 'Finished'
                episodes += self.get_episodes(show, [search_thread], search_status)

        # Finished Searches
        search_status = 'Finished'
        for search_thread in sickrage.app.search_queue.MANUAL_SEARCH_HISTORY:
            if show is not None:
                if not str(search_thread.show_id) == show:
                    continue

            if isinstance(search_thread, (ManualSearchQueueItem, FailedQueueItem)):
                if not [x for x in episodes if x['season'] == search_thread.season and x['episode'] == search_thread.episode]:
                    episodes += self.get_episodes(show, [search_thread], search_status)
            else:
                # These are only Failed Downloads/Retry SearchThreadItems.. lets loop through the episodes
                if not [i for i, j in zip(search_thread, episodes) if i.season == j['season'] and i.episode == j['episode']]:
                    episodes += self.get_episodes(show, [search_thread], search_status)

        return self.write(json_encode({'episodes': episodes}))

    def get_episodes(self, show_id, items, search_status):
        results = []

        if not show_id:
            return results

        show_object = find_show(show_id, session=self.db_session)
        if not show_object:
            return results

        for item in items:
            try:
                episode_object = show_object.get_episode(item.season, item.episode)
            except EpisodeNotFoundException:
                continue

            results.append({'show': show_id,
                            'season': episode_object.season,
                            'episode': episode_object.episode,
                            'searchstatus': search_status,
                            'status': statusStrings[episode_object.status],
                            'quality': self.get_quality_class(episode_object.status),
                            'overview': Overview.overviewStrings[show_object.get_overview(int(episode_object.status or -1))]})

        return results

    def get_quality_class(self, status):
        __, ep_quality = Quality.split_composite_status(status)
        if ep_quality in Quality.cssClassStrings:
            quality_class = Quality.cssClassStrings[ep_quality]
        else:
            quality_class = Quality.cssClassStrings[Quality.UNKNOWN]

        return quality_class


class SearchEpisodeSubtitlesHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        season = self.get_argument('season')
        episode = self.get_argument('episode')

        ep_obj = _get_episode(show, season, episode, session=self.db_session)
        if isinstance(ep_obj, TVEpisode):
            try:
                subs = ep_obj.download_subtitles()
            except Exception as e:
                return self.write(json_encode({'result': 'failure'}))

            if subs:
                languages = [Subtitles().name_from_code(sub) for sub in subs]
                status = _('New subtitles downloaded: %s') % ', '.join([lang for lang in languages])
            else:
                status = _('No subtitles downloaded')

            sickrage.app.alerts.message(ep_obj.show.name, status)
            return self.write(json_encode({'result': status, 'subtitles': ','.join(ep_obj.subtitles)}))

        return self.write(json_encode({'result': 'failure'}))


class SetSceneNumberingHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        indexer = self.get_argument('indexer')
        for_season = self.get_argument('forSeason', '')
        for_episode = self.get_argument('forEpisode', '')
        for_absolute = self.get_argument('forAbsolute', '')
        scene_season = self.get_argument('sceneSeason', '')
        scene_episode = self.get_argument('sceneEpisode', '')
        scene_absolute = self.get_argument('sceneAbsolute', '')

        # sanitize:
        if for_season in ['null', '']:
            for_season = None
        if for_episode in ['null', '']:
            for_episode = None
        if for_absolute in ['null', '']:
            for_absolute = None
        if scene_season in ['null', '']:
            scene_season = None
        if scene_episode in ['null', '']:
            scene_episode = None
        if scene_absolute in ['null', '']:
            scene_absolute = None

        show_obj = find_show(int(show), session=self.db_session)

        if show_obj.is_anime:
            result = {
                'success': True,
                'forAbsolute': for_absolute,
            }
        else:
            result = {
                'success': True,
                'forSeason': for_season,
                'forEpisode': for_episode,
            }

        # retrieve the episode object and fail if we can't get one
        if show_obj.is_anime:
            ep_obj = _get_episode(show, absolute=for_absolute, session=self.db_session)
        else:
            ep_obj = _get_episode(show, for_season, for_episode, session=self.db_session)

        if isinstance(ep_obj, str):
            result['success'] = False
            result['errorMessage'] = ep_obj
        elif show_obj.is_anime:
            sickrage.app.log.debug("setAbsoluteSceneNumbering for %s from %s to %s" % (show, for_absolute, scene_absolute))

            show = int(show)
            indexer = int(indexer)
            for_absolute = int(for_absolute)
            if scene_absolute is not None:
                scene_absolute = int(scene_absolute)

            set_scene_numbering(show, indexer, absolute_number=for_absolute, sceneAbsolute=scene_absolute)
        else:
            sickrage.app.log.debug("setEpisodeSceneNumbering for %s from %sx%s to %sx%s" % (show, for_season, for_episode, scene_season, scene_episode))

            show = int(show)
            indexer = int(indexer)
            for_season = int(for_season)
            for_episode = int(for_episode)
            if scene_season is not None:
                scene_season = int(scene_season)
            if scene_episode is not None:
                scene_episode = int(scene_episode)

            set_scene_numbering(show, indexer, season=for_season, episode=for_episode, sceneSeason=scene_season, sceneEpisode=scene_episode)

        if show_obj.is_anime:
            sn = get_scene_absolute_numbering(show, indexer, for_absolute)
            if sn:
                result['sceneAbsolute'] = sn
            else:
                result['sceneAbsolute'] = None
        else:
            sn = get_scene_numbering(show, indexer, for_season, for_episode)
            if sn:
                (result['sceneSeason'], result['sceneEpisode']) = sn
            else:
                (result['sceneSeason'], result['sceneEpisode']) = (None, None)

        return self.write(json_encode(result))


class RetryEpisodeHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        season = self.get_argument('season')
        episode = self.get_argument('episode')
        down_cur_quality = self.get_argument('downCurQuality')

        # retrieve the episode object and fail if we can't get one
        # make a queue item for it and put it on the queue
        ep_queue_item = FailedQueueItem(show, season, episode, bool(int(down_cur_quality)))

        sickrage.app.io_loop.add_callback(sickrage.app.search_queue.put, ep_queue_item)
        if not all([ep_queue_item.started, ep_queue_item.success]):
            return self.write(json_encode({'result': 'success'}))

        return self.write(json_encode({'result': 'failure'}))


class FetchReleasegroupsHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        show_name = self.get_argument('show_name')

        sickrage.app.log.info('ReleaseGroups: {}'.format(show_name))

        try:
            groups = await self.run_task(get_release_groups_for_anime, show_name)
            sickrage.app.log.info('ReleaseGroups: {}'.format(groups))
        except AnidbAdbaConnectionException as e:
            sickrage.app.log.debug('Unable to get ReleaseGroups: {}'.format(e))
        else:
            return self.write(json_encode({'result': 'success', 'groups': groups}))

        return self.write(json_encode({'result': 'failure'}))
