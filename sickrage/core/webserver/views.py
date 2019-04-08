# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import os
import re
import time
import traceback
from collections import OrderedDict
from functools import cmp_to_key
from urllib.parse import urljoin, urlparse, unquote_plus, quote_plus

import dateutil.tz
import markdown2
import tornado.gen
import tornado.locale
from keycloak.exceptions import KeycloakClientError
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup
from requests import HTTPError
from sqlalchemy import orm, or_
from tornado.escape import json_encode, recursive_unicode
from tornado.web import RequestHandler, authenticated

import sickrage
import sickrage.subtitles
from sickrage.clients import getClientIstance
from sickrage.clients.sabnzbd import SabNZBd
from sickrage.core.api import API
from sickrage.core.blackandwhitelist import BlackAndWhiteList
from sickrage.core.classes import ErrorViewer, AllShowsUI
from sickrage.core.classes import WarningViewer
from sickrage.core.common import FAILED, IGNORED, Overview, Quality, SKIPPED, \
    SNATCHED, UNAIRED, WANTED, cpu_presets, statusStrings
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import CantRefreshShowException, \
    CantUpdateShowException, EpisodeDeletedException, \
    NoNFOException, CantRemoveShowException, AnidbAdbaConnectionException
from sickrage.core.helpers import argToBool, backupSR, chmod_as_parent, findCertainShow, generateApiKey, \
    getDiskSpaceUsage, makeDir, readFileBuffered, \
    remove_article, restoreConfigZip, \
    sanitizeFileName, clean_url, try_int, torrent_webui_url, checkbox_to_value, clean_host, \
    clean_hosts, app_statistics, encryption
from sickrage.core.helpers.anidb import short_group_names, get_release_groups_for_anime
from sickrage.core.helpers.browser import foldersAtPath
from sickrage.core.helpers.srdatetime import srDateTime
from sickrage.core.imdb_popular import imdbPopular
from sickrage.core.nameparser import validator
from sickrage.core.queues.search import BacklogQueueItem, FailedQueueItem, \
    MANUAL_SEARCH_HISTORY, ManualSearchQueueItem
from sickrage.core.scene_exceptions import get_scene_exceptions, update_scene_exceptions
from sickrage.core.scene_numbering import get_scene_absolute_numbering, \
    get_scene_absolute_numbering_for_show, get_scene_numbering, \
    get_scene_numbering_for_show, get_xem_absolute_numbering_for_show, \
    get_xem_numbering_for_show, set_scene_numbering, xem_refresh
from sickrage.core.traktapi import srTraktAPI
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show.coming_episodes import ComingEpisodes
from sickrage.core.tv.show.history import History as HistoryTool
from sickrage.core.webserver import ApiHandler
from sickrage.core.webserver.routes import Route
from sickrage.indexers import IndexerApi
from sickrage.providers import NewznabProvider, TorrentRssProvider


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.startTime = time.time()

        # template settings
        self.mako_lookup = TemplateLookup(
            directories=[sickrage.app.config.gui_views_dir],
            module_directory=os.path.join(sickrage.app.cache_dir, 'mako'),
            filesystem_checks=True,
            strict_undefined=True,
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace',
            future_imports=['unicode_literals']
        )

    def get_user_locale(self):
        return tornado.locale.get(sickrage.app.config.gui_lang)

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if sickrage.app.config.web_root and self.request.uri.startswith(sickrage.app.config.web_root):
                url = url[len(sickrage.app.config.web_root) + 1:]

            if url[:3] != 'api':
                self.write(self.render(
                    '/errors/404.mako',
                    title=_('HTTP Error 404'),
                    header=_('HTTP Error 404')))
            else:
                self.write('Wrong API key used')
        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br>" % line for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br>" % (k, self.request.__dict__[k]) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            sickrage.app.log.error(error)

            self.set_header('Content-Type', 'text/html')
            self.write("""<html>
                             <title>{error}</title>
                             <body>
                                <button onclick="window.location='{webroot}/logs/';">View Log(Errors)</button>
                                <button onclick="window.location='{webroot}/home/restart?force=1';">Restart SiCKRAGE</button>
                                <button onclick="window.location='{webroot}/logout';">Logout</button>
                                <h2>Error</h2>
                                <p>{error}</p>
                                <h2>Traceback</h2>
                                <p>{traceback}</p>
                                <h2>Request Info</h2>
                                <p>{request}</p>
                             </body>
                           </html>""".format(error=error,
                                             traceback=trace_info,
                                             request=request_info,
                                             webroot=sickrage.app.config.web_root))

    def get_current_user(self):
        try:
            try:
                return sickrage.app.oidc_client.userinfo(self.get_secure_cookie('sr_access_token'))
            except (KeycloakClientError, HTTPError):
                token = sickrage.app.oidc_client.refresh_token(self.get_secure_cookie('sr_refresh_token'))
                self.set_secure_cookie('sr_access_token', token['access_token'])
                self.set_secure_cookie('sr_refresh_token', token['refresh_token'])
                return sickrage.app.oidc_client.userinfo(token['access_token'])
        except Exception as e:
            pass

    def render_string(self, template_name, **kwargs):
        template_kwargs = {
            'title': "",
            'header': "",
            'topmenu': "",
            'submenu': "",
            'controller': "home",
            'action': "index",
            'srPID': sickrage.app.pid,
            'srHttpsEnabled': sickrage.app.config.enable_https or bool(
                self.request.headers.get('X-Forwarded-Proto') == 'https'),
            'srHost': self.request.headers.get('X-Forwarded-Host', self.request.host.split(':')[0]),
            'srHttpPort': self.request.headers.get('X-Forwarded-Port', sickrage.app.config.web_port),
            'srHttpsPort': sickrage.app.config.web_port,
            'srHandleReverseProxy': sickrage.app.config.handle_reverse_proxy,
            'srThemeName': sickrage.app.config.theme_name,
            'srDefaultPage': sickrage.app.config.default_page,
            'srWebRoot': sickrage.app.config.web_root,
            'srLocale': self.get_user_locale().code,
            'srLocaleDir': sickrage.LOCALE_DIR,
            'numErrors': len(ErrorViewer.errors),
            'numWarnings': len(WarningViewer.errors),
            'srStartTime': self.startTime,
            'makoStartTime': time.time(),
            'overall_stats': None,
            'torrent_webui_url': torrent_webui_url(),
            'application': self.application,
            'request': self.request,
        }

        template_kwargs.update(self.get_template_namespace())
        template_kwargs.update(kwargs)

        try:
            return self.mako_lookup.get_template(template_name).render_unicode(**template_kwargs)
        except Exception:
            kwargs['title'] = _('HTTP Error 500')
            kwargs['header'] = _('HTTP Error 500')
            kwargs['backtrace'] = RichTraceback()
            template_kwargs.update(kwargs)

            sickrage.app.log.error(
                "%s: %s" % (str(kwargs['backtrace'].error.__class__.__name__), kwargs['backtrace'].error))

            return self.mako_lookup.get_template('/errors/500.mako').render_unicode(**template_kwargs)

    def render(self, template_name, **kwargs):
        return self.render_string(template_name, **kwargs)

    def worker(self, function, **kwargs):
        kwargs = recursive_unicode(kwargs)
        for arg, value in kwargs.items():
            if len(value) == 1:
                kwargs[arg] = value[0]

        return function(**kwargs)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

    def redirect(self, url, permanent=True, status=None):
        if sickrage.app.config.web_root not in url:
            url = urljoin(sickrage.app.config.web_root + '/', url.lstrip('/'))
        super(BaseHandler, self).redirect(url, permanent, status)

    def previous_url(self):
        url = urlparse(self.request.headers.get("referer", "/{}/".format(sickrage.app.config.default_page)))
        return url._replace(scheme="", netloc="").geturl()


class WebHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(WebHandler, self).__init__(*args, **kwargs)

    @authenticated
    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        result = self.route()
        if result:
            self.write(result)

    @authenticated
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        result = self.route()
        if result:
            self.write(result)

    def route(self):
        # route -> method obj
        method = getattr(
            self, self.request.path.strip('/').split('/')[::-1][0].replace('.', '_'),
            getattr(self, 'index', None)
        )

        if method:
            return self.worker(method, **self.request.arguments)

    def _genericMessage(self, subject, message):
        return self.render(
            "/generic_message.mako",
            message=message,
            subject=subject,
            title="",
            controller='root',
            action='genericmessage'
        )


class LoginHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(LoginHandler, self).__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        redirect_uri = "{}://{}{}/login".format(self.request.protocol, self.request.host, sickrage.app.config.web_root)

        code = self.get_argument('code', False)
        if code:
            try:
                token = sickrage.app.oidc_client.authorization_code(code, redirect_uri)
                userinfo = sickrage.app.oidc_client.userinfo(token['access_token'])

                self.set_secure_cookie('sr_access_token', token['access_token'])
                self.set_secure_cookie('sr_refresh_token', token['refresh_token'])

                if not userinfo.get('sub'):
                    return self.redirect('/logout')

                if not sickrage.app.config.app_sub:
                    sickrage.app.config.app_sub = userinfo.get('sub')
                    sickrage.app.config.save()
                elif sickrage.app.config.app_sub != userinfo.get('sub'):
                    if API().token:
                        allowed_usernames = API().allowed_usernames()['data']
                        if not userinfo['preferred_username'] in allowed_usernames:
                            sickrage.app.log.debug(
                                "USERNAME:{} IP:{} - ACCESS DENIED".format(userinfo['preferred_username'],
                                                                           self.request.remote_ip)
                            )
                            return self.redirect('/logout')
                    else:
                        return self.redirect('/logout')

                if not API().token:
                    exchange = {'scope': 'offline_access', 'subject_token': token['access_token']}
                    API().token = sickrage.app.oidc_client.token_exchange(**exchange)
                    encryption.initialize()
            except Exception as e:
                return self.redirect('/logout')

            redirect_uri = self.get_argument('next', "/{}/".format(sickrage.app.config.default_page))
            return self.redirect("{}".format(redirect_uri))
        else:
            authorization_url = sickrage.app.oidc_client.authorization_url(redirect_uri=redirect_uri)
            return super(BaseHandler, self).redirect(authorization_url)


class LogoutHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(LogoutHandler, self).__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        logout_uri = sickrage.app.oidc_client.get_url('end_session_endpoint')
        redirect_uri = "{}://{}{}/login".format(self.request.protocol, self.request.host, sickrage.app.config.web_root)

        if self.get_secure_cookie('sr_refresh_token'):
            sickrage.app.oidc_client.logout(self.get_secure_cookie('sr_refresh_token'))

        self.clear_all_cookies()

        return super(BaseHandler, self).redirect('{}?redirect_uri={}'.format(logout_uri, redirect_uri))


class CalendarHandler(BaseHandler):
    def prepare(self, *args, **kwargs):
        if sickrage.app.config.calendar_unprotected:
            self.write(self.calendar())
        else:
            self.calendar_auth()

    @authenticated
    def calendar_auth(self):
        self.write(self.calendar())

    # Raw iCalendar implementation by Pedro Jose Pereira Vieito (@pvieito).
    #
    # iCalendar (iCal) - Standard RFC 5545 <http://tools.ietf.org/html/rfc5546>
    # Works with iCloud, Google Calendar and Outlook.
    def calendar(self):
        """ Provides a subscribeable URL for iCal subscriptions
        """

        utc = dateutil.tz.gettz('GMT')

        sickrage.app.log.info("Receiving iCal request from %s" % self.request.remote_ip)

        # Create a iCal string
        ical = 'BEGIN:VCALENDAR\r\n'
        ical += 'VERSION:2.0\r\n'
        ical += 'X-WR-CALNAME:SiCKRAGE\r\n'
        ical += 'X-WR-CALDESC:SiCKRAGE\r\n'
        ical += 'PRODID://SiCKRAGE Upcoming Episodes//\r\n'

        # Limit dates
        past_date = (datetime.date.today() + datetime.timedelta(weeks=-52)).toordinal()
        future_date = (datetime.date.today() + datetime.timedelta(weeks=52)).toordinal()

        # Get all the shows that are not paused and are currently on air (from kjoconnor Fork)
        for show in [x for x in sickrage.app.showlist if
                     x.status.lower() in ['continuing', 'returning series'] and x.paused != 1]:
            for dbData in MainDB.TVEpisode.query.filter_by(showid=int(show.indexerid)).filter(
                    past_date <= MainDB.TVEpisode.airdate < future_date):
                air_date_time = sickrage.app.tz_updater.parse_date_time(dbData.airdate, show.airs,
                                                                        show.network).astimezone(utc)
                air_date_time_end = air_date_time + datetime.timedelta(minutes=try_int(show.runtime, 60))

                # Create event for episode
                ical += 'BEGIN:VEVENT\r\n'
                ical += 'DTSTART:' + air_date_time.strftime("%Y%m%d") + 'T' + air_date_time.strftime("%H%M%S") + 'Z\r\n'
                ical += 'DTEND:' + air_date_time_end.strftime("%Y%m%d") + 'T' + air_date_time_end.strftime(
                    "%H%M%S") + 'Z\r\n'
                if sickrage.app.config.calendar_icons:
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-ICON:https://www.sickrage.ca/favicon.ico\r\n'
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-DISPLAY:CHIP\r\n'
                ical += 'SUMMARY: {0} - {1}x{2} - {3}\r\n'.format(show.name, dbData.season, dbData.episode, dbData.name)
                ical += 'UID:SiCKRAGE-' + str(datetime.date.today().isoformat()) + '-' + \
                        show.name.replace(" ", "-") + '-E' + str(dbData.episode) + \
                        'S' + str(dbData.season) + '\r\n'
                if dbData.description:
                    ical += 'DESCRIPTION: {0} on {1} \\n\\n {2}\r\n'.format(
                        (show.airs or '(Unknown airs)'),
                        (show.network or 'Unknown network'),
                        dbData.description.splitlines()[0])
                else:
                    ical += 'DESCRIPTION:' + (show.airs or '(Unknown airs)') + ' on ' + (
                            show.network or 'Unknown network') + '\r\n'

                ical += 'END:VEVENT\r\n'

        # Ending the iCal
        ical += 'END:VCALENDAR'

        return ical


@Route('(.*)(/?.*)')
class WebRoot(WebHandler):
    def __init__(self, *args, **kwargs):
        super(WebRoot, self).__init__(*args, **kwargs)

    def index(self):
        return self.redirect("/{}/".format(sickrage.app.config.default_page))

    def robots_txt(self):
        """ Keep web crawlers out """
        self.set_header('Content-Type', 'text/plain')
        return "User-agent: *\nDisallow: /"

    def messages_po(self):
        """ Get /sickrage/locale/{lang_code}/LC_MESSAGES/messages.po """
        if sickrage.app.config.gui_lang:
            locale_file = os.path.join(sickrage.LOCALE_DIR, sickrage.app.config.gui_lang, 'LC_MESSAGES/messages.po')
            if os.path.isfile(locale_file):
                with open(locale_file, 'r', encoding='utf8') as f:
                    return f.read()

    def apibuilder(self):
        def titler(x):
            return (remove_article(x), x)[not x or sickrage.app.config.sort_article]

        episodes = {}

        for result in MainDB.TVEpisode.query.order_by(MainDB.TVEpisode.season, MainDB.TVEpisode.episode):

            if result['showid'] not in episodes:
                episodes[result['showid']] = {}

            if result['season'] not in episodes[result['showid']]:
                episodes[result['showid']][result['season']] = []

            episodes[result['showid']][result['season']].append(result['episode'])

        if len(sickrage.app.config.api_key) == 32:
            apikey = sickrage.app.config.api_key
        else:
            apikey = _('API Key not generated')

        return self.render(
            'api_builder.mako',
            title=_('API Builder'),
            header=_('API Builder'),
            shows=sorted(sickrage.app.showlist, key=cmp_to_key(lambda x, y: titler(x.name) < titler(y.name))),
            episodes=episodes,
            apikey=apikey,
            commands=ApiHandler(self.application, self.request).api_calls,
            controller='root',
            action='api_builder'
        )

    def setHomeLayout(self, layout):
        if layout not in ('poster', 'small', 'banner', 'simple', 'coverflow'):
            layout = 'poster'

        sickrage.app.config.home_layout = layout

        # Don't redirect to default page so user can see new layout
        return self.redirect("/home/")

    @staticmethod
    def setPosterSortBy(sort):

        if sort not in ('name', 'date', 'network', 'progress'):
            sort = 'name'

        sickrage.app.config.poster_sortby = sort
        sickrage.app.config.save()

    @staticmethod
    def setPosterSortDir(direction):

        sickrage.app.config.poster_sortdir = int(direction)
        sickrage.app.config.save()

    def setHistoryLayout(self, layout):

        if layout not in ('compact', 'detailed'):
            layout = 'detailed'

        sickrage.app.config.history_layout = layout

        return self.redirect("/history/")

    def toggleDisplayShowSpecials(self, show):

        sickrage.app.config.display_show_specials = not sickrage.app.config.display_show_specials

        return self.redirect("/home/displayShow?show=" + show)

    def setScheduleLayout(self, layout):
        if layout not in ('poster', 'banner', 'list', 'calendar'):
            layout = 'banner'

        if layout == 'calendar':
            sickrage.app.config.coming_eps_sort = 'date'

        sickrage.app.config.coming_eps_layout = layout

        return self.redirect("/schedule/")

    def toggleScheduleDisplayPaused(self):

        sickrage.app.config.coming_eps_display_paused = not sickrage.app.config.coming_eps_display_paused

        return self.redirect("/schedule/")

    def setScheduleSort(self, sort):
        if sort not in ('date', 'network', 'show'):
            sort = 'date'

        if sickrage.app.config.coming_eps_layout == 'calendar':
            sort = 'date'

        sickrage.app.config.coming_eps_sort = sort

        return self.redirect("/schedule/")

    def schedule(self, layout=None):
        next_week = datetime.date.today() + datetime.timedelta(days=7)
        next_week1 = datetime.datetime.combine(next_week,
                                               datetime.datetime.now().time().replace(tzinfo=sickrage.app.tz))
        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories,
                                                     sickrage.app.config.coming_eps_sort,
                                                     False)
        today = datetime.datetime.now().replace(tzinfo=sickrage.app.tz)

        # Allow local overriding of layout parameter
        if layout and layout in ('poster', 'banner', 'list', 'calendar'):
            layout = layout
        else:
            layout = sickrage.app.config.coming_eps_layout

        return self.render(
            'schedule.mako',
            next_week=next_week1,
            today=today,
            results=results,
            layout=layout,
            title=_('Schedule'),
            header=_('Schedule'),
            topmenu='schedule',
            controller='root',
            action='schedule'
        )

    def unlink(self):
        if not sickrage.app.config.app_sub == self.get_current_user().get('sub'):
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        sickrage.app.config.app_sub = ""
        sickrage.app.config.save()

        API().token = sickrage.app.oidc_client.logout(API().token['refresh_token'])

        return self.redirect('/logout/')

    def quicksearch_json(self, term):
        shows = sickrage.app.quicksearch_cache.get_shows(term)
        episodes = sickrage.app.quicksearch_cache.get_episodes(term)

        if not len(shows):
            shows = [{
                'category': 'shows',
                'showid': '',
                'name': term,
                'img': '/images/poster-thumb.png',
                'seasons': 0,
            }]

        return json_encode(str(shows + episodes))


@Route('/browser(/?.*)')
class WebFileBrowser(WebHandler):
    def __init__(self, *args, **kwargs):
        super(WebFileBrowser, self).__init__(*args, **kwargs)

    def index(self, path='', includeFiles=False, fileTypes=''):
        self.set_header('Content-Type', 'application/json')
        return json_encode(foldersAtPath(path, True, bool(int(includeFiles)), fileTypes.split(',')))

    def complete(self, term, includeFiles=False, fileTypes=''):
        self.set_header('Content-Type', 'application/json')
        return json_encode([entry['path'] for entry in foldersAtPath(
            os.path.dirname(term),
            includeFiles=bool(int(includeFiles)),
            fileTypes=fileTypes.split(',')
        ) if 'path' in entry])


