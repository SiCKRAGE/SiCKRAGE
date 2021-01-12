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
from collections import OrderedDict
from time import sleep
from urllib.parse import unquote_plus, quote_plus

from tornado.escape import json_encode
from tornado.httputil import url_concat
from tornado.web import authenticated

import sickrage
from sickrage.clients import get_client_instance
from sickrage.clients.nzb.sabnzbd import SabNZBd
from sickrage.core.common import Overview, Quality, Qualities
from sickrage.core.enums import SeriesProviderID, TorrentMethod, NzbMethod
from sickrage.core.exceptions import (
    AnidbAdbaConnectionException,
    CantRefreshShowException,
    CantUpdateShowException,
    CantRemoveShowException,
    EpisodeDeletedException,
    EpisodeNotFoundException,
    MultipleEpisodesInDatabaseException
)
from sickrage.core.helpers import clean_url, clean_host, clean_hosts, get_disk_space_usage
from sickrage.core.helpers.anidb import get_release_groups_for_anime
from sickrage.core.helpers.srdatetime import SRDateTime
from sickrage.core.queues import TaskStatus
from sickrage.core.queues.search import FailedSearchTask, ManualSearchTask
from sickrage.core.scene_numbering import (
    get_scene_numbering_for_show,
    get_xem_numbering_for_show,
    get_scene_absolute_numbering_for_show,
    get_xem_absolute_numbering_for_show,
    set_scene_numbering,
    get_scene_absolute_numbering,
    get_scene_numbering
)
from sickrage.core.traktapi import TraktAPI
from sickrage.core.tv.show.helpers import find_show, get_show_list
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.subtitles import Subtitles


class HomeHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show_list = [x for x in get_show_list() if not sickrage.app.show_queue.is_being_removed(x.series_id)]

        if not len(show_list):
            return self.redirect('/home/addShows/')

        show_lists = OrderedDict({
            'Shows': [x for x in show_list if x.anime is False],
            'Anime': [x for x in show_list if x.anime is True]
        })

        return self.render('home/index.mako',
                           title="Home",
                           header="Show List",
                           topmenu="home",
                           showlists=show_lists,
                           controller='home',
                           action='index')

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
                'total': len(get_show_list()),
            },
            'total_size': 0
        }

        for show in get_show_list():
            if sickrage.app.show_queue.is_being_added(show.series_id) or sickrage.app.show_queue.is_being_removed(show.series_id):
                show_stat[show.series_id] = {
                    'ep_airs_next': datetime.date.min,
                    'ep_airs_prev': datetime.date.min,
                    'ep_snatched': 0,
                    'ep_downloaded': 0,
                    'ep_total': 0,
                    'total_size': 0
                }
            else:
                show_stat[show.series_id] = {
                    'ep_airs_next': show.airs_next or datetime.date.min,
                    'ep_airs_prev': show.airs_prev or datetime.date.min,
                    'ep_snatched': show.episodes_snatched or 0,
                    'ep_downloaded': show.episodes_downloaded or 0,
                    'ep_total': len(show.episodes),
                    'total_size': show.total_size or 0
                }

            overall_stats['episodes']['snatched'] += show_stat[show.series_id]['ep_snatched']
            overall_stats['episodes']['downloaded'] += show_stat[show.series_id]['ep_downloaded']
            overall_stats['episodes']['total'] += show_stat[show.series_id]['ep_total']
            overall_stats['total_size'] += show_stat[show.series_id]['total_size']

        return show_stat, overall_stats


class ShowProgressHandler(BaseHandler):
    def get(self, *args, **kwargs):
        series_id = self.get_argument('show-id')

        show = find_show(int(series_id))
        if not show:
            return

        episodes_snatched = show.episodes_snatched
        episodes_downloaded = show.episodes_downloaded
        episodes_total = show.episodes_total
        progressbar_percent = int(episodes_downloaded * 100 / episodes_total if episodes_total > 0 else 1)

        progress_text = '?'
        progress_tip = _("no data")
        if episodes_total != 0:
            progress_text = str(episodes_downloaded)
            progress_tip = _("Downloaded: ") + str(episodes_downloaded)
            if episodes_snatched > 0:
                progress_text = progress_text + "+" + str(episodes_snatched)
                progress_tip = progress_tip + "&#013;" + _("Snatched: ") + str(episodes_snatched)

            progress_text = progress_text + " / " + str(episodes_total)
            progress_tip = progress_tip + "&#013;" + _("Total: ") + str(episodes_total)

        return self.write(json_encode({'progress_text': progress_text, 'progress_tip': progress_tip, 'progressbar_percent': progressbar_percent}))


class IsAliveHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/javascript')

        srcallback = self.get_argument('srcallback')

        if not srcallback:
            return self.write(_("Error: Unsupported Request. Send jsonp request with 'srcallback' variable in the query string."))

        return self.write("{}({})".format(srcallback, {'msg': str(sickrage.app.pid) if sickrage.app.started else 'nope'}))


class TestSABnzbdHandler(BaseHandler):
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


class TestSynologyDSMHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_url(self.get_argument('host'))
        nzb_method = self.get_argument('nzb_method')
        username = self.get_argument('username')
        password = self.get_argument('password')

        client = get_client_instance(NzbMethod[nzb_method].value, client_type='nzb')
        __, access_msg = client(host, username, password).test_authentication()
        return self.write(access_msg)


class TestTorrentHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_url(self.get_argument('host'))
        torrent_method = self.get_argument('torrent_method')
        username = self.get_argument('username')
        password = self.get_argument('password')

        client = get_client_instance(TorrentMethod[torrent_method].value, client_type='torrent')
        __, access_msg = client(host, username, password).test_authentication()
        return self.write(access_msg)


class TestFreeMobileHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        freemobile_id = self.get_argument('freemobile_id')
        freemobile_apikey = self.get_argument('freemobile_apikey')

        result, message = sickrage.app.notification_providers['freemobile'].test_notify(freemobile_id, freemobile_apikey)
        if result:
            return self.write(_('SMS sent successfully'))
        return self.write(_('Problem sending SMS: ') + message)


class TestTelegramHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        telegram_id = self.get_argument('telegram_id')
        telegram_apikey = self.get_argument('telegram_apikey')

        result, message = sickrage.app.notification_providers['telegram'].test_notify(telegram_id, telegram_apikey)
        if result:
            return self.write(_('Telegram notification succeeded. Check your Telegram clients to make sure it worked'))
        return self.write(_('Error sending Telegram notification: {message}').format(message=message))


class TestJoinHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        join_id = self.get_argument('join_id')
        join_apikey = self.get_argument('join_apikey')

        result, message = sickrage.app.notification_providers['join'].test_notify(join_id, join_apikey)
        if result:
            return self.write(_('Join notification succeeded. Check your Join clients to make sure it worked'))
        return self.write(_('Error sending Join notification: {message}').format(message=message))


class TestGrowlHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'), default_port=23053)
        password = self.get_argument('password')

        result = sickrage.app.notification_providers['growl'].test_notify(host, password)
        if password is None or password == '':
            pw_append = ''
        else:
            pw_append = _(' with password: ') + password

        if result:
            return self.write(_('Registered and tested Growl successfully ') + unquote_plus(host) + pw_append)
        return self.write(_('Registration and testing of Growl failed ') + unquote_plus(host) + pw_append)


class TestProwlHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        prowl_apikey = self.get_argument('prowl_apikey')
        prowl_priority = self.get_argument('prowl_priority')

        result = sickrage.app.notification_providers['prowl'].test_notify(prowl_apikey, prowl_priority)
        if result:
            return self.write(_('Test prowl notice sent successfully'))
        return self.write(_('Test prowl notice failed'))


class TestBoxcar2Handler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        accesstoken = self.get_argument('accesstoken')

        result = sickrage.app.notification_providers['boxcar2'].test_notify(accesstoken)
        if result:
            return self.write(_('Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked'))
        return self.write(_('Error sending Boxcar2 notification'))


class TestPushoverHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        user_key = self.get_argument('userKey')
        api_key = self.get_argument('apiKey')

        result = sickrage.app.notification_providers['pushover'].test_notify(user_key, api_key)
        if result:
            return self.write(_('Pushover notification succeeded. Check your Pushover clients to make sure it worked'))
        return self.write(_('Error sending Pushover notification'))


class TwitterStep1Handler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.write(sickrage.app.notification_providers['twitter']._get_authorization())


class TwitterStep2Handler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        key = self.get_argument('key')

        result = sickrage.app.notification_providers['twitter']._get_credentials(key)
        sickrage.app.log.info("result: " + str(result))
        if result:
            return self.write(_('Key verification successful'))
        return self.write(_('Unable to verify key'))


class TestTwitterHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        result = sickrage.app.notification_providers['twitter'].test_notify()
        if result:
            return self.write(_('Tweet successful, check your twitter to make sure it worked'))
        return self.write(_('Error sending tweet'))


class TestTwilioHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        account_sid = self.get_argument('account_sid')
        auth_token = self.get_argument('auth_token')
        phone_sid = self.get_argument('phone_sid')
        to_number = self.get_argument('to_number')

        if not sickrage.app.notification_providers['twilio'].account_regex.match(account_sid):
            return self.write(_('Please enter a valid account sid'))

        if not sickrage.app.notification_providers['twilio'].auth_regex.match(auth_token):
            return self.write(_('Please enter a valid auth token'))

        if not sickrage.app.notification_providers['twilio'].phone_regex.match(phone_sid):
            return self.write(_('Please enter a valid phone sid'))

        if not sickrage.app.notification_providers['twilio'].number_regex.match(to_number):
            return self.write(_('Please format the phone number as "+1-###-###-####"'))

        result = sickrage.app.notification_providers['twilio'].test_notify()
        if result:
            return self.write(_('Authorization successful and number ownership verified'))
        return self.write(_('Error sending sms'))


class TestAlexaHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        result = sickrage.app.notification_providers['alexa'].test_notify()
        if result:
            return self.write(_('Alexa notification successful'))
        return self.write(_('Alexa notification failed'))


class TestSlackHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        result = sickrage.app.notification_providers['slack'].test_notify()
        if result:
            return self.write(_('Slack message successful'))
        return self.write(_('Slack message failed'))


class TestDiscordHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        result = sickrage.app.notification_providers['discord'].test_notify()
        if result:
            return self.write(_('Discord message successful'))
        return self.write(_('Discord message failed'))


class TestKODIHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_hosts(self.get_argument('host'))
        username = self.get_argument('username')
        password = self.get_argument('password')

        final_result = ''
        for curHost in [x.strip() for x in host.split(",")]:
            cur_result = sickrage.app.notification_providers['kodi'].test_notify(unquote_plus(curHost), username, password)
            if len(cur_result.split(":")) > 2 and 'OK' in cur_result.split(":")[2]:
                final_result += _('Test KODI notice sent successfully to ') + unquote_plus(curHost)
            else:
                final_result += _('Test KODI notice failed to ') + unquote_plus(curHost)
            final_result += "<br>\n"

        return self.write(final_result)


class TestPMCHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_hosts(self.get_argument('host'))
        username = self.get_argument('username')
        password = self.get_argument('password', None)

        if password and set('*') == set(password):
            password = sickrage.app.config.plex.client_password

        final_result = ''
        for curHost in [x.strip() for x in host.split(',')]:
            cur_result = sickrage.app.notification_providers['plex'].test_notify_pmc(unquote_plus(curHost), username,
                                                                                     password)
            if len(cur_result.split(':')) > 2 and 'OK' in cur_result.split(':')[2]:
                final_result += _('Successful test notice sent to Plex client ... ') + unquote_plus(curHost)
            else:
                final_result += _('Test failed for Plex client ... ') + unquote_plus(curHost)
            final_result += '<br>' + '\n'

        sickrage.app.alerts.message(_('Tested Plex client(s): '),
                                    unquote_plus(host.replace(',', ', ')))

        return self.write(final_result)


class TestPMSHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_hosts(self.get_argument('host'))
        username = self.get_argument('username')
        password = self.get_argument('password', None)
        plex_server_token = self.get_argument('plex_server_token')

        if password and set('*') == set(password):
            password = sickrage.app.config.plex.password

        final_result = ''

        cur_result = sickrage.app.notification_providers['plex'].test_notify_pms(unquote_plus(host), username, password,
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


class TestLibnotifyHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        if sickrage.app.notification_providers['libnotify'].test_notify():
            return self.write(_('Tried sending desktop notification via libnotify'))
        return self.write(sickrage.app.notification_providers['libnotify'].diagnose())


class TestEMBYHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        emby_apikey = self.get_argument('emby_apikey')

        result = sickrage.app.notification_providers['emby'].test_notify(unquote_plus(host), emby_apikey)
        if result:
            return self.write(_('Test notice sent successfully to ') + unquote_plus(host))
        return self.write(_('Test notice failed to ') + unquote_plus(host))


class TestNMJHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        database = self.get_argument('database')
        mount = self.get_argument('mount')

        result = sickrage.app.notification_providers['nmj'].test_notify(unquote_plus(host), database, mount)
        if result:
            return self.write(_('Successfully started the scan update'))
        return self.write(_('Test failed to start the scan update'))


class SettingsNMJHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))

        result = sickrage.app.notification_providers['nmj'].notify_settings(unquote_plus(host))
        if result:
            return self.write(
                '{"message": "%(message)s %(host)s", "database": "%(database)s", "mount": "%(mount)s"}' % {
                    "message": _('Got settings from'),
                    "host": host, "database": sickrage.app.config.nmj.database,
                    "mount": sickrage.app.config.nmj.mount
                })

        message = _('Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for '
                    'detailed info)')

        return self.write('{"message": {}, "database": "", "mount": ""}'.format(message))


class TestNMJv2Handler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))

        result = sickrage.app.notification_providers['nmjv2'].test_notify(unquote_plus(host))
        if result:
            return self.write(_('Test notice sent successfully to ') + unquote_plus(host))
        return self.write(_('Test notice failed to ') + unquote_plus(host))


class SettingsNMJv2Handler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        dbloc = self.get_argument('dbloc')
        instance = self.get_argument('instance')

        result = sickrage.app.notification_providers['nmjv2'].notify_settings(unquote_plus(host), dbloc, instance)
        if result:
            return self.write(
                '{"message": "NMJ Database found at: %(host)s", "database": "%(database)s"}' % {"host": host,
                                                                                                "database": sickrage.app.config.nmjv2.database}
            )
        return self.write(
            '{"message": "Unable to find NMJ Database at location: %(dbloc)s. Is the right location selected and PCH '
            'running?", "database": ""}' % {"dbloc": dbloc}
        )


class GetTraktTokenHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        trakt_pin = self.get_argument('trakt_pin')

        if TraktAPI().authenticate(trakt_pin):
            return self.write(_('Trakt Authorized'))
        return self.write(_('Trakt Not Authorized!'))


class TestTraktHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        username = self.get_argument('username')
        blacklist_name = self.get_argument('blacklist_name')

        return self.write(sickrage.app.notification_providers['trakt'].test_notify(username, blacklist_name))


class LoadShowNotifyListsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        data = {'_size': 0}
        for s in sorted(get_show_list(), key=lambda k: k.name):
            data[s.series_id] = {'id': s.series_id, 'name': s.name, 'list': s.notify_list}
            data['_size'] += 1
        return self.write(json_encode(data))


class SaveShowNotifyListHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        emails = self.get_argument('emails')

        try:
            show = find_show(int(show))
            show.notify_list = emails
        except Exception:
            return self.write('ERROR')


class TestEmailHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        host = clean_host(self.get_argument('host'))
        port = self.get_argument('port')
        smtp_from = self.get_argument('smtp_from')
        use_tls = self.get_argument('use_tls')
        user = self.get_argument('user')
        pwd = self.get_argument('pwd')
        to = self.get_argument('to')

        if sickrage.app.notification_providers['email'].test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return self.write(_('Test email sent successfully! Check inbox.'))
        return self.write(_('ERROR: %s') % sickrage.app.notification_providers['email'].last_err)


class TestNMAHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        nma_api = self.get_argument('nma_api')
        nma_priority = self.get_argument('nma_priority')

        result = sickrage.app.notification_providers['nma'].test_notify(nma_api, nma_priority)
        if result:
            return self.write(_('Test NMA notice sent successfully'))
        return self.write(_('Test NMA notice failed'))


class TestPushalotHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        authorization_token = self.get_argument('authorizationToken')

        result = sickrage.app.notification_providers['pushalot'].test_notify(authorization_token)
        if result:
            return self.write(_('Pushalot notification succeeded. Check your Pushalot clients to make sure it worked'))
        return self.write(_('Error sending Pushalot notification'))


class TestPushbulletHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        api = self.get_argument('api')

        result = sickrage.app.notification_providers['pushbullet'].test_notify(api)
        if result:
            return self.write(_('Pushbullet notification succeeded. Check your device to make sure it worked'))
        return self.write(_('Error sending Pushbullet notification'))


class GetPushbulletDevicesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        api = self.get_argument('api')

        result = sickrage.app.notification_providers['pushbullet'].get_devices(api)
        if result:
            return self.write(result)
        return self.write(_('Error getting Pushbullet devices'))


class ServerStatusHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        tvdir_free = get_disk_space_usage(sickrage.app.config.general.tv_download_dir)
        root_dir = {}
        if sickrage.app.config.general.root_dirs:
            backend_pieces = sickrage.app.config.general.root_dirs.split('|')
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if len(backend_dirs):
            for subject in backend_dirs:
                root_dir[subject] = get_disk_space_usage(subject)

        return self.render('home/server_status.mako',
                           title=_('Server Status'),
                           header=_('Server Status'),
                           topmenu='system',
                           tvdirFree=tvdir_free,
                           rootDir=root_dir,
                           controller='home',
                           action='server_status')


class ProviderStatusHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('home/provider_status.mako',
                           title=_('Provider Status'),
                           header=_('Provider Status'),
                           topmenu='system',
                           controller='home',
                           action='provider_status')


class ShutdownHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')

        if str(pid) != str(sickrage.app.pid):
            return self.redirect("/{}/".format(sickrage.app.config.general.default_page.value))

        self._genericMessage(_("Shutting down"), _("SiCKRAGE is shutting down"))
        sickrage.app.shutdown()


class RestartHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')
        force = self.get_argument('force', None)

        if str(pid) != str(sickrage.app.pid) and not force:
            return self.redirect("/{}/".format(sickrage.app.config.general.default_page.value))

        # clear current user to disable header and footer
        self.current_user = None

        sickrage.app.wserver.io_loop.add_timeout(datetime.timedelta(seconds=5), sickrage.app.shutdown, restart=True)

        # sickrage.app.scheduler.add_job(
        #     sickrage.app.shutdown,
        #     DateTrigger(
        #         run_date=datetime.datetime.utcnow() + datetime.timedelta(seconds=5),
        #         timezone='utc'
        #     ),
        #     kwargs={'restart': True}
        # )

        return self.render('home/restart.mako',
                           title="Home",
                           header="Restarting SiCKRAGE",
                           topmenu="system",
                           controller='home',
                           action="restart")


class UpdateCheckHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')

        if str(pid) != str(sickrage.app.pid) or sickrage.app.disable_updates:
            return self.redirect("/{}/".format(sickrage.app.config.general.default_page.value))

        sickrage.app.alerts.message(_("Updater"), _('Checking for updates'))

        # check for new app updates
        if not sickrage.app.version_updater.check_for_new_version(force=True):
            sickrage.app.alerts.message(_("Updater"), _('No new updates available!'))

        return self.redirect(self.previous_url())


class UpdateHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        pid = self.get_argument('pid')

        if str(pid) != str(sickrage.app.pid):
            return self.redirect("/{}/".format(sickrage.app.config.general.default_page.value))

        sickrage.app.alerts.message(_("Updater"), _('Updating SiCKRAGE'))

        sickrage.app.version_updater.update(webui=True)

        return self.redirect(self.previous_url())


class VerifyPathHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        path = self.get_argument('path')

        if os.path.isfile(path):
            return self.write(_('Successfully found {path}'.format(path=path)))
        return self.write(_('Failed to find {path}'.format(path=path)))


class InstallRequirementsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        sickrage.app.alerts.message(_('Upgrading PIP'))
        if sickrage.app.version_updater.updater.upgrade_pip():
            sickrage.app.alerts.message(_('Upgraded PIP successfully!'))

            sickrage.app.alerts.message(_('Installing SiCKRAGE requirements'))
            if sickrage.app.version_updater.updater.install_requirements(sickrage.app.version_updater.updater.current_branch):
                sickrage.app.alerts.message(_('Installed SiCKRAGE requirements successfully!'))
            else:
                sickrage.app.alerts.message(_('Failed to install SiCKRAGE requirements'))
        else:
            sickrage.app.alerts.message(_('Failed to upgrade PIP'))

        return self.redirect(self.previous_url())


class BranchCheckoutHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        branch = self.get_argument('branch')

        if sickrage.app.version_updater.updater.current_branch != branch:
            sickrage.app.alerts.message(_('Checking out branch: '), branch)
            if sickrage.app.version_updater.updater.checkout_branch(branch):
                sickrage.app.alerts.message(_('Branch checkout successful, restarting: '), branch)
                return self.redirect(url_concat("/home/restart", {'pid': sickrage.app.pid}))
        else:
            sickrage.app.alerts.message(_('Already on branch: '), branch)

        return self.redirect(self.previous_url())


class DisplayShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        submenu = []

        show_obj = find_show(int(show))
        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        episode_objects = sorted(show_obj.episodes, key=lambda x: (x.season, x.episode), reverse=True)
        season_results = set()

        submenu.append({
            'title': _('Edit'),
            'path': '/manage/editShow?show=%d' % show_obj.series_id,
            'icon': 'fas fa-edit'
        })

        show_loc = show_obj.location

        show_message = ''

        if sickrage.app.show_queue.is_being_added(show_obj.series_id):
            show_message = _('This show is in the process of being downloaded - the info below is incomplete.')

        elif sickrage.app.show_queue.is_being_updated(show_obj.series_id):
            show_message = _('The information on this page is in the process of being updated.')

        elif sickrage.app.show_queue.is_being_refreshed(show_obj.series_id):
            show_message = _('The episodes below are currently being refreshed from disk')

        elif sickrage.app.show_queue.is_being_subtitled(show_obj.series_id):
            show_message = _('Currently downloading subtitles for this show')

        elif sickrage.app.show_queue.is_queued_to_refresh(show_obj.series_id):
            show_message = _('This show is queued to be refreshed.')

        elif sickrage.app.show_queue.is_queued_to_update(show_obj.series_id):
            show_message = _('This show is queued and awaiting an update.')

        elif sickrage.app.show_queue.is_queued_to_subtitle(show_obj.series_id):
            show_message = _('This show is queued and awaiting subtitles download.')

        if not sickrage.app.show_queue.is_being_added(show_obj.series_id):
            if not sickrage.app.show_queue.is_being_updated(show_obj.series_id):
                if show_obj.paused:
                    submenu.append({
                        'title': _('Resume'),
                        'path': '/home/togglePause?show=%d' % show_obj.series_id,
                        'icon': 'fas fa-play'
                    })
                else:
                    submenu.append({
                        'title': _('Pause'),
                        'path': '/home/togglePause?show=%d' % show_obj.series_id,
                        'icon': 'fas fa-pause'
                    })

                submenu.append({
                    'title': _('Remove'),
                    'path': '/home/deleteShow?show=%d' % show_obj.series_id,
                    'class': 'removeshow',
                    'confirm': True,
                    'icon': 'fas fa-trash'
                })

                submenu.append({
                    'title': _('Re-scan files'),
                    'path': '/home/refreshShow?show=%d' % show_obj.series_id,
                    'icon': 'fas fa-compass'
                })

                submenu.append({
                    'title': _('Full Update'),
                    'path': '/home/updateShow?show=%d&amp;force=1' % show_obj.series_id,
                    'icon': 'fas fa-sync'
                })

                submenu.append({
                    'title': _('Update show in KODI'),
                    'path': '/home/updateKODI?show=%d' % show_obj.series_id,
                    'requires': self.have_kodi(),
                    'icon': 'fas fa-tv'
                })

                submenu.append({
                    'title': _('Update show in Emby'),
                    'path': '/home/updateEMBY?show=%d' % show_obj.series_id,
                    'requires': self.have_emby(),
                    'icon': 'fas fa-tv'
                })

                submenu.append({
                    'title': _('Preview Rename'),
                    'path': '/home/testRename?show=%d' % show_obj.series_id,
                    'icon': 'fas fa-tag'
                })

                if sickrage.app.config.subtitles.enable and show_obj.subtitles:
                    if not sickrage.app.show_queue.is_being_subtitled(show_obj.series_id):
                        submenu.append({
                            'title': _('Download Subtitles'),
                            'path': '/home/subtitleShow?show=%d' % show_obj.series_id,
                            'icon': 'fas fa-comment'
                        })

        ep_cats = {}
        ep_counts = {
            Overview.SKIPPED: 0,
            Overview.WANTED: 0,
            Overview.LOW_QUALITY: 0,
            Overview.GOOD: 0,
            Overview.UNAIRED: 0,
            Overview.SNATCHED: 0,
            Overview.SNATCHED_PROPER: 0,
            Overview.SNATCHED_BEST: 0,
            Overview.MISSED: 0,
        }

        for episode_object in episode_objects:
            season_results.add(episode_object.season)

            cur_ep_cat = episode_object.overview or -1

            if episode_object.airdate > datetime.date.min:
                today = datetime.datetime.now().replace(tzinfo=sickrage.app.tz).date()
                air_date = episode_object.airdate
                if air_date.year >= 1970 or show_obj.network:
                    air_date = SRDateTime(sickrage.app.tz_updater.parse_date_time(episode_object.airdate, show_obj.airs, show_obj.network),
                                          convert=True).dt.date()

                if cur_ep_cat == Overview.WANTED and air_date < today:
                    cur_ep_cat = Overview.MISSED

            if cur_ep_cat:
                ep_cats[str(episode_object.season) + "x" + str(episode_object.episode)] = cur_ep_cat
                ep_counts[cur_ep_cat] += 1

        if sickrage.app.config.anidb.split_home:
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

        # Insert most recent show
        for index, recentShow in enumerate(sickrage.app.shows_recent):
            if recentShow['series_id'] == show_obj.series_id:
                break
        else:
            sickrage.app.shows_recent.append({
                'series_id': show_obj.series_id,
                'name': show_obj.name,
            })

        return self.render('home/display_show.mako',
                           submenu=submenu,
                           showLoc=show_loc,
                           show_message=show_message,
                           show=show_obj,
                           episode_objects=episode_objects,
                           seasonResults=list(season_results),
                           sortedShowLists=sorted_show_lists,
                           bwl=bwl,
                           epCounts=ep_counts,
                           epCats=ep_cats,
                           scene_numbering=get_scene_numbering_for_show(show_obj.series_id, show_obj.series_provider_id),
                           xem_numbering=get_xem_numbering_for_show(show_obj.series_id, show_obj.series_provider_id),
                           scene_absolute_numbering=get_scene_absolute_numbering_for_show(show_obj.series_id, show_obj.series_provider_id),
                           xem_absolute_numbering=get_xem_absolute_numbering_for_show(show_obj.series_id, show_obj.series_provider_id),
                           title=show_obj.name,
                           controller='home',
                           action="display_show")

    def have_kodi(self):
        return sickrage.app.config.kodi.enable and sickrage.app.config.kodi.update_library

    def have_plex(self):
        return sickrage.app.config.plex.enable and sickrage.app.config.plex.update_library

    def have_emby(self):
        return sickrage.app.config.emby.enable


class TogglePauseHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        session = sickrage.app.main_db.session()
        show_obj = find_show(int(show))

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        show_obj.paused = not show_obj.paused
        show_obj.save()

        sickrage.app.alerts.message(
            _('%s has been %s') % (show_obj.name, (_('resumed'), _('paused'))[show_obj.paused]))

        return self.redirect("/home/displayShow?show=%i" % show_obj.series_id)


class DeleteShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        full = self.get_argument('full', None)

        show_obj = find_show(int(show))

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        try:
            sickrage.app.show_queue.remove_show(show_obj.series_id, show_obj.series_provider_id, bool(full))
            sickrage.app.alerts.message(
                _('%s has been %s %s') %
                (
                    show_obj.name,
                    (_('deleted'), _('trashed'))[bool(sickrage.app.config.general.trash_remove_show)],
                    (_('(media untouched)'), _('(with all related media)'))[bool(full)]
                )
            )
        except CantRemoveShowException as e:
            sickrage.app.alerts.error(_('Unable to delete this show.'), str(e))

        sleep(sickrage.app.config.general.cpu_preset.value)

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')


class RefreshShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_obj = find_show(int(show))

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        try:
            sickrage.app.show_queue.refresh_show(show_obj.series_id, show_obj.series_provider_id, True)
        except CantRefreshShowException as e:
            sickrage.app.alerts.error(_('Unable to refresh this show.'), str(e))

        sleep(sickrage.app.config.general.cpu_preset.value)

        return self.redirect("/home/displayShow?show=" + str(show_obj.series_id))


class UpdateShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        force = self.get_argument('force', None)

        show_obj = find_show(int(show))

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # force the update
        try:
            sickrage.app.show_queue.update_show(show_obj.series_id, show_obj.series_provider_id, force=bool(force))
        except CantUpdateShowException as e:
            sickrage.app.alerts.error(_("Unable to update this show."), str(e))

        # just give it some time
        sleep(sickrage.app.config.general.cpu_preset.value)

        return self.redirect("/home/displayShow?show=" + str(show_obj.series_id))


class SubtitleShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_obj = find_show(int(show))

        if show_obj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # search and download subtitles
        sickrage.app.show_queue.download_subtitles(show_obj.series_id, show_obj.series_provider_id)

        sleep(sickrage.app.config.general.cpu_preset.value)

        return self.redirect("/home/displayShow?show=" + str(show_obj.series_id))


class UpdateKODIHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_name = None

        show_obj = find_show(int(show))
        if show_obj:
            show_name = quote_plus(show_obj.name.encode())

        if show_name:
            if sickrage.app.config.kodi.update_only_first:
                host = sickrage.app.config.kodi.host.split(",")[0].strip()
            else:
                host = sickrage.app.config.kodi.host

            if sickrage.app.notification_providers['kodi'].update_library(showName=show_name):
                sickrage.app.alerts.message(_("Library update command sent to KODI host(s): ") + host)
            else:
                sickrage.app.alerts.error(_("Unable to contact one or more KODI host(s): ") + host)

        if show_obj:
            return self.redirect('/home/displayShow?show=' + str(show_obj.series_id))
        else:
            return self.redirect('/home/')


class UpdatePLEXHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        if not sickrage.app.notification_providers['plex'].update_library():
            sickrage.app.alerts.message(
                _("Library update command sent to Plex Media Server host: ") +
                sickrage.app.config.plex.server_host)
        else:
            sickrage.app.alerts.error(
                _("Unable to contact Plex Media Server host: ") +
                sickrage.app.config.plex.server_host)
        return self.redirect('/home/')


class UpdateEMBYHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_obj = find_show(int(show))

        if show_obj:
            if sickrage.app.notification_providers['emby'].update_library(show_obj):
                sickrage.app.alerts.message(
                    _("Library update command sent to Emby host: ") + sickrage.app.config.emby.host)
            else:
                sickrage.app.alerts.error(
                    _("Unable to contact Emby host: ") + sickrage.app.config.emby.host)

            return self.redirect('/home/displayShow?show=' + str(show_obj.series_id))
        else:
            return self.redirect('/home/')


class SyncTraktHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        sickrage.app.log.info("Syncing Trakt with SiCKRAGE")
        sickrage.app.alerts.message(_('Syncing Trakt with SiCKRAGE'))

        job = sickrage.app.scheduler.get_job(sickrage.app.trakt_searcher.name)
        if job:
            job.modify(next_run_time=datetime.datetime.utcnow(), kwargs={'force': True})
            sickrage.app.wserver.io_loop.add_timeout(datetime.timedelta(seconds=10), job.modify, kwargs={})

        return self.redirect("/home/")


class DeleteEpisodeHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        eps = self.get_argument('eps')
        direct = self.get_argument('direct', None)

        show_obj = find_show(int(show))

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
                if not len(ep_info):
                    continue

                season = int(ep_info[0])
                episode = int(ep_info[1])

                try:
                    if not show_obj.delete_episode(season, episode, full=True):
                        return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))
                except EpisodeDeletedException:
                    pass

        if direct:
            return self.write(json_encode({'result': 'success'}))
        else:
            return self.redirect("/home/displayShow?show=" + show)


class TestRenameHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        show_object = find_show(int(show))

        if show_object is None:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        if not os.path.isdir(show_object.location):
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        episode_objects = []

        for cur_ep_obj in (x for x in show_object.episodes if x.location):
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
            {'title': _('Edit'), 'path': '/manage/editShow?show=%d' % show_object.series_id,
             'icon': 'fas fa-edit'}]

        return self.render('home/test_renaming.mako',
                           submenu=submenu,
                           episode_objects=episode_objects,
                           show=show_object,
                           title=_('Preview Rename'),
                           header=_('Preview Rename'),
                           controller='home',
                           action="test_renaming")


class DoRenameHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        eps = self.get_argument('eps')

        tv_show = find_show(int(show))
        if tv_show is None:
            err_msg = _("Show not in show list")
            return self._genericMessage(_("Error"), err_msg)

        if not os.path.isdir(tv_show.location):
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        if eps is None:
            return self.redirect("/home/displayShow?show=" + show)

        for curEp in eps.split('|'):
            ep_info = curEp.split('x')
            root_ep_season = int(ep_info[0])
            root_ep_episode = int(ep_info[1])

            try:
                root_ep_obj = tv_show.get_episode(season=root_ep_season, episode=root_ep_episode)
            except EpisodeNotFoundException:
                sickrage.app.log.warning("Unable to find an episode for " + curEp + ", skipping")
                continue

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)


class SearchEpisodeHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        series_provider_id = self.get_argument('seriesProviderID')
        season = self.get_argument('season')
        episode = self.get_argument('episode')
        down_cur_quality = self.get_argument('downCurQuality')

        # make a queue item for it and put it on the queue
        ep_queue_item = ManualSearchTask(int(show), SeriesProviderID[series_provider_id], int(season), int(episode), bool(int(down_cur_quality)))

        sickrage.app.search_queue.put(ep_queue_item)
        if not all([ep_queue_item.started, ep_queue_item.success]):
            return self.write(json_encode({'result': 'success'}))

        return self.write(json_encode({'result': 'failure'}))


class GetManualSearchStatusHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        episodes = []

        for task_id, task_items in sickrage.app.search_queue.TASK_HISTORY.copy().items():
            search_task = sickrage.app.search_queue.fetch_task(task_id)
            if not search_task:
                # Finished Manual Searches
                episodes += self.get_episodes(int(show), task_items['season'], task_items['episode'], 'Finished')
                del sickrage.app.search_queue.TASK_HISTORY[task_id]

            if isinstance(search_task, (ManualSearchTask, FailedSearchTask)):
                if search_task.status == TaskStatus.QUEUED:
                    # Queued Manual Searches
                    episodes += self.get_episodes(int(show), task_items['season'], task_items['episode'], 'Queued')
                elif search_task.status == TaskStatus.STARTED:
                    # Running Manual Searches
                    episodes += self.get_episodes(int(show), task_items['season'], task_items['episode'], 'Searching')

        return self.write(json_encode({'episodes': episodes}))

    def get_episodes(self, series_id, season, episode, search_status):
        results = []

        if not series_id:
            return results

        show_object = find_show(series_id)
        if not show_object:
            return results

        try:
            episode_object = show_object.get_episode(season, episode)
        except EpisodeNotFoundException:
            return results

        results.append({'show': series_id,
                        'season': episode_object.season,
                        'episode': episode_object.episode,
                        'searchstatus': search_status,
                        'status': episode_object.status.display_name,
                        'quality': self.get_quality_class(episode_object.status),
                        'overview': episode_object.overview.css_name})

        return results

    def get_quality_class(self, status):
        __, ep_quality = Quality.split_composite_status(status)
        if ep_quality in Qualities:
            quality_class = ep_quality.css_name
        else:
            quality_class = Qualities.UNKNOWN.css_name

        return quality_class


class SearchEpisodeSubtitlesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        season = self.get_argument('season')
        episode = self.get_argument('episode')

        tv_show = find_show(int(show))
        if tv_show is None:
            return _("Invalid show paramaters")

        try:
            tv_episode = tv_show.get_episode(int(season), int(episode))
            subtitles = tv_episode.download_subtitles()

            if subtitles:
                languages = [Subtitles().name_from_code(subtitle) for subtitle in subtitles]
                status = _('New subtitles downloaded: %s') % ', '.join([lang for lang in languages])
            else:
                status = _('No subtitles downloaded')

            sickrage.app.alerts.message(tv_show.name, status)
            return self.write(json_encode({'result': status, 'subtitles': ','.join(tv_episode.subtitles)}))
        except (EpisodeNotFoundException, MultipleEpisodesInDatabaseException):
            return self.write(json_encode({'result': _("Episode couldn't be retrieved")}))
        except Exception:
            return self.write(json_encode({'result': 'failure'}))


class SetSceneNumberingHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        series_provider_id = self.get_argument('series_provider_id')
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

        show_obj = find_show(int(show))
        if show_obj.is_anime:
            result = {
                'success': True,
                'forAbsolute': for_absolute,
                'sceneAbsolute': 0
            }
        else:
            result = {
                'success': True,
                'forSeason': for_season,
                'forEpisode': for_episode,
                'sceneSeason': 0,
                'sceneEpisode': 0
            }

        try:
            if for_absolute is not None:
                show_obj.get_episode(absolute_number=for_absolute)

                show = int(show)
                series_provider_id = SeriesProviderID[series_provider_id]
                for_absolute = int(for_absolute)
                if scene_absolute is not None:
                    scene_absolute = int(scene_absolute)

                if set_scene_numbering(show, series_provider_id, absolute_number=for_absolute, scene_absolute=scene_absolute):
                    sickrage.app.log.debug("setAbsoluteSceneNumbering for %s from %s to %s" % (show, for_absolute, scene_absolute))
                    if scene_absolute is not None:
                        result['sceneAbsolute'] = get_scene_absolute_numbering(show, series_provider_id, for_absolute)
                else:
                    result['errorMessage'] = _("Another episode already has the same scene absolute numbering")
                    result['success'] = False
            else:
                show_obj.get_episode(season=for_season, episode=for_episode)

                show = int(show)
                series_provider_id = SeriesProviderID[series_provider_id]
                for_season = int(for_season)
                for_episode = int(for_episode)
                if scene_season is not None:
                    scene_season = int(scene_season)
                if scene_episode is not None:
                    scene_episode = int(scene_episode)

                if set_scene_numbering(show, series_provider_id, season=for_season, episode=for_episode, scene_season=scene_season,
                                       scene_episode=scene_episode):
                    sickrage.app.log.debug(
                        "setEpisodeSceneNumbering for %s from %sx%s to %sx%s" % (show, for_season, for_episode, scene_season, scene_episode))
                    if scene_season is not None and scene_episode is not None:
                        result['sceneSeason'], result['sceneEpisode'] = get_scene_numbering(show, series_provider_id, for_season, for_episode)
                else:
                    result['errorMessage'] = _("Another episode already has the same scene numbering")
                    result['success'] = False
        except EpisodeNotFoundException:
            result['errorMessage'] = _("Episode couldn't be retrieved")
            result['success'] = False

        return self.write(json_encode(result))


class RetryEpisodeHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        series_provider_id = self.get_argument('seriesProviderID')
        season = self.get_argument('season')
        episode = self.get_argument('episode')
        down_cur_quality = self.get_argument('downCurQuality')

        # retrieve the episode object and fail if we can't get one
        # make a queue item for it and put it on the queue
        ep_queue_item = FailedSearchTask(int(show), SeriesProviderID[series_provider_id], int(season), int(episode), bool(int(down_cur_quality)))

        sickrage.app.search_queue.put(ep_queue_item)
        if not all([ep_queue_item.started, ep_queue_item.success]):
            return self.write(json_encode({'result': 'success'}))

        return self.write(json_encode({'result': 'failure'}))


class FetchReleasegroupsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show_name = self.get_argument('show_name')

        sickrage.app.log.info('ReleaseGroups: {}'.format(show_name))

        try:
            groups = get_release_groups_for_anime(show_name)
            sickrage.app.log.info('ReleaseGroups: {}'.format(groups))
        except AnidbAdbaConnectionException as e:
            sickrage.app.log.debug('Unable to get ReleaseGroups: {}'.format(e))
        else:
            return self.write(json_encode({'result': 'success', 'groups': groups}))

        return self.write(json_encode({'result': 'failure'}))