@Route('/home(/?.*)')
class Home(WebHandler):
    def __init__(self, *args, **kwargs):
        super(Home, self).__init__(*args, **kwargs)

    @staticmethod
    def _getEpisode(show, season=None, episode=None, absolute=None):
        if show is None:
            return _("Invalid show parameters")

        showObj = findCertainShow(int(show))

        if showObj is None:
            return _("Invalid show paramaters")

        if absolute:
            epObj = showObj.get_episode(absolute_number=int(absolute))
        elif season and episode:
            epObj = showObj.get_episode(int(season), int(episode))
        else:
            return _("Invalid paramaters")

        if epObj is None:
            return _("Episode couldn't be retrieved")

        return epObj

    def index(self):
        if not len(sickrage.app.showlist):
            return self.redirect('/home/addShows/')

        showlists = OrderedDict({'Shows': []})
        if sickrage.app.config.anime_split_home:
            for show in sickrage.app.showlist:
                if show.is_anime:
                    if 'Anime' not in list(showlists.keys()):
                        showlists['Anime'] = []
                    showlists['Anime'] += [show]
                else:
                    showlists['Shows'] += [show]
        else:
            showlists['Shows'] = sickrage.app.showlist

        app_stats = app_statistics()
        return self.render(
            "/home/index.mako",
            title="Home",
            header="Show List",
            topmenu="home",
            showlists=showlists,
            show_stat=app_stats[0],
            overall_stats=app_stats[1],
            max_download_count=app_stats[2],
            controller='home',
            action='index'
        )

    def is_alive(self, *args, **kwargs):
        self.set_header('Content-Type', 'text/javascript')

        if not all([kwargs.get('srcallback'), kwargs.get('_')]):
            return _("Error: Unsupported Request. Send jsonp request with 'srcallback' variable in the query string.")

        if sickrage.app.started:
            return "%s({'msg':%s})" % (kwargs['srcallback'], str(sickrage.app.pid))
        else:
            return "%s({'msg':%s})" % (kwargs['srcallback'], "nope")

    @staticmethod
    def haveKODI():
        return sickrage.app.config.use_kodi and sickrage.app.config.kodi_update_library

    @staticmethod
    def havePLEX():
        return sickrage.app.config.use_plex and sickrage.app.config.plex_update_library

    @staticmethod
    def haveEMBY():
        return sickrage.app.config.use_emby

    @staticmethod
    def haveTORRENT():
        if sickrage.app.config.use_torrents and sickrage.app.config.torrent_method != 'blackhole' and \
                (sickrage.app.config.enable_https and sickrage.app.config.torrent_host[:5] == 'https' or not
                sickrage.app.config.enable_https and sickrage.app.config.torrent_host[:5] == 'http:'):
            return True
        else:
            return False

    @staticmethod
    def testSABnzbd(host=None, username=None, password=None, apikey=None):
        host = clean_url(host)

        connection, accesMsg = SabNZBd.getSabAccesMethod(host)
        if connection:
            authed, authMsg = SabNZBd.test_authentication(host, username, password, apikey)
            if authed:
                return _('Success. Connected and authenticated')
            else:
                return _('Authentication failed. SABnzbd expects ') + accesMsg + _(
                    ' as authentication method, ') + authMsg
        else:
            return _('Unable to connect to host')

    @staticmethod
    def testTorrent(torrent_method=None, host=None, username=None, password=None):

        host = clean_url(host)

        client = getClientIstance(torrent_method)

        __, accesMsg = client(host, username, password).test_authentication()

        return accesMsg

    @staticmethod
    def testFreeMobile(freemobile_id=None, freemobile_apikey=None):

        result, message = sickrage.app.notifier_providers['freemobile'].test_notify(freemobile_id, freemobile_apikey)
        if result:
            return _('SMS sent successfully')
        else:
            return _('Problem sending SMS: ') + message

    @staticmethod
    def testTelegram(telegram_id=None, telegram_apikey=None):

        result, message = sickrage.app.notifier_providers['telegram'].test_notify(telegram_id, telegram_apikey)
        if result:
            return _('Telegram notification succeeded. Check your Telegram clients to make sure it worked')
        else:
            return _('Error sending Telegram notification: {message}').format(message=message)

    @staticmethod
    def testJoin(join_id=None, join_apikey=None):

        result, message = sickrage.app.notifier_providers['join'].test_notify(join_id, join_apikey)
        if result:
            return _('Join notification succeeded. Check your Join clients to make sure it worked')
        else:
            return _('Error sending Join notification: {message}').format(message=message)

    @staticmethod
    def testGrowl(host=None, password=None):
        host = clean_host(host, default_port=23053)

        result = sickrage.app.notifier_providers['growl'].test_notify(host, password)
        if password is None or password == '':
            pw_append = ''
        else:
            pw_append = _(' with password: ') + password

        if result:
            return _('Registered and Tested growl successfully ') + unquote_plus(host) + pw_append
        else:
            return _('Registration and Testing of growl failed ') + unquote_plus(host) + pw_append

    @staticmethod
    def testProwl(prowl_api=None, prowl_priority=0):

        result = sickrage.app.notifier_providers['prowl'].test_notify(prowl_api, prowl_priority)
        if result:
            return _('Test prowl notice sent successfully')
        else:
            return _('Test prowl notice failed')

    @staticmethod
    def testBoxcar2(accesstoken=None):

        result = sickrage.app.notifier_providers['boxcar2'].test_notify(accesstoken)
        if result:
            return _('Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked')
        else:
            return _('Error sending Boxcar2 notification')

    @staticmethod
    def testPushover(userKey=None, apiKey=None):

        result = sickrage.app.notifier_providers['pushover'].test_notify(userKey, apiKey)
        if result:
            return _('Pushover notification succeeded. Check your Pushover clients to make sure it worked')
        else:
            return _('Error sending Pushover notification')

    @staticmethod
    def twitterStep1():
        return sickrage.app.notifier_providers['twitter']._get_authorization()

    @staticmethod
    def twitterStep2(key):

        result = sickrage.app.notifier_providers['twitter']._get_credentials(key)
        sickrage.app.log.info("result: " + str(result))
        if result:
            return _('Key verification successful')
        else:
            return _('Unable to verify key')

    @staticmethod
    def testTwitter():

        result = sickrage.app.notifier_providers['twitter'].test_notify()
        if result:
            return _('Tweet successful, check your twitter to make sure it worked')
        else:
            return _('Error sending tweet')

    @staticmethod
    def testTwilio(account_sid=None, auth_token=None, phone_sid=None, to_number=None):
        if not sickrage.app.notifier_providers['twilio'].account_regex.match(account_sid):
            return _('Please enter a valid account sid')

        if not sickrage.app.notifier_providers['twilio'].auth_regex.match(auth_token):
            return _('Please enter a valid auth token')

        if not sickrage.app.notifier_providers['twilio'].phone_regex.match(phone_sid):
            return _('Please enter a valid phone sid')

        if not sickrage.app.notifier_providers['twilio'].number_regex.match(to_number):
            return _('Please format the phone number as "+1-###-###-####"')

        result = sickrage.app.notifier_providers['twilio'].test_notify()
        if result:
            return _('Authorization successful and number ownership verified')
        else:
            return _('Error sending sms')

    @staticmethod
    def testSlack():
        result = sickrage.app.notifier_providers['slack'].test_notify()
        if result:
            return _('Slack message successful')
        else:
            return _('Slack message failed')

    @staticmethod
    def testDiscord():
        result = sickrage.app.notifier_providers['discord'].test_notify()
        if result:
            return _('Discord message successful')
        else:
            return _('Discord message failed')

    @staticmethod
    def testKODI(host=None, username=None, password=None):

        host = clean_hosts(host)
        finalResult = ''
        for curHost in [x.strip() for x in host.split(",")]:
            curResult = sickrage.app.notifier_providers['kodi'].test_notify(unquote_plus(curHost), username,
                                                                            password)
            if len(curResult.split(":")) > 2 and 'OK' in curResult.split(":")[2]:
                finalResult += _('Test KODI notice sent successfully to ') + unquote_plus(curHost)
            else:
                finalResult += _('Test KODI notice failed to ') + unquote_plus(curHost)
            finalResult += "<br>\n"

        return finalResult

    def testPMC(self, host=None, username=None, password=None):
        if None is not password and set('*') == set(password):
            password = sickrage.app.config.plex_client_password

        finalResult = ''
        for curHost in [x.strip() for x in host.split(',')]:
            curResult = sickrage.app.notifier_providers['plex'].test_notify_pmc(unquote_plus(curHost),
                                                                                username,
                                                                                password)
            if len(curResult.split(':')) > 2 and 'OK' in curResult.split(':')[2]:
                finalResult += _('Successful test notice sent to Plex client ... ') + unquote_plus(curHost)
            else:
                finalResult += _('Test failed for Plex client ... ') + unquote_plus(curHost)
            finalResult += '<br>' + '\n'

        sickrage.app.alerts.message(_('Tested Plex client(s): '),
                                    unquote_plus(host.replace(',', ', ')))

        return finalResult

    def testPMS(self, host=None, username=None, password=None, plex_server_token=None):
        if password is not None and set('*') == set(password):
            password = sickrage.app.config.plex_password

        finalResult = ''

        curResult = sickrage.app.notifier_providers['plex'].test_notify_pms(unquote_plus(host), username,
                                                                            password,
                                                                            plex_server_token)
        if curResult is None:
            finalResult += _('Successful test of Plex server(s) ... ') + \
                           unquote_plus(host.replace(',', ', '))
        elif curResult is False:
            finalResult += _('Test failed, No Plex Media Server host specified')
        else:
            finalResult += _('Test failed for Plex server(s) ... ') + \
                           unquote_plus(str(curResult).replace(',', ', '))
        finalResult += '<br>' + '\n'

        sickrage.app.alerts.message(_('Tested Plex Media Server host(s): '),
                                    unquote_plus(host.replace(',', ', ')))

        return finalResult

    @staticmethod
    def testLibnotify():
        if sickrage.app.notifier_providers['libnotify'].notifier.test_notify():
            return _('Tried sending desktop notification via libnotify')
        else:
            return sickrage.app.notifier_providers['libnotify'].diagnose()

    @staticmethod
    def testEMBY(host=None, emby_apikey=None):
        host = clean_host(host)
        result = sickrage.app.notifier_providers['emby'].test_notify(unquote_plus(host), emby_apikey)
        if result:
            return _('Test notice sent successfully to ') + unquote_plus(host)
        else:
            return _('Test notice failed to ') + unquote_plus(host)

    @staticmethod
    def testNMJ(host=None, database=None, mount=None):
        host = clean_host(host)
        result = sickrage.app.notifier_providers['nmj'].test_notify(unquote_plus(host), database, mount)
        if result:
            return _('Successfully started the scan update')
        else:
            return _('Test failed to start the scan update')

    @staticmethod
    def settingsNMJ(host=None):
        host = clean_host(host)
        result = sickrage.app.notifier_providers['nmj'].notify_settings(unquote_plus(host))
        if result:
            return '{"message": "%(message)s %(host)s", "database": "%(database)s", "mount": "%(mount)s"}' % {
                "message": _('Got settings from'),
                "host": host, "database": sickrage.app.config.nmj_database,
                "mount": sickrage.app.config.nmj_mount
            }
        else:
            message = _('Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for '
                        'detailed info)')
            return '{"message": {}, "database": "", "mount": ""}'.format(message)

    @staticmethod
    def testNMJv2(host=None):
        host = clean_host(host)
        result = sickrage.app.notifier_providers['nmjv2'].test_notify(unquote_plus(host))
        if result:
            return _('Test notice sent successfully to ') + unquote_plus(host)
        else:
            return _('Test notice failed to ') + unquote_plus(host)

    @staticmethod
    def settingsNMJv2(host=None, dbloc=None, instance=None):
        host = clean_host(host)
        result = sickrage.app.notifier_providers['nmjv2'].notify_settings(unquote_plus(host), dbloc,
                                                                          instance)
        if result:
            return '{"message": "NMJ Database found at: %(host)s", "database": "%(database)s"}' % {"host": host,
                                                                                                   "database": sickrage.app.config.nmjv2_database}
        else:
            return '{"message": "Unable to find NMJ Database at location: %(dbloc)s. Is the right location selected and PCH running?", "database": ""}' % {
                "dbloc": dbloc}

    @staticmethod
    def getTraktToken(trakt_pin=None):
        if srTraktAPI().authenticate(trakt_pin):
            return _('Trakt Authorized')
        return _('Trakt Not Authorized!')

    @staticmethod
    def testTrakt(username=None, blacklist_name=None):
        return sickrage.app.notifier_providers['trakt'].test_notify(username, blacklist_name)

    @staticmethod
    def loadShowNotifyLists():
        data = {'_size': 0}
        for s in sorted(sickrage.app.showlist, key=lambda k: k.name):
            data[s.indexerid] = {'id': s.indexerid, 'name': s.name, 'list': s.notify_list}
            data['_size'] += 1
        return json_encode(data)

    @staticmethod
    def saveShowNotifyList(show=None, emails=None):
        try:
            show = findCertainShow(int(show))
            show.notify_list = emails
            show.save_to_db()
        except Exception:
            return 'ERROR'

    @staticmethod
    def testEmail(host=None, port=None, smtp_from=None, use_tls=None, user=None, pwd=None, to=None):
        host = clean_host(host)
        if sickrage.app.notifier_providers['email'].test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return _('Test email sent successfully! Check inbox.')
        else:
            return _('ERROR: %s') % sickrage.app.notifier_providers['email'].last_err

    @staticmethod
    def testNMA(nma_api=None, nma_priority=0):

        result = sickrage.app.notifier_providers['nma'].test_notify(nma_api, nma_priority)
        if result:
            return _('Test NMA notice sent successfully')
        else:
            return _('Test NMA notice failed')

    @staticmethod
    def testPushalot(authorizationToken=None):
        result = sickrage.app.notifier_providers['pushalot'].test_notify(authorizationToken)
        if result:
            return _('Pushalot notification succeeded. Check your Pushalot clients to make sure it worked')
        else:
            return _('Error sending Pushalot notification')

    @staticmethod
    def testPushbullet(api=None):
        result = sickrage.app.notifier_providers['pushbullet'].test_notify(api)
        if result:
            return _('Pushbullet notification succeeded. Check your device to make sure it worked')
        else:
            return _('Error sending Pushbullet notification')

    @staticmethod
    def getPushbulletDevices(api=None):
        result = sickrage.app.notifier_providers['pushbullet'].get_devices(api)
        if result:
            return result
        else:
            return _('Error getting Pushbullet devices')

    def status(self):
        tvdirFree = getDiskSpaceUsage(sickrage.app.config.tv_download_dir)
        rootDir = {}
        if sickrage.app.config.root_dirs:
            backend_pieces = sickrage.app.config.root_dirs.split('|')
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if len(backend_dirs):
            for subject in backend_dirs:
                rootDir[subject] = getDiskSpaceUsage(subject)

        return self.render(
            "/home/status.mako",
            title=_('Status'),
            header=_('Status'),
            topmenu='system',
            tvdirFree=tvdirFree,
            rootDir=rootDir,
            controller='home',
            action='status'
        )

    def shutdown(self, pid=None):
        if str(pid) != str(sickrage.app.pid):
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        self._genericMessage(_("Shutting down"), _("SiCKRAGE is shutting down"))
        sickrage.app.shutdown()

    def restart(self, pid=None, force=False):
        if str(pid) != str(sickrage.app.pid) and not force:
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        # clear current user to disable header and footer
        self.current_user = None

        if not force:
            self._genericMessage(_("Restarting"), _("SiCKRAGE is restarting"))

        sickrage.app.io_loop.add_timeout(datetime.timedelta(seconds=5), sickrage.app.shutdown, restart=True)

        return self.render(
            "/home/restart.mako",
            title="Home",
            header="Restarting SiCKRAGE",
            topmenu="system",
            controller='home',
            action="restart",
        )  # if not force else 'SiCKRAGE is now restarting, please wait a minute then manually go back to the main page'

    def updateCheck(self, pid=None):
        if str(pid) != str(sickrage.app.pid):
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        sickrage.app.alerts.message(_("Updater"), _('Checking for updates'))

        # check for new app updates
        if not sickrage.app.version_updater.check_for_new_version(force=True):
            sickrage.app.alerts.message(_("Updater"), _('No new updates available!'))

        return self.redirect(self.previous_url())

    def update(self, pid=None):
        if str(pid) != str(sickrage.app.pid):
            return self.redirect("/{}/".format(sickrage.app.config.default_page))

        sickrage.app.alerts.message(_("Updater"), _('Updating SiCKRAGE'))

        sickrage.app.event_queue.fire_event(sickrage.app.version_updater.update, webui=True)

        return self.redirect(self.previous_url())

    def verifyPath(self, path):
        if os.path.isfile(path):
            return _('Successfully found {path}'.format(path=path))
        else:
            return _('Failed to find {path}'.format(path=path))

    def installRequirements(self):
        sickrage.app.alerts.message(_('Installing SiCKRAGE requirements'))
        if not sickrage.app.version_updater.updater.install_requirements(
                sickrage.app.version_updater.updater.current_branch):
            sickrage.app.alerts.message(_('Failed to install SiCKRAGE requirements'))
        else:
            sickrage.app.alerts.message(_('Installed SiCKRAGE requirements successfully!'))

        return self.redirect(self.previous_url())

    def branchCheckout(self, branch):
        if branch and sickrage.app.version_updater.updater.current_branch != branch:
            sickrage.app.alerts.message(_('Checking out branch: '), branch)
            if sickrage.app.version_updater.updater.checkout_branch(branch):
                sickrage.app.alerts.message(_('Branch checkout successful, restarting: '), branch)
                return self.restart(sickrage.app.pid)
        else:
            sickrage.app.alerts.message(_('Already on branch: '), branch)

        return self.redirect(self.previous_url())

    def displayShow(self, show=None):
        submenu = []

        if show is None:
            return self._genericMessage(_("Error"), _("Invalid show ID"))
        else:
            showObj = findCertainShow(int(show))

            if showObj is None:
                return self._genericMessage(_("Error"), _("Show not in show list"))

        episodeResults = MainDB.TVEpisode.query.filter_by(showid=showObj.indexerid).order_by(MainDB.TVEpisode.season.desc(),
                                                                                   MainDB.TVEpisode.episode.desc())

        seasonResults = list({x.season for x in episodeResults})

        submenu.append({
            'title': _('Edit'),
            'path': '/home/editShow?show=%d' % showObj.indexerid,
            'icon': 'fas fa-edit'
        })

        showLoc = showObj.location

        show_message = ''

        if sickrage.app.show_queue.is_being_added(showObj):
            show_message = _('This show is in the process of being downloaded - the info below is incomplete.')

        elif sickrage.app.show_queue.is_being_updated(showObj):
            show_message = _('The information on this page is in the process of being updated.')

        elif sickrage.app.show_queue.is_being_refreshed(showObj):
            show_message = _('The episodes below are currently being refreshed from disk')

        elif sickrage.app.show_queue.is_being_subtitled(showObj):
            show_message = _('Currently downloading subtitles for this show')

        elif sickrage.app.show_queue.is_in_refresh_queue(showObj):
            show_message = _('This show is queued to be refreshed.')

        elif sickrage.app.show_queue.is_in_update_queue(showObj):
            show_message = _('This show is queued and awaiting an update.')

        elif sickrage.app.show_queue.is_in_subtitle_queue(showObj):
            show_message = _('This show is queued and awaiting subtitles download.')

        if not sickrage.app.show_queue.is_being_added(showObj):
            if not sickrage.app.show_queue.is_being_updated(showObj):
                if showObj.paused:
                    submenu.append({
                        'title': _('Resume'),
                        'path': '/home/togglePause?show=%d' % showObj.indexerid,
                        'icon': 'fas fa-play'
                    })
                else:
                    submenu.append({
                        'title': _('Pause'),
                        'path': '/home/togglePause?show=%d' % showObj.indexerid,
                        'icon': 'fas fa-pause'
                    })

                submenu.append({
                    'title': _('Remove'),
                    'path': '/home/deleteShow?show=%d' % showObj.indexerid,
                    'class': 'removeshow',
                    'confirm': True,
                    'icon': 'fas fa-trash'
                })

                submenu.append({
                    'title': _('Re-scan files'),
                    'path': '/home/refreshShow?show=%d' % showObj.indexerid,
                    'icon': 'fas fa-compass'
                })

                submenu.append({
                    'title': _('Full Update'),
                    'path': '/home/updateShow?show=%d&amp;force=1' % showObj.indexerid,
                    'icon': 'fas fa-sync'
                })

                submenu.append({
                    'title': _('Update show in KODI'),
                    'path': '/home/updateKODI?show=%d' % showObj.indexerid,
                    'requires': self.haveKODI(),
                    'icon': 'fas fa-tv'
                })

                submenu.append({
                    'title': _('Update show in Emby'),
                    'path': '/home/updateEMBY?show=%d' % showObj.indexerid,
                    'requires': self.haveEMBY(),
                    'icon': 'fas fa-tv'
                })

                submenu.append({
                    'title': _('Preview Rename'),
                    'path': '/home/testRename?show=%d' % showObj.indexerid,
                    'icon': 'fas fa-tag'
                })

                if sickrage.app.config.use_subtitles and showObj.subtitles:
                    if not sickrage.app.show_queue.is_being_subtitled(showObj):
                        submenu.append({
                            'title': _('Download Subtitles'),
                            'path': '/home/subtitleShow?show=%d' % showObj.indexerid,
                            'icon': 'fas fa-comment'
                        })

        epCats = {}
        epCounts = {
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

        for curEp in episodeResults:
            curEpCat = showObj.get_overview(int(curEp.status or -1))

            if curEp.airdate != 1:
                today = datetime.datetime.now().replace(tzinfo=sickrage.app.tz)
                airDate = datetime.datetime.fromordinal(curEp.airdate)
                if airDate.year >= 1970 or showObj.network:
                    airDate = srDateTime(
                        sickrage.app.tz_updater.parse_date_time(curEp.airdate, showObj.airs, showObj.network),
                        convert=True).dt

                if curEpCat == Overview.WANTED and airDate < today:
                    curEpCat = Overview.MISSED

            if curEpCat:
                epCats[str(curEp.season) + "x" + str(curEp.episode)] = curEpCat
                epCounts[curEpCat] += 1

        def titler(x):
            return (remove_article(x), x)[not x or sickrage.app.config.sort_article]

        if sickrage.app.config.anime_split_home:
            shows = []
            anime = []
            for show in sickrage.app.showlist:
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)

            sortedShowLists = {"Shows": sorted(shows, key=cmp_to_key(
                lambda x, y: titler(x.name).lower() < titler(y.name).lower())),
                               "Anime": sorted(anime, key=cmp_to_key(
                                   lambda x, y: titler(x.name).lower() < titler(y.name).lower()))}
        else:
            sortedShowLists = {"Shows": sorted(sickrage.app.showlist, key=cmp_to_key(
                lambda x, y: titler(x.name).lower() < titler(y.name).lower()))}

        bwl = None
        if showObj.is_anime:
            bwl = showObj.release_groups

        showObj.exceptions = get_scene_exceptions(showObj.indexerid)

        indexerid = int(showObj.indexerid)
        indexer = int(showObj.indexer)

        # Delete any previous occurrances
        for index, recentShow in enumerate(sickrage.app.config.shows_recent):
            if recentShow['indexerid'] == indexerid:
                del sickrage.app.config.shows_recent[index]

        # Only track 5 most recent shows
        del sickrage.app.config.shows_recent[4:]

        # Insert most recent show
        sickrage.app.config.shows_recent.insert(0, {
            'indexerid': indexerid,
            'name': showObj.name,
        })

        return self.render(
            "/home/display_show.mako",
            submenu=submenu,
            showLoc=showLoc,
            show_message=show_message,
            show=showObj,
            episodeResults=episodeResults,
            seasonResults=seasonResults,
            sortedShowLists=sortedShowLists,
            bwl=bwl,
            epCounts=epCounts,
            epCats=epCats,
            all_scene_exceptions=showObj.exceptions,
            scene_numbering=get_scene_numbering_for_show(indexerid, indexer),
            xem_numbering=get_xem_numbering_for_show(indexerid, indexer),
            scene_absolute_numbering=get_scene_absolute_numbering_for_show(indexerid, indexer),
            xem_absolute_numbering=get_xem_absolute_numbering_for_show(indexerid, indexer),
            title=showObj.name,
            controller='home',
            action="display_show"
        )

    def editShow(self, show=None, location=None, anyQualities=None, bestQualities=None, exceptions_list=None,
                 flatten_folders=None, paused=None, directCall=False, air_by_date=None, sports=None, dvdorder=None,
                 indexerLang=None, subtitles=None, subtitles_sr_metadata=None, skip_downloaded=None,
                 rls_ignore_words=None, rls_require_words=None, anime=None, blacklist=None, whitelist=None,
                 scene=None, defaultEpStatus=None, quality_preset=None, search_delay=None):

        if exceptions_list is None:
            exceptions_list = []
        if bestQualities is None:
            bestQualities = []
        if anyQualities is None:
            anyQualities = []

        if show is None:
            errString = _("Invalid show ID: ") + str(show)
            if directCall:
                return [errString]
            else:
                return self._genericMessage(_("Error"), errString)

        showObj = findCertainShow(int(show))

        if not showObj:
            errString = _("Unable to find the specified show: ") + str(show)
            if directCall:
                return [errString]
            else:
                return self._genericMessage(_("Error"), errString)

        showObj.exceptions = get_scene_exceptions(showObj.indexerid)

        groups = []
        if not location and not anyQualities and not bestQualities and not quality_preset and not flatten_folders:
            if showObj.is_anime:
                whitelist = showObj.release_groups.whitelist
                blacklist = showObj.release_groups.blacklist

                try:
                    groups = get_release_groups_for_anime(showObj.name)
                except AnidbAdbaConnectionException as e:
                    sickrage.app.log.debug('Unable to get ReleaseGroups: {}'.format(e))

            with showObj.lock:
                scene_exceptions = get_scene_exceptions(showObj.indexerid)

            if showObj.is_anime:
                return self.render(
                    "/home/edit_show.mako",
                    show=showObj,
                    quality=showObj.quality,
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
                    show=showObj,
                    quality=showObj.quality,
                    scene_exceptions=scene_exceptions,
                    title=_('Edit Show'),
                    header=_('Edit Show'),
                    controller='home',
                    action="edit_show"
                )

        flatten_folders = not checkbox_to_value(flatten_folders)  # UI inverts this value
        dvdorder = checkbox_to_value(dvdorder)
        skip_downloaded = checkbox_to_value(skip_downloaded)
        paused = checkbox_to_value(paused)
        air_by_date = checkbox_to_value(air_by_date)
        scene = checkbox_to_value(scene)
        sports = checkbox_to_value(sports)
        anime = checkbox_to_value(anime)
        subtitles = checkbox_to_value(subtitles)
        subtitles_sr_metadata = checkbox_to_value(subtitles_sr_metadata)

        if indexerLang and indexerLang in IndexerApi(showObj.indexer).indexer().languages.keys():
            indexer_lang = indexerLang
        else:
            indexer_lang = showObj.lang

        # if we changed the language then kick off an update
        if indexer_lang == showObj.lang:
            do_update = False
        else:
            do_update = True

        if scene == showObj.scene or anime == showObj.anime:
            do_update_scene_numbering = False
        else:
            do_update_scene_numbering = True

        if not isinstance(anyQualities, list):
            anyQualities = [anyQualities]

        if not isinstance(bestQualities, list):
            bestQualities = [bestQualities]

        if not isinstance(exceptions_list, list):
            exceptions_list = [exceptions_list]

        # If directCall from mass_edit_update no scene exceptions handling or blackandwhite list handling
        if directCall:
            do_update_exceptions = False
        else:
            if set(exceptions_list) == set(showObj.exceptions):
                do_update_exceptions = False
            else:
                do_update_exceptions = True

            with showObj.lock:
                if anime:
                    if not showObj.release_groups:
                        showObj.release_groups = BlackAndWhiteList(showObj.indexerid)

                    if whitelist:
                        shortwhitelist = short_group_names(whitelist)
                        showObj.release_groups.set_white_keywords(shortwhitelist)
                    else:
                        showObj.release_groups.set_white_keywords([])

                    if blacklist:
                        shortblacklist = short_group_names(blacklist)
                        showObj.release_groups.set_black_keywords(shortblacklist)
                    else:
                        showObj.release_groups.set_black_keywords([])

        warnings, errors = [], []

        with showObj.lock:
            newQuality = try_int(quality_preset, None)
            if not newQuality:
                newQuality = Quality.combine_qualities(map(int, anyQualities), map(int, bestQualities))

            showObj.quality = newQuality
            showObj.skip_downloaded = skip_downloaded

            # reversed for now
            if bool(showObj.flatten_folders) != bool(flatten_folders):
                showObj.flatten_folders = flatten_folders
                try:
                    sickrage.app.show_queue.refreshShow(showObj, True)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh this show: {}").format(e))

            showObj.paused = paused
            showObj.scene = scene
            showObj.anime = anime
            showObj.sports = sports
            showObj.subtitles = subtitles
            showObj.subtitles_sr_metadata = subtitles_sr_metadata
            showObj.air_by_date = air_by_date
            showObj.default_ep_status = int(defaultEpStatus)

            if not directCall:
                showObj.lang = indexer_lang
                showObj.dvdorder = dvdorder
                showObj.rls_ignore_words = rls_ignore_words.strip()
                showObj.rls_require_words = rls_require_words.strip()
                showObj.search_delay = int(search_delay)

            # if we change location clear the db of episodes, change it, write to db, and rescan
            if os.path.normpath(showObj.location) != os.path.normpath(location):
                sickrage.app.log.debug(os.path.normpath(showObj.location) + " != " + os.path.normpath(location))
                if not os.path.isdir(location) and not sickrage.app.config.create_missing_show_dirs:
                    warnings.append("New location {} does not exist".format(location))

                # don't bother if we're going to update anyway
                elif not do_update:
                    # change it
                    try:
                        showObj.location = location
                        try:
                            sickrage.app.show_queue.refreshShow(showObj, True)
                        except CantRefreshShowException as e:
                            errors.append(_("Unable to refresh this show:{}").format(e))
                            # grab updated info from TVDB
                            # showObj.loadEpisodesFromIndexer()
                            # rescan the episodes in the new folder
                    except NoNFOException:
                        warnings.append(
                            _("The folder at %s doesn't contain a tvshow.nfo - copy your files to that folder before "
                              "you change the directory in SiCKRAGE.") % location)

            # save it to the DB
            showObj.save_to_db()

        # force the update
        if do_update:
            try:
                sickrage.app.show_queue.updateShow(showObj, force=True)
                time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            except CantUpdateShowException as e:
                errors.append(_("Unable to update show: {}").format(e))

        if do_update_exceptions:
            try:
                update_scene_exceptions(showObj.indexerid, exceptions_list)
                time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            except CantUpdateShowException as e:
                warnings.append(_("Unable to force an update on scene exceptions of the show."))

        if do_update_scene_numbering:
            try:
                xem_refresh(showObj.indexerid, showObj.indexer, True)
                time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            except CantUpdateShowException as e:
                warnings.append(_("Unable to force an update on scene numbering of the show."))

        if directCall:
            return map(str, warnings + errors)

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

    def togglePause(self, show=None):
        if show is None:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        showObj = findCertainShow(int(show))

        if showObj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        showObj.paused = not showObj.paused

        showObj.save_to_db()

        sickrage.app.alerts.message(
            _('%s has been %s') % (showObj.name, (_('resumed'), _('paused'))[showObj.paused]))

        return self.redirect("/home/displayShow?show=%i" % showObj.indexerid)

    def deleteShow(self, show=None, full=0):
        if show is None:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        showObj = findCertainShow(int(show))

        if showObj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        try:
            sickrage.app.show_queue.removeShow(showObj, bool(full))
            sickrage.app.alerts.message(
                _('%s has been %s %s') %
                (
                    showObj.name,
                    (_('deleted'), _('trashed'))[bool(sickrage.app.config.trash_remove_show)],
                    (_('(media untouched)'), _('(with all related media)'))[bool(full)]
                )
            )
        except CantRemoveShowException as e:
            sickrage.app.alerts.error(_('Unable to delete this show.'), str(e))

        time.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')

    def refreshShow(self, show=None):
        if show is None:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        showObj = findCertainShow(int(show))

        if showObj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        try:
            sickrage.app.show_queue.refreshShow(showObj, True)
        except CantRefreshShowException as e:
            sickrage.app.alerts.error(_('Unable to refresh this show.'), str(e))

        time.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def updateShow(self, show=None, force=0):
        if show is None:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        showObj = findCertainShow(int(show))

        if showObj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # force the update
        try:
            sickrage.app.show_queue.updateShow(showObj, force=bool(force))
        except CantUpdateShowException as e:
            sickrage.app.alerts.error(_("Unable to update this show."), str(e))

        # just give it some time
        time.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def subtitleShow(self, show=None):

        if show is None:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        showObj = findCertainShow(int(show))

        if showObj is None:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # search and download subtitles
        sickrage.app.show_queue.download_subtitles(showObj)

        time.sleep(cpu_presets[sickrage.app.config.cpu_preset])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def updateKODI(self, show=None):
        showName = None
        showObj = None

        if show:
            showObj = findCertainShow(int(show))
            if showObj:
                showName = quote_plus(showObj.name.encode())

        if sickrage.app.config.kodi_update_onlyfirst:
            host = sickrage.app.config.kodi_host.split(",")[0].strip()
        else:
            host = sickrage.app.config.kodi_host

        if sickrage.app.notifier_providers['kodi'].update_library(showName=showName):
            sickrage.app.alerts.message(_("Library update command sent to KODI host(s): ") + host)
        else:
            sickrage.app.alerts.error(_("Unable to contact one or more KODI host(s): ") + host)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def updatePLEX(self):
        if None is sickrage.app.notifier_providers['plex'].update_library():
            sickrage.app.alerts.message(
                _("Library update command sent to Plex Media Server host: ") +
                sickrage.app.config.plex_server_host)
        else:
            sickrage.app.alerts.error(
                _("Unable to contact Plex Media Server host: ") +
                sickrage.app.config.plex_server_host)
        return self.redirect('/home/')

    def updateEMBY(self, show=None):
        showObj = None

        if show:
            showObj = findCertainShow(int(show))

        if sickrage.app.notifier_providers['emby'].update_library(showObj):
            sickrage.app.alerts.message(
                _("Library update command sent to Emby host: ") + sickrage.app.config.emby_host)
        else:
            sickrage.app.alerts.error(
                _("Unable to contact Emby host: ") + sickrage.app.config.emby_host)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def syncTrakt(self):
        if sickrage.app.scheduler.get_job('TRAKTSEARCHER').func():
            sickrage.app.log.info("Syncing Trakt with SiCKRAGE")
            sickrage.app.alerts.message(_('Syncing Trakt with SiCKRAGE'))

        return self.redirect("/home/")

    def deleteEpisode(self, show=None, eps=None, direct=False):
        if not all([show, eps]):
            errMsg = _("You must specify a show and at least one episode")
            if direct:
                sickrage.app.alerts.error(_('Error'), errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        showObj = findCertainShow(int(show))
        if not showObj:
            errMsg = _("Error", "Show not in show list")
            if direct:
                sickrage.app.alerts.error(_('Error'), errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        if eps:
            for curEp in eps.split('|'):
                if not curEp:
                    sickrage.app.log.debug("curEp was empty when trying to deleteEpisode")

                sickrage.app.log.debug("Attempting to delete episode " + curEp)

                epInfo = curEp.split('x')

                if not all(epInfo):
                    sickrage.app.log.debug(
                        "Something went wrong when trying to deleteEpisode, epInfo[0]: %s, epInfo[1]: %s" % (
                            epInfo[0], epInfo[1]))
                    continue

                epObj = showObj.get_episode(int(epInfo[0]), int(epInfo[1]))
                if not epObj:
                    return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))

                with epObj.lock:
                    try:
                        epObj.deleteEpisode(full=True)
                    except EpisodeDeletedException:
                        pass

        if direct:
            return json_encode({'result': 'success'})
        else:
            return self.redirect("/home/displayShow?show=" + show)

    def setStatus(self, show=None, eps=None, status=None, direct=False):

        if not all([show, eps, status]):
            errMsg = _("You must specify a show and at least one episode")
            if direct:
                sickrage.app.alerts.error(_('Error'), errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        if int(status) not in statusStrings:
            errMsg = _("Invalid status")
            if direct:
                sickrage.app.alerts.error(_('Error'), errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        showObj = findCertainShow(int(show))

        if not showObj:
            errMsg = _("Error", "Show not in show list")
            if direct:
                sickrage.app.alerts.error(_('Error'), errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        segments = {}
        trakt_data = []
        if eps:
            for curEp in eps.split('|'):

                if not curEp:
                    sickrage.app.log.debug("curEp was empty when trying to setStatus")

                sickrage.app.log.debug("Attempting to set status on episode " + curEp + " to " + status)

                epInfo = curEp.split('x')

                if not all(epInfo):
                    sickrage.app.log.debug(
                        "Something went wrong when trying to setStatus, epInfo[0]: %s, epInfo[1]: %s" % (
                            epInfo[0], epInfo[1]))
                    continue

                epObj = showObj.get_episode(int(epInfo[0]), int(epInfo[1]))

                if not epObj:
                    return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))

                if int(status) in [WANTED, FAILED]:
                    # figure out what episodes are wanted so we can backlog them
                    if epObj.season in segments:
                        segments[epObj.season].append(epObj)
                    else:
                        segments[epObj.season] = [epObj]

                with epObj.lock:
                    # don't let them mess up UNAIRED episodes
                    if epObj.status == UNAIRED:
                        sickrage.app.log.warning(
                            "Refusing to change status of " + curEp + " because it is UNAIRED")
                        continue

                    if int(status) in Quality.DOWNLOADED and epObj.status not in Quality.SNATCHED + \
                            Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + [
                        IGNORED] and not os.path.isfile(epObj.location):
                        sickrage.app.log.warning(
                            "Refusing to change status of " + curEp + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if int(status) == FAILED and epObj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + \
                            Quality.SNATCHED_BEST + Quality.DOWNLOADED + Quality.ARCHIVED:
                        sickrage.app.log.warning(
                            "Refusing to change status of " + curEp + " to FAILED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if epObj.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        sickrage.app.log.info(
                            "Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced")
                        epObj.release_name = ""

                    epObj.status = int(status)

                    # save to database
                    epObj.save_to_db()

                    trakt_data.append((epObj.season, epObj.episode))

            data = sickrage.app.notifier_providers['trakt'].trakt_episode_data_generate(trakt_data)
            if data and sickrage.app.config.use_trakt and sickrage.app.config.trakt_sync_watchlist:
                if int(status) in [WANTED, FAILED]:
                    sickrage.app.log.debug(
                        "Add episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(
                            showObj.name) + " to Watchlist")
                    sickrage.app.notifier_providers['trakt'].update_watchlist(showObj, data_episode=data,
                                                                              update="add")
                elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                    sickrage.app.log.debug(
                        "Remove episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(
                            showObj.name) + " from Watchlist")
                    sickrage.app.notifier_providers['trakt'].update_watchlist(showObj, data_episode=data,
                                                                              update="remove")

        if int(status) == WANTED and not showObj.paused:
            msg = _(
                "Backlog was automatically started for the following seasons of ") + "<b>" + showObj.name + "</b>:<br>"
            msg += '<ul>'

            for season, segment in segments.items():
                sickrage.app.search_queue.put(BacklogQueueItem(showObj, segment))

                msg += "<li>" + _("Season ") + str(season) + "</li>"
                sickrage.app.log.info("Sending backlog for " + showObj.name + " season " + str(
                    season) + " because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                sickrage.app.alerts.message(_("Backlog started"), msg)
        elif int(status) == WANTED and showObj.paused:
            sickrage.app.log.info(
                "Some episodes were set to wanted, but " + showObj.name + " is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = _(
                "Retrying Search was automatically started for the following season of ") + "<b>" + showObj.name + "</b>:<br>"
            msg += '<ul>'

            for season, segment in segments.items():
                sickrage.app.search_queue.put(FailedQueueItem(showObj, segment))

                msg += "<li>" + _("Season ") + str(season) + "</li>"
                sickrage.app.log.info("Retrying Search for " + showObj.name + " season " + str(
                    season) + " because some eps were set to failed")

            msg += "</ul>"

            if segments:
                sickrage.app.alerts.message(_("Retry Search started"), msg)

        if direct:
            return json_encode({'result': 'success'})
        else:
            return self.redirect("/home/displayShow?show=" + show)

    def testRename(self, show=None):

        if show is None:
            return self._genericMessage(_("Error"), _("You must specify a show"))

        showObj = findCertainShow(int(show))

        if showObj is None:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        if not os.path.isdir(showObj.location):
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        ep_obj_rename_list = []

        ep_obj_list = showObj.get_all_episodes(has_location=True)

        for cur_ep_obj in ep_obj_list:
            # Only want to rename if we have a location
            if cur_ep_obj.location:
                if cur_ep_obj.relatedEps:
                    # do we have one of multi-episodes in the rename list already
                    have_already = False
                    for cur_related_ep in cur_ep_obj.relatedEps + [cur_ep_obj]:
                        if cur_related_ep in ep_obj_rename_list:
                            have_already = True
                            break
                        if not have_already:
                            ep_obj_rename_list.append(cur_ep_obj)
                else:
                    ep_obj_rename_list.append(cur_ep_obj)

        if ep_obj_rename_list:
            # present season DESC episode DESC on screen
            ep_obj_rename_list.reverse()

        submenu = [
            {'title': _('Edit'), 'path': '/home/editShow?show=%d' % showObj.indexerid,
             'icon': 'fas fa-edit'}]

        return self.render(
            "/home/test_renaming.mako",
            submenu=submenu,
            ep_obj_list=ep_obj_rename_list,
            show=showObj,
            title=_('Preview Rename'),
            header=_('Preview Rename'),
            controller='home',
            action="test_renaming"
        )

    def doRename(self, show=None, eps=None):
        if show is None or eps is None:
            errMsg = _("You must specify a show and at least one episode")
            return self._genericMessage(_("Error"), errMsg)

        show_obj = findCertainShow(int(show))

        if show_obj is None:
            errMsg = _("Show not in show list")
            return self._genericMessage(_("Error"), errMsg)

        if not os.path.isdir(show_obj.location):
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        if eps is None:
            return self.redirect("/home/displayShow?show=" + show)

        for curEp in eps.split('|'):
            epInfo = curEp.split('x')

            try:
                ep_result = MainDB.TVEpisode.query.filter_by(showid=int(show), season=int(epInfo[0]),
                                                   episode=int(epInfo[1])).one()
            except orm.exc.NoResultFound:
                sickrage.app.log.warning("Unable to find an episode for " + curEp + ", skipping")
                continue

            root_ep_obj = show_obj.get_episode(int(epInfo[0]), int(epInfo[1]))
            root_ep_obj.relatedEps = []

            for cur_related_ep in MainDB.TVEpisode.query.filter_by(location=ep_result.location).filter(
                    MainDB.TVEpisode.episode != int(epInfo[1])):
                related_ep_obj = show_obj.get_episode(int(cur_related_ep.season), int(cur_related_ep.episode))
                if related_ep_obj not in root_ep_obj.relatedEps:
                    root_ep_obj.relatedEps.append(related_ep_obj)

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)

    def searchEpisode(self, show=None, season=None, episode=None, downCurQuality=0):

        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, TVEpisode):
            # make a queue item for it and put it on the queue
            ep_queue_item = ManualSearchQueueItem(ep_obj.show, ep_obj, bool(int(downCurQuality)))

            sickrage.app.search_queue.put(ep_queue_item)
            if not all([ep_queue_item.started, ep_queue_item.success]):
                return json_encode({'result': 'success'})
        return json_encode({'result': 'failure'})

    ### Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self, show=None):
        def getEpisodes(searchThread, searchstatus):
            results = []
            showObj = findCertainShow(int(searchThread.show.indexerid))

            if not showObj:
                sickrage.app.log.warning(
                    'No Show Object found for show with indexerID: ' + str(searchThread.show.indexerid))
                return results

            if isinstance(searchThread, ManualSearchQueueItem):
                results.append({'show': searchThread.show.indexerid,
                                'episode': searchThread.segment.episode,
                                'episodeindexid': searchThread.segment.indexerid,
                                'season': searchThread.segment.season,
                                'searchstatus': searchstatus,
                                'status': statusStrings[searchThread.segment.status],
                                'quality': self.getQualityClass(searchThread.segment),
                                'overview': Overview.overviewStrings[
                                    showObj.get_overview(int(searchThread.segment.status or -1))]})
            else:
                for epObj in searchThread.segment:
                    results.append({'show': epObj.show.indexerid,
                                    'episode': epObj.episode,
                                    'episodeindexid': epObj.indexerid,
                                    'season': epObj.season,
                                    'searchstatus': searchstatus,
                                    'status': statusStrings[epObj.status],
                                    'quality': self.getQualityClass(epObj),
                                    'overview': Overview.overviewStrings[
                                        showObj.get_overview(int(epObj.status or -1))]})

            return results

        episodes = []

        # Queued Searches
        searchstatus = 'queued'
        for searchThread in sickrage.app.search_queue.get_all_ep_from_queue(show):
            episodes += getEpisodes(searchThread, searchstatus)

        # Running Searches
        searchstatus = 'searching'
        if sickrage.app.search_queue.is_manualsearch_in_progress():
            searchThread = sickrage.app.search_queue.current_item

            if searchThread.success:
                searchstatus = 'finished'

            episodes += getEpisodes(searchThread, searchstatus)

        # Finished Searches
        searchstatus = 'finished'
        for searchThread in MANUAL_SEARCH_HISTORY:
            if show is not None:
                if not str(searchThread.show.indexerid) == show:
                    continue

            if isinstance(searchThread, ManualSearchQueueItem):
                if not [x for x in episodes if x['episodeindexid'] == searchThread.segment.indexerid]:
                    episodes += getEpisodes(searchThread, searchstatus)
            else:
                ### These are only Failed Downloads/Retry SearchThreadItems.. lets loop through the segement/episodes
                if not [i for i, j in zip(searchThread.segment, episodes) if i.indexerid == j['episodeindexid']]:
                    episodes += getEpisodes(searchThread, searchstatus)

        return json_encode({'episodes': episodes})

    @staticmethod
    def getQualityClass(ep_obj):
        # return the correct json value

        # Find the quality class for the episode
        __, ep_quality = Quality.split_composite_status(ep_obj.status)
        if ep_quality in Quality.cssClassStrings:
            quality_class = Quality.cssClassStrings[ep_quality]
        else:
            quality_class = Quality.cssClassStrings[Quality.UNKNOWN]

        return quality_class

    def searchEpisodeSubtitles(self, show=None, season=None, episode=None):
        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, TVEpisode):
            try:
                newSubtitles = ep_obj.download_subtitles()
            except Exception:
                return json_encode({'result': 'failure'})

            if newSubtitles:
                newLangs = [sickrage.subtitles.name_from_code(newSub) for newSub in newSubtitles]
                status = _('New subtitles downloaded: %s') % ', '.join([newLang for newLang in newLangs])
            else:
                status = _('No subtitles downloaded')

            sickrage.app.alerts.message(ep_obj.show.name, status)
            return json_encode({'result': status, 'subtitles': ','.join(ep_obj.subtitles)})

        return json_encode({'result': 'failure'})

    def setSceneNumbering(self, show, indexer, forSeason=None, forEpisode=None, forAbsolute=None, sceneSeason=None,
                          sceneEpisode=None, sceneAbsolute=None):

        # sanitize:
        if forSeason in ['null', '']:
            forSeason = None
        if forEpisode in ['null', '']:
            forEpisode = None
        if forAbsolute in ['null', '']:
            forAbsolute = None
        if sceneSeason in ['null', '']:
            sceneSeason = None
        if sceneEpisode in ['null', '']:
            sceneEpisode = None
        if sceneAbsolute in ['null', '']:
            sceneAbsolute = None

        showObj = findCertainShow(int(show))

        if showObj.is_anime:
            result = {
                'success': True,
                'forAbsolute': forAbsolute,
            }
        else:
            result = {
                'success': True,
                'forSeason': forSeason,
                'forEpisode': forEpisode,
            }

        # retrieve the episode object and fail if we can't get one
        if showObj.is_anime:
            ep_obj = self._getEpisode(show, absolute=forAbsolute)
        else:
            ep_obj = self._getEpisode(show, forSeason, forEpisode)

        if isinstance(ep_obj, str):
            result['success'] = False
            result['errorMessage'] = ep_obj
        elif showObj.is_anime:
            sickrage.app.log.debug("setAbsoluteSceneNumbering for %s from %s to %s" %
                                   (show, forAbsolute, sceneAbsolute))

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None:
                sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            sickrage.app.log.debug("setEpisodeSceneNumbering for %s from %sx%s to %sx%s" %
                                   (show, forSeason, forEpisode, sceneSeason, sceneEpisode))

            show = int(show)
            indexer = int(indexer)
            forSeason = int(forSeason)
            forEpisode = int(forEpisode)
            if sceneSeason is not None:
                sceneSeason = int(sceneSeason)
            if sceneEpisode is not None:
                sceneEpisode = int(sceneEpisode)

            set_scene_numbering(show, indexer, season=forSeason, episode=forEpisode, sceneSeason=sceneSeason,
                                sceneEpisode=sceneEpisode)

        if showObj.is_anime:
            sn = get_scene_absolute_numbering(show, indexer, forAbsolute)
            if sn:
                result['sceneAbsolute'] = sn
            else:
                result['sceneAbsolute'] = None
        else:
            sn = get_scene_numbering(show, indexer, forSeason, forEpisode)
            if sn:
                (result['sceneSeason'], result['sceneEpisode']) = sn
            else:
                (result['sceneSeason'], result['sceneEpisode']) = (None, None)

        return json_encode(result)

    def retryEpisode(self, show, season, episode, downCurQuality):
        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, TVEpisode):
            # make a queue item for it and put it on the queue
            ep_queue_item = FailedQueueItem(ep_obj.show, [ep_obj], bool(int(downCurQuality)))

            sickrage.app.search_queue.put(ep_queue_item)
            if not all([ep_queue_item.started, ep_queue_item.success]):
                return json_encode({'result': 'success'})
        return json_encode({'result': 'failure'})

    @staticmethod
    def fetch_releasegroups(show_name):
        sickrage.app.log.info('ReleaseGroups: {}'.format(show_name))

        try:
            groups = get_release_groups_for_anime(show_name)
            sickrage.app.log.info('ReleaseGroups: {}'.format(groups))
        except AnidbAdbaConnectionException as e:
            sickrage.app.log.debug('Unable to get ReleaseGroups: {}'.format(e))
        else:
            return json_encode({'result': 'success', 'groups': groups})

        return json_encode({'result': 'failure'})


@Route('/googleDrive(/?.*)')
class GoogleDrive(WebHandler):
    def __init__(self, *args, **kwargs):
        super(GoogleDrive, self).__init__(*args, **kwargs)

    def getProgress(self):
        return google_drive.GoogleDrive.get_progress()

    def syncRemote(self):
        self._genericMessage(_("Google Drive Sync"), _("Syncing app data to Google Drive"))
        google_drive.GoogleDrive().sync_remote()

    def syncLocal(self):
        self._genericMessage(_("Google Drive Sync"), _("Syncing app data from Google Drive"))
        google_drive.GoogleDrive().sync_local()


@Route('/IRC(/?.*)')
class irc(WebHandler):
    def __init__(self, *args, **kwargs):
        super(irc, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/irc.mako",
            topmenu="system",
            header="IRC",
            title="IRC",
            controller='root',
            action='irc'
        )


@Route('/changes(/?.*)')
class changelog(WebHandler):
    def __init__(self, *args, **kwargs):
        super(changelog, self).__init__(*args, **kwargs)

    def index(self):
        try:
            data = markdown2.markdown(sickrage.changelog(), extras=['header-ids'])
        except Exception:
            data = ''

        sickrage.app.config.view_changelog = False
        sickrage.app.config.save()
        return data


@Route('/home/postprocess(/?.*)')
class HomePostProcess(Home):
    def __init__(self, *args, **kwargs):
        super(HomePostProcess, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/home/postprocess.mako",
            title=_('Post Processing'),
            header=_('Post Processing'),
            topmenu='home',
            controller='home',
            action='postprocess'
        )

    def processEpisode(self, *args, **kwargs):
        pp_options = dict(
            ("proc_dir" if k.lower() == "dir" else k,
             argToBool(v)
             if k.lower() not in ['proc_dir', 'dir', 'nzbname', 'process_method', 'proc_type'] else v
             ) for k, v in kwargs.items())

        proc_dir = pp_options.pop("proc_dir", None)
        quiet = pp_options.pop("quiet", None)

        if not proc_dir:
            return self.redirect("/home/postprocess/")

        result = sickrage.app.postprocessor_queue.put(proc_dir, **pp_options)

        if quiet:
            return result

        return self._genericMessage(_("Postprocessing results"), result.replace("\n", "<br>\n"))


@Route('/home/addShows(/?.*)')
class HomeAddShows(Home):
    def __init__(self, *args, **kwargs):
        super(HomeAddShows, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/home/add_shows.mako",
            title=_('Add Shows'),
            header=_('Add Shows'),
            topmenu='home',
            controller='home',
            action='add_shows'
        )

    @staticmethod
    def getIndexerLanguages():
        return json_encode({'results': IndexerApi().indexer().language.keys()})

    @staticmethod
    def sanitizeFileName(name):
        return sanitizeFileName(name)

    @staticmethod
    def searchIndexersForShowName(search_term, lang=None, indexer=None):
        if not lang or lang == 'null':
            lang = sickrage.app.config.indexer_default_language

        results = {}
        final_results = []

        # Query Indexers for each search term and build the list of results
        for indexer in IndexerApi().indexers if not int(indexer) else [int(indexer)]:
            lINDEXER_API_PARMS = IndexerApi(indexer).api_params.copy()
            lINDEXER_API_PARMS['language'] = lang
            lINDEXER_API_PARMS['custom_ui'] = AllShowsUI
            t = IndexerApi(indexer).indexer(**lINDEXER_API_PARMS)

            sickrage.app.log.debug("Searching for Show with searchterm: %s on Indexer: %s" % (
                search_term, IndexerApi(indexer).name))

            try:
                # search via seriesname
                results.setdefault(indexer, []).extend(t[search_term])
            except Exception:
                continue

        for i, shows in results.items():
            final_results.extend([[IndexerApi(i).name, i, IndexerApi(i).config["show_url"],
                                   int(show['id']), show['seriesname'], show['firstaired'],
                                   ('', 'disabled')[bool(findCertainShow(show['id'], False))]] for show in shows])

        lang_id = IndexerApi().indexer().languages[lang] or 7
        return json_encode({'results': final_results, 'langid': lang_id})

    def massAddTable(self, rootDir=None):
        if not rootDir:
            return _('No folders selected.')
        elif not isinstance(rootDir, list):
            root_dirs = [rootDir]
        else:
            root_dirs = rootDir

        root_dirs = [unquote_plus(x) for x in root_dirs]

        if sickrage.app.config.root_dirs:
            default_index = int(sickrage.app.config.root_dirs.split('|')[0])
        else:
            default_index = 0

        if len(root_dirs) > default_index:
            tmp = root_dirs[default_index]
            if tmp in root_dirs:
                root_dirs.remove(tmp)
                root_dirs = [tmp] + root_dirs

        dir_list = []

        for root_dir in root_dirs:
            try:
                file_list = os.listdir(root_dir)
            except Exception:
                continue

            for cur_file in file_list:
                try:
                    cur_path = os.path.normpath(os.path.join(root_dir, cur_file))
                    if not os.path.isdir(cur_path):
                        continue

                    # ignore Synology folders
                    if cur_file.lower() in ['#recycle', '@eadir']:
                        continue

                    cur_dir = {
                        'dir': cur_path,
                        'display_dir': '<b>{}{}</b>{}'.format(os.path.dirname(cur_path), os.sep,
                                                              os.path.basename(cur_path)),
                    }

                    # see if the folder is in database already
                    if [x for x in sickrage.app.showlist if x.location == cur_path]:
                        cur_dir['added_already'] = True
                    else:
                        cur_dir['added_already'] = False

                    dir_list.append(cur_dir)

                    showid = show_name = indexer = None
                    for cur_provider in sickrage.app.metadata_providers.values():
                        if all([showid, show_name, indexer]):
                            continue

                        (showid, show_name, indexer) = cur_provider.retrieveShowMetadata(cur_path)

                        # default to TVDB if indexer was not detected
                        if show_name and not (indexer or showid):
                            (sn, idxr, i) = IndexerApi(indexer).searchForShowID(show_name, showid)

                            # set indexer and indexer_id from found info
                            if not indexer and idxr:
                                indexer = idxr

                            if not showid and i:
                                showid = i

                    cur_dir['existing_info'] = (showid, show_name, indexer)
                    if showid and findCertainShow(showid):
                        cur_dir['added_already'] = True
                except Exception:
                    pass

        return self.render(
            "/home/mass_add_table.mako",
            dirList=dir_list,
            controller='home',
            action="mass_add_table"
        )

    def newShow(self, show_to_add=None, other_shows=None, search_string=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """

        indexer, show_dir, indexer_id, show_name = self.split_extra_show(show_to_add)

        use_provided_info = False
        if indexer_id and indexer and show_name:
            use_provided_info = True

        # use the given show_dir for the indexer search if available
        default_show_name = show_name or ''
        if not show_dir and search_string:
            default_show_name = search_string
        elif not show_name and show_dir:
            default_show_name = re.sub(r' \(\d{4}\)', '',
                                       os.path.basename(os.path.normpath(show_dir)).replace('.', ' '))

        # carry a list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
            other_shows = [other_shows]

        provided_indexer_id = int(indexer_id or 0)
        provided_indexer_name = show_name or ''
        provided_indexer = int(indexer or sickrage.app.config.indexer_default)

        return self.render(
            "/home/new_show.mako",
            enable_anime_options=True,
            use_provided_info=use_provided_info,
            default_show_name=default_show_name,
            other_shows=other_shows,
            provided_show_dir=show_dir,
            provided_indexer_id=provided_indexer_id,
            provided_indexer_name=provided_indexer_name,
            provided_indexer=provided_indexer,
            indexers=IndexerApi().indexers,
            quality=sickrage.app.config.quality_default,
            whitelist=[],
            blacklist=[],
            groups=[],
            title=_('New Show'),
            header=_('New Show'),
            topmenu='home',
            controller='home',
            action="new_show"
        )

    def traktShows(self, list='trending', limit=10):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """

        trakt_shows, black_list = getattr(srTraktAPI()['shows'], list)(extended="full", limit=limit), False

        # filter shows
        trakt_shows = [x for x in trakt_shows if
                       'tvdb' in x.ids and not findCertainShow(int(x.ids['tvdb']))]

        return self.render("/home/trakt_shows.mako",
                           title="Trakt {} Shows".format(list.capitalize()),
                           header="Trakt {} Shows".format(list.capitalize()),
                           enable_anime_options=False,
                           black_list=black_list,
                           trakt_shows=trakt_shows,
                           trakt_list=list,
                           limit=limit,
                           controller='home',
                           action="trakt_shows")

    def popularShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        e = None

        try:
            popular_shows = imdbPopular().fetch_popular_shows()
        except Exception as e:
            popular_shows = None

        return self.render("/home/imdb_shows.mako",
                           title="IMDB Popular Shows",
                           header="IMDB Popular Shows",
                           popular_shows=popular_shows,
                           imdb_exception=e,
                           topmenu="home",
                           controller='home',
                           action="popular_shows")

    def addShowToBlacklist(self, indexer_id):
        # URL parameters
        data = {'shows': [{'ids': {'tvdb': indexer_id}}]}

        srTraktAPI()["users/me/lists/{list}".format(list=sickrage.app.config.trakt_blacklist_name)].add(data)

        return self.redirect('/home/addShows/trendingShows/')

    def existingShows(self):
        """
        Prints out the page to add existing shows from a root dir
        """
        return self.render("/home/add_existing_shows.mako",
                           enable_anime_options=False,
                           quality=sickrage.app.config.quality_default,
                           title=_('Existing Show'),
                           header=_('Existing Show'),
                           topmenu="home",
                           controller='home',
                           action="add_existing_shows")

    def addShowByID(self, indexer_id, showName):
        if re.search(r'tt\d+', indexer_id):
            lINDEXER_API_PARMS = IndexerApi(1).api_params.copy()
            t = IndexerApi(1).indexer(**lINDEXER_API_PARMS)
            indexer_id = t[indexer_id]['id']

        if findCertainShow(int(indexer_id)):
            return

        location = None
        if sickrage.app.config.root_dirs:
            root_dirs = sickrage.app.config.root_dirs.split('|')
            location = root_dirs[int(root_dirs[0]) + 1]

        if not location:
            sickrage.app.log.warning("There was an error creating the show, no root directory setting found")
            return _('No root directories setup, please go back and add one.')

        show_dir = os.path.join(location, sanitizeFileName(showName))

        return self.newShow('1|{show_dir}|{indexer_id}|{show_name}'.format(**{
            'show_dir': '',
            'indexer_id': indexer_id,
            'show_name': showName
        }))

    def addNewShow(self, whichSeries=None, indexerLang=None, rootDir=None, defaultStatus=None,
                   quality_preset=None, anyQualities=None, bestQualities=None, flatten_folders=None, subtitles=None,
                   subtitles_sr_metadata=None, fullShowPath=None, other_shows=None, skipShow=None, providedIndexer=None,
                   anime=None, scene=None, blacklist=None, whitelist=None, defaultStatusAfter=None,
                   skip_downloaded=None, providedName=None, add_show_year=None):
        """
        Receive tvdb id, dir, and other options and create a show from them. If extra show dirs are
        provided then it forwards back to newShow, if not it goes to /home.
        """

        indexerLang = indexerLang or sickrage.app.config.indexer_default_language

        # grab our list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
            other_shows = [other_shows]

        def finishAddShow():
            # if there are no extra shows then go home
            if not other_shows:
                return self.redirect('/home/')

            # peel off the next one
            next_show_dir = other_shows[0]
            rest_of_show_dirs = other_shows[1:]

            # go to add the next show
            return self.newShow(next_show_dir, rest_of_show_dirs)

        # if we're skipping then behave accordingly
        if skipShow:
            return finishAddShow()

        # sanity check on our inputs
        if not whichSeries or not any([rootDir, fullShowPath, providedName]):
            return self.redirect("/home/")

        # figure out what show we're adding and where
        series_pieces = whichSeries.split('|')
        if (whichSeries and rootDir or whichSeries and fullShowPath) and len(series_pieces) > 1:
            if len(series_pieces) < 6:
                sickrage.app.log.error(
                    'Unable to add show due to show selection. Not anough arguments: %s' % (repr(series_pieces)))
                sickrage.app.alerts.error(
                    _('Unknown error. Unable to add show due to problem with show selection.'))
                return self.redirect('/home/addShows/existingShows/')

            indexer = int(series_pieces[1])
            indexer_id = int(series_pieces[3])
            show_name = series_pieces[4]
        else:
            indexer = int(providedIndexer or sickrage.app.config.indexer_default)
            indexer_id = int(whichSeries)
            if fullShowPath:
                show_name = os.path.basename(os.path.normpath(fullShowPath))
            else:
                show_name = providedName

        # use the whole path if it's given, or else append the show name to the root dir to get the full show path
        if fullShowPath:
            show_dir = os.path.normpath(fullShowPath)
        else:
            show_dir = os.path.join(rootDir, sanitizeFileName(show_name))
            if add_show_year and not re.match(r'.*\(\d+\)$', show_dir):
                show_dir = "{} ({})".format(show_dir, re.search(r'\d{4}', series_pieces[5]).group(0))

        # blanket policy - if the dir exists you should have used "add existing show" numbnuts
        if os.path.isdir(show_dir) and not fullShowPath:
            sickrage.app.alerts.error(_("Unable to add show"),
                                      _("Folder ") + show_dir + _(" exists already"))
            return self.redirect('/home/addShows/existingShows/')

        # don't create show dir if config says not to
        if sickrage.app.config.add_shows_wo_dir:
            sickrage.app.log.info(
                "Skipping initial creation of " + show_dir + " due to sickrage.CONFIG.ini setting")
        else:
            dir_exists = makeDir(show_dir)
            if not dir_exists:
                sickrage.app.log.warning("Unable to create the folder " + show_dir + ", can't add the show")
                sickrage.app.alerts.error(_("Unable to add show"),
                                          _("Unable to create the folder " +
                                            show_dir + ", can't add the show"))

                # Don't redirect to default page because user wants to see the new show
                return self.redirect("/home/")
            else:
                chmod_as_parent(show_dir)

        # prepare the inputs for passing along
        scene = checkbox_to_value(scene)
        anime = checkbox_to_value(anime)
        flatten_folders = checkbox_to_value(flatten_folders)
        subtitles = checkbox_to_value(subtitles)
        subtitles_sr_metadata = checkbox_to_value(subtitles_sr_metadata)
        skip_downloaded = checkbox_to_value(skip_downloaded)

        if whitelist:
            whitelist = short_group_names(whitelist)
        if blacklist:
            blacklist = short_group_names(blacklist)

        if not anyQualities:
            anyQualities = []
        if not bestQualities:
            bestQualities = []
        if not isinstance(anyQualities, list):
            anyQualities = [anyQualities]
        if not isinstance(bestQualities, list):
            bestQualities = [bestQualities]

        newQuality = try_int(quality_preset, None)
        if not newQuality:
            newQuality = Quality.combine_qualities(map(int, anyQualities), map(int, bestQualities))

        # add the show
        sickrage.app.show_queue.addShow(indexer=indexer,
                                        indexer_id=indexer_id,
                                        showDir=show_dir,
                                        default_status=int(defaultStatus),
                                        quality=newQuality,
                                        flatten_folders=flatten_folders,
                                        lang=indexerLang,
                                        subtitles=subtitles,
                                        subtitles_sr_metadata=subtitles_sr_metadata,
                                        anime=anime,
                                        scene=scene,
                                        paused=None,
                                        blacklist=blacklist,
                                        whitelist=whitelist,
                                        default_status_after=int(defaultStatusAfter),
                                        skip_downloaded=skip_downloaded)

        sickrage.app.alerts.message(_('Adding Show'), _('Adding the specified show into ') + show_dir)

        return finishAddShow()

    @staticmethod
    def split_extra_show(extra_show):
        if not extra_show:
            return None, None, None, None
        split_vals = extra_show.split('|')
        if len(split_vals) < 4:
            indexer = split_vals[0]
            show_dir = split_vals[1]
            return indexer, show_dir, None, None
        indexer = split_vals[0]
        show_dir = split_vals[1]
        indexer_id = split_vals[2]
        show_name = '|'.join(split_vals[3:])

        return indexer, show_dir, indexer_id, show_name

    def addExistingShows(self, shows_to_add, promptForSettings, **kwargs):
        """
        Receives a dir list and add them. Adds the ones with given TVDB IDs first, then forwards
        along to the newShow page.
        """
        # grab a list of other shows to add, if provided
        if not shows_to_add:
            shows_to_add = []
        elif not isinstance(shows_to_add, list):
            shows_to_add = [shows_to_add]

        shows_to_add = [unquote_plus(x) for x in shows_to_add]

        promptForSettings = checkbox_to_value(promptForSettings)

        indexer_id_given = []
        dirs_only = []
        # separate all the ones with Indexer IDs
        for cur_dir in shows_to_add:
            split_vals = cur_dir.split('|')
            if split_vals:
                if len(split_vals) > 2:
                    indexer, show_dir, indexer_id, show_name = self.split_extra_show(cur_dir)
                    if all([show_dir, indexer_id, show_name]):
                        indexer_id_given.append((int(indexer), show_dir, int(indexer_id), show_name))
                else:
                    dirs_only.append(cur_dir)
            else:
                dirs_only.append(cur_dir)

        # if they want me to prompt for settings then I will just carry on to the newShow page
        if promptForSettings and shows_to_add:
            return self.newShow(shows_to_add[0], shows_to_add[1:])

        # if they don't want me to prompt for settings then I can just add all the nfo shows now
        num_added = 0
        for cur_show in indexer_id_given:
            indexer, show_dir, indexer_id, show_name = cur_show

            if indexer is not None and indexer_id is not None:
                # add the show
                sickrage.app.show_queue.addShow(indexer,
                                                indexer_id,
                                                show_dir,
                                                default_status=sickrage.app.config.status_default,
                                                quality=sickrage.app.config.quality_default,
                                                flatten_folders=sickrage.app.config.flatten_folders_default,
                                                subtitles=sickrage.app.config.subtitles_default,
                                                anime=sickrage.app.config.anime_default,
                                                scene=sickrage.app.config.scene_default,
                                                default_status_after=sickrage.app.config.status_default_after,
                                                skip_downloaded=sickrage.app.config.skip_downloaded_default)
                num_added += 1

        if num_added:
            sickrage.app.alerts.message(_("Shows Added"),
                                        _("Automatically added ") + str(
                                            num_added) + _(" from their existing metadata files"))

        # if we're done then go home
        if not dirs_only:
            return self.redirect('/home/')

        # for the remaining shows we need to prompt for each one, so forward this on to the newShow page
        return self.newShow(dirs_only[0], dirs_only[1:])


@Route('/manage(/?.*)')
class Manage(Home, WebRoot):
    def __init__(self, *args, **kwargs):
        super(Manage, self).__init__(*args, **kwargs)

    def index(self):
        return self.redirect('/manage/massUpdate')

    @staticmethod
    def showEpisodeStatuses(indexer_id, whichStatus):
        status_list = [int(whichStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER

        result = {}
        for dbData in MainDB.TVEpisode.query.filter_by(showid=int(indexer_id)).filter(MainDB.TVEpisode.season != 0,
                                                                            MainDB.TVEpisode.status.in_(status_list)):
            cur_season = int(dbData.season)
            cur_episode = int(dbData.episode)

            if cur_season not in result:
                result[cur_season] = {}

            result[cur_season][cur_episode] = dbData.name

        return json_encode(result)

    def episodeStatuses(self, whichStatus=None):
        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        status_list = []

        if whichStatus:
            status_list = [int(whichStatus)]
            if int(whichStatus) == SNATCHED:
                status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

        # if we have no status then this is as far as we need to go
        if len(status_list):
            for cur_status_result in sorted((s for s in sickrage.app.showlist for __ in
                                             MainDB.TVEpisode.query.filter_by(showid=s.indexerid).filter(
                                                 MainDB.TVEpisode.status.in_(status_list),
                                                 MainDB.TVEpisode.season != 0)), key=lambda d: d.name):
                cur_indexer_id = int(cur_status_result.indexerid)
                if cur_indexer_id not in ep_counts:
                    ep_counts[cur_indexer_id] = 1
                else:
                    ep_counts[cur_indexer_id] += 1

                show_names[cur_indexer_id] = cur_status_result.name
                if cur_indexer_id not in sorted_show_ids:
                    sorted_show_ids.append(cur_indexer_id)

        return self.render(
            "/manage/episode_statuses.mako",
            title="Episode Overview",
            header="Episode Overview",
            topmenu='manage',
            whichStatus=whichStatus,
            show_names=show_names,
            ep_counts=ep_counts,
            sorted_show_ids=sorted_show_ids,
            controller='manage',
            action='episode_statuses'
        )

    def changeEpisodeStatuses(self, oldStatus, newStatus, *args, **kwargs):
        status_list = [int(oldStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER

        to_change = {}

        # make a list of all shows and their associated args
        for arg in kwargs:
            indexer_id, what = arg.split('-')

            # we don't care about unchecked checkboxes
            if kwargs[arg] != 'on':
                continue

            if indexer_id not in to_change:
                to_change[indexer_id] = []

            to_change[indexer_id].append(what)

        for cur_indexer_id in to_change:
            # get a list of all the eps we want to change if they just said "all"
            if 'all' in to_change[cur_indexer_id]:
                all_eps = ['{}x{}'.format(x.season, x.episode) for x in
                           MainDB.TVEpisode.query.filter_by(showid=int(cur_indexer_id)).filter(
                               MainDB.TVEpisode.status.in_(status_list), MainDB.TVEpisode.season != 0)]
                to_change[cur_indexer_id] = all_eps

            self.setStatus(cur_indexer_id, '|'.join(to_change[cur_indexer_id]), newStatus, direct=True)

        return self.redirect('/manage/episodeStatuses/')

    @staticmethod
    def showSubtitleMissed(indexer_id, whichSubs):
        result = {}
        for dbData in MainDB.TVEpisode.query.filter_by(showid=int(indexer_id)).filter(MainDB.TVEpisode.status.endswith(4),
                                                                            MainDB.TVEpisode.season != 0):
            if whichSubs == 'all':
                if not frozenset(sickrage.subtitles.wanted_languages()).difference(dbData["subtitles"].split(',')):
                    continue
            elif whichSubs in dbData["subtitles"]:
                continue

            cur_season = int(dbData["season"])
            cur_episode = int(dbData["episode"])

            if cur_season not in result:
                result[cur_season] = {}

            if cur_episode not in result[cur_season]:
                result[cur_season][cur_episode] = {}

            result[cur_season][cur_episode]["name"] = dbData["name"]

            result[cur_season][cur_episode]["subtitles"] = dbData["subtitles"]

        return json_encode(result)

    def subtitleMissed(self, whichSubs=None):
        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        status_results = []

        if whichSubs:
            for s in sickrage.app.showlist:
                if not s.subtitles == 1:
                    continue

                for e in MainDB.TVEpisode.query.filter_by(showid=s.indexerid).filter(
                        or_(MainDB.TVEpisode.status.endswith(4), MainDB.TVEpisode.status.endswith(6)),
                        MainDB.TVEpisode.season != 0):
                    status_results += [{
                        'show_name': s.name,
                        'indexer_id': s.indexerid,
                        'subtitles': e.subtitles
                    }]

            for cur_status_result in sorted(status_results, key=lambda k: k['show_name']):
                if whichSubs == 'all':
                    if not frozenset(sickrage.subtitles.wanted_languages()).difference(
                            cur_status_result["subtitles"].split(',')):
                        continue
                elif whichSubs in cur_status_result["subtitles"]:
                    continue

                cur_indexer_id = int(cur_status_result["indexer_id"])
                if cur_indexer_id not in ep_counts:
                    ep_counts[cur_indexer_id] = 1
                else:
                    ep_counts[cur_indexer_id] += 1

                show_names[cur_indexer_id] = cur_status_result["show_name"]
                if cur_indexer_id not in sorted_show_ids:
                    sorted_show_ids.append(cur_indexer_id)

        return self.render(
            "/manage/subtitles_missed.mako",
            whichSubs=whichSubs,
            show_names=show_names,
            ep_counts=ep_counts,
            sorted_show_ids=sorted_show_ids,
            title=_('Missing Subtitles'),
            header=_('Missing Subtitles'),
            topmenu='manage',
            controller='manage',
            action='subtitles_missed'
        )

    def downloadSubtitleMissed(self, *args, **kwargs):
        to_download = {}

        # make a list of all shows and their associated args
        for arg in kwargs:
            indexer_id, what = arg.split('-')

            # we don't care about unchecked checkboxes
            if kwargs[arg] != 'on':
                continue

            if indexer_id not in to_download:
                to_download[indexer_id] = []

            to_download[indexer_id].append(what)

        for cur_indexer_id in to_download:
            # get a list of all the eps we want to download subtitles if they just said "all"
            if 'all' in to_download[cur_indexer_id]:
                to_download[cur_indexer_id] = ['{}x{}'.format(x.season, x.episode) for x in
                                               MainDB.TVEpisode.query.filter_by(showid=int(cur_indexer_id)).filter(
                                                   MainDB.TVEpisode.status.endswith(4), MainDB.TVEpisode.season != 0)]

            for epResult in to_download[cur_indexer_id]:
                season, episode = epResult.split('x')

                show = findCertainShow(int(cur_indexer_id))
                show.get_episode(int(season), int(episode)).download_subtitles()

        return self.redirect('/manage/subtitleMissed/')

    def backlogShow(self, indexer_id):
        show_obj = findCertainShow(int(indexer_id))

        if show_obj:
            sickrage.app.backlog_searcher.search_backlog([show_obj])

        return self.redirect("/manage/backlogOverview/")

    def backlogOverview(self):
        showCounts = {}
        showCats = {}
        showResults = {}

        for curShow in sickrage.app.showlist:
            if curShow.paused:
                continue

            epCats = {}
            epCounts = {
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

            showResults[curShow.indexerid] = []

            for curResult in MainDB.TVEpisode.query.filter_by(showid=curShow.indexerid).order_by(MainDB.TVEpisode.season.desc(),
                                                                                       MainDB.TVEpisode.episode.desc()):
                curEpCat = curShow.get_overview(int(curResult.status or -1))
                if curEpCat:
                    epCats["{}x{}".format(curResult.season, curResult.episode)] = curEpCat
                    epCounts[curEpCat] += 1

                showResults[curShow.indexerid] += [curResult]

            showCounts[curShow.indexerid] = epCounts
            showCats[curShow.indexerid] = epCats

        return self.render(
            "/manage/backlog_overview.mako",
            showCounts=showCounts,
            showCats=showCats,
            showResults=showResults,
            title=_('Backlog Overview'),
            header=_('Backlog Overview'),
            topmenu='manage',
            controller='manage',
            action='backlog_overview'
        )

    def massEdit(self, toEdit=None):
        if not toEdit:
            return self.redirect("/manage/")

        showIDs = toEdit.split("|")
        showList = []
        showNames = []
        for curID in showIDs:
            curID = int(curID)
            showObj = findCertainShow(curID)
            if showObj:
                showList.append(showObj)
                showNames.append(showObj.name)

        skip_downloaded_all_same = True
        last_skip_downloaded = None

        flatten_folders_all_same = True
        last_flatten_folders = None

        paused_all_same = True
        last_paused = None

        default_ep_status_all_same = True
        last_default_ep_status = None

        anime_all_same = True
        last_anime = None

        sports_all_same = True
        last_sports = None

        quality_all_same = True
        last_quality = None

        subtitles_all_same = True
        last_subtitles = None

        scene_all_same = True
        last_scene = None

        air_by_date_all_same = True
        last_air_by_date = None

        root_dir_list = []

        for curShow in showList:

            cur_root_dir = os.path.dirname(curShow.location)
            if cur_root_dir not in root_dir_list:
                root_dir_list.append(cur_root_dir)

            if skip_downloaded_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_skip_downloaded not in (None, curShow.skip_downloaded):
                    skip_downloaded_all_same = False
                else:
                    last_skip_downloaded = curShow.skip_downloaded

            # if we know they're not all the same then no point even bothering
            if paused_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_paused not in (None, curShow.paused):
                    paused_all_same = False
                else:
                    last_paused = curShow.paused

            if default_ep_status_all_same:
                if last_default_ep_status not in (None, curShow.default_ep_status):
                    default_ep_status_all_same = False
                else:
                    last_default_ep_status = curShow.default_ep_status

            if anime_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_anime not in (None, curShow.is_anime):
                    anime_all_same = False
                else:
                    last_anime = curShow.anime

            if flatten_folders_all_same:
                if last_flatten_folders not in (None, curShow.flatten_folders):
                    flatten_folders_all_same = False
                else:
                    last_flatten_folders = curShow.flatten_folders

            if quality_all_same:
                if last_quality not in (None, curShow.quality):
                    quality_all_same = False
                else:
                    last_quality = curShow.quality

            if subtitles_all_same:
                if last_subtitles not in (None, curShow.subtitles):
                    subtitles_all_same = False
                else:
                    last_subtitles = curShow.subtitles

            if scene_all_same:
                if last_scene not in (None, curShow.scene):
                    scene_all_same = False
                else:
                    last_scene = curShow.scene

            if sports_all_same:
                if last_sports not in (None, curShow.sports):
                    sports_all_same = False
                else:
                    last_sports = curShow.sports

            if air_by_date_all_same:
                if last_air_by_date not in (None, curShow.air_by_date):
                    air_by_date_all_same = False
                else:
                    last_air_by_date = curShow.air_by_date

        skip_downloaded_value = last_skip_downloaded if skip_downloaded_all_same else None
        default_ep_status_value = last_default_ep_status if default_ep_status_all_same else None
        paused_value = last_paused if paused_all_same else None
        anime_value = last_anime if anime_all_same else None
        flatten_folders_value = last_flatten_folders if flatten_folders_all_same else None
        quality_value = last_quality if quality_all_same else None
        subtitles_value = last_subtitles if subtitles_all_same else None
        scene_value = last_scene if scene_all_same else None
        sports_value = last_sports if sports_all_same else None
        air_by_date_value = last_air_by_date if air_by_date_all_same else None
        root_dir_list = root_dir_list

        return self.render(
            "/manage/mass_edit.mako",
            showList=toEdit,
            showNames=showNames,
            skip_downloaded_value=skip_downloaded_value,
            default_ep_status_value=default_ep_status_value,
            paused_value=paused_value,
            anime_value=anime_value,
            flatten_folders_value=flatten_folders_value,
            quality_value=quality_value,
            subtitles_value=subtitles_value,
            scene_value=scene_value,
            sports_value=sports_value,
            air_by_date_value=air_by_date_value,
            root_dir_list=root_dir_list,
            title=_('Mass Edit'),
            header=_('Mass Edit'),
            topmenu='manage',
            controller='manage',
            action='mass_edit'
        )

    def massEditSubmit(self, skip_downloaded=None, paused=None, default_ep_status=None,
                       anime=None, sports=None, scene=None, flatten_folders=None, quality_preset=None,
                       subtitles=None, air_by_date=None, anyQualities=None, bestQualities=None, toEdit=None, **kwargs):
        if bestQualities is None:
            bestQualities = []
        if anyQualities is None:
            anyQualities = []
        dir_map = {}
        for cur_arg in kwargs:
            if not cur_arg.startswith('orig_root_dir_'):
                continue
            which_index = cur_arg.replace('orig_root_dir_', '')
            end_dir = kwargs['new_root_dir_' + which_index]
            dir_map[kwargs[cur_arg]] = end_dir

        showIDs = toEdit.split("|")
        errors = []
        for curShow in showIDs:
            curErrors = []
            showObj = findCertainShow(int(curShow))
            if not showObj:
                continue

            cur_root_dir = os.path.dirname(showObj.location)
            cur_show_dir = os.path.basename(showObj.location)
            if cur_root_dir in dir_map and cur_root_dir != dir_map[cur_root_dir]:
                new_show_dir = os.path.join(dir_map[cur_root_dir], cur_show_dir)
                sickrage.app.log.info(
                    "For show " + showObj.name + " changing dir from " + showObj.location + " to " + new_show_dir)
            else:
                new_show_dir = showObj.location

            if skip_downloaded == 'keep':
                new_skip_downloaded = showObj.skip_downloaded
            else:
                new_skip_downloaded = True if skip_downloaded == 'enable' else False
            new_skip_downloaded = 'on' if new_skip_downloaded else 'off'

            if paused == 'keep':
                new_paused = showObj.paused
            else:
                new_paused = True if paused == 'enable' else False
            new_paused = 'on' if new_paused else 'off'

            if default_ep_status == 'keep':
                new_default_ep_status = showObj.default_ep_status
            else:
                new_default_ep_status = default_ep_status

            if anime == 'keep':
                new_anime = showObj.anime
            else:
                new_anime = True if anime == 'enable' else False
            new_anime = 'on' if new_anime else 'off'

            if sports == 'keep':
                new_sports = showObj.sports
            else:
                new_sports = True if sports == 'enable' else False
            new_sports = 'on' if new_sports else 'off'

            if scene == 'keep':
                new_scene = showObj.is_scene
            else:
                new_scene = True if scene == 'enable' else False
            new_scene = 'on' if new_scene else 'off'

            if air_by_date == 'keep':
                new_air_by_date = showObj.air_by_date
            else:
                new_air_by_date = True if air_by_date == 'enable' else False
            new_air_by_date = 'on' if new_air_by_date else 'off'

            if flatten_folders == 'keep':
                new_flatten_folders = showObj.flatten_folders
            else:
                new_flatten_folders = True if flatten_folders == 'enable' else False
            new_flatten_folders = 'on' if new_flatten_folders else 'off'

            if subtitles == 'keep':
                new_subtitles = showObj.subtitles
            else:
                new_subtitles = True if subtitles == 'enable' else False

            new_subtitles = 'on' if new_subtitles else 'off'

            if quality_preset == 'keep':
                anyQualities, bestQualities = Quality.split_quality(showObj.quality)
            elif try_int(quality_preset, None):
                bestQualities = []

            exceptions_list = []

            curErrors += self.editShow(curShow, new_show_dir, anyQualities,
                                       bestQualities, exceptions_list,
                                       defaultEpStatus=new_default_ep_status,
                                       skip_downloaded=new_skip_downloaded,
                                       flatten_folders=new_flatten_folders,
                                       paused=new_paused, sports=new_sports,
                                       subtitles=new_subtitles, anime=new_anime,
                                       scene=new_scene, air_by_date=new_air_by_date,
                                       directCall=True)

            if curErrors:
                sickrage.app.log.error("Errors: " + str(curErrors))
                errors.append('<b>%s:</b>\n<ul>' % showObj.name + ' '.join(
                    ['<li>%s</li>' % error for error in curErrors]) + "</ul>")

        if len(errors) > 0:
            sickrage.app.alerts.error(
                _('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors),
                                                                               plural="" if len(errors) == 1 else "s"),
                " ".join(errors))

        return self.redirect("/manage/")

    def massUpdate(self, toUpdate=None, toRefresh=None, toRename=None, toDelete=None, toRemove=None, toMetadata=None,
                   toSubtitle=None):

        if toUpdate is not None:
            toUpdate = toUpdate.split('|')
        else:
            toUpdate = []

        if toRefresh is not None:
            toRefresh = toRefresh.split('|')
        else:
            toRefresh = []

        if toRename is not None:
            toRename = toRename.split('|')
        else:
            toRename = []

        if toSubtitle is not None:
            toSubtitle = toSubtitle.split('|')
        else:
            toSubtitle = []

        if toDelete is not None:
            toDelete = toDelete.split('|')
        else:
            toDelete = []

        if toRemove is not None:
            toRemove = toRemove.split('|')
        else:
            toRemove = []

        if toMetadata is not None:
            toMetadata = toMetadata.split('|')
        else:
            toMetadata = []

        errors = []
        refreshes = []
        updates = []
        renames = []
        subtitles = []

        for curShowID in set(toUpdate + toRefresh + toRename + toSubtitle + toDelete + toRemove + toMetadata):

            if curShowID == '':
                continue

            showObj = findCertainShow(int(curShowID))

            if showObj is None:
                continue

            if curShowID in toDelete:
                sickrage.app.show_queue.removeShow(showObj, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in toRemove:
                sickrage.app.show_queue.removeShow(showObj)
                # don't do anything else if it's being remove
                continue

            if curShowID in toUpdate:
                try:
                    sickrage.app.show_queue.updateShow(showObj, force=True)
                    updates.append(showObj.name)
                except CantUpdateShowException as e:
                    errors.append(_("Unable to update show: {}").format(e))

            # don't bother refreshing shows that were updated anyway
            if curShowID in toRefresh and curShowID not in toUpdate:
                try:
                    sickrage.app.show_queue.refreshShow(showObj, True)
                    refreshes.append(showObj.name)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh show ") + showObj.name + ": {}".format(e))

            if curShowID in toRename:
                sickrage.app.show_queue.renameShowEpisodes(showObj)
                renames.append(showObj.name)

            if curShowID in toSubtitle:
                sickrage.app.show_queue.download_subtitles(showObj)
                subtitles.append(showObj.name)

        if errors:
            sickrage.app.alerts.error(_("Errors encountered"),
                                      '<br >\n'.join(errors))

        messageDetail = ""

        if updates:
            messageDetail += _("<br><b>Updates</b><br><ul><li>")
            messageDetail += "</li><li>".join(updates)
            messageDetail += "</li></ul>"

        if refreshes:
            messageDetail += _("<br><b>Refreshes</b><br><ul><li>")
            messageDetail += "</li><li>".join(refreshes)
            messageDetail += "</li></ul>"

        if renames:
            messageDetail += _("<br><b>Renames</b><br><ul><li>")
            messageDetail += "</li><li>".join(renames)
            messageDetail += "</li></ul>"

        if subtitles:
            messageDetail += _("<br><b>Subtitles</b><br><ul><li>")
            messageDetail += "</li><li>".join(subtitles)
            messageDetail += "</li></ul>"

        if updates + refreshes + renames + subtitles:
            sickrage.app.alerts.message(_("The following actions were queued:"),
                                        messageDetail)

        return self.render(
            '/manage/mass_update.mako',
            title=_('Mass Update'),
            header=_('Mass Update'),
            topmenu='manage',
            controller='manage',
            action='mass_update'
        )

    def failedDownloads(self, limit=100, toRemove=None):
        if int(limit) == 0:
            dbData = MainDB.FailedSnatch.query.all()
        else:
            dbData = MainDB.FailedSnatch.query.limit(int(limit))

        toRemove = toRemove.split("|") if toRemove is not None else []
        if toRemove:
            MainDB().delete(MainDB.FailedSnatch, MainDB.FailedSnatch.release.in_(toRemove))
            return self.redirect('/manage/failedDownloads/')

        return self.render(
            "/manage/failed_downloads.mako",
            limit=int(limit),
            failedResults=dbData,
            title=_('Failed Downloads'),
            header=_('Failed Downloads'),
            topmenu='manage',
            controller='manage',
            action='failed_downloads'
        )


@Route('/manage/manageQueues(/?.*)')
class ManageQueues(Manage):
    def __init__(self, *args, **kwargs):
        super(ManageQueues, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/manage/queues.mako",
            backlogSearchPaused=sickrage.app.search_queue.is_backlog_searcher_paused(),
            dailySearchPaused=sickrage.app.search_queue.is_daily_searcher_paused(),
            backlogSearchStatus=sickrage.app.search_queue.is_backlog_in_progress(),
            dailySearchStatus=sickrage.app.search_queue.is_dailysearch_in_progress(),
            findPropersStatus=sickrage.app.proper_searcher.amActive,
            searchQueueLength=sickrage.app.search_queue.queue_length(),
            postProcessorPaused=sickrage.app.postprocessor_queue.is_paused,
            postProcessorRunning=sickrage.app.postprocessor_queue.is_in_progress,
            postProcessorQueueLength=sickrage.app.postprocessor_queue.queue_length,
            title=_('Manage Queues'),
            header=_('Manage Queues'),
            topmenu='manage',
            controller='manage',
            action='queues'
        )

    def forceBacklogSearch(self):
        # force it to run the next time it looks
        if sickrage.app.scheduler.get_job(sickrage.app.backlog_searcher.name).func(True):
            sickrage.app.log.info("Backlog search forced")
            sickrage.app.alerts.message(_('Backlog search started'))

        return self.redirect("/manage/manageQueues/")

    def forceDailySearch(self):
        # force it to run the next time it looks
        if sickrage.app.scheduler.get_job(sickrage.app.daily_searcher.name).func(True):
            sickrage.app.log.info("Daily search forced")
            sickrage.app.alerts.message(_('Daily search started'))

        return self.redirect("/manage/manageQueues/")

    def forceFindPropers(self):
        # force it to run the next time it looks
        if sickrage.app.scheduler.get_job(sickrage.app.proper_searcher.name).func(True):
            sickrage.app.log.info("Find propers search forced")
            sickrage.app.alerts.message(_('Find propers search started'))

        return self.redirect("/manage/manageQueues/")

    def pauseDailySearcher(self, paused=None):
        if paused == "1":
            sickrage.app.search_queue.pause_daily_searcher()
        else:
            sickrage.app.search_queue.unpause_daily_searcher()

        return self.redirect("/manage/manageQueues/")

    def pauseBacklogSearcher(self, paused=None):
        if paused == "1":
            sickrage.app.search_queue.pause_backlog_searcher()
        else:
            sickrage.app.search_queue.unpause_backlog_searcher()

        return self.redirect("/manage/manageQueues/")

    def pausePostProcessor(self, paused=None):
        if paused == "1":
            sickrage.app.postprocessor_queue.pause()
        else:
            sickrage.app.postprocessor_queue.unpause()

        return self.redirect("/manage/manageQueues/")


@Route('/history(/?.*)')
class History(WebHandler):
    def __init__(self, *args, **kwargs):
        super(History, self).__init__(*args, **kwargs)
        self.historyTool = HistoryTool()

    def index(self, limit=None):

        if limit is None:
            if sickrage.app.config.history_limit:
                limit = int(sickrage.app.config.history_limit)
            else:
                limit = 100
        else:
            limit = int(limit)

        sickrage.app.config.history_limit = limit

        sickrage.app.config.save()

        compact = []
        data = self.historyTool.get(limit)

        for row in data:
            action = {
                'action': row['action'],
                'provider': row['provider'],
                'resource': row['resource'],
                'time': row['date']
            }

            if not any((history['show_id'] == row['show_id'] and
                        history['season'] == row['season'] and
                        history['episode'] == row['episode'] and
                        history['quality'] == row['quality']) for history in compact):

                history = {
                    'actions': [action],
                    'episode': row['episode'],
                    'quality': row['quality'],
                    'resource': row['resource'],
                    'season': row['season'],
                    'show_id': row['show_id'],
                    'show_name': row['show_name']
                }

                compact.append(history)
            else:
                index = [i for i, item in enumerate(compact)
                         if item['show_id'] == row['show_id'] and
                         item['season'] == row['season'] and
                         item['episode'] == row['episode'] and
                         item['quality'] == row['quality']][0]

                history = compact[index]
                history['actions'].append(action)

                history['actions'].sort(key=lambda d: d['time'], reverse=True)

        submenu = [
            {'title': _('Clear History'), 'path': '/history/clearHistory', 'icon': 'fas fa-trash',
             'class': 'clearhistory', 'confirm': True},
            {'title': _('Trim History'), 'path': '/history/trimHistory', 'icon': 'fas fa-cut',
             'class': 'trimhistory', 'confirm': True},
        ]

        return self.render(
            "/history.mako",
            historyResults=data,
            compactResults=compact,
            limit=limit,
            submenu=submenu,
            title=_('History'),
            header=_('History'),
            topmenu="history",
            controller='root',
            action='history'
        )

    def clearHistory(self):
        self.historyTool.clear()

        sickrage.app.alerts.message(_('History cleared'))

        return self.redirect("/history/")

    def trimHistory(self):
        self.historyTool.trim()

        sickrage.app.alerts.message(_('Removed history entries older than 30 days'))

        return self.redirect("/history/")


@Route('/config(/?.*)')
class Config(WebHandler):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    @staticmethod
    def ConfigMenu():
        menu = [
            {'title': _('Help and Info'), 'path': '/config/', 'icon': 'fas fa-info'},
            {'title': _('General'), 'path': '/config/general/', 'icon': 'fas fa-cogs'},
            {'title': _('Backup/Restore'), 'path': '/config/backuprestore/', 'icon': 'fas fa-upload'},
            {'title': _('Search Clients'), 'path': '/config/search/', 'icon': 'fas fa-binoculars'},
            {'title': _('Search Providers'), 'path': '/config/providers/', 'icon': 'fas fa-share-alt'},
            {'title': _('Subtitles Settings'), 'path': '/config/subtitles/', 'icon': 'fas fa-cc'},
            {'title': _('Quality Settings'), 'path': '/config/qualitySettings/', 'icon': 'fas fa-wrench'},
            {'title': _('Post Processing'), 'path': '/config/postProcessing/', 'icon': 'fas fa-refresh'},
            {'title': _('Notifications'), 'path': '/config/notifications/', 'icon': 'fas fa-bell'},
            {'title': _('Anime'), 'path': '/config/anime/', 'icon': 'fas fa-eye'},
        ]

        return menu

    def index(self):
        return self.render(
            "/config/index.mako",
            submenu=self.ConfigMenu(),
            title=_('Configuration'),
            header=_('Configuration'),
            topmenu="config",
            controller='config',
            action='index'
        )

    def reset(self):
        sickrage.app.config.load(True)
        sickrage.app.alerts.message(_('Configuration Reset to Defaults'),
                                    os.path.join(sickrage.app.config_file))
        return self.redirect("/config/general")


@Route('/config/general(/?.*)')
class ConfigGeneral(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigGeneral, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/general.mako",
            title=_('Config - General'),
            header=_('General Configuration'),
            topmenu='config',
            submenu=self.ConfigMenu(),
            controller='config',
            action='general',
        )

    @staticmethod
    def generateApiKey():
        return generateApiKey()

    @staticmethod
    def saveRootDirs(rootDirString=None):
        sickrage.app.config.root_dirs = rootDirString

    @staticmethod
    def saveAddShowDefaults(defaultStatus, anyQualities, bestQualities, defaultFlattenFolders, subtitles=False,
                            anime=False, scene=False, defaultStatusAfter=WANTED, skip_downloaded=False,
                            add_show_year=False):

        if anyQualities:
            anyQualities = anyQualities.split(',')
        else:
            anyQualities = []

        if bestQualities:
            bestQualities = bestQualities.split(',')
        else:
            bestQualities = []

        newQuality = Quality.combine_qualities(map(int, anyQualities), map(int, bestQualities))

        sickrage.app.config.status_default = int(defaultStatus)
        sickrage.app.config.status_default_after = int(defaultStatusAfter)
        sickrage.app.config.quality_default = int(newQuality)

        sickrage.app.config.flatten_folders_default = checkbox_to_value(
            defaultFlattenFolders)
        sickrage.app.config.subtitles_default = checkbox_to_value(subtitles)

        sickrage.app.config.anime_default = checkbox_to_value(anime)
        sickrage.app.config.scene_default = checkbox_to_value(scene)
        sickrage.app.config.skip_downloaded_default = checkbox_to_value(skip_downloaded)
        sickrage.app.config.add_show_year_default = checkbox_to_value(add_show_year)

        sickrage.app.config.save()

    def saveGeneral(self, log_dir=None, log_nr=5, log_size=1048576, web_port=None, web_log=None,
                    web_ipv6=None, trash_remove_show=None, trash_rotate_logs=None,
                    update_frequency=None, skip_removed_files=None, indexerDefaultLang='en',
                    ep_default_deleted_status=None, launch_browser=None, showupdate_hour=3,
                    api_key=None, indexer_default=None, timezone_display=None, cpu_preset='NORMAL',
                    version_notify=None, enable_https=None, https_cert=None, https_key=None, handle_reverse_proxy=None,
                    sort_article=None, auto_update=None, notify_on_update=None, proxy_setting=None, proxy_indexers=None,
                    anon_redirect=None, git_path=None, pip3_path=None, calendar_unprotected=None, calendar_icons=None,
                    debug=None, ssl_verify=None, no_restart=None, coming_eps_missed_range=None, filter_row=None,
                    fuzzy_dating=None, trim_zero=None, date_preset=None, date_preset_na=None, time_preset=None,
                    indexer_timeout=None, download_url=None, rootDir=None, theme_name=None, default_page=None,
                    git_reset=None, git_username=None, git_password=None, git_autoissues=None, gui_language=None,
                    display_all_seasons=None, showupdate_stale=None, notify_on_login=None, allowed_video_file_exts=None,
                    enable_api_providers_cache=None, enable_upnp=None, web_external_port=None,
                    strip_special_file_bits=None, **kwargs):

        results = []

        # API
        sickrage.app.config.enable_api_providers_cache = checkbox_to_value(enable_api_providers_cache)

        # Language
        sickrage.app.config.change_gui_lang(gui_language)

        # Debug
        sickrage.app.config.debug = checkbox_to_value(debug)
        sickrage.app.log.set_level()

        # Misc
        sickrage.app.config.enable_upnp = checkbox_to_value(enable_upnp)
        sickrage.app.config.download_url = download_url
        sickrage.app.config.indexer_default_language = indexerDefaultLang
        sickrage.app.config.ep_default_deleted_status = ep_default_deleted_status
        sickrage.app.config.skip_removed_files = checkbox_to_value(skip_removed_files)
        sickrage.app.config.launch_browser = checkbox_to_value(launch_browser)
        sickrage.app.config.change_showupdate_hour(showupdate_hour)
        sickrage.app.config.change_version_notify(checkbox_to_value(version_notify))
        sickrage.app.config.auto_update = checkbox_to_value(auto_update)
        sickrage.app.config.notify_on_update = checkbox_to_value(notify_on_update)
        sickrage.app.config.notify_on_login = checkbox_to_value(notify_on_login)
        sickrage.app.config.showupdate_stale = checkbox_to_value(showupdate_stale)
        sickrage.app.config.log_nr = log_nr
        sickrage.app.config.log_size = log_size

        sickrage.app.config.trash_remove_show = checkbox_to_value(trash_remove_show)
        sickrage.app.config.trash_rotate_logs = checkbox_to_value(trash_rotate_logs)
        sickrage.app.config.change_updater_freq(update_frequency)
        sickrage.app.config.launch_browser = checkbox_to_value(launch_browser)
        sickrage.app.config.sort_article = checkbox_to_value(sort_article)
        sickrage.app.config.cpu_preset = cpu_preset
        sickrage.app.config.anon_redirect = anon_redirect
        sickrage.app.config.proxy_setting = proxy_setting
        sickrage.app.config.proxy_indexers = checkbox_to_value(proxy_indexers)
        sickrage.app.config.git_username = git_username
        sickrage.app.config.git_password = git_password
        sickrage.app.config.git_reset = 1
        sickrage.app.config.git_autoissues = checkbox_to_value(git_autoissues)
        sickrage.app.config.git_path = git_path
        sickrage.app.config.pip3_path = pip3_path
        sickrage.app.config.calendar_unprotected = checkbox_to_value(calendar_unprotected)
        sickrage.app.config.calendar_icons = checkbox_to_value(calendar_icons)
        sickrage.app.config.no_restart = checkbox_to_value(no_restart)

        sickrage.app.config.ssl_verify = checkbox_to_value(ssl_verify)
        sickrage.app.config.coming_eps_missed_range = try_int(coming_eps_missed_range, 7)
        sickrage.app.config.display_all_seasons = checkbox_to_value(display_all_seasons)

        sickrage.app.config.web_port = try_int(web_port)
        sickrage.app.config.web_ipv6 = checkbox_to_value(web_ipv6)

        sickrage.app.config.filter_row = checkbox_to_value(filter_row)
        sickrage.app.config.fuzzy_dating = checkbox_to_value(fuzzy_dating)
        sickrage.app.config.trim_zero = checkbox_to_value(trim_zero)

        sickrage.app.config.allowed_video_file_exts = [x.lower() for x in allowed_video_file_exts.split(',')]

        sickrage.app.config.strip_special_file_bits = checkbox_to_value(strip_special_file_bits)

        # sickrage.app.config.change_web_external_port(web_external_port)

        if date_preset:
            sickrage.app.config.date_preset = date_preset

        if indexer_default:
            sickrage.app.config.indexer_default = try_int(indexer_default)

        if indexer_timeout:
            sickrage.app.config.indexer_timeout = try_int(indexer_timeout)

        if time_preset:
            sickrage.app.config.time_preset_w_seconds = time_preset
            sickrage.app.config.time_preset = sickrage.app.config.time_preset_w_seconds.replace(":%S", "")

        sickrage.app.config.timezone_display = timezone_display

        sickrage.app.config.api_key = api_key

        sickrage.app.config.enable_https = checkbox_to_value(enable_https)

        if not sickrage.app.config.change_https_cert(https_cert):
            results += [
                "Unable to create directory " + os.path.normpath(https_cert) + ", https cert directory not changed."]

        if not sickrage.app.config.change_https_key(https_key):
            results += [
                "Unable to create directory " + os.path.normpath(https_key) + ", https key directory not changed."]

        sickrage.app.config.handle_reverse_proxy = checkbox_to_value(handle_reverse_proxy)

        sickrage.app.config.theme_name = theme_name

        sickrage.app.config.default_page = default_page

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[GENERAL] Configuration Saved'),
                                        os.path.join(sickrage.app.config_file))

        return self.redirect("/config/general/")


@Route('/config/backuprestore(/?.*)')
class ConfigBackupRestore(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigBackupRestore, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/backup_restore.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Backup/Restore'),
            header=_('Backup/Restore'),
            topmenu='config',
            controller='config',
            action='backup_restore'
        )

    @staticmethod
    def backup(backupDir=None):
        finalResult = ''

        if backupDir:
            if backupSR(backupDir):
                finalResult += _("Backup SUCCESSFUL")
            else:
                finalResult += _("Backup FAILED!")
        else:
            finalResult += _("You need to choose a folder to save your backup to first!")

        finalResult += "<br>\n"

        return finalResult

    @staticmethod
    def restore(backupFile=None, restore_database=None, restore_config=None, restore_cache=None):
        finalResult = ''

        if backupFile:
            source = backupFile
            target_dir = os.path.join(sickrage.app.data_dir, 'restore')

            restore_database = checkbox_to_value(restore_database)
            restore_config = checkbox_to_value(restore_config)
            restore_cache = checkbox_to_value(restore_cache)

            if restoreConfigZip(source, target_dir, restore_database, restore_config, restore_cache):
                finalResult += _("Successfully extracted restore files to " + target_dir)
                finalResult += _("<br>Restart sickrage to complete the restore.")
            else:
                finalResult += _("Restore FAILED")
        else:
            finalResult += _("You need to select a backup file to restore!")

        finalResult += "<br>\n"

        return finalResult

    def saveBackupRestore(self, **kwargs):
        return self.redirect("/config/backuprestore/")


@Route('/config/search(/?.*)')
class ConfigSearch(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSearch, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/search.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Search Clients'),
            header=_('Search Clients'),
            topmenu='config',
            controller='config',
            action='search'
        )

    def saveSearch(self, use_nzbs=None, use_torrents=None, nzb_dir=None, sab_username=None, sab_password=None,
                   sab_apikey=None, sab_category=None, sab_category_anime=None, sab_category_backlog=None,
                   sab_category_anime_backlog=None, sab_host=None, nzbget_username=None,
                   nzbget_password=None, nzbget_category=None, nzbget_category_backlog=None, nzbget_category_anime=None,
                   nzbget_category_anime_backlog=None, nzbget_priority=None,
                   nzbget_host=None, nzbget_use_https=None, backlog_frequency=None,
                   dailysearch_frequency=None, nzb_method=None, torrent_method=None, usenet_retention=None,
                   download_propers=None, check_propers_interval=None, allow_high_priority=None, sab_forced=None,
                   randomize_providers=None, use_failed_snatcher=None, failed_snatch_age=None,
                   torrent_dir=None, torrent_username=None, torrent_password=None, torrent_host=None,
                   torrent_label=None, torrent_label_anime=None, torrent_path=None, torrent_verify_cert=None,
                   torrent_seed_time=None, torrent_paused=None, torrent_high_bandwidth=None,
                   torrent_rpcurl=None, torrent_auth_type=None, ignore_words=None, require_words=None,
                   ignored_subs_list=None, enable_rss_cache=None,
                   torrent_file_to_magnet=None, download_unverified_magnet_link=None):

        results = []

        if not sickrage.app.config.change_nzb_dir(nzb_dir):
            results += [_("Unable to create directory ") + os.path.normpath(nzb_dir) + _(", dir not changed.")]

        if not sickrage.app.config.change_torrent_dir(torrent_dir):
            results += [_("Unable to create directory ") + os.path.normpath(torrent_dir) + _(", dir not changed.")]

        sickrage.app.config.change_failed_snatch_age(failed_snatch_age)
        sickrage.app.config.use_failed_snatcher = checkbox_to_value(use_failed_snatcher)
        sickrage.app.config.change_daily_searcher_freq(dailysearch_frequency)
        sickrage.app.config.change_backlog_searcher_freq(backlog_frequency)
        sickrage.app.config.use_nzbs = checkbox_to_value(use_nzbs)
        sickrage.app.config.use_torrents = checkbox_to_value(use_torrents)
        sickrage.app.config.nzb_method = nzb_method
        sickrage.app.config.torrent_method = torrent_method
        sickrage.app.config.usenet_retention = try_int(usenet_retention, 500)
        sickrage.app.config.ignore_words = ignore_words if ignore_words else ""
        sickrage.app.config.require_words = require_words if require_words else ""
        sickrage.app.config.ignored_subs_list = ignored_subs_list if ignored_subs_list else ""
        sickrage.app.config.randomize_providers = checkbox_to_value(randomize_providers)
        sickrage.app.config.enable_rss_cache = checkbox_to_value(enable_rss_cache)
        sickrage.app.config.torrent_file_to_magnet = checkbox_to_value(torrent_file_to_magnet)
        sickrage.app.config.download_unverified_magnet_link = checkbox_to_value(download_unverified_magnet_link)
        sickrage.app.config.download_propers = checkbox_to_value(download_propers)
        sickrage.app.config.proper_searcher_interval = check_propers_interval
        sickrage.app.config.allow_high_priority = checkbox_to_value(allow_high_priority)
        sickrage.app.config.sab_username = sab_username
        sickrage.app.config.sab_password = sab_password
        sickrage.app.config.sab_apikey = sab_apikey.strip()
        sickrage.app.config.sab_category = sab_category
        sickrage.app.config.sab_category_backlog = sab_category_backlog
        sickrage.app.config.sab_category_anime = sab_category_anime
        sickrage.app.config.sab_category_anime_backlog = sab_category_anime_backlog
        sickrage.app.config.sab_host = clean_url(sab_host)
        sickrage.app.config.sab_forced = checkbox_to_value(sab_forced)
        sickrage.app.config.nzbget_username = nzbget_username
        sickrage.app.config.nzbget_password = nzbget_password
        sickrage.app.config.nzbget_category = nzbget_category
        sickrage.app.config.nzbget_category_backlog = nzbget_category_backlog
        sickrage.app.config.nzbget_category_anime = nzbget_category_anime
        sickrage.app.config.nzbget_category_anime_backlog = nzbget_category_anime_backlog
        sickrage.app.config.nzbget_host = clean_host(nzbget_host)
        sickrage.app.config.nzbget_use_https = checkbox_to_value(nzbget_use_https)
        sickrage.app.config.nzbget_priority = try_int(nzbget_priority, 100)
        sickrage.app.config.torrent_username = torrent_username
        sickrage.app.config.torrent_password = torrent_password
        sickrage.app.config.torrent_label = torrent_label
        sickrage.app.config.torrent_label_anime = torrent_label_anime
        sickrage.app.config.torrent_verify_cert = checkbox_to_value(torrent_verify_cert)
        sickrage.app.config.torrent_path = torrent_path.rstrip('/\\')
        sickrage.app.config.torrent_seed_time = torrent_seed_time
        sickrage.app.config.torrent_paused = checkbox_to_value(torrent_paused)
        sickrage.app.config.torrent_high_bandwidth = checkbox_to_value(torrent_high_bandwidth)
        sickrage.app.config.torrent_host = clean_url(torrent_host)
        sickrage.app.config.torrent_rpcurl = torrent_rpcurl
        sickrage.app.config.torrent_auth_type = torrent_auth_type

        torrent_webui_url(True)

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[SEARCH] Configuration Saved'),
                                        os.path.join(sickrage.app.config_file))

        return self.redirect("/config/search/")


@Route('/config/postProcessing(/?.*)')
class ConfigPostProcessing(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigPostProcessing, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/postprocessing.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Post Processing'),
            header=_('Post Processing'),
            topmenu='config',
            controller='config',
            action='postprocessing'
        )

    def savePostProcessing(self, naming_pattern=None, naming_multi_ep=None,
                           kodi_data=None, kodi_12plus_data=None,
                           mediabrowser_data=None, sony_ps3_data=None,
                           wdtv_data=None, tivo_data=None, mede8er_data=None,
                           keep_processed_dir=None, process_method=None,
                           del_rar_contents=None, process_automatically=None,
                           no_delete=None, rename_episodes=None, airdate_episodes=None,
                           file_timestamp_timezone=None, unpack=None, move_associated_files=None,
                           sync_files=None, postpone_if_sync_files=None, nfo_rename=None,
                           tv_download_dir=None, naming_custom_abd=None, naming_anime=None,
                           create_missing_show_dirs=None, add_shows_wo_dir=None,
                           naming_abd_pattern=None, naming_strip_year=None,
                           delete_failed=None, extra_scripts=None,
                           naming_custom_sports=None, naming_sports_pattern=None,
                           naming_custom_anime=None, naming_anime_pattern=None,
                           naming_anime_multi_ep=None, autopostprocessor_frequency=None,
                           delete_non_associated_files=None, allowed_extensions=None,
                           processor_follow_symlinks=None, unpack_dir=None):

        results = []

        if not sickrage.app.config.change_tv_download_dir(tv_download_dir):
            results += [_("Unable to create directory ") + os.path.normpath(tv_download_dir) + _(", dir not changed.")]

        sickrage.app.config.change_autopostprocessor_freq(autopostprocessor_frequency)
        sickrage.app.config.process_automatically = checkbox_to_value(process_automatically)

        if unpack:
            if self.isRarSupported() != 'not supported':
                sickrage.app.config.unpack = checkbox_to_value(unpack)
                sickrage.app.config.unpack_dir = unpack_dir
            else:
                sickrage.app.config.unpack = 0
                results.append(_("Unpacking Not Supported, disabling unpack setting"))
        else:
            sickrage.app.config.unpack = checkbox_to_value(unpack)

        sickrage.app.config.no_delete = checkbox_to_value(no_delete)
        sickrage.app.config.keep_processed_dir = checkbox_to_value(keep_processed_dir)
        sickrage.app.config.create_missing_show_dirs = checkbox_to_value(create_missing_show_dirs)
        sickrage.app.config.add_shows_wo_dir = checkbox_to_value(add_shows_wo_dir)
        sickrage.app.config.process_method = process_method
        sickrage.app.config.delrarcontents = checkbox_to_value(del_rar_contents)
        sickrage.app.config.extra_scripts = [x.strip() for x in extra_scripts.split('|') if x.strip()]
        sickrage.app.config.rename_episodes = checkbox_to_value(rename_episodes)
        sickrage.app.config.airdate_episodes = checkbox_to_value(airdate_episodes)
        sickrage.app.config.file_timestamp_timezone = file_timestamp_timezone
        sickrage.app.config.move_associated_files = checkbox_to_value(move_associated_files)
        sickrage.app.config.sync_files = sync_files
        sickrage.app.config.postpone_if_sync_files = checkbox_to_value(postpone_if_sync_files)
        sickrage.app.config.allowed_extensions = ','.join(
            {x.strip() for x in allowed_extensions.split(',') if x.strip()})
        sickrage.app.config.naming_custom_abd = checkbox_to_value(naming_custom_abd)
        sickrage.app.config.naming_custom_sports = checkbox_to_value(naming_custom_sports)
        sickrage.app.config.naming_custom_anime = checkbox_to_value(naming_custom_anime)
        sickrage.app.config.naming_strip_year = checkbox_to_value(naming_strip_year)
        sickrage.app.config.delete_failed = checkbox_to_value(delete_failed)
        sickrage.app.config.nfo_rename = checkbox_to_value(nfo_rename)
        sickrage.app.config.delete_non_associated_files = checkbox_to_value(delete_non_associated_files)
        sickrage.app.config.processor_follow_symlinks = checkbox_to_value(processor_follow_symlinks)

        if self.isNamingValid(naming_pattern, naming_multi_ep, anime_type=naming_anime) != "invalid":
            sickrage.app.config.naming_pattern = naming_pattern
            sickrage.app.config.naming_multi_ep = int(naming_multi_ep)
            sickrage.app.config.naming_anime = int(naming_anime)
            sickrage.app.config.naming_force_folders = validator.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))
            else:
                results.append(_("You tried saving an invalid naming config, not saving your naming settings"))

        if self.isNamingValid(naming_anime_pattern, naming_anime_multi_ep, anime_type=naming_anime) != "invalid":
            sickrage.app.config.naming_anime_pattern = naming_anime_pattern
            sickrage.app.config.naming_anime_multi_ep = int(naming_anime_multi_ep)
            sickrage.app.config.naming_anime = int(naming_anime)
            sickrage.app.config.naming_force_folders = validator.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))
            else:
                results.append(_("You tried saving an invalid naming config, not saving your naming settings"))

        if self.isNamingValid(naming_abd_pattern, None, abd=True) != "invalid":
            sickrage.app.config.naming_abd_pattern = naming_abd_pattern
        else:
            results.append(
                _("You tried saving an invalid air-by-date naming config, not saving your air-by-date settings"))

        if self.isNamingValid(naming_sports_pattern, None, sports=True) != "invalid":
            sickrage.app.config.naming_sports_pattern = naming_sports_pattern
        else:
            results.append(
                _("You tried saving an invalid sports naming config, not saving your sports settings"))

        sickrage.app.metadata_providers['kodi'].set_config(kodi_data)
        sickrage.app.metadata_providers['kodi_12plus'].set_config(kodi_12plus_data)
        sickrage.app.metadata_providers['mediabrowser'].set_config(mediabrowser_data)
        sickrage.app.metadata_providers['sony_ps3'].set_config(sony_ps3_data)
        sickrage.app.metadata_providers['wdtv'].set_config(wdtv_data)
        sickrage.app.metadata_providers['tivo'].set_config(tivo_data)
        sickrage.app.metadata_providers['mede8er'].set_config(mede8er_data)

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.warning(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[POST-PROCESSING] Configuration Saved'),
                                        os.path.join(sickrage.app.config_file))

        return self.redirect("/config/postProcessing/")

    @staticmethod
    def testNaming(pattern=None, multi=None, abd=False, sports=False, anime_type=None):

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        result = validator.test_name(pattern, multi, abd, sports, anime_type)

        result = os.path.join(result['dir'], result['name'])

        return result

    @staticmethod
    def isNamingValid(pattern=None, multi=None, abd=False, sports=False, anime_type=None):
        if pattern is None:
            return 'invalid'

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        # air by date shows just need one check, we don't need to worry about season folders
        if abd:
            is_valid = validator.check_valid_abd_naming(pattern)
            require_season_folders = False

        # sport shows just need one check, we don't need to worry about season folders
        elif sports:
            is_valid = validator.check_valid_sports_naming(pattern)
            require_season_folders = False

        else:
            # check validity of single and multi ep cases for the whole path
            is_valid = validator.check_valid_naming(pattern, multi, anime_type)

            # check validity of single and multi ep cases for only the file name
            require_season_folders = validator.check_force_season_folders(pattern, multi, anime_type)

        if is_valid and not require_season_folders:
            return 'valid'
        elif is_valid and require_season_folders:
            return 'seasonfolders'
        else:
            return 'invalid'

    @staticmethod
    def isRarSupported():
        """
        Test Packing Support:
            - Simulating in memory rar extraction on test.rar file
        """

        check = sickrage.app.config.change_unrar_tool(sickrage.app.config.unrar_tool,
                                                      sickrage.app.config.unrar_alt_tool)

        if not check:
            sickrage.app.log.warning('Looks like unrar is not installed, check failed')
        return ('not supported', 'supported')[check]


@Route('/config/providers(/?.*)')
class ConfigProviders(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigProviders, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/providers.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Search Providers'),
            header=_('Search Providers'),
            topmenu='config',
            controller='config',
            action='providers'
        )

    @staticmethod
    def canAddNewznabProvider(name):
        if not name: return json_encode({'error': 'No Provider Name specified'})

        providerObj = NewznabProvider(name, '')
        if providerObj.id not in sickrage.app.search_providers.newznab():
            return json_encode({'success': providerObj.id})
        return json_encode({'error': 'Provider Name already exists as ' + name})

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, titleTAG):
        if not name: return json_encode({'error': 'No Provider Name specified'})

        providerObj = TorrentRssProvider(name, url, cookies, titleTAG)
        if providerObj.id not in sickrage.app.search_providers.torrentrss():
            validate = providerObj.validateRSS()
            if validate['result']:
                return json_encode({'success': providerObj.id})
            return json_encode({'error': validate['message']})
        return json_encode({'error': 'Provider name already exists as {}'.format(name)})

    @staticmethod
    def getNewznabCategories(name, url, key):
        """
        Retrieves a list of possible categories with category id's
        Using the default url/api?cat
        http://yournewznaburl.com/api?t=caps&apikey=yourapikey
        """

        error = ""
        success = False
        tv_categories = []

        if not name:
            error += _("\nNo Provider Name specified")
        if not url:
            error += _("\nNo Provider Url specified")
        if not key:
            error += _("\nNo Provider Api key specified")

        if not error:
            tempProvider = NewznabProvider(name, url, key)
            success, tv_categories, error = tempProvider.get_newznab_categories()
        return json_encode({'success': success, 'tv_categories': tv_categories, 'error': error})

    def saveProviders(self, **kwargs):
        results = []

        # custom providers
        custom_providers = ''
        for curProviderStr in kwargs.get('provider_strings', '').split('!!!'):
            if not len(curProviderStr):
                continue

            custom_providers += '{}!!!'.format(curProviderStr)
            cur_type, curProviderData = curProviderStr.split('|', 1)

            if cur_type == "newznab":
                cur_name, cur_url, cur_key, cur_cat = curProviderData.split('|')

                providerObj = NewznabProvider(cur_name, cur_url, cur_key, cur_cat)
                sickrage.app.search_providers.newznab().update(**{providerObj.id: providerObj})

                kwargs[providerObj.id + '_name'] = cur_name
                kwargs[providerObj.id + '_key'] = cur_key
                kwargs[providerObj.id + '_catIDs'] = cur_cat

            elif cur_type == "torrentrss":
                cur_name, cur_url, cur_cookies, cur_title_tag = curProviderData.split('|')

                providerObj = TorrentRssProvider(cur_name, cur_url, cur_cookies, cur_title_tag)
                sickrage.app.search_providers.torrentrss().update(**{providerObj.id: providerObj})

                kwargs[providerObj.id + '_name'] = cur_name
                kwargs[providerObj.id + '_cookies'] = cur_cookies
                kwargs[providerObj.id + '_curTitleTAG'] = cur_title_tag

        sickrage.app.config.custom_providers = custom_providers

        # remove providers
        for p in list(set(sickrage.app.search_providers.provider_order).difference(
                [x.split(':')[0] for x in kwargs.get('provider_order', '').split('!!!')])):
            providerObj = sickrage.app.search_providers.all()[p]
            del sickrage.app.search_providers[providerObj.type][p]

        # enable/disable/sort providers
        sickrage.app.search_providers.provider_order = []
        for curProviderStr in kwargs.get('provider_order', '').split('!!!'):
            curProvider, curEnabled = curProviderStr.split(':')
            sickrage.app.search_providers.provider_order += [curProvider]
            if curProvider in sickrage.app.search_providers.all():
                curProvObj = sickrage.app.search_providers.all()[curProvider]
                curProvObj.enabled = bool(try_int(curEnabled))

        # dynamically load provider settings
        for providerID, providerObj in sickrage.app.search_providers.all().items():
            try:
                providerSettings = {
                    'minseed': try_int(kwargs.get(providerID + '_minseed', 0)),
                    'minleech': try_int(kwargs.get(providerID + '_minleech', 0)),
                    'ratio': str(kwargs.get(providerID + '_ratio', '')).strip(),
                    'digest': str(kwargs.get(providerID + '_digest', '')).strip(),
                    'hash': str(kwargs.get(providerID + '_hash', '')).strip(),
                    'key': str(kwargs.get(providerID + '_key', '')).strip(),
                    'api_key': str(kwargs.get(providerID + '_api_key', '')).strip(),
                    'username': str(kwargs.get(providerID + '_username', '')).strip(),
                    'password': str(kwargs.get(providerID + '_password', '')).strip(),
                    'passkey': str(kwargs.get(providerID + '_passkey', '')).strip(),
                    'pin': str(kwargs.get(providerID + '_pin', '')).strip(),
                    'confirmed': checkbox_to_value(kwargs.get(providerID + '_confirmed', 0)),
                    'ranked': checkbox_to_value(kwargs.get(providerID + '_ranked', 0)),
                    'engrelease': checkbox_to_value(kwargs.get(providerID + '_engrelease', 0)),
                    'onlyspasearch': checkbox_to_value(kwargs.get(providerID + '_onlyspasearch', 0)),
                    'sorting': str(kwargs.get(providerID + '_sorting', 'seeders')).strip(),
                    'freeleech': checkbox_to_value(kwargs.get(providerID + '_freeleech', 0)),
                    'reject_m2ts': checkbox_to_value(kwargs.get(providerID + '_reject_m2ts', 0)),
                    'search_mode': str(kwargs.get(providerID + '_search_mode', 'eponly')).strip(),
                    'search_fallback': checkbox_to_value(kwargs.get(providerID + '_search_fallback', 0)),
                    'enable_daily': checkbox_to_value(kwargs.get(providerID + '_enable_daily', 0)),
                    'enable_backlog': checkbox_to_value(kwargs.get(providerID + '_enable_backlog', 0)),
                    'cat': try_int(kwargs.get(providerID + '_cat', 0)),
                    'subtitle': checkbox_to_value(kwargs.get(providerID + '_subtitle', 0)),
                    'cookies': str(kwargs.get(providerID + '_cookies', '')).strip(),
                    'custom_url': str(kwargs.get(providerID + '_custom_url', '')).strip()
                }

                # update provider object
                [setattr(providerObj, k, v) for k, v in providerSettings.items() if hasattr(providerObj, k)]
            except Exception as e:
                continue

        # save provider settings
        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[PROVIDERS] Configuration Saved'),
                                        os.path.join(sickrage.app.config_file))

        return self.redirect("/config/providers/")


@Route('/config/notifications(/?.*)')
class ConfigNotifications(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigNotifications, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/notifications.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Notifications'),
            header=_('Notifications'),
            topmenu='config',
            controller='config',
            action='notifications'
        )

    def saveNotifications(self, use_kodi=None, kodi_always_on=None, kodi_notify_onsnatch=None,
                          kodi_notify_ondownload=None, kodi_notify_onsubtitledownload=None, kodi_update_onlyfirst=None,
                          kodi_update_library=None, kodi_update_full=None, kodi_host=None, kodi_username=None,
                          kodi_password=None, use_plex=None, plex_notify_onsnatch=None, plex_notify_ondownload=None,
                          plex_notify_onsubtitledownload=None, plex_update_library=None,
                          plex_server_host=None, plex_server_token=None, plex_host=None, plex_username=None,
                          plex_password=None, use_emby=None, emby_notify_onsnatch=None,
                          emby_notify_ondownload=None, emby_notify_onsubtitledownload=None, emby_host=None,
                          emby_apikey=None, use_growl=None, growl_notify_onsnatch=None, growl_notify_ondownload=None,
                          growl_notify_onsubtitledownload=None, growl_host=None, growl_password=None,
                          use_freemobile=None, freemobile_notify_onsnatch=None, freemobile_notify_ondownload=None,
                          freemobile_notify_onsubtitledownload=None, freemobile_id=None, freemobile_apikey=None,
                          use_telegram=None, telegram_notify_onsnatch=None, telegram_notify_ondownload=None,
                          telegram_notify_onsubtitledownload=None, telegram_id=None, telegram_apikey=None,
                          use_join=None, join_notify_onsnatch=None, join_notify_ondownload=None,
                          join_notify_onsubtitledownload=None, join_id=None, join_apikey=None,
                          use_prowl=None, prowl_notify_onsnatch=None, prowl_notify_ondownload=None,
                          prowl_notify_onsubtitledownload=None, prowl_api=None, prowl_priority=0,
                          use_twitter=None, twitter_notify_onsnatch=None, twitter_notify_ondownload=None,
                          twitter_notify_onsubtitledownload=None, twitter_usedm=None, twitter_dmto=None,
                          use_twilio=None, twilio_notify_onsnatch=None, twilio_notify_ondownload=None,
                          twilio_notify_onsubtitledownload=None, twilio_phone_sid=None, twilio_account_sid=None,
                          twilio_auth_token=None, twilio_to_number=None,
                          use_boxcar2=None, boxcar2_notify_onsnatch=None, boxcar2_notify_ondownload=None,
                          boxcar2_notify_onsubtitledownload=None, boxcar2_accesstoken=None,
                          use_pushover=None, pushover_notify_onsnatch=None, pushover_notify_ondownload=None,
                          pushover_notify_onsubtitledownload=None, pushover_userkey=None, pushover_apikey=None,
                          pushover_device=None, pushover_sound=None,
                          use_libnotify=None, libnotify_notify_onsnatch=None, libnotify_notify_ondownload=None,
                          libnotify_notify_onsubtitledownload=None,
                          use_nmj=None, nmj_host=None, nmj_database=None, nmj_mount=None, use_synoindex=None,
                          use_nmjv2=None, nmjv2_host=None, nmjv2_dbloc=None, nmjv2_database=None,
                          use_trakt=None, trakt_username=None,
                          trakt_remove_watchlist=None, trakt_sync_watchlist=None, trakt_remove_show_from_sickrage=None,
                          trakt_method_add=None,
                          trakt_start_paused=None, trakt_use_recommended=None, trakt_sync=None, trakt_sync_remove=None,
                          trakt_default_indexer=None, trakt_remove_serieslist=None, trakt_timeout=None,
                          trakt_blacklist_name=None, use_synologynotifier=None, synologynotifier_notify_onsnatch=None,
                          synologynotifier_notify_ondownload=None, synologynotifier_notify_onsubtitledownload=None,
                          use_pytivo=None, pytivo_notify_onsnatch=None, pytivo_notify_ondownload=None,
                          pytivo_notify_onsubtitledownload=None, pytivo_update_library=None,
                          pytivo_host=None, pytivo_share_name=None, pytivo_tivo_name=None,
                          use_nma=None, nma_notify_onsnatch=None, nma_notify_ondownload=None,
                          nma_notify_onsubtitledownload=None, nma_api=None, nma_priority=0,
                          use_pushalot=None, pushalot_notify_onsnatch=None, pushalot_notify_ondownload=None,
                          pushalot_notify_onsubtitledownload=None, pushalot_authorizationtoken=None,
                          use_pushbullet=None, pushbullet_notify_onsnatch=None, pushbullet_notify_ondownload=None,
                          pushbullet_notify_onsubtitledownload=None, pushbullet_api=None, pushbullet_device_list=None,
                          use_email=None, email_notify_onsnatch=None, email_notify_ondownload=None,
                          email_notify_onsubtitledownload=None, email_host=None, email_port=25, email_from=None,
                          email_tls=None, email_user=None, email_password=None, email_list=None, use_slack=None,
                          slack_notify_onsnatch=None, slack_notify_ondownload=None,
                          slack_notify_onsubtitledownload=None, slack_webhook=None, use_discord=False,
                          discord_notify_onsnatch=None, discord_notify_ondownload=None,
                          discord_notify_onsubtitledownload=None, discord_webhook=None, discord_name=None,
                          discord_avatar_url=None, discord_tts=None,
                          **kwargs):

        results = []

        sickrage.app.config.use_kodi = checkbox_to_value(use_kodi)
        sickrage.app.config.kodi_always_on = checkbox_to_value(kodi_always_on)
        sickrage.app.config.kodi_notify_onsnatch = checkbox_to_value(kodi_notify_onsnatch)
        sickrage.app.config.kodi_notify_ondownload = checkbox_to_value(
            kodi_notify_ondownload)
        sickrage.app.config.kodi_notify_onsubtitledownload = checkbox_to_value(
            kodi_notify_onsubtitledownload)
        sickrage.app.config.kodi_update_library = checkbox_to_value(kodi_update_library)
        sickrage.app.config.kodi_update_full = checkbox_to_value(kodi_update_full)
        sickrage.app.config.kodi_update_onlyfirst = checkbox_to_value(
            kodi_update_onlyfirst)
        sickrage.app.config.kodi_host = clean_hosts(kodi_host)
        sickrage.app.config.kodi_username = kodi_username
        sickrage.app.config.kodi_password = kodi_password

        sickrage.app.config.use_plex = checkbox_to_value(use_plex)
        sickrage.app.config.plex_notify_onsnatch = checkbox_to_value(plex_notify_onsnatch)
        sickrage.app.config.plex_notify_ondownload = checkbox_to_value(
            plex_notify_ondownload)
        sickrage.app.config.plex_notify_onsubtitledownload = checkbox_to_value(
            plex_notify_onsubtitledownload)
        sickrage.app.config.plex_update_library = checkbox_to_value(plex_update_library)
        sickrage.app.config.plex_host = clean_hosts(plex_host)
        sickrage.app.config.plex_server_host = clean_hosts(plex_server_host)
        sickrage.app.config.plex_server_token = clean_host(plex_server_token)
        sickrage.app.config.plex_username = plex_username
        sickrage.app.config.plex_password = plex_password
        sickrage.app.config.use_plex_client = checkbox_to_value(use_plex)
        sickrage.app.config.plex_client_username = plex_username
        sickrage.app.config.plex_client_password = plex_password

        sickrage.app.config.use_emby = checkbox_to_value(use_emby)
        sickrage.app.config.emby_notify_onsnatch = checkbox_to_value(
            emby_notify_onsnatch)
        sickrage.app.config.emby_notify_ondownload = checkbox_to_value(
            emby_notify_ondownload)
        sickrage.app.config.emby_notify_onsubtitledownload = checkbox_to_value(
            emby_notify_onsubtitledownload)
        sickrage.app.config.emby_host = clean_host(emby_host)
        sickrage.app.config.emby_apikey = emby_apikey

        sickrage.app.config.use_growl = checkbox_to_value(use_growl)
        sickrage.app.config.growl_notify_onsnatch = checkbox_to_value(
            growl_notify_onsnatch)
        sickrage.app.config.growl_notify_ondownload = checkbox_to_value(
            growl_notify_ondownload)
        sickrage.app.config.growl_notify_onsubtitledownload = checkbox_to_value(
            growl_notify_onsubtitledownload)
        sickrage.app.config.growl_host = clean_host(growl_host, default_port=23053)
        sickrage.app.config.growl_password = growl_password

        sickrage.app.config.use_freemobile = checkbox_to_value(use_freemobile)
        sickrage.app.config.freemobile_notify_onsnatch = checkbox_to_value(
            freemobile_notify_onsnatch)
        sickrage.app.config.freemobile_notify_ondownload = checkbox_to_value(
            freemobile_notify_ondownload)
        sickrage.app.config.freemobile_notify_onsubtitledownload = checkbox_to_value(
            freemobile_notify_onsubtitledownload)
        sickrage.app.config.freemobile_id = freemobile_id
        sickrage.app.config.freemobile_apikey = freemobile_apikey

        sickrage.app.config.use_telegram = checkbox_to_value(use_telegram)
        sickrage.app.config.telegram_notify_onsnatch = checkbox_to_value(
            telegram_notify_onsnatch)
        sickrage.app.config.telegram_notify_ondownload = checkbox_to_value(
            telegram_notify_ondownload)
        sickrage.app.config.telegram_notify_onsubtitledownload = checkbox_to_value(
            telegram_notify_onsubtitledownload)
        sickrage.app.config.telegram_id = telegram_id
        sickrage.app.config.telegram_apikey = telegram_apikey

        sickrage.app.config.use_join = checkbox_to_value(use_join)
        sickrage.app.config.join_notify_onsnatch = checkbox_to_value(
            join_notify_onsnatch)
        sickrage.app.config.join_notify_ondownload = checkbox_to_value(
            join_notify_ondownload)
        sickrage.app.config.join_notify_onsubtitledownload = checkbox_to_value(
            join_notify_onsubtitledownload)
        sickrage.app.config.join_id = join_id
        sickrage.app.config.join_apikey = join_apikey

        sickrage.app.config.use_prowl = checkbox_to_value(use_prowl)
        sickrage.app.config.prowl_notify_onsnatch = checkbox_to_value(
            prowl_notify_onsnatch)
        sickrage.app.config.prowl_notify_ondownload = checkbox_to_value(
            prowl_notify_ondownload)
        sickrage.app.config.prowl_notify_onsubtitledownload = checkbox_to_value(
            prowl_notify_onsubtitledownload)
        sickrage.app.config.prowl_api = prowl_api
        sickrage.app.config.prowl_priority = prowl_priority

        sickrage.app.config.use_twitter = checkbox_to_value(use_twitter)
        sickrage.app.config.twitter_notify_onsnatch = checkbox_to_value(
            twitter_notify_onsnatch)
        sickrage.app.config.twitter_notify_ondownload = checkbox_to_value(
            twitter_notify_ondownload)
        sickrage.app.config.twitter_notify_onsubtitledownload = checkbox_to_value(
            twitter_notify_onsubtitledownload)
        sickrage.app.config.twitter_usedm = checkbox_to_value(twitter_usedm)
        sickrage.app.config.twitter_dmto = twitter_dmto

        sickrage.app.config.use_twilio = checkbox_to_value(use_twilio)
        sickrage.app.config.twilio_notify_onsnatch = checkbox_to_value(
            twilio_notify_onsnatch)
        sickrage.app.config.twilio_notify_ondownload = checkbox_to_value(
            twilio_notify_ondownload)
        sickrage.app.config.twilio_notify_onsubtitledownload = checkbox_to_value(
            twilio_notify_onsubtitledownload)
        sickrage.app.config.twilio_phone_sid = twilio_phone_sid
        sickrage.app.config.twilio_account_sid = twilio_account_sid
        sickrage.app.config.twilio_auth_token = twilio_auth_token
        sickrage.app.config.twilio_to_number = twilio_to_number

        sickrage.app.config.use_slack = checkbox_to_value(use_slack)
        sickrage.app.config.slack_notify_onsnatch = checkbox_to_value(
            slack_notify_onsnatch)
        sickrage.app.config.slack_notify_ondownload = checkbox_to_value(
            slack_notify_ondownload)
        sickrage.app.config.slack_notify_onsubtitledownload = checkbox_to_value(
            slack_notify_onsubtitledownload)
        sickrage.app.config.slack_webhook = slack_webhook

        sickrage.app.config.use_discord = checkbox_to_value(use_discord)
        sickrage.app.config.discord_notify_onsnatch = checkbox_to_value(
            discord_notify_onsnatch)
        sickrage.app.config.discord_notify_ondownload = checkbox_to_value(
            discord_notify_ondownload)
        sickrage.app.config.discord_notify_onsubtitledownload = checkbox_to_value(
            discord_notify_onsubtitledownload)
        sickrage.app.config.discord_webhook = discord_webhook
        sickrage.app.config.discord_name = discord_name
        sickrage.app.config.discord_avatar_url = discord_avatar_url
        sickrage.app.config.discord_tts = checkbox_to_value(discord_tts)

        sickrage.app.config.use_boxcar2 = checkbox_to_value(use_boxcar2)
        sickrage.app.config.boxcar2_notify_onsnatch = checkbox_to_value(
            boxcar2_notify_onsnatch)
        sickrage.app.config.boxcar2_notify_ondownload = checkbox_to_value(
            boxcar2_notify_ondownload)
        sickrage.app.config.boxcar2_notify_onsubtitledownload = checkbox_to_value(
            boxcar2_notify_onsubtitledownload)
        sickrage.app.config.boxcar2_accesstoken = boxcar2_accesstoken

        sickrage.app.config.use_pushover = checkbox_to_value(use_pushover)
        sickrage.app.config.pushover_notify_onsnatch = checkbox_to_value(
            pushover_notify_onsnatch)
        sickrage.app.config.pushover_notify_ondownload = checkbox_to_value(
            pushover_notify_ondownload)
        sickrage.app.config.pushover_notify_onsubtitledownload = checkbox_to_value(
            pushover_notify_onsubtitledownload)
        sickrage.app.config.pushover_userkey = pushover_userkey
        sickrage.app.config.pushover_apikey = pushover_apikey
        sickrage.app.config.pushover_device = pushover_device
        sickrage.app.config.pushover_sound = pushover_sound

        sickrage.app.config.use_libnotify = checkbox_to_value(use_libnotify)
        sickrage.app.config.libnotify_notify_onsnatch = checkbox_to_value(
            libnotify_notify_onsnatch)
        sickrage.app.config.libnotify_notify_ondownload = checkbox_to_value(
            libnotify_notify_ondownload)
        sickrage.app.config.libnotify_notify_onsubtitledownload = checkbox_to_value(
            libnotify_notify_onsubtitledownload)

        sickrage.app.config.use_nmj = checkbox_to_value(use_nmj)
        sickrage.app.config.nmj_host = clean_host(nmj_host)
        sickrage.app.config.nmj_database = nmj_database
        sickrage.app.config.nmj_mount = nmj_mount

        sickrage.app.config.use_nmjv2 = checkbox_to_value(use_nmjv2)
        sickrage.app.config.nmjv2_host = clean_host(nmjv2_host)
        sickrage.app.config.nmjv2_database = nmjv2_database
        sickrage.app.config.nmjv2_dbloc = nmjv2_dbloc

        sickrage.app.config.use_synoindex = checkbox_to_value(use_synoindex)

        sickrage.app.config.use_synologynotifier = checkbox_to_value(use_synologynotifier)
        sickrage.app.config.synologynotifier_notify_onsnatch = checkbox_to_value(
            synologynotifier_notify_onsnatch)
        sickrage.app.config.synologynotifier_notify_ondownload = checkbox_to_value(
            synologynotifier_notify_ondownload)
        sickrage.app.config.synologynotifier_notify_onsubtitledownload = checkbox_to_value(
            synologynotifier_notify_onsubtitledownload)

        sickrage.app.config.use_trakt = checkbox_to_value(use_trakt)
        sickrage.app.config.trakt_username = trakt_username
        sickrage.app.config.trakt_remove_watchlist = checkbox_to_value(
            trakt_remove_watchlist)
        sickrage.app.config.trakt_remove_serieslist = checkbox_to_value(
            trakt_remove_serieslist)
        sickrage.app.config.trakt_remove_show_from_sickrage = checkbox_to_value(
            trakt_remove_show_from_sickrage)
        sickrage.app.config.trakt_sync_watchlist = checkbox_to_value(trakt_sync_watchlist)
        sickrage.app.config.trakt_method_add = int(trakt_method_add)
        sickrage.app.config.trakt_start_paused = checkbox_to_value(trakt_start_paused)
        sickrage.app.config.trakt_use_recommended = checkbox_to_value(
            trakt_use_recommended)
        sickrage.app.config.trakt_sync = checkbox_to_value(trakt_sync)
        sickrage.app.config.trakt_sync_remove = checkbox_to_value(trakt_sync_remove)
        sickrage.app.config.trakt_default_indexer = int(trakt_default_indexer)
        sickrage.app.config.trakt_timeout = int(trakt_timeout)
        sickrage.app.config.trakt_blacklist_name = trakt_blacklist_name

        sickrage.app.config.use_email = checkbox_to_value(use_email)
        sickrage.app.config.email_notify_onsnatch = checkbox_to_value(
            email_notify_onsnatch)
        sickrage.app.config.email_notify_ondownload = checkbox_to_value(
            email_notify_ondownload)
        sickrage.app.config.email_notify_onsubtitledownload = checkbox_to_value(
            email_notify_onsubtitledownload)
        sickrage.app.config.email_host = clean_host(email_host)
        sickrage.app.config.email_port = try_int(email_port, 25)
        sickrage.app.config.email_from = email_from
        sickrage.app.config.email_tls = checkbox_to_value(email_tls)
        sickrage.app.config.email_user = email_user
        sickrage.app.config.email_password = email_password
        sickrage.app.config.email_list = email_list

        sickrage.app.config.use_pytivo = checkbox_to_value(use_pytivo)
        sickrage.app.config.pytivo_notify_onsnatch = checkbox_to_value(
            pytivo_notify_onsnatch)
        sickrage.app.config.pytivo_notify_ondownload = checkbox_to_value(
            pytivo_notify_ondownload)
        sickrage.app.config.pytivo_notify_onsubtitledownload = checkbox_to_value(
            pytivo_notify_onsubtitledownload)
        sickrage.app.config.pytivo_update_library = checkbox_to_value(
            pytivo_update_library)
        sickrage.app.config.pytivo_host = clean_host(pytivo_host)
        sickrage.app.config.pytivo_share_name = pytivo_share_name
        sickrage.app.config.pytivo_tivo_name = pytivo_tivo_name

        sickrage.app.config.use_nma = checkbox_to_value(use_nma)
        sickrage.app.config.nma_notify_onsnatch = checkbox_to_value(nma_notify_onsnatch)
        sickrage.app.config.nma_notify_ondownload = checkbox_to_value(
            nma_notify_ondownload)
        sickrage.app.config.nma_notify_onsubtitledownload = checkbox_to_value(
            nma_notify_onsubtitledownload)
        sickrage.app.config.nma_api = nma_api
        sickrage.app.config.nma_priority = nma_priority

        sickrage.app.config.use_pushalot = checkbox_to_value(use_pushalot)
        sickrage.app.config.pushalot_notify_onsnatch = checkbox_to_value(
            pushalot_notify_onsnatch)
        sickrage.app.config.pushalot_notify_ondownload = checkbox_to_value(
            pushalot_notify_ondownload)
        sickrage.app.config.pushalot_notify_onsubtitledownload = checkbox_to_value(
            pushalot_notify_onsubtitledownload)
        sickrage.app.config.pushalot_authorizationtoken = pushalot_authorizationtoken

        sickrage.app.config.use_pushbullet = checkbox_to_value(use_pushbullet)
        sickrage.app.config.pushbullet_notify_onsnatch = checkbox_to_value(
            pushbullet_notify_onsnatch)
        sickrage.app.config.pushbullet_notify_ondownload = checkbox_to_value(
            pushbullet_notify_ondownload)
        sickrage.app.config.pushbullet_notify_onsubtitledownload = checkbox_to_value(
            pushbullet_notify_onsubtitledownload)
        sickrage.app.config.pushbullet_api = pushbullet_api
        sickrage.app.config.pushbullet_device = pushbullet_device_list

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[NOTIFICATIONS] Configuration Saved'),
                                        os.path.join(sickrage.app.config_file))

        return self.redirect("/config/notifications/")


@Route('/config/subtitles(/?.*)')
class ConfigSubtitles(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSubtitles, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/subtitles.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Subtitles Settings'),
            header=_('Subtitles Settings'),
            topmenu='config',
            controller='config',
            action='subtitles'
        )

    def get_code(self, q=None, **kwargs):
        codes = [{"id": code, "name": sickrage.subtitles.name_from_code(code)} for code in
                 sickrage.subtitles.subtitle_code_filter()]

        codes = list(filter(lambda code: q.lower() in code['name'].lower(), codes))

        return json_encode(codes)

    def wanted_languages(self):
        codes = [{"id": code, "name": sickrage.subtitles.name_from_code(code)} for code in
                 sickrage.subtitles.subtitle_code_filter()]

        codes = list(filter(lambda code: code['id'] in sickrage.subtitles.wanted_languages(), codes))

        return json_encode(codes)

    def saveSubtitles(self, use_subtitles=None, subtitles_dir=None, service_order=None, subtitles_history=None,
                      subtitles_finder_frequency=None, subtitles_multi=None, embedded_subtitles_all=None,
                      subtitles_extra_scripts=None, subtitles_hearing_impaired=None, itasa_user=None, itasa_pass=None,
                      addic7ed_user=None, addic7ed_pass=None, legendastv_user=None, legendastv_pass=None,
                      opensubtitles_user=None, opensubtitles_pass=None, **kwargs):

        results = []

        sickrage.app.config.change_subtitle_searcher_freq(subtitles_finder_frequency)
        sickrage.app.config.use_subtitles = checkbox_to_value(use_subtitles)
        sickrage.app.config.subtitles_dir = subtitles_dir
        sickrage.app.config.subtitles_history = checkbox_to_value(subtitles_history)
        sickrage.app.config.embedded_subtitles_all = checkbox_to_value(embedded_subtitles_all)
        sickrage.app.config.subtitles_hearing_impaired = checkbox_to_value(subtitles_hearing_impaired)
        sickrage.app.config.subtitles_multi = checkbox_to_value(subtitles_multi)
        sickrage.app.config.subtitles_extra_scripts = [x.strip() for x in subtitles_extra_scripts.split('|') if
                                                       x.strip()]

        # Subtitle languages
        sickrage.app.config.subtitles_languages = kwargs.get('subtitles_languages[]', 'eng')
        if not isinstance(sickrage.app.config.subtitles_languages, list):
            sickrage.app.config.subtitles_languages = [sickrage.app.config.subtitles_languages]

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            curService, curEnabled = curServiceStr.split(':')
            subtitles_services_list.append(curService)
            subtitles_services_enabled.append(int(curEnabled))

        sickrage.app.config.subtitles_services_list = subtitles_services_list
        sickrage.app.config.subtitles_services_enabled = subtitles_services_enabled

        sickrage.app.config.addic7ed_user = addic7ed_user or ''
        sickrage.app.config.addic7ed_pass = addic7ed_pass or ''
        sickrage.app.config.legendastv_user = legendastv_user or ''
        sickrage.app.config.legendastv_pass = legendastv_pass or ''
        sickrage.app.config.itasa_user = itasa_user or ''
        sickrage.app.config.itasa_pass = itasa_pass or ''
        sickrage.app.config.opensubtitles_user = opensubtitles_user or ''
        sickrage.app.config.opensubtitles_pass = opensubtitles_pass or ''

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[SUBTITLES] Configuration Saved'),
                                        os.path.join(sickrage.app.config_file))

        return self.redirect("/config/subtitles/")


@Route('/config/anime(/?.*)')
class ConfigAnime(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigAnime, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/anime.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Anime'),
            header=_('Anime'),
            topmenu='config',
            controller='config',
            action='anime'
        )

    def saveAnime(self, use_anidb=None, anidb_username=None, anidb_password=None, anidb_use_mylist=None,
                  split_home=None):

        results = []

        sickrage.app.config.use_anidb = checkbox_to_value(use_anidb)
        sickrage.app.config.anidb_username = anidb_username
        sickrage.app.config.anidb_password = anidb_password
        sickrage.app.config.anidb_use_mylist = checkbox_to_value(anidb_use_mylist)
        sickrage.app.config.anime_split_home = checkbox_to_value(split_home)

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[ANIME] Configuration Saved'),
                                        os.path.join(sickrage.app.config_file))

        return self.redirect("/config/anime/")


@Route('/config/qualitySettings(/?.*)')
class ConfigQualitySettings(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigQualitySettings, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/quality_settings.mako",
            submenu=self.ConfigMenu(),
            title=_('Config - Quality Settings'),
            header=_('Quality Settings'),
            topmenu='config',
            controller='config',
            action='quality_settings'
        )

    def saveQualities(self, **kwargs):
        sickrage.app.config.quality_sizes.update(dict((int(k), int(v)) for k, v in kwargs.items()))

        sickrage.app.config.save()

        sickrage.app.alerts.message(_('[QUALITY SETTINGS] Configuration Saved'),
                                    os.path.join(sickrage.app.config_file))

        return self.redirect("/config/qualitySettings/")


@Route('/logs(/?.*)')
class Logs(WebHandler):
    def __init__(self, *args, **kwargs):
        super(Logs, self).__init__(*args, **kwargs)

    def LogsMenu(self):
        menu = [
            {'title': _('Clear All'), 'path': '/logs/clearAll/',
             'requires': self.haveErrors() or self.haveWarnings(),
             'icon': 'fas fa-trash'},
        ]

        return menu

    def index(self, level=None):
        level = int(level or sickrage.app.log.ERROR)
        return self.render(
            "/logs/errors.mako",
            header="Logs &amp; Errors",
            title="Logs &amp; Errors",
            topmenu="system",
            submenu=self.LogsMenu(),
            logLevel=level,
            controller='logs',
            action='errors'
        )

    @staticmethod
    def haveErrors():
        if len(ErrorViewer.errors) > 0:
            return True

    @staticmethod
    def haveWarnings():
        if len(WarningViewer.errors) > 0:
            return True

    def clearAll(self):
        WarningViewer.clear()
        ErrorViewer.clear()

        return self.redirect("/logs/viewlog/")

    def viewlog(self, minLevel=None, logFilter='', logSearch='', maxLines=500):
        logNameFilters = {
            '': 'No Filter',
            'DAILYSEARCHER': _('Daily Searcher'),
            'BACKLOG': _('Backlog'),
            'SHOWUPDATER': _('Show Updater'),
            'VERSIONUPDATER': _('Check Version'),
            'SHOWQUEUE': _('Show Queue'),
            'SEARCHQUEUE': _('Search Queue'),
            'FINDPROPERS': _('Find Propers'),
            'POSTPROCESSOR': _('Postprocessor'),
            'SUBTITLESEARCHER': _('Find Subtitles'),
            'TRAKTSEARCHER': _('Trakt Checker'),
            'EVENT': _('Event'),
            'ERROR': _('Error'),
            'TORNADO': _('Tornado'),
            'Thread': _('Thread'),
            'MAIN': _('Main'),
        }

        minLevel = minLevel or sickrage.app.log.INFO

        logFiles = [sickrage.app.log.logFile] + \
                   ["{}.{}".format(sickrage.app.log.logFile, x) for x in
                    range(int(sickrage.app.log.logNr))]

        levelsFiltered = '|'.join(
            [x for x in sickrage.app.log.logLevels.keys() if
             sickrage.app.log.logLevels[x] >= int(minLevel)])

        logRegex = re.compile(
            r"(?P<entry>^\d+\-\d+\-\d+\s+\d+\:\d+\:\d+\s+(?:{})[\s\S]+?(?:{})[\s\S]+?$)".format(levelsFiltered,
                                                                                                logFilter),
            re.S + re.M)

        data = []
        try:
            for logFile in [x for x in logFiles if os.path.isfile(x)]:
                data += list(reversed(re.findall("((?:^.+?{}.+?$))".format(logSearch),
                                                 "\n".join(next(readFileBuffered(logFile, reverse=True)).splitlines()),
                                                 re.M + re.I)))
                maxLines -= len(data)
                if len(data) == maxLines:
                    raise StopIteration

        except StopIteration:
            pass

        return self.render(
            "/logs/view.mako",
            header="Log File",
            title="Logs",
            topmenu="system",
            logLines="\n".join(logRegex.findall("\n".join(data))),
            minLevel=int(minLevel),
            logNameFilters=logNameFilters,
            logFilter=logFilter,
            logSearch=logSearch,
            controller='logs',
            action='view'
        )

    def submit_errors(self):
        # submitter_result, issue_id = logging.submit_errors()
        # LOGGER.warning(submitter_result, [issue_id is None])
        # submitter_notification = notifications.error if issue_id is None else notifications.message
        # submitter_notification(submitter_result)

        return self.redirect("/logs/")
