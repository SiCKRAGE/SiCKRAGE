# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import re
import threading
import time
import traceback
import urllib

import markdown2
from UnRAR2 import RarFile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date, timedelta
from dateutil import tz
from mako.exceptions import html_error_template, TemplateLookupException
from mako.lookup import TemplateLookup
from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.escape import json_encode, recursive_unicode
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.web import HTTPError, RequestHandler, authenticated

import sickrage
from api import ApiHandler
from clients import getClientIstance
from clients.sabnzbd_client import SabNZBd
from core.blackandwhitelist import BlackAndWhiteList, \
    short_group_names
from core.classes import ErrorViewer, AllShowsListUI
from core.classes import WarningViewer
from core.common import FAILED, IGNORED, Overview, Quality, SKIPPED, \
    SNATCHED, UNAIRED, WANTED, cpu_presets, statusStrings
from core.databases import failed_db, main_db
from core.exceptions import CantRefreshShowException, \
    CantUpdateShowException, EpisodeDeletedException, \
    MultipleShowObjectsException, NoNFOException, \
    ShowDirectoryNotFoundException
from core.helpers import argToBool, backupAll, check_url, \
    chmodAsParent, findCertainShow, generateApiKey, getDiskSpaceUsage, getURL, \
    get_lan_ip, makeDir, readFileBuffered, remove_article, restoreConfigZip, \
    sanitizeFileName, searchIndexerForShowID, set_up_anidb_connection, tryInt
from core.helpers.browser import foldersAtPath
from core.imdb_popular import imdb_popular
from core.nameparser import validator
from core.process_tv import processDir
from core.queues.search import BacklogQueueItem, FailedQueueItem, \
    MANUAL_SEARCH_HISTORY, ManualSearchQueueItem
from core.scene_exceptions import get_all_scene_exceptions, \
    get_scene_exceptions, update_scene_exceptions
from core.scene_numbering import get_scene_absolute_numbering, \
    get_scene_absolute_numbering_for_show, get_scene_numbering, \
    get_scene_numbering_for_show, get_xem_absolute_numbering_for_show, \
    get_xem_numbering_for_show, set_scene_numbering, xem_refresh
from core.searchers import subtitle_searcher
from core.trakt import TraktAPI, traktException
from core.tv.episode import TVEpisode
from core.tv.show import TVShow
from core.tv.show.coming_episodes import ComingEpisodes
from core.tv.show.history import History as HistoryTool
from core.ui import notifications
from core.updaters import tz_updater
from core.webserver.routes import Route
from indexers.adba import aniDBAbstracter
from providers import GenericProvider, NewznabProvider, \
    TorrentRssProvider, sortedProviderDict


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.io_loop = IOLoop.instance()
        self.executor = ThreadPoolExecutor(50)

    def initialize(self):
        self.startTime = time.time()
        self.mako_lookup = TemplateLookup(
            directories=[os.path.join(sickrage.srConfig.GUI_DIR, 'views{}'.format(os.sep))],
            module_directory=os.path.join(sickrage.srConfig.CACHE_DIR, 'mako{}'.format(os.sep)),
            format_exceptions=False,
            strict_undefined=True,
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace',
            future_imports=['unicode_literals']
        )

    @run_on_executor
    def async_call(self, function, **kwargs):
        threading.currentThread().setName("WEB")

        try:
            return recursive_unicode(function(
                **{k: ''.join(v) if isinstance(v, list) else v for k, v in recursive_unicode(kwargs.items())}))
        except Exception:
            sickrage.srLogger.debug(
                'Failed doing webui callback [{}]: {}'.format(self.request.uri, traceback.format_exc()))
            return html_error_template().render_unicode()

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if sickrage.srConfig.WEB_ROOT and self.request.uri.startswith(sickrage.srConfig.WEB_ROOT):
                url = url[len(sickrage.srConfig.WEB_ROOT) + 1:]

            if url[:3] != 'api':
                return self.redirect('/')
            else:
                self.write('Wrong API key used')

        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs[b"exc_info"]
            trace_info = ''.join(["%s<br>" % line for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br>" % (k, self.request.__dict__[k]) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.finish("""<html>
                                 <title>{}</title>
                                 <body>
                                    <h2>Error</h2>
                                    <p>{}</p>
                                    <h2>Traceback</h2>
                                    <p>{}</p>
                                    <h2>Request Info</h2>
                                    <p>{}</p>
                                    <button onclick="window.location='{}/errorlogs/';">View Log(Errors)</button>
                                 </body>
                               </html>""".format(error, error, trace_info, request_info,
                                                 sickrage.srConfig.WEB_ROOT))

    def redirect(self, url, *args, **kwargs):
        if not url.startswith(sickrage.srConfig.WEB_ROOT):
            url = sickrage.srConfig.WEB_ROOT + url
        super(BaseHandler, self).redirect(url, *args, **kwargs)

    def get_current_user(self):
        return self.get_secure_cookie('user')

    def render_string(self, template_name, **kwargs):
        template_kwargs = {
            'title': "",
            'header': "",
            'topmenu': "",
            'submenu': "",
            'srPID': sickrage.srCore.PID,
            'srRoot': sickrage.srConfig.WEB_ROOT,
            'srHttpsEnabled': sickrage.srConfig.ENABLE_HTTPS or bool(
                self.request.headers.get('X-Forwarded-Proto') == 'https'),
            'srHost': self.request.headers.get('X-Forwarded-Host', self.request.host.split(':')[0]),
            'srHttpPort': self.request.headers.get('X-Forwarded-Port', sickrage.srConfig.WEB_PORT),
            'srHttpsPort': sickrage.srConfig.WEB_PORT,
            'srHandleReverseProxy': sickrage.srConfig.HANDLE_REVERSE_PROXY,
            'srThemeName': sickrage.srConfig.THEME_NAME,
            'srDefaultPage': sickrage.srConfig.DEFAULT_PAGE,
            'numErrors': len(ErrorViewer.errors),
            'numWarnings': len(WarningViewer.errors),
            'srStartTime': self.startTime,
            'makoStartTime': time.time()
        }

        template_kwargs.update(self.get_template_namespace())
        template_kwargs.update(kwargs)

        try:
            return self.mako_lookup.get_template(template_name).render_unicode(**template_kwargs)
        except TemplateLookupException as e:
            sickrage.srLogger.error(e)
            raise

    def render(self, template_name, **kwargs):
        return self.render_string(template_name, **kwargs)


class WebHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(WebHandler, self).__init__(*args, **kwargs)

    @coroutine
    @authenticated
    def prepare(self, *args, **kwargs):
        try:
            # route -> method obj
            method = getattr(self, self.request.path.strip('/').split('/')[::-1][0].replace('.', '_'),
                             getattr(self, 'index'))

            result = yield self.async_call(method, **self.request.arguments)

            if not self._finished:
                self.finish(result)
        except Exception:
            sickrage.srLogger.debug(
                'Failed doing webui request [{}]: {}'.format(self.request.uri, traceback.format_exc()))
            raise HTTPError(404)


class LoginHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(LoginHandler, self).__init__(*args, **kwargs)

    @coroutine
    def prepare(self, *args, **kwargs):
        try:
            result = yield self.async_call(self.checkAuth)
            if not self._finished:
                self.finish(result)
        except Exception:
            sickrage.srLogger.debug(
                'Failed doing webui login request [{}]: {}'.format(self.request.uri, traceback.format_exc()))
            raise HTTPError(404)

    def checkAuth(self):
        try:
            username = self.get_argument('username', '')
            password = self.get_argument('password', '')

            if cmp([username, password],
                   [sickrage.srConfig.WEB_USERNAME, sickrage.srConfig.WEB_PASSWORD]) == 0:
                remember_me = int(self.get_argument('remember_me', default=0))
                self.set_secure_cookie('user', json_encode(sickrage.srConfig.API_KEY),
                                       expires_days=30 if remember_me > 0 else None)
                sickrage.srLogger.debug('User logged into the SiCKRAGE web interface')
                return self.redirect(self.get_argument("next", "/"))
            elif username and password:
                sickrage.srLogger.warning(
                    'User attempted a failed login to the SiCKRAGE web interface from IP: {}'.format(
                        self.request.remote_ip)
                )

            return self.render("login.mako", title="Login", header="Login", topmenu="login")
        except Exception:
            sickrage.srLogger.debug(
                'Failed doing webui login callback [{}]: {}'.format(self.request.uri, traceback.format_exc()))
            return html_error_template().render_unicode()


class LogoutHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(LogoutHandler, self).__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        self.clear_cookie("user")
        return self.redirect(self.get_argument("next", "/"))


@Route('(.*)(/?)')
class WebRoot(WebHandler):
    def __init__(self, *args, **kwargs):
        super(WebRoot, self).__init__(*args, **kwargs)

    def index(self):
        return self.redirect('/' + sickrage.srConfig.DEFAULT_PAGE + '/')

    def robots_txt(self):
        """ Keep web crawlers out """
        self.set_header('Content-Type', 'text/plain')
        return "User-agent: *\nDisallow: /"

    def apibuilder(self):
        def titler(x):
            return (remove_article(x), x)[not x or sickrage.srConfig.SORT_ARTICLE]

        myDB = main_db.MainDB(row_type='dict')
        shows = sorted(sickrage.srCore.SHOWLIST, lambda x, y: cmp(titler(x.name), titler(y.name)))
        episodes = {}

        results = myDB.select(
            'SELECT episode, season, showid '
            'FROM tv_episodes '
            'ORDER BY season ASC, episode ASC'
        )

        for result in results:
            if result[b'showid'] not in episodes:
                episodes[result[b'showid']] = {}

            if result[b'season'] not in episodes[result[b'showid']]:
                episodes[result[b'showid']][result[b'season']] = []

            episodes[result[b'showid']][result[b'season']].append(result[b'episode'])

        if len(sickrage.srConfig.API_KEY) == 32:
            apikey = sickrage.srConfig.API_KEY
        else:
            apikey = 'API Key not generated'

        return self.render('apiBuilder.mako',
                           title='API Builder',
                           header='API Builder',
                           shows=shows,
                           episodes=episodes,
                           apikey=apikey,
                           commands=ApiHandler.function_mapper)

    def setHomeLayout(self, layout):

        if layout not in ('poster', 'small', 'banner', 'simple', 'coverflow'):
            layout = 'poster'

        sickrage.srConfig.HOME_LAYOUT = layout
        # Don't redirect to default page so user can see new layout
        return self.redirect("/home/")

    @staticmethod
    def setPosterSortBy(sort):

        if sort not in ('name', 'date', 'network', 'progress'):
            sort = 'name'

        sickrage.srConfig.POSTER_SORTBY = sort
        sickrage.srConfig.save_config()

    @staticmethod
    def setPosterSortDir(direction):

        sickrage.srConfig.POSTER_SORTDIR = int(direction)
        sickrage.srConfig.save_config()

    def setHistoryLayout(self, layout):

        if layout not in ('compact', 'detailed'):
            layout = 'detailed'

        sickrage.srConfig.HISTORY_LAYOUT = layout

        return self.redirect("/history/")

    def toggleDisplayShowSpecials(self, show):

        sickrage.srConfig.DISPLAY_SHOW_SPECIALS = not sickrage.srConfig.DISPLAY_SHOW_SPECIALS

        return self.redirect("/home/displayShow?show=" + show)

    def setScheduleLayout(self, layout):
        if layout not in ('poster', 'banner', 'list', 'calendar'):
            layout = 'banner'

        if layout == 'calendar':
            sickrage.srConfig.COMING_EPS_SORT = 'date'

        sickrage.srConfig.COMING_EPS_LAYOUT = layout

        return self.redirect("/schedule/")

    def toggleScheduleDisplayPaused(self):

        sickrage.srConfig.COMING_EPS_DISPLAY_PAUSED = not sickrage.srConfig.COMING_EPS_DISPLAY_PAUSED

        return self.redirect("/schedule/")

    def setScheduleSort(self, sort):
        if sort not in ('date', 'network', 'show'):
            sort = 'date'

        if sickrage.srConfig.COMING_EPS_LAYOUT == 'calendar':
            sort \
                = 'date'

        sickrage.srConfig.COMING_EPS_SORT = sort

        return self.redirect("/schedule/")

    def schedule(self, layout=None):
        next_week = date.today() + timedelta(days=7)
        next_week1 = datetime.combine(next_week, datetime.now().replace(tzinfo=tz_updater.sr_timezone))
        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, sickrage.srConfig.COMING_EPS_SORT,
                                                     False)
        today = datetime.now().replace(tzinfo=tz_updater.sr_timezone)

        submenu = [
            {
                'title': 'Sort by:',
                'path': {
                    'Date': 'setScheduleSort/?sort=date',
                    'Show': 'setScheduleSort/?sort=show',
                    'Network': 'setScheduleSort/?sort=network',
                }
            },
            {
                'title': 'Layout:',
                'path': {
                    'Banner': 'setScheduleLayout/?layout=banner',
                    'Poster': 'setScheduleLayout/?layout=poster',
                    'List': 'setScheduleLayout/?layout=list',
                    'Calendar': 'setScheduleLayout/?layout=calendar',
                }
            },
            {
                'title': 'View Paused:',
                'path': {
                    'Hide': 'toggleScheduleDisplayPaused'
                } if sickrage.srConfig.COMING_EPS_DISPLAY_PAUSED else {
                    'Show': 'toggleScheduleDisplayPaused'
                }
            },
        ]

        # Allow local overriding of layout parameter
        if layout and layout in ('poster', 'banner', 'list', 'calendar'):
            layout = layout
        else:
            layout = sickrage.srConfig.COMING_EPS_LAYOUT

        return self.render('schedule.mako',
                           submenu=submenu,
                           next_week=next_week1,
                           today=today,
                           results=results,
                           layout=layout,
                           title='Schedule',
                           header='Schedule',
                           topmenu='schedule')


class CalendarHandler(BaseHandler):
    def prepare(self, *args, **kwargs):
        if sickrage.srConfig.CALENDAR_UNPROTECTED:
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

        sickrage.srLogger.info("Receiving iCal request from %s" % self.request.remote_ip)

        # Create a iCal string
        ical = 'BEGIN:VCALENDAR\r\n'
        ical += 'VERSION:2.0\r\n'
        ical += 'X-WR-CALNAME:SiCKRAGE\r\n'
        ical += 'X-WR-CALDESC:SiCKRAGE\r\n'
        ical += 'PRODID://Sick-Beard Upcoming Episodes//\r\n'

        # Limit dates
        past_date = (date.today() + timedelta(weeks=-52)).toordinal()
        future_date = (date.today() + timedelta(weeks=52)).toordinal()

        # Get all the shows that are not paused and are currently on air (from kjoconnor Fork)
        calendar_shows = main_db.MainDB().select(
            "SELECT show_name, indexer_id, network, airs, runtime FROM tv_shows WHERE ( status = 'Continuing' OR status = 'Returning Series' ) AND paused != '1'")
        for show in calendar_shows:
            # Get all episodes of this show airing between today and next month
            episode_list = main_db.MainDB().select(
                "SELECT indexerid, name, season, episode, description, airdate FROM tv_episodes WHERE airdate >= ? AND airdate < ? AND showid = ?",
                (past_date, future_date, int(show[b"indexer_id"])))

            utc = tz.gettz('GMT')

            for episode in episode_list:

                air_date_time = tz_updater.parse_date_time(episode[b'airdate'], show[b"airs"],
                                                           show[b'network']).astimezone(utc)
                air_date_time_end = air_date_time + timedelta(
                    minutes=tryInt(show[b"runtime"], 60))

                # Create event for episode
                ical += 'BEGIN:VEVENT\r\n'
                ical += 'DTSTART:' + air_date_time.strftime("%Y%m%d") + 'T' + air_date_time.strftime(
                    "%H%M%S") + 'Z\r\n'
                ical += 'DTEND:' + air_date_time_end.strftime(
                    "%Y%m%d") + 'T' + air_date_time_end.strftime(
                    "%H%M%S") + 'Z\r\n'
                if sickrage.srConfig.CALENDAR_ICONS:
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-ICON:https://lh3.googleusercontent.com/-Vp_3ZosvTgg/VjiFu5BzQqI/AAAAAAAA_TY/3ZL_1bC0Pgw/s16-Ic42/SiCKRAGE.png\r\n'
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-DISPLAY:CHIP\r\n'
                ical += 'SUMMARY: {0} - {1}x{2} - {3}\r\n'.format(
                    show[b'show_name'], episode[b'season'], episode[b'episode'], episode[b'name']
                )
                ical += 'UID:SiCKRAGE-' + str(date.today().isoformat()) + '-' + \
                        show[b'show_name'].replace(" ", "-") + '-E' + str(episode[b'episode']) + \
                        'S' + str(episode[b'season']) + '\r\n'
                if episode[b'description']:
                    ical += 'DESCRIPTION: {0} on {1} \\n\\n {2}\r\n'.format(
                        (show[b'airs'] or '(Unknown airs)'),
                        (show[b'network'] or 'Unknown network'),
                        episode[b'description'].splitlines()[0])
                else:
                    ical += 'DESCRIPTION:' + (show[b'airs'] or '(Unknown airs)') + ' on ' + (
                        show[b'network'] or 'Unknown network') + '\r\n'

                ical += 'END:VEVENT\r\n'

        # Ending the iCal
        ical += 'END:VCALENDAR'

        return ical


@Route('/ui(/?.*)')
class UI(WebRoot):
    def __init__(self, *args, **kwargs):
        super(UI, self).__init__(*args, **kwargs)
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")

    @staticmethod
    def add_message():
        notifications.message('Test 1', 'This is test number 1')
        notifications.error('Test 2', 'This is test number 2')
        return "ok"

    def get_messages(self):
        messages = {}
        cur_notification_num = 0
        for cur_notification in notifications.get_notifications(self.request.remote_ip):
            cur_notification_num += 1
            messages['notification-{}'.format(cur_notification_num)] = {
                'title': cur_notification.title,
                'message': cur_notification.message,
                'type': cur_notification.type
            }

        try:
            return json_encode(messages)
        except:
            pass


@Route('/browser(/?.*)')
class WebFileBrowser(WebRoot):
    def __init__(self, *args, **kwargs):
        super(WebFileBrowser, self).__init__(*args, **kwargs)

    def index(self, path='', includeFiles=False, *args, **kwargs):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")
        return json_encode(foldersAtPath(path, True, bool(int(includeFiles))))

    def complete(self, term, includeFiles=0, *args, **kwargs):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")
        paths = [entry[b'path'] for entry in
                 foldersAtPath(os.path.dirname(term), includeFiles=bool(int(includeFiles))) if 'path' in entry]

        return json_encode(paths)


@Route('/home(/?.*)')
class Home(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Home, self).__init__(*args, **kwargs)

    def _genericMessage(self, subject, message):
        return self.render("genericMessage.mako",
                           message=message,
                           subject=subject,
                           topmenu="home",
                           title="")

    @staticmethod
    def _getEpisode(show, season=None, episode=None, absolute=None):
        if show is None:
            return "Invalid show parameters"

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if showObj is None:
            return "Invalid show paramaters"

        if absolute:
            epObj = showObj.getEpisode(absolute_number=int(absolute))
        elif season and episode:
            epObj = showObj.getEpisode(int(season), int(episode))
        else:
            return "Invalid paramaters"

        if epObj is None:
            return "Episode couldn't be retrieved"

        return epObj

    def index(self):
        if sickrage.srConfig.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in sickrage.srCore.SHOWLIST:
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)
            showlists = [["Shows", shows], ["Anime", anime]]
        else:
            showlists = [["Shows", sickrage.srCore.SHOWLIST]]

        stats = self.show_statistics()
        return self.render("home.mako",
                           title="Home",
                           header="Show List",
                           topmenu="home",
                           showlists=showlists,
                           show_stat=stats[0],
                           max_download_count=stats[1])

    @staticmethod
    def show_statistics():
        today = str(date.today().toordinal())

        status_quality = '(' + ','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER]) + ')'
        status_download = '(' + ','.join([str(x) for x in Quality.DOWNLOADED + Quality.ARCHIVED]) + ')'

        sql_statement = 'SELECT showid, '

        sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_quality + ') AS ep_snatched, '
        sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_download + ') AS ep_downloaded, '
        sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 '
        sql_statement += ' AND ((airdate <= ' + today + ' AND (status = ' + str(SKIPPED) + ' OR status = ' + str(
            WANTED) + ' OR status = ' + str(FAILED) + ')) '
        sql_statement += ' OR (status IN ' + status_quality + ') OR (status IN ' + status_download + '))) AS ep_total, '

        sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate >= ' + today + ' AND (status = ' + str(
            UNAIRED) + ' OR status = ' + str(WANTED) + ') ORDER BY airdate ASC LIMIT 1) AS ep_airs_next, '
        sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate > 1 AND status <> ' + str(
            UNAIRED) + ' ORDER BY airdate DESC LIMIT 1) AS ep_airs_prev '
        sql_statement += ' FROM tv_episodes tv_eps GROUP BY showid'

        sql_result = main_db.MainDB().select(sql_statement)

        show_stat = {}
        max_download_count = 1000
        for cur_result in sql_result:
            show_stat[cur_result[b'showid']] = cur_result
            if cur_result[b'ep_total'] > max_download_count:
                max_download_count = cur_result[b'ep_total']

        max_download_count *= 100

        return show_stat, max_download_count

    def is_alive(self, *args, **kwargs):
        if 'callback' in kwargs and '_' in kwargs:
            callback, _ = kwargs['callback'], kwargs['_']
        else:
            return "Error: Unsupported Request. Send jsonp request with 'callback' variable in the query string."

        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header('Content-Type', 'text/javascript')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with')

        if sickrage.srConfig.STARTED:
            return callback + '(' + json_encode({"msg": str(sickrage.srCore.PID)}) + ');'
        else:
            return callback + '(' + json_encode({"msg": "nope"}) + ');'

    @staticmethod
    def haveKODI():
        return sickrage.srConfig.USE_KODI and sickrage.srConfig.KODI_UPDATE_LIBRARY

    @staticmethod
    def havePLEX():
        return sickrage.srConfig.USE_PLEX and sickrage.srConfig.PLEX_UPDATE_LIBRARY

    @staticmethod
    def haveEMBY():
        return sickrage.srConfig.USE_EMBY

    @staticmethod
    def haveTORRENT():
        if sickrage.srConfig.USE_TORRENTS and sickrage.srConfig.TORRENT_METHOD != 'blackhole' and \
                (sickrage.srConfig.ENABLE_HTTPS and sickrage.srConfig.TORRENT_HOST[:5] == 'https' or not
                sickrage.srConfig.ENABLE_HTTPS and sickrage.srConfig.TORRENT_HOST[:5] == 'http:'):
            return True
        else:
            return False

    @staticmethod
    def testSABnzbd(host=None, username=None, password=None, apikey=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = sickrage.srConfig.clean_url(host)

        connection, accesMsg = SabNZBd.getSabAccesMethod(host, username, password, apikey)
        if connection:
            authed, authMsg = SabNZBd.testAuthentication(host, username, password, apikey)  # @UnusedVariable
            if authed:
                return "Success. Connected and authenticated"
            else:
                return "Authentication failed. SABnzbd expects '" + accesMsg + "' as authentication method, '" + authMsg + "'"
        else:
            return "Unable to connect to host"

    @staticmethod
    def testTorrent(torrent_method=None, host=None, username=None, password=None):

        host = sickrage.srConfig.clean_url(host)

        client = getClientIstance(torrent_method)

        _, accesMsg = client(host, username, password).testAuthentication()

        return accesMsg

    @staticmethod
    def testFreeMobile(freemobile_id=None, freemobile_apikey=None):

        result, message = sickrage.srCore.NOTIFIERS.freemobile_notifier.test_notify(freemobile_id, freemobile_apikey)
        if result:
            return "SMS sent successfully"
        else:
            return "Problem sending SMS: " + message

    @staticmethod
    def testGrowl(host=None, password=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = sickrage.srConfig.clean_host(host, default_port=23053)

        result = sickrage.srCore.NOTIFIERS.growl_notifier.test_notify(host, password)
        if password is None or password == '':
            pw_append = ''
        else:
            pw_append = " with password: " + password

        if result:
            return "Registered and Tested growl successfully " + urllib.unquote_plus(host) + pw_append
        else:
            return "Registration and Testing of growl failed " + urllib.unquote_plus(host) + pw_append

    @staticmethod
    def testProwl(prowl_api=None, prowl_priority=0):

        result = sickrage.srCore.NOTIFIERS.prowl_notifier.test_notify(prowl_api, prowl_priority)
        if result:
            return "Test prowl notice sent successfully"
        else:
            return "Test prowl notice failed"

    @staticmethod
    def testBoxcar(username=None):

        result = sickrage.srCore.NOTIFIERS.boxcar_notifier.test_notify(username)
        if result:
            return "Boxcar notification succeeded. Check your Boxcar clients to make sure it worked"
        else:
            return "Error sending Boxcar notification"

    @staticmethod
    def testBoxcar2(accesstoken=None):

        result = sickrage.srCore.NOTIFIERS.boxcar2_notifier.test_notify(accesstoken)
        if result:
            return "Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked"
        else:
            return "Error sending Boxcar2 notification"

    @staticmethod
    def testPushover(userKey=None, apiKey=None):

        result = sickrage.srCore.NOTIFIERS.pushover_notifier.test_notify(userKey, apiKey)
        if result:
            return "Pushover notification succeeded. Check your Pushover clients to make sure it worked"
        else:
            return "Error sending Pushover notification"

    @staticmethod
    def twitterStep1():
        return sickrage.srCore.NOTIFIERS.twitter_notifier._get_authorization()

    @staticmethod
    def twitterStep2(key):

        result = sickrage.srCore.NOTIFIERS.twitter_notifier._get_credentials(key)
        sickrage.srLogger.info("result: " + str(result))
        if result:
            return "Key verification successful"
        else:
            return "Unable to verify key"

    @staticmethod
    def testTwitter():

        result = sickrage.srCore.NOTIFIERS.twitter_notifier.test_notify()
        if result:
            return "Tweet successful, check your twitter to make sure it worked"
        else:
            return "Error sending tweet"

    @staticmethod
    def testKODI(host=None, username=None, password=None):

        host = sickrage.srConfig.clean_hosts(host)
        finalResult = ''
        for curHost in [x.strip() for x in host.split(",")]:
            curResult = sickrage.srCore.NOTIFIERS.kodi_notifier.test_notify(urllib.unquote_plus(curHost), username,
                                                                            password)
            if len(curResult.split(":")) > 2 and 'OK' in curResult.split(":")[2]:
                finalResult += "Test KODI notice sent successfully to " + urllib.unquote_plus(curHost)
            else:
                finalResult += "Test KODI notice failed to " + urllib.unquote_plus(curHost)
            finalResult += "<br>\n"

        return finalResult

    def testPMC(self, host=None, username=None, password=None):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if None is not password and set('*') == set(password):
            password = sickrage.srConfig.PLEX_CLIENT_PASSWORD

        finalResult = ''
        for curHost in [x.strip() for x in host.split(',')]:
            curResult = sickrage.srCore.NOTIFIERS.plex_notifier.test_notify_pmc(urllib.unquote_plus(curHost), username,
                                                                                password)
            if len(curResult.split(':')) > 2 and 'OK' in curResult.split(':')[2]:
                finalResult += 'Successful test notice sent to Plex client ... ' + urllib.unquote_plus(curHost)
            else:
                finalResult += 'Test failed for Plex client ... ' + urllib.unquote_plus(curHost)
            finalResult += '<br>' + '\n'

        notifications.message('Tested Plex client(s): ', urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    def testPMS(self, host=None, username=None, password=None, plex_server_token=None):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if password is not None and set('*') == set(password):
            password = sickrage.srConfig.PLEX_PASSWORD

        finalResult = ''

        curResult = sickrage.srCore.NOTIFIERS.plex_notifier.test_notify_pms(urllib.unquote_plus(host), username,
                                                                            password,
                                                                            plex_server_token)
        if curResult is None:
            finalResult += 'Successful test of Plex server(s) ... ' + urllib.unquote_plus(host.replace(',', ', '))
        elif curResult is False:
            finalResult += 'Test failed, No Plex Media Server host specified'
        else:
            finalResult += 'Test failed for Plex server(s) ... ' + urllib.unquote_plus(
                str(curResult).replace(',', ', '))
        finalResult += '<br>' + '\n'

        notifications.message('Tested Plex Media Server host(s): ', urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    @staticmethod
    def testLibnotify():

        if sickrage.srCore.NOTIFIERS.libnotify_notifier.test_notify():
            return "Tried sending desktop notification via libnotify"
        else:
            return sickrage.srCore.NOTIFIERS.libnotify.diagnose()

    @staticmethod
    def testEMBY(host=None, emby_apikey=None):

        host = sickrage.srConfig.clean_host(host)
        result = sickrage.srCore.NOTIFIERS.emby_notifier.test_notify(urllib.unquote_plus(host), emby_apikey)
        if result:
            return "Test notice sent successfully to " + urllib.unquote_plus(host)
        else:
            return "Test notice failed to " + urllib.unquote_plus(host)

    @staticmethod
    def testNMJ(host=None, database=None, mount=None):

        host = sickrage.srConfig.clean_host(host)
        result = sickrage.srCore.NOTIFIERS.nmj_notifier.test_notify(urllib.unquote_plus(host), database, mount)
        if result:
            return "Successfully started the scan update"
        else:
            return "Test failed to start the scan update"

    @staticmethod
    def settingsNMJ(host=None):

        host = sickrage.srConfig.clean_host(host)
        result = sickrage.srCore.NOTIFIERS.nmj_notifier.notify_settings(urllib.unquote_plus(host))
        if result:
            return '{"message": "Got settings from %(host)s", "database": "%(database)s", "mount": "%(mount)s"}' % {
                "host": host, "database": sickrage.srConfig.NMJ_DATABASE,
                "mount": sickrage.srConfig.NMJ_MOUNT}
        else:
            return '{"message": "Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for detailed info)", "database": "", "mount": ""}'

    @staticmethod
    def testNMJv2(host=None):

        host = sickrage.srConfig.clean_host(host)
        result = sickrage.srCore.NOTIFIERS.nmjv2_notifier.test_notify(urllib.unquote_plus(host))
        if result:
            return "Test notice sent successfully to " + urllib.unquote_plus(host)
        else:
            return "Test notice failed to " + urllib.unquote_plus(host)

    @staticmethod
    def settingsNMJv2(host=None, dbloc=None, instance=None):

        host = sickrage.srConfig.clean_host(host)
        result = sickrage.srCore.NOTIFIERS.nmjv2_notifier.notify_settings(urllib.unquote_plus(host), dbloc, instance)
        if result:
            return '{"message": "NMJ Database found at: %(host)s", "database": "%(database)s"}' % {"host": host,
                                                                                                   "database": sickrage.srConfig.NMJv2_DATABASE}
        else:
            return '{"message": "Unable to find NMJ Database at location: %(dbloc)s. Is the right location selected and PCH running?", "database": ""}' % {
                "dbloc": dbloc}

    @staticmethod
    def getTraktToken(trakt_pin=None):

        trakt_api = TraktAPI(sickrage.srConfig.SSL_VERIFY, sickrage.srConfig.TRAKT_TIMEOUT)
        response = trakt_api.traktToken(trakt_pin)
        if response:
            return "Trakt Authorized"
        return "Trakt Not Authorized!"

    @staticmethod
    def testTrakt(username=None, blacklist_name=None):
        return sickrage.srCore.NOTIFIERS.trakt_notifier.test_notify(username, blacklist_name)

    @staticmethod
    def loadShowNotifyLists():

        rows = main_db.MainDB().select("SELECT show_id, show_name, notify_list FROM tv_shows ORDER BY show_name ASC")

        data = {}
        size = 0
        for r in rows:
            data[r[b'show_id']] = {'id': r[b'show_id'], 'name': r[b'show_name'], 'list': r[b'notify_list']}
            size += 1
        data[b'_size'] = size
        return json_encode(data)

    @staticmethod
    def saveShowNotifyList(show=None, emails=None):

        if main_db.MainDB().action("UPDATE tv_shows SET notify_list = ? WHERE show_id = ?", [emails, show]):
            return 'OK'
        else:
            return 'ERROR'

    @staticmethod
    def testEmail(host=None, port=None, smtp_from=None, use_tls=None, user=None, pwd=None, to=None):

        host = sickrage.srConfig.clean_host(host)
        if sickrage.srCore.NOTIFIERS.email_notifier.test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return 'Test email sent successfully! Check inbox.'
        else:
            return 'ERROR: %s' % sickrage.srCore.NOTIFIERS.email_notifier.last_err

    @staticmethod
    def testNMA(nma_api=None, nma_priority=0):

        result = sickrage.srCore.NOTIFIERS.nma_notifier.test_notify(nma_api, nma_priority)
        if result:
            return "Test NMA notice sent successfully"
        else:
            return "Test NMA notice failed"

    @staticmethod
    def testPushalot(authorizationToken=None):

        result = sickrage.srCore.NOTIFIERS.pushalot_notifier.test_notify(authorizationToken)
        if result:
            return "Pushalot notification succeeded. Check your Pushalot clients to make sure it worked"
        else:
            return "Error sending Pushalot notification"

    @staticmethod
    def testPushbullet(api=None):

        result = sickrage.srCore.NOTIFIERS.pushbullet_notifier.test_notify(api)
        if result:
            return "Pushbullet notification succeeded. Check your device to make sure it worked"
        else:
            return "Error sending Pushbullet notification"

    @staticmethod
    def getPushbulletDevices(api=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = sickrage.srCore.NOTIFIERS.pushbullet_notifier.get_devices(api)
        if result:
            return result
        else:
            return "Error sending Pushbullet notification"

    def status(self):
        tvdirFree = getDiskSpaceUsage(sickrage.srConfig.TV_DOWNLOAD_DIR)
        rootDir = {}
        if sickrage.srConfig.ROOT_DIRS:
            backend_pieces = sickrage.srConfig.ROOT_DIRS.split('|')
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if len(backend_dirs):
            for subject in backend_dirs:
                rootDir[subject] = getDiskSpaceUsage(subject)

        return self.render("status.mako",
                           title='Status',
                           header='Status',
                           topmenu='system',
                           tvdirFree=tvdirFree,
                           rootDir=rootDir)

    def shutdown(self, pid=None):
        if sickrage.srCore.WEBSERVER:
            self._genericMessage("Shutting down", "SiCKRAGE is shutting down")
            raise KeyboardInterrupt
        return self.redirect('/{}/'.format(sickrage.srConfig.DEFAULT_PAGE))

    def restart(self, pid=None):
        if sickrage.srCore.WEBSERVER:
            self._genericMessage("Restarting", "SiCKRAGE is restarting")
            self.io_loop.add_timeout(timedelta(seconds=5), sickrage.srCore.WEBSERVER.server_restart)
            return self.render("restart.mako", title="Home", header="Restarting SiCKRAGE", topmenu="system")
        return self.redirect('/{}/'.format(sickrage.srConfig.DEFAULT_PAGE))

    def updateCheck(self, pid=None):
        if str(pid) != str(sickrage.srCore.PID):
            return self.redirect('/home/')

        sickrage.srCore.VERSIONUPDATER.check_for_new_version(True)
        sickrage.srCore.VERSIONUPDATER.check_for_new_news(True)

        return self.redirect('/' + sickrage.srConfig.DEFAULT_PAGE + '/')

    def update(self, pid=None):

        if str(pid) != str(sickrage.srCore.PID):
            return self.redirect('/home/')

        if sickrage.srCore.VERSIONUPDATER._runbackup() is True:
            if sickrage.srCore.VERSIONUPDATER.update():
                self.io_loop.add_timeout(timedelta(seconds=5), sickrage.srCore.WEBSERVER.server_restart)
                return self.render("restart.mako",
                                   title="Home",
                                   header="Restarting SiCKRAGE",
                                   topmenu="home")
            else:
                return self._genericMessage("Update Failed",
                                            "Update wasn't successful, not restarting. Check your log for more information.")
        else:
            return self.redirect('/' + sickrage.srConfig.DEFAULT_PAGE + '/')

    def branchCheckout(self, branch):
        if branch and sickrage.srCore.VERSION != branch:
            sickrage.srCore.VERSION = branch
            notifications.message('Checking out branch: ', branch)
            return self.update(sickrage.srCore.PID)
        else:
            notifications.message('Already on branch: ', branch)
            return self.redirect('/' + sickrage.srConfig.DEFAULT_PAGE + '/')

    def displayShow(self, show=None):

        if show is None:
            return self._genericMessage("Error", "Invalid show ID")
        else:
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

            if showObj is None:
                return self._genericMessage("Error", "Show not in show list")

        seasonResults = main_db.MainDB().select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season DESC",
            [showObj.indexerid]
        )

        sqlResults = main_db.MainDB().select(
            "SELECT * FROM tv_episodes WHERE showid = ? ORDER BY season DESC, episode DESC",
            [showObj.indexerid]
        )

        submenu = [
            {'title': 'Edit', 'path': 'home/editShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-pencil'}]

        try:
            showLoc = (showObj.location, True)
        except ShowDirectoryNotFoundException:
            showLoc = (showObj.location, False)

        show_message = ''

        if sickrage.srCore.SHOWQUEUE.isBeingAdded(showObj):
            show_message = 'This show is in the process of being downloaded - the info below is incomplete.'

        elif sickrage.srCore.SHOWQUEUE.isBeingUpdated(showObj):
            show_message = 'The information on this page is in the process of being updated.'

        elif sickrage.srCore.SHOWQUEUE.isBeingRefreshed(showObj):
            show_message = 'The episodes below are currently being refreshed from disk'

        elif sickrage.srCore.SHOWQUEUE.isBeingSubtitled(showObj):
            show_message = 'Currently downloading subtitles for this show'

        elif sickrage.srCore.SHOWQUEUE.isInRefreshQueue(showObj):
            show_message = 'This show is queued to be refreshed.'

        elif sickrage.srCore.SHOWQUEUE.isInUpdateQueue(showObj):
            show_message = 'This show is queued and awaiting an update.'

        elif sickrage.srCore.SHOWQUEUE.isInSubtitleQueue(showObj):
            show_message = 'This show is queued and awaiting subtitles download.'

        if not sickrage.srCore.SHOWQUEUE.isBeingAdded(showObj):
            if not sickrage.srCore.SHOWQUEUE.isBeingUpdated(showObj):
                if showObj.paused:
                    submenu.append({'title': 'Resume', 'path': 'home/togglePause?show=%d' % showObj.indexerid,
                                    'icon': 'ui-icon ui-icon-play'})
                else:
                    submenu.append({'title': 'Pause', 'path': 'home/togglePause?show=%d' % showObj.indexerid,
                                    'icon': 'ui-icon ui-icon-pause'})

                submenu.append({'title': 'Remove', 'path': 'home/deleteShow?show=%d' % showObj.indexerid,
                                'class': 'removeshow', 'confirm': True, 'icon': 'ui-icon ui-icon-trash'})
                submenu.append({'title': 'Re-scan files', 'path': 'home/refreshShow?show=%d' % showObj.indexerid,
                                'icon': 'ui-icon ui-icon-refresh'})
                submenu.append({'title': 'Force Full Update',
                                'path': 'home/updateShow?show=%d&amp;force=1' % showObj.indexerid,
                                'icon': 'ui-icon ui-icon-transfer-e-w'})
                submenu.append({'title': 'Update show in KODI', 'path': 'home/updateKODI?show=%d' % showObj.indexerid,
                                'requires': self.haveKODI(), 'icon': 'submenu-icon-kodi'})
                submenu.append({'title': 'Update show in Emby', 'path': 'home/updateEMBY?show=%d' % showObj.indexerid,
                                'requires': self.haveEMBY(), 'icon': 'ui-icon ui-icon-refresh'})
                submenu.append({'title': 'Preview Rename', 'path': 'home/testRename?show=%d' % showObj.indexerid,
                                'icon': 'ui-icon ui-icon-tag'})

                if sickrage.srConfig.USE_SUBTITLES and not sickrage.srCore.SHOWQUEUE.isBeingSubtitled(
                        showObj) and showObj.subtitles:
                    submenu.append(
                        {'title': 'Download Subtitles', 'path': 'home/subtitleShow?show=%d' % showObj.indexerid,
                         'icon': 'ui-icon ui-icon-comment'})

        epCounts = {}
        epCats = {}
        epCounts[Overview.SKIPPED] = 0
        epCounts[Overview.WANTED] = 0
        epCounts[Overview.QUAL] = 0
        epCounts[Overview.GOOD] = 0
        epCounts[Overview.UNAIRED] = 0
        epCounts[Overview.SNATCHED] = 0

        for curResult in sqlResults:
            curEpCat = showObj.getOverview(int(curResult[b"status"] or -1))
            if curEpCat:
                epCats[str(curResult[b"season"]) + "x" + str(curResult[b"episode"])] = curEpCat
                epCounts[curEpCat] += 1

        def titler(x):
            return (remove_article(x), x)[not x or sickrage.srConfig.SORT_ARTICLE]

        if sickrage.srConfig.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in sickrage.srCore.SHOWLIST:
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)
            sortedShowLists = [["Shows", sorted(shows, lambda x, y: cmp(titler(x.name), titler(y.name)))],
                               ["Anime", sorted(anime, lambda x, y: cmp(titler(x.name), titler(y.name)))]]
        else:
            sortedShowLists = [
                ["Shows", sorted(sickrage.srCore.SHOWLIST, lambda x, y: cmp(titler(x.name), titler(y.name)))]]

        bwl = None
        if showObj.is_anime:
            bwl = showObj.release_groups

        showObj.exceptions = get_scene_exceptions(showObj.indexerid)

        indexerid = int(showObj.indexerid)
        indexer = int(showObj.indexer)

        # Delete any previous occurrances
        for index, recentShow in enumerate(sickrage.srConfig.SHOWS_RECENT):
            if recentShow[b'indexerid'] == indexerid:
                del sickrage.srConfig.SHOWS_RECENT[index]

        # Only track 5 most recent shows
        del sickrage.srConfig.SHOWS_RECENT[4:]

        # Insert most recent show
        sickrage.srConfig.SHOWS_RECENT.insert(0, {
            'indexerid': indexerid,
            'name': showObj.name,
        })

        return self.render("displayShow.mako",
                           submenu=submenu,
                           showLoc=showLoc,
                           show_message=show_message,
                           show=showObj,
                           sqlResults=sqlResults,
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
                           title=showObj.name
                           )

    @staticmethod
    def plotDetails(show, season, episode):

        try:
            result = main_db.MainDB().select(
                "SELECT description FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                (int(show), int(season), int(episode)))[0][b'description']
        except:
            result = 'Episode not found.'
        return result

    @staticmethod
    def sceneExceptions(show):
        exceptionsList = get_all_scene_exceptions(show)
        if not exceptionsList:
            return "No scene exceptions"

        out = []
        for season, names in iter(sorted(exceptionsList.iteritems())):
            if season == -1:
                season = "*"
            out.append("S" + str(season) + ": " + ", ".join(names))
        return "<br>".join(out)

    def editShow(self, show=None, location=None, anyQualities=[], bestQualities=[], exceptions_list=[],
                 flatten_folders=None, paused=None, directCall=False, air_by_date=None, sports=None, dvdorder=None,
                 indexerLang=None, subtitles=None, archive_firstmatch=None, rls_ignore_words=None,
                 rls_require_words=None, anime=None, blacklist=None, whitelist=None,
                 scene=None, defaultEpStatus=None, quality_preset=None):

        anidb_failed = False
        if show is None:
            errString = "Invalid show ID: " + str(show)
            if directCall:
                return [errString]
            else:
                return self._genericMessage("Error", errString)

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if not showObj:
            errString = "Unable to find the specified show: " + str(show)
            if directCall:
                return [errString]
            else:
                return self._genericMessage("Error", errString)

        showObj.exceptions = get_scene_exceptions(showObj.indexerid)

        groups = []
        if not location and not anyQualities and not bestQualities and not quality_preset and not flatten_folders:
            if showObj.is_anime:
                whitelist = showObj.release_groups.whitelist
                blacklist = showObj.release_groups.blacklist

                if set_up_anidb_connection() and not anidb_failed:
                    try:
                        anime = aniDBAbstracter.Anime(sickrage.srConfig.ADBA_CONNECTION, name=showObj.name)
                        groups = anime.get_groups()
                    except Exception as e:
                        anidb_failed = True
                        notifications.error('Unable to retreive Fansub Groups from AniDB.')
                        sickrage.srLogger.debug(
                            'Unable to retreive Fansub Groups from AniDB. Error is {}'.format(str(e)))

            with showObj.lock:
                scene_exceptions = get_scene_exceptions(showObj.indexerid)

            if showObj.is_anime:
                return self.render("editShow.mako",
                                   show=showObj,
                                   quality=showObj.quality,
                                   scene_exceptions=scene_exceptions,
                                   groups=groups,
                                   whitelist=whitelist,
                                   blacklist=blacklist,
                                   title='Edit Show',
                                   header='Edit Show')
            else:
                return self.render("editShow.mako",
                                   show=showObj,
                                   quality=showObj.quality,
                                   scene_exceptions=scene_exceptions,
                                   title='Edit Show',
                                   header='Edit Show')

        flatten_folders = not sickrage.srConfig.checkbox_to_value(flatten_folders)  # UI inverts this value
        dvdorder = sickrage.srConfig.checkbox_to_value(dvdorder)
        archive_firstmatch = sickrage.srConfig.checkbox_to_value(archive_firstmatch)
        paused = sickrage.srConfig.checkbox_to_value(paused)
        air_by_date = sickrage.srConfig.checkbox_to_value(air_by_date)
        scene = sickrage.srConfig.checkbox_to_value(scene)
        sports = sickrage.srConfig.checkbox_to_value(sports)
        anime = sickrage.srConfig.checkbox_to_value(anime)
        subtitles = sickrage.srConfig.checkbox_to_value(subtitles)

        if indexerLang and indexerLang in sickrage.srCore.INDEXER_API(showObj.indexer).indexer().config[
            b'valid_languages']:
            indexer_lang = indexerLang
        else:
            indexer_lang = showObj.lang

        # if we changed the language then kick off an update
        if indexer_lang == showObj.lang:
            do_update = False
        else:
            do_update = True

        if scene == showObj.scene and anime == showObj.anime:
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

        errors = []
        with showObj.lock:
            newQuality = tryInt(quality_preset, None)
            if not newQuality:
                newQuality = Quality.combineQualities([int(q) for q in anyQualities], [int(q) for q in bestQualities])

            showObj.quality = newQuality
            showObj.archive_firstmatch = archive_firstmatch

            # reversed for now
            if bool(showObj.flatten_folders) != bool(flatten_folders):
                showObj.flatten_folders = flatten_folders
                try:
                    sickrage.srCore.SHOWQUEUE.refreshShow(showObj)
                except CantRefreshShowException as e:
                    errors.append("Unable to refresh this show: {}".format(e.message))

            showObj.paused = paused
            showObj.scene = scene
            showObj.anime = anime
            showObj.sports = sports
            showObj.subtitles = subtitles
            showObj.air_by_date = air_by_date
            showObj.default_ep_status = int(defaultEpStatus)

            if not directCall:
                showObj.lang = indexer_lang
                showObj.dvdorder = dvdorder
                showObj.rls_ignore_words = rls_ignore_words.strip()
                showObj.rls_require_words = rls_require_words.strip()

            # if we change location clear the db of episodes, change it, write to db, and rescan
            if os.path.normpath(showObj.location) != os.path.normpath(location):
                sickrage.srLogger.debug(os.path.normpath(showObj.location) + " != " + os.path.normpath(location))
                if not os.path.isdir(location) and not sickrage.srConfig.CREATE_MISSING_SHOW_DIRS:
                    errors.append("New location <tt>%s</tt> does not exist" % location)

                # don't bother if we're going to update anyway
                elif not do_update:
                    # change it
                    try:
                        showObj.location = location
                        try:
                            sickrage.srCore.SHOWQUEUE.refreshShow(showObj)
                        except CantRefreshShowException as e:
                            errors.append("Unable to refresh this show:{}".format(e.message))
                            # grab updated info from TVDB
                            # showObj.loadEpisodesFromIndexer()
                            # rescan the episodes in the new folder
                    except NoNFOException:
                        errors.append(
                            "The folder at <tt>%s</tt> doesn't contain a tvshow.nfo - copy your files to that folder before you change the directory in SiCKRAGE." % location)

            # save it to the DB
            showObj.saveToDB()

        # force the update
        if do_update:
            try:
                sickrage.srCore.SHOWQUEUE.updateShow(showObj, True)
                gen.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append("Unable to update show: {0}".format(str(e)))

        if do_update_exceptions:
            try:
                update_scene_exceptions(showObj.indexerid,
                                        exceptions_list)  # @UndefinedVdexerid)
                gen.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append("Unable to force an update on scene exceptions of the show.")

        if do_update_scene_numbering:
            try:
                xem_refresh(showObj.indexerid, showObj.indexer)
                gen.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append("Unable to force an update on scene numbering of the show.")

        if directCall:
            return errors

        if len(errors) > 0:
            notifications.error('%d error%s while saving changes:' % (len(errors), "" if len(errors) == 1 else "s"),
                                '<ul>' + '\n'.join(['<li>%s</li>' % error for error in errors]) + "</ul>")

        return self.redirect("/home/displayShow?show=" + show)

    def togglePause(self, show=None):
        error, show = TVShow.pause(show)

        if error is not None:
            return self._genericMessage('Error', error)

        notifications.message('%s has been %s' % (show.name, ('resumed', 'paused')[show.paused]))

        return self.redirect("/home/displayShow?show=%i" % show.indexerid)

    def deleteShow(self, show=None, full=0):
        if show:
            error, show = TVShow.delete(show, full)

            if error is not None:
                return self._genericMessage('Error', error)

            notifications.message(
                '%s has been %s %s' %
                (
                    show.name,
                    ('deleted', 'trashed')[bool(sickrage.srConfig.TRASH_REMOVE_SHOW)],
                    ('(media untouched)', '(with all related media)')[bool(full)]
                )
            )

            gen.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')

    def refreshShow(self, show=None):
        error, show = TVShow.refresh(show)

        # This is a show validation error
        if error is not None and show is None:
            return self._genericMessage('Error', error)

        # This is a refresh error
        if error is not None:
            notifications.error('Unable to refresh this show.', error)

        gen.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show.indexerid))

    def updateShow(self, show=None, force=0):

        if show is None:
            return self._genericMessage("Error", "Invalid show ID")

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if showObj is None:
            return self._genericMessage("Error", "Unable to find the specified show")

        # force the update
        try:
            sickrage.srCore.SHOWQUEUE.updateShow(showObj, bool(force))
        except CantUpdateShowException as e:
            notifications.error("Unable to update this show.", e.message)

        # just give it some time
        gen.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def subtitleShow(self, show=None, force=0):

        if show is None:
            return self._genericMessage("Error", "Invalid show ID")

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if showObj is None:
            return self._genericMessage("Error", "Unable to find the specified show")

        # search and download subtitles
        sickrage.srCore.SHOWQUEUE.downloadSubtitles(showObj, bool(force))

        gen.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def updateKODI(self, show=None):
        showName = None
        showObj = None

        if show:
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))
            if showObj:
                showName = urllib.quote_plus(showObj.name.encode('utf-8'))

        if sickrage.srConfig.KODI_UPDATE_ONLYFIRST:
            host = sickrage.srConfig.KODI_HOST.split(",")[0].strip()
        else:
            host = sickrage.srConfig.KODI_HOST

        if sickrage.srCore.NOTIFIERS.kodi_notifier.update_library(showName=showName):
            notifications.message("Library update command sent to KODI host(s): " + host)
        else:
            notifications.error("Unable to contact one or more KODI host(s): " + host)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def updatePLEX(self):
        if None is sickrage.srCore.NOTIFIERS.plex_notifier.update_library():
            notifications.message(
                "Library update command sent to Plex Media Server host: " + sickrage.srConfig.PLEX_SERVER_HOST)
        else:
            notifications.error("Unable to contact Plex Media Server host: " + sickrage.srConfig.PLEX_SERVER_HOST)
        return self.redirect('/home/')

    def updateEMBY(self, show=None):
        showObj = None

        if show:
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if sickrage.srCore.NOTIFIERS.emby_notifier.update_library(showObj):
            notifications.message(
                "Library update command sent to Emby host: " + sickrage.srConfig.EMBY_HOST)
        else:
            notifications.error("Unable to contact Emby host: " + sickrage.srConfig.EMBY_HOST)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def deleteEpisode(self, show=None, eps=None, direct=False):
        if not all([show, eps]):
            errMsg = "You must specify a show and at least one episode"
            if direct:
                notifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))
        if not showObj:
            errMsg = "Error", "Show not in show list"
            if direct:
                notifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        if eps:
            for curEp in eps.split('|'):
                if not curEp:
                    sickrage.srLogger.debug("curEp was empty when trying to deleteEpisode")

                sickrage.srLogger.debug("Attempting to delete episode " + curEp)

                epInfo = curEp.split('x')

                if not all(epInfo):
                    sickrage.srLogger.debug(
                        "Something went wrong when trying to deleteEpisode, epInfo[0]: %s, epInfo[1]: %s" % (
                            epInfo[0], epInfo[1]))
                    continue

                epObj = showObj.getEpisode(int(epInfo[0]), int(epInfo[1]))
                if not epObj:
                    return self._genericMessage("Error", "Episode couldn't be retrieved")

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
            errMsg = "You must specify a show and at least one episode"
            if direct:
                notifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        if not statusStrings.has_key(int(status)):
            errMsg = "Invalid status"
            if direct:
                notifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if not showObj:
            errMsg = "Error", "Show not in show list"
            if direct:
                notifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        segments = {}
        trakt_data = []
        if eps:
            sql_l = []
            for curEp in eps.split('|'):

                if not curEp:
                    sickrage.srLogger.debug("curEp was empty when trying to setStatus")

                sickrage.srLogger.debug("Attempting to set status on episode " + curEp + " to " + status)

                epInfo = curEp.split('x')

                if not all(epInfo):
                    sickrage.srLogger.debug(
                        "Something went wrong when trying to setStatus, epInfo[0]: %s, epInfo[1]: %s" % (
                            epInfo[0], epInfo[1]))
                    continue

                epObj = showObj.getEpisode(int(epInfo[0]), int(epInfo[1]))

                if not epObj:
                    return self._genericMessage("Error", "Episode couldn't be retrieved")

                if int(status) in [WANTED, FAILED]:
                    # figure out what episodes are wanted so we can backlog them
                    if epObj.season in segments:
                        segments[epObj.season].append(epObj)
                    else:
                        segments[epObj.season] = [epObj]

                with epObj.lock:
                    # don't let them mess up UNAIRED episodes
                    if epObj.status == UNAIRED:
                        sickrage.srLogger.warning(
                            "Refusing to change status of " + curEp + " because it is UNAIRED")
                        continue

                    if int(status) in Quality.DOWNLOADED and epObj.status not in Quality.SNATCHED + \
                            Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + [
                        IGNORED] and not os.path.isfile(epObj.location):
                        sickrage.srLogger.warning(
                            "Refusing to change status of " + curEp + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if int(status) == FAILED and epObj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + \
                            Quality.SNATCHED_BEST + Quality.DOWNLOADED + Quality.ARCHIVED:
                        sickrage.srLogger.warning(
                            "Refusing to change status of " + curEp + " to FAILED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if epObj.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        sickrage.srLogger.info(
                            "Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced")
                        epObj.release_name = ""

                    epObj.status = int(status)

                    # mass add to database
                    sql_q = epObj.saveToDB(False)
                    if sql_q:
                        sql_l.append(sql_q)

                    trakt_data.append((epObj.season, epObj.episode))

            data = sickrage.srCore.NOTIFIERS.trakt_notifier.trakt_episode_data_generate(trakt_data)
            if data and sickrage.srConfig.USE_TRAKT and sickrage.srConfig.TRAKT_SYNC_WATCHLIST:
                if int(status) in [WANTED, FAILED]:
                    sickrage.srLogger.debug(
                        "Add episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(
                            showObj.name) + " to Watchlist")
                    sickrage.srCore.NOTIFIERS.trakt_notifier.update_watchlist(showObj, data_episode=data, update="add")
                elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                    sickrage.srLogger.debug(
                        "Remove episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(
                            showObj.name) + " from Watchlist")
                    sickrage.srCore.NOTIFIERS.trakt_notifier.update_watchlist(showObj, data_episode=data,
                                                                              update="remove")

            if len(sql_l) > 0:
                main_db.MainDB().mass_upsert(sql_l)

        if int(status) == WANTED and not showObj.paused:
            msg = "Backlog was automatically started for the following seasons of <b>" + showObj.name + "</b>:<br>"
            msg += '<ul>'

            for season, segment in segments.iteritems():
                cur_backlog_queue_item = BacklogQueueItem(showObj, segment)
                sickrage.srCore.SEARCHQUEUE.add_item(cur_backlog_queue_item)

                msg += "<li>Season " + str(season) + "</li>"
                sickrage.srLogger.info("Sending backlog for " + showObj.name + " season " + str(
                    season) + " because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                notifications.message("Backlog started", msg)
        elif int(status) == WANTED and showObj.paused:
            sickrage.srLogger.info(
                "Some episodes were set to wanted, but " + showObj.name + " is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = "Retrying Search was automatically started for the following season of <b>" + showObj.name + "</b>:<br>"
            msg += '<ul>'

            for season, segment in segments.iteritems():
                cur_failed_queue_item = FailedQueueItem(showObj, segment)
                sickrage.srCore.SEARCHQUEUE.add_item(cur_failed_queue_item)

                msg += "<li>Season " + str(season) + "</li>"
                sickrage.srLogger.info("Retrying Search for " + showObj.name + " season " + str(
                    season) + " because some eps were set to failed")

            msg += "</ul>"

            if segments:
                notifications.message("Retry Search started", msg)

        if direct:
            return json_encode({'result': 'success'})
        else:
            return self.redirect("/home/displayShow?show=" + show)

    def testRename(self, show=None):

        if show is None:
            return self._genericMessage("Error", "You must specify a show")

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if showObj is None:
            return self._genericMessage("Error", "Show not in show list")

        try:
            showObj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage("Error", "Can't rename episodes when the show dir is missing.")

        ep_obj_rename_list = []

        ep_obj_list = showObj.getAllEpisodes(has_location=True)

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
            {'title': 'Edit', 'path': 'home/editShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-pencil'}]

        return self.render("testRename.mako",
                           submenu=submenu,
                           ep_obj_list=ep_obj_rename_list,
                           show=showObj,
                           title='Preview Rename',
                           header='Preview Rename')

    def doRename(self, show=None, eps=None):
        if show is None or eps is None:
            errMsg = "You must specify a show and at least one episode"
            return self._genericMessage("Error", errMsg)

        show_obj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if show_obj is None:
            errMsg = "Error", "Show not in show list"
            return self._genericMessage("Error", errMsg)

        try:
            show_obj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage("Error", "Can't rename episodes when the show dir is missing.")

        if eps is None:
            return self.redirect("/home/displayShow?show=" + show)

        for curEp in eps.split('|'):

            epInfo = curEp.split('x')

            # this is probably the worst possible way to deal with double eps but I've kinda painted myself into a corner here with this stupid database
            ep_result = main_db.MainDB().select(
                "SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? AND 5=5",
                [show, epInfo[0], epInfo[1]])
            if not ep_result:
                sickrage.srLogger.warning("Unable to find an episode for " + curEp + ", skipping")
                continue
            related_eps_result = main_db.MainDB().select(
                "SELECT * FROM tv_episodes WHERE location = ? AND episode != ?",
                [ep_result[0][b"location"], epInfo[1]])

            root_ep_obj = show_obj.getEpisode(int(epInfo[0]), int(epInfo[1]))
            root_ep_obj.relatedEps = []

            for cur_related_ep in related_eps_result:
                related_ep_obj = show_obj.getEpisode(int(cur_related_ep[b"season"]), int(cur_related_ep[b"episode"]))
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

            sickrage.srCore.SEARCHQUEUE.add_item(ep_queue_item)

            if not ep_queue_item.started and ep_queue_item.success is None:
                return json_encode(
                    {
                        'result': 'success'})  # I Actually want to call it queued, because the search hasnt been started yet!
            if ep_queue_item.started and ep_queue_item.success is None:
                return json_encode({'result': 'success'})
            else:
                return json_encode({'result': 'failure'})

        return json_encode({'result': 'failure'})

    ### Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self, show=None):
        def getEpisodes(searchThread, searchstatus):
            results = []
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(searchThread.show.indexerid))

            if not showObj:
                sickrage.srLogger.error(
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
                                    showObj.getOverview(int(searchThread.segment.status or -1))]})
            else:
                for epObj in searchThread.segment:
                    results.append({'show': epObj.show.indexerid,
                                    'episode': epObj.episode,
                                    'episodeindexid': epObj.indexerid,
                                    'season': epObj.season,
                                    'searchstatus': searchstatus,
                                    'status': statusStrings[epObj.status],
                                    'quality': self.getQualityClass(epObj),
                                    'overview': Overview.overviewStrings[showObj.getOverview(int(epObj.status or -1))]})

            return results

        episodes = []

        # Queued Searches
        searchstatus = 'queued'
        for searchThread in sickrage.srCore.SEARCHQUEUE.get_all_ep_from_queue(show):
            episodes += getEpisodes(searchThread, searchstatus)

        # Running Searches
        searchstatus = 'searching'
        if sickrage.srCore.SEARCHQUEUE.is_manualsearch_in_progress():
            searchThread = sickrage.srCore.SEARCHQUEUE.currentItem

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
                if not [x for x in episodes if x[b'episodeindexid'] == searchThread.segment.indexerid]:
                    episodes += getEpisodes(searchThread, searchstatus)
            else:
                ### These are only Failed Downloads/Retry SearchThreadItems.. lets loop through the segement/episodes
                if not [i for i, j in zip(searchThread.segment, episodes) if i.indexerid == j[b'episodeindexid']]:
                    episodes += getEpisodes(searchThread, searchstatus)

        return json_encode({'episodes': episodes})

    @staticmethod
    def getQualityClass(ep_obj):
        # return the correct json value

        # Find the quality class for the episode
        _, ep_quality = Quality.splitCompositeStatus(ep_obj.status)
        if ep_quality in Quality.cssClassStrings:
            quality_class = Quality.cssClassStrings[ep_quality]
        else:
            quality_class = Quality.cssClassStrings[Quality.UNKNOWN]

        return quality_class

    def searchEpisodeSubtitles(self, show=None, season=None, episode=None):
        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, TVEpisode):
            # try do download subtitles for that episode
            previous_subtitles = ep_obj.subtitles
            try:
                ep_obj.downloadSubtitles()
            except Exception:
                return json_encode({'result': 'failure'})

            # return the correct json value
            newSubtitles = frozenset(ep_obj.subtitles).difference(previous_subtitles)
            if newSubtitles:
                newLangs = [subtitle_searcher.fromietf(newSub) for newSub in newSubtitles]
                status = 'New subtitles downloaded: %s' % ', '.join([newLang.name for newLang in newLangs])
            else:
                status = 'No subtitles downloaded'
            notifications.message(ep_obj.show.name, status)
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

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

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
            result[b'success'] = False
            result[b'errorMessage'] = ep_obj
        elif showObj.is_anime:
            sickrage.srLogger.debug("setAbsoluteSceneNumbering for %s from %s to %s" %
                                         (show, forAbsolute, sceneAbsolute))

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None:
                sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            sickrage.srLogger.debug("setEpisodeSceneNumbering for %s from %sx%s to %sx%s" %
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
                result[b'sceneAbsolute'] = sn
            else:
                result[b'sceneAbsolute'] = None
        else:
            sn = get_scene_numbering(show, indexer, forSeason, forEpisode)
            if sn:
                (result[b'sceneSeason'], result[b'sceneEpisode']) = sn
            else:
                (result[b'sceneSeason'], result[b'sceneEpisode']) = (None, None)

        return json_encode(result)

    def retryEpisode(self, show, season, episode, downCurQuality):
        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, TVEpisode):
            # make a queue item for it and put it on the queue
            ep_queue_item = FailedQueueItem(ep_obj.show, [ep_obj], bool(int(downCurQuality)))
            sickrage.srCore.SEARCHQUEUE.add_item(ep_queue_item)

            if not ep_queue_item.started and ep_queue_item.success is None:
                return json_encode(
                    {
                        'result': 'success'})  # I Actually want to call it queued, because the search hasnt been started yet!
            if ep_queue_item.started and ep_queue_item.success is None:
                return json_encode({'result': 'success'})
            else:
                return json_encode({'result': 'failure'})

        return json_encode({'result': 'failure'})

    @staticmethod
    def fetch_releasegroups(show_name):
        sickrage.srLogger.info('ReleaseGroups: %s' % show_name)
        if set_up_anidb_connection():
            anime = aniDBAbstracter.Anime(sickrage.srConfig.ADBA_CONNECTION, name=show_name)
            groups = anime.get_groups()
            sickrage.srLogger.info('ReleaseGroups: %s' % groups)
            return json_encode({'result': 'success', 'groups': groups})

        return json_encode({'result': 'failure'})


@Route('/IRC(/?.*)')
class HomeIRC(Home):
    def __init__(self, *args, **kwargs):
        super(HomeIRC, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("IRC.mako",
                           topmenu="system",
                           header="IRC",
                           title="IRC")


@Route('/news(/?.*)')
class HomeNews(Home):
    def __init__(self, *args, **kwargs):
        super(HomeNews, self).__init__(*args, **kwargs)

    def index(self):
        try:
            news = sickrage.srCore.VERSIONUPDATER.check_for_new_news(force=True)
        except Exception:
            sickrage.srLogger.debug('Could not load news from repo, giving a link!')
            news = 'Could not load news from the repo. [Click here for news.md](' + sickrage.srConfig.NEWS_URL + ')'

        sickrage.srConfig.NEWS_LAST_READ = sickrage.srConfig.NEWS_LATEST
        sickrage.srConfig.NEWS_UNREAD = 0
        sickrage.srConfig.save_config()

        data = markdown2.markdown(
            news if news else "The was a problem connecting to github, please refresh and try again",
            extras=['header-ids'])

        return self.render("markdown.mako",
                           title="News",
                           header="News",
                           topmenu="system",
                           data=data)


@Route('/changes(/?.*)')
class HomeChangeLog(Home):
    def __init__(self, *args, **kwargs):
        super(HomeChangeLog, self).__init__(*args, **kwargs)

    def index(self):
        try:
            changes = getURL(sickrage.srConfig.CHANGES_URL)
        except Exception:
            sickrage.srLogger.debug('Could not load changes from repo, giving a link!')
            changes = 'Could not load changes from the repo. [Click here for CHANGES.md]({})'.format(sickrage.srConfig.CHANGES_URL)

        data = markdown2.markdown(
            changes if changes else "The was a problem connecting to github, please refresh and try again",
            extras=['header-ids'])

        return self.render("markdown.mako",
                           title="Changelog",
                           header="Changelog",
                           topmenu="system",
                           data=data)


@Route('/home/postprocess(/?.*)')
class HomePostProcess(Home):
    def __init__(self, *args, **kwargs):
        super(HomePostProcess, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("home_postprocess.mako",
                           title='Post Processing',
                           header='Post Processing',
                           topmenu='home')

    def processEpisode(self, *args, **kwargs):
        pp_options = dict(
            ("proc_dir" if k.lower() == "dir" else k,
             argToBool(v)
             if k.lower() not in ['proc_dir', 'dir', 'nzbname', 'process_method', 'proc_type'] else v
             ) for k, v in kwargs.items())

        if not pp_options.has_key('proc_dir'):
            return self.redirect("/home/postprocess/")

        result = processDir(pp_options[b"proc_dir"], **pp_options)
        if pp_options.get("quiet", None):
            return result

        return self._genericMessage("Postprocessing results", result.replace("\n", "<br>\n"))


@Route('/home/addShows(/?.*)')
class HomeAddShows(Home):
    def __init__(self, *args, **kwargs):
        super(HomeAddShows, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("home_addShows.mako",
                           title='Add Shows',
                           header='Add Shows',
                           topmenu='home')

    @staticmethod
    def getIndexerLanguages():
        result = sickrage.srCore.INDEXER_API().config[b'valid_languages']

        return json_encode({'results': result})

    @staticmethod
    def sanitizeFileName(name):
        return sanitizeFileName(name)

    @staticmethod
    def searchIndexersForShowName(search_term, lang=None, indexer=None):
        if not lang or lang == 'null':
            lang = sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE

        results = {}
        final_results = []

        # Query Indexers for each search term and build the list of results
        for indexer in sickrage.srCore.INDEXER_API().indexers if not int(indexer) else [int(indexer)]:
            lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(indexer).api_params.copy()
            lINDEXER_API_PARMS[b'language'] = lang
            lINDEXER_API_PARMS[b'custom_ui'] = AllShowsListUI
            t = sickrage.srCore.INDEXER_API(indexer).indexer(**lINDEXER_API_PARMS)

            sickrage.srLogger.debug("Searching for Show with searchterm: %s on Indexer: %s" % (
                search_term, sickrage.srCore.INDEXER_API(indexer).name))
            try:
                # add search results
                results.setdefault(indexer, []).extend(t[search_term])
            except Exception:
                continue

        for i, shows in results.items():
            final_results.extend(
                [[sickrage.srCore.INDEXER_API(i).name, i, sickrage.srCore.INDEXER_API(i).config[b"show_url"],
                  int(show[b'id']), show[b'seriesname'], show[b'firstaired']] for show in shows])

        lang_id = sickrage.srCore.INDEXER_API().config[b'langabbv_to_id'][lang]
        return json_encode({'results': final_results, 'langid': lang_id})

    def massAddTable(self, rootDir=None):
        if not rootDir:
            return "No folders selected."
        elif not isinstance(rootDir, list):
            root_dirs = [rootDir]
        else:
            root_dirs = rootDir

        root_dirs = [urllib.unquote_plus(x) for x in root_dirs]

        if sickrage.srConfig.ROOT_DIRS:
            default_index = int(sickrage.srConfig.ROOT_DIRS.split('|')[0])
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
                except Exception:
                    continue

                try:
                    cur_dir = {
                        'dir': cur_path,
                        'display_dir': '<b>{}{}</b>{}'
                            .format(os.path.dirname(cur_path), os.sep, os.path.basename(cur_path)),
                    }
                except Exception as e:
                    pass

                # see if the folder is in KODI already
                dirResults = main_db.MainDB().select("SELECT * FROM tv_shows WHERE location = ?", [cur_path])

                if dirResults:
                    cur_dir[b'added_already'] = True
                else:
                    cur_dir[b'added_already'] = False

                dir_list.append(cur_dir)

                indexer_id = show_name = indexer = None
                for cur_provider in sickrage.srCore.metadataProviderDict.values():
                    if not (indexer_id and show_name):
                        (indexer_id, show_name, indexer) = cur_provider.retrieveShowMetadata(cur_path)

                        # default to TVDB if indexer was not detected
                        if show_name and not (indexer or indexer_id):
                            (sn, idxr, i) = searchIndexerForShowID(show_name, indexer, indexer_id)

                            # set indexer and indexer_id from found info
                            if not indexer and idxr:
                                indexer = idxr

                            if not indexer_id and i:
                                indexer_id = i

                cur_dir[b'existing_info'] = (indexer_id, show_name, indexer)

                if indexer_id and findCertainShow(sickrage.srCore.SHOWLIST, indexer_id):
                    cur_dir[b'added_already'] = True

        return self.render("home_massAddTable.mako",
                           dirList=dir_list)

    def newShow(self, show_to_add=None, other_shows=None, search_string=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """

        indexer, show_dir, indexer_id, show_name = self.split_extra_show(show_to_add)

        if indexer_id and indexer and show_name:
            use_provided_info = True
        else:
            use_provided_info = False

        # use the given show_dir for the indexer search if available
        if not show_dir:
            if search_string:
                default_show_name = search_string
            else:
                default_show_name = ''

        elif not show_name:
            default_show_name = re.sub(r' \(\d{4}\)', '',
                                       os.path.basename(os.path.normpath(show_dir)).replace('.', ' '))
        else:
            default_show_name = show_name

        # carry a list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
            other_shows = [other_shows]

        provided_indexer_id = int(indexer_id or 0)
        provided_indexer_name = show_name

        provided_indexer = int(indexer or sickrage.srConfig.INDEXER_DEFAULT)

        return self.render("home_newShow.mako",
                           enable_anime_options=True,
                           use_provided_info=use_provided_info,
                           default_show_name=default_show_name,
                           other_shows=other_shows,
                           provided_show_dir=show_dir,
                           provided_indexer_id=provided_indexer_id,
                           provided_indexer_name=provided_indexer_name,
                           provided_indexer=provided_indexer,
                           indexers=sickrage.srCore.INDEXER_API().indexers,
                           quality=sickrage.srConfig.QUALITY_DEFAULT,
                           whitelist=[],
                           blacklist=[],
                           groups=[],
                           title='New Show',
                           header='New Show',
                           topmenu='home'
                           )

    def recommendedShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        return self.render("home_recommendedShows.mako",
                           title="Recommended Shows",
                           header="Recommended Shows",
                           enable_anime_options=False)

    def getRecommendedShows(self):
        blacklist = False
        trending_shows = []
        trakt_api = TraktAPI(sickrage.srConfig.SSL_VERIFY, sickrage.srConfig.TRAKT_TIMEOUT)

        try:
            shows = trakt_api.traktRequest("recommendations/shows?extended=full,images") or []
            for show in shows:
                show = {'show': show}
                show_id = int(show[b'show'][b'ids'][b'tvdb']) or None

                try:
                    if not findCertainShow(sickrage.srCore.SHOWLIST, [show_id]):
                        library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
                        if show_id in (lshow[b'show'][b'ids'][b'tvdb'] for lshow in library_shows):
                            continue

                    if sickrage.srConfig.TRAKT_BLACKLIST_NAME is not None and sickrage.srConfig.TRAKT_BLACKLIST_NAME:
                        not_liked_show = trakt_api.traktRequest(
                            "users/{}/lists/{}/items".format(sickrage.srConfig.TRAKT_USERNAME,
                                                             sickrage.srConfig.TRAKT_BLACKLIST_NAME))
                        if not_liked_show and [nlshow for nlshow in not_liked_show if (
                                        show_id == nlshow[b'show'][b'ids'][b'tvdb'] and nlshow[b'type'] == 'show')]:
                            continue

                        trending_shows += [show]
                except MultipleShowObjectsException:
                    continue

            if sickrage.srConfig.TRAKT_BLACKLIST_NAME != '':
                blacklist = True

        except traktException as e:
            sickrage.srLogger.warning("Could not connect to Trakt service: %s" % e)

        return self.render("trendingShows.mako",
                           title="Trending Shows",
                           header="Trending Shows",
                           trending_shows=trending_shows,
                           blacklist=blacklist)

    def trendingShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        return self.render("home_trendingShows.mako",
                           title="Trending Shows",
                           header="Trending Shows",
                           enable_anime_options=False)

    def getTrendingShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """

        blacklist = False
        trending_shows = []
        trakt_api = TraktAPI(sickrage.srConfig.SSL_VERIFY, sickrage.srConfig.TRAKT_TIMEOUT)

        try:
            not_liked_show = ""
            if sickrage.srConfig.TRAKT_BLACKLIST_NAME is not None and sickrage.srConfig.TRAKT_BLACKLIST_NAME:
                not_liked_show = trakt_api.traktRequest(
                    "users/" + sickrage.srConfig.TRAKT_USERNAME + "/lists/" + sickrage.srConfig.TRAKT_BLACKLIST_NAME + "/items") or []
            else:
                sickrage.srLogger.debug("trending blacklist name is empty")

            limit_show = 50 + len(not_liked_show)

            shows = trakt_api.traktRequest("shows/trending?limit=" + str(limit_show) + "&extended=full,images") or []

            library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
            for show in shows:
                show = {'show': show}
                show_id = show[b'show'][b'ids'][b'tvdb']

                try:
                    if not findCertainShow(sickrage.srCore.SHOWLIST, [int(show[b'show'][b'ids'][b'tvdb'])]):
                        if show_id not in [lshow[b'show'][b'ids'][b'tvdb'] for lshow in library_shows]:
                            if sickrage.srConfig.TRAKT_BLACKLIST_NAME:
                                not_liked_show = trakt_api.traktRequest(
                                    "users/{}/lists/{}/items".format(sickrage.srConfig.TRAKT_USERNAME,
                                                                     sickrage.srConfig.TRAKT_BLACKLIST_NAME))
                                if not_liked_show and [nlshow for nlshow in not_liked_show if (
                                                show_id == nlshow[b'show'][b'ids'][b'tvdb'] and nlshow[
                                            b'type'] == 'show')]:
                                    continue

                                trending_shows += [show]
                            else:
                                trending_shows += [show]

                except MultipleShowObjectsException:
                    continue

            if sickrage.srConfig.TRAKT_BLACKLIST_NAME != '':
                blacklist = True

        except traktException as e:
            sickrage.srLogger.warning("Could not connect to Trakt service: %s" % e)

        return self.render("trendingShows.mako",
                           blacklist=blacklist,
                           trending_shows=trending_shows)

    def popularShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        e = None

        try:
            popular_shows = imdb_popular.fetch_popular_shows()
        except Exception as e:
            popular_shows = None

        return self.render("home_popularShows.mako",
                           title="Popular Shows",
                           header="Popular Shows",
                           popular_shows=popular_shows,
                           imdb_exception=e,
                           topmenu="home")

    def addShowToBlacklist(self, indexer_id):
        # URL parameters
        data = {'shows': [{'ids': {'tvdb': indexer_id}}]}

        trakt_api = TraktAPI(sickrage.srConfig.SSL_VERIFY, sickrage.srConfig.TRAKT_TIMEOUT)

        trakt_api.traktRequest(
            "users/" + sickrage.srConfig.TRAKT_USERNAME + "/lists/" + sickrage.srConfig.TRAKT_BLACKLIST_NAME + "/items",
            data,
            method='POST')

        return self.redirect('/home/addShows/trendingShows/')

    def existingShows(self):
        """
        Prints out the page to add existing shows from a root dir
        """
        return self.render("home_addExistingShow.mako",
                           enable_anime_options=False,
                           quality=sickrage.srConfig.QUALITY_DEFAULT,
                           title='Existing Show',
                           header='Existing Show',
                           topmenu="home")

    def addTraktShow(self, indexer_id, showName):
        if findCertainShow(sickrage.srCore.SHOWLIST, int(indexer_id)):
            return

        if sickrage.srConfig.ROOT_DIRS:
            root_dirs = sickrage.srConfig.ROOT_DIRS.split('|')
            location = root_dirs[int(root_dirs[0]) + 1]
        else:
            location = None

        if location:
            show_dir = os.path.join(location, sanitizeFileName(showName))
            dir_exists = makeDir(show_dir)
            if not dir_exists:
                sickrage.srLogger.error("Unable to create the folder " + show_dir + ", can't add the show")
                return
            else:
                chmodAsParent(show_dir)

            sickrage.srCore.SHOWQUEUE.addShow(1, int(indexer_id), show_dir,
                                              default_status=sickrage.srConfig.STATUS_DEFAULT,
                                              quality=sickrage.srConfig.QUALITY_DEFAULT,
                                              flatten_folders=sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT,
                                              subtitles=sickrage.srConfig.SUBTITLES_DEFAULT,
                                              anime=sickrage.srConfig.ANIME_DEFAULT,
                                              scene=sickrage.srConfig.SCENE_DEFAULT,
                                              default_status_after=sickrage.srConfig.STATUS_DEFAULT_AFTER,
                                              archive=sickrage.srConfig.ARCHIVE_DEFAULT)

            notifications.message('Show added', 'Adding the specified show into ' + show_dir)
        else:
            sickrage.srLogger.error("There was an error creating the show, no root directory setting found")
            return "No root directories setup, please go back and add one."

        # done adding show
        return self.redirect('/home/')

    def addNewShow(self, whichSeries=None, indexerLang=None, rootDir=None, defaultStatus=None,
                   quality_preset=None, anyQualities=None, bestQualities=None, flatten_folders=None, subtitles=None,
                   fullShowPath=None, other_shows=None, skipShow=None, providedIndexer=None, anime=None,
                   scene=None, blacklist=None, whitelist=None, defaultStatusAfter=None, archive=None, ):
        """
        Receive tvdb id, dir, and other options and create a show from them. If extra show dirs are
        provided then it forwards back to newShow, if not it goes to /home.
        """

        if indexerLang is None:
            indexerLang = sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE

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
        if (not rootDir and not fullShowPath) or not whichSeries:
            return "Missing params, no Indexer ID or folder:" + repr(whichSeries) + " and " + repr(
                rootDir) + "/" + repr(fullShowPath)

        # figure out what show we're adding and where
        series_pieces = whichSeries.split('|')
        if (whichSeries and rootDir) or (whichSeries and fullShowPath and len(series_pieces) > 1):
            if len(series_pieces) < 6:
                sickrage.srLogger.error(
                    "Unable to add show due to show selection. Not anough arguments: %s" % (repr(series_pieces)))
                notifications.error("Unknown error. Unable to add show due to problem with show selection.")
                return self.redirect('/home/addShows/existingShows/')

            indexer = int(series_pieces[1])
            indexer_id = int(series_pieces[3])
            # Show name was sent in UTF-8 in the form
            show_name = series_pieces[4].decode('utf-8')
        else:
            # if no indexer was provided use the default indexer set in General settings
            if not providedIndexer:
                providedIndexer = sickrage.srConfig.INDEXER_DEFAULT

            indexer = int(providedIndexer)
            indexer_id = int(whichSeries)
            show_name = os.path.basename(os.path.normpath(fullShowPath))

        # use the whole path if it's given, or else append the show name to the root dir to get the full show path
        if fullShowPath:
            show_dir = os.path.normpath(fullShowPath)
        else:
            show_dir = os.path.join(rootDir, sanitizeFileName(show_name))

        # blanket policy - if the dir exists you should have used "add existing show" numbnuts
        if os.path.isdir(show_dir) and not fullShowPath:
            notifications.error("Unable to add show", "Folder " + show_dir + " exists already")
            return self.redirect('/home/addShows/existingShows/')

        # don't create show dir if config says not to
        if sickrage.srConfig.ADD_SHOWS_WO_DIR:
            sickrage.srLogger.info(
                "Skipping initial creation of " + show_dir + " due to sickrage.CONFIG.ini setting")
        else:
            dir_exists = makeDir(show_dir)
            if not dir_exists:
                sickrage.srLogger.error("Unable to create the folder " + show_dir + ", can't add the show")
                notifications.error("Unable to add show",
                                    "Unable to create the folder " + show_dir + ", can't add the show")
                # Don't redirect to default page because user wants to see the new show
                return self.redirect("/home/")
            else:
                chmodAsParent(show_dir)

        # prepare the inputs for passing along
        scene = sickrage.srConfig.checkbox_to_value(scene)
        anime = sickrage.srConfig.checkbox_to_value(anime)
        flatten_folders = sickrage.srConfig.checkbox_to_value(flatten_folders)
        subtitles = sickrage.srConfig.checkbox_to_value(subtitles)
        archive = sickrage.srConfig.checkbox_to_value(archive)

        if whitelist:
            whitelist = short_group_names(whitelist)
        if blacklist:
            blacklist = short_group_names(blacklist)

        if not anyQualities:
            anyQualities = []
        if not bestQualities or tryInt(quality_preset, None):
            bestQualities = []
        if not isinstance(anyQualities, list):
            anyQualities = [anyQualities]
        if not isinstance(bestQualities, list):
            bestQualities = [bestQualities]
        newQuality = Quality.combineQualities([int(q) for q in anyQualities], [int(q) for q in bestQualities])

        # add the show
        sickrage.srCore.SHOWQUEUE.addShow(indexer, indexer_id, show_dir, int(defaultStatus), newQuality,
                                          flatten_folders, indexerLang, subtitles, anime,
                                          scene, None, blacklist, whitelist, int(defaultStatusAfter), archive)
        notifications.message('Show added', 'Adding the specified show into ' + show_dir)

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

    def addExistingShows(self, shows_to_add=None, promptForSettings=None):
        """
        Receives a dir list and add them. Adds the ones with given TVDB IDs first, then forwards
        along to the newShow page.
        """
        # grab a list of other shows to add, if provided
        if not shows_to_add:
            shows_to_add = []
        elif not isinstance(shows_to_add, list):
            shows_to_add = [shows_to_add]

        shows_to_add = [urllib.unquote_plus(x) for x in shows_to_add]

        promptForSettings = sickrage.srConfig.checkbox_to_value(promptForSettings)

        indexer_id_given = []
        dirs_only = []
        # separate all the ones with Indexer IDs
        for cur_dir in shows_to_add:
            indexer, show_dir, indexer_id, show_name = None, None, None, None
            split_vals = cur_dir.split('|')
            if split_vals:
                if len(split_vals) > 2:
                    indexer, show_dir, indexer_id, show_name = self.split_extra_show(cur_dir)
                else:
                    dirs_only.append(cur_dir)
            if '|' not in cur_dir:
                dirs_only.append(cur_dir)
            else:
                dirs_only.append(cur_dir)

            if all([show_dir, indexer_id, show_name]):
                indexer_id_given.append((int(indexer), show_dir, int(indexer_id), show_name))

        # if they want me to prompt for settings then I will just carry on to the newShow page
        if promptForSettings and shows_to_add:
            return self.newShow(shows_to_add[0], shows_to_add[1:])

        # if they don't want me to prompt for settings then I can just add all the nfo shows now
        num_added = 0
        for cur_show in indexer_id_given:
            indexer, show_dir, indexer_id, show_name = cur_show

            if indexer is not None and indexer_id is not None:
                # add the show
                sickrage.srCore.SHOWQUEUE.addShow(indexer, indexer_id, show_dir,
                                                  default_status=sickrage.srConfig.STATUS_DEFAULT,
                                                  quality=sickrage.srConfig.QUALITY_DEFAULT,
                                                  flatten_folders=sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT,
                                                  subtitles=sickrage.srConfig.SUBTITLES_DEFAULT,
                                                  anime=sickrage.srConfig.ANIME_DEFAULT,
                                                  scene=sickrage.srConfig.SCENE_DEFAULT,
                                                  default_status_after=sickrage.srConfig.STATUS_DEFAULT_AFTER,
                                                  archive=sickrage.srConfig.ARCHIVE_DEFAULT)
                num_added += 1

        if num_added:
            notifications.message("Shows Added",
                                  "Automatically added " + str(num_added) + " from their existing metadata files")

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
        return self.render("manage.mako",
                           title='Mass Update',
                           header='Mass Update',
                           topmenu='manage')

    @staticmethod
    def showEpisodeStatuses(indexer_id, whichStatus):
        status_list = [int(whichStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER

        cur_show_results = main_db.MainDB().select(
            "SELECT season, episode, name FROM tv_episodes WHERE showid = ? AND season != 0 AND status IN (" + ','.join(
                ['?'] * len(status_list)) + ")", [int(indexer_id)] + status_list)

        result = {}
        for cur_result in cur_show_results:
            cur_season = int(cur_result[b"season"])
            cur_episode = int(cur_result[b"episode"])

            if cur_season not in result:
                result[cur_season] = {}

            result[cur_season][cur_episode] = cur_result[b"name"]

        return json_encode(result)

    def episodeStatuses(self, whichStatus=None):
        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        status_list = []

        if whichStatus:
            status_list = [int(whichStatus)]
            if int(whichStatus) == SNATCHED:
                status_list += Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

        # if we have no status then this is as far as we need to go
        if len(status_list):

            status_results = main_db.MainDB().select(
                "SELECT show_name, tv_shows.indexer_id AS indexer_id FROM tv_episodes, tv_shows WHERE tv_episodes.status IN (" + ','.join(
                    ['?'] * len(
                        status_list)) + ") AND season != 0 AND tv_episodes.showid = tv_shows.indexer_id ORDER BY show_name",
                status_list)

            for cur_status_result in status_results:
                cur_indexer_id = int(cur_status_result[b"indexer_id"])
                if cur_indexer_id not in ep_counts:
                    ep_counts[cur_indexer_id] = 1
                else:
                    ep_counts[cur_indexer_id] += 1

                show_names[cur_indexer_id] = cur_status_result[b"show_name"]
                if cur_indexer_id not in sorted_show_ids:
                    sorted_show_ids.append(cur_indexer_id)

        return self.render("manage_episodeStatuses.mako",
                           title="Episode Overview",
                           header="Episode Overview",
                           topmenu='manage',
                           whichStatus=whichStatus,
                           show_names=show_names,
                           ep_counts=ep_counts,
                           sorted_show_ids=sorted_show_ids)

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
                all_eps_results = main_db.MainDB().select(
                    "SELECT season, episode FROM tv_episodes WHERE status IN (" + ','.join(
                        ['?'] * len(status_list)) + ") AND season != 0 AND showid = ?",
                    status_list + [cur_indexer_id])
                all_eps = [str(x[b"season"]) + 'x' + str(x[b"episode"]) for x in all_eps_results]
                to_change[cur_indexer_id] = all_eps

            self.setStatus(cur_indexer_id, '|'.join(to_change[cur_indexer_id]), newStatus, direct=True)

        return self.redirect('/manage/episodeStatuses/')

    @staticmethod
    def showSubtitleMissed(indexer_id, whichSubs):

        cur_show_results = main_db.MainDB().select(
            "SELECT season, episode, name, subtitles FROM tv_episodes WHERE showid = ? AND season != 0 AND status LIKE '%4'",
            [int(indexer_id)])

        result = {}
        for cur_result in cur_show_results:
            if whichSubs == 'all':
                if not frozenset(subtitle_searcher.wantedLanguages()).difference(cur_result[b"subtitles"].split(',')):
                    continue
            elif whichSubs in cur_result[b"subtitles"]:
                continue

            cur_season = int(cur_result[b"season"])
            cur_episode = int(cur_result[b"episode"])

            if cur_season not in result:
                result[cur_season] = {}

            if cur_episode not in result[cur_season]:
                result[cur_season][cur_episode] = {}

            result[cur_season][cur_episode][b"name"] = cur_result[b"name"]

            result[cur_season][cur_episode][b"subtitles"] = cur_result[b"subtitles"]

        return json_encode(result)

    def subtitleMissed(self, whichSubs=None):
        if not whichSubs:
            return self.render("manage_subtitleMissed.mako",
                               whichSubs=whichSubs,
                               title='Episode Overview',
                               header='Episode Overview',
                               topmenu='manage')

        status_results = main_db.MainDB().select(
            "SELECT show_name, tv_shows.indexer_id as indexer_id, tv_episodes.subtitles subtitles " +
            "FROM tv_episodes, tv_shows " +
            "WHERE tv_shows.subtitles = 1 AND tv_episodes.status LIKE '%4' AND tv_episodes.season != 0 " +
            "AND tv_episodes.showid = tv_shows.indexer_id ORDER BY show_name")

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        for cur_status_result in status_results:
            if whichSubs == 'all':
                if not frozenset(subtitle_searcher.wantedLanguages()).difference(
                        cur_status_result[b"subtitles"].split(',')):
                    continue
            elif whichSubs in cur_status_result[b"subtitles"]:
                continue

            cur_indexer_id = int(cur_status_result[b"indexer_id"])
            if cur_indexer_id not in ep_counts:
                ep_counts[cur_indexer_id] = 1
            else:
                ep_counts[cur_indexer_id] += 1

            show_names[cur_indexer_id] = cur_status_result[b"show_name"]
            if cur_indexer_id not in sorted_show_ids:
                sorted_show_ids.append(cur_indexer_id)

        return self.render("manage_subtitleMissed.mako",
                           whichSubs=whichSubs,
                           show_names=show_names,
                           ep_counts=ep_counts,
                           sorted_show_ids=sorted_show_ids,
                           title='Missing Subtitles',
                           header='Missing Subtitles',
                           topmenu='manage')

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
                all_eps_results = main_db.MainDB().select(
                    "SELECT season, episode FROM tv_episodes WHERE status LIKE '%4' AND season != 0 AND showid = ?",
                    [cur_indexer_id])
                to_download[cur_indexer_id] = [str(x[b"season"]) + 'x' + str(x[b"episode"]) for x in all_eps_results]

            for epResult in to_download[cur_indexer_id]:
                season, episode = epResult.split('x')

                show = findCertainShow(sickrage.srCore.SHOWLIST, int(cur_indexer_id))
                show.getEpisode(int(season), int(episode)).downloadSubtitles()

        return self.redirect('/manage/subtitleMissed/')

    def backlogShow(self, indexer_id):
        show_obj = findCertainShow(sickrage.srCore.SHOWLIST, int(indexer_id))

        if show_obj:
            sickrage.srCore.BACKLOGSEARCHER.searchBacklog([show_obj])

        return self.redirect("/manage/backlogOverview/")

    def backlogOverview(self):
        showCounts = {}
        showCats = {}
        showSQLResults = {}

        for curShow in sickrage.srCore.SHOWLIST:

            epCounts = {}
            epCats = {}
            epCounts[Overview.SKIPPED] = 0
            epCounts[Overview.WANTED] = 0
            epCounts[Overview.QUAL] = 0
            epCounts[Overview.GOOD] = 0
            epCounts[Overview.UNAIRED] = 0
            epCounts[Overview.SNATCHED] = 0

            sqlResults = main_db.MainDB().select(
                "SELECT * FROM tv_episodes WHERE tv_episodes.showid IN (SELECT tv_shows.indexer_id FROM tv_shows WHERE tv_shows.indexer_id = ? AND paused = 0) ORDER BY tv_episodes.season DESC, tv_episodes.episode DESC",
                [curShow.indexerid])

            for curResult in sqlResults:
                curEpCat = curShow.getOverview(int(curResult[b"status"] or -1))
                if curEpCat:
                    epCats[str(curResult[b"season"]) + "x" + str(curResult[b"episode"])] = curEpCat
                    epCounts[curEpCat] += 1

            showCounts[curShow.indexerid] = epCounts
            showCats[curShow.indexerid] = epCats
            showSQLResults[curShow.indexerid] = sqlResults

        return self.render("manage_backlogOverview.mako",
                           showCounts=showCounts,
                           showCats=showCats,
                           showSQLResults=showSQLResults,
                           title='Backlog Overview',
                           header='Backlog Overview',
                           topmenu='manage')

    def massEdit(self, toEdit=None):
        if not toEdit:
            return self.redirect("/manage/")

        showIDs = toEdit.split("|")
        showList = []
        showNames = []
        for curID in showIDs:
            curID = int(curID)
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, curID)
            if showObj:
                showList.append(showObj)
                showNames.append(showObj.name)

        archive_firstmatch_all_same = True
        last_archive_firstmatch = None

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

            if archive_firstmatch_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_archive_firstmatch not in (None, curShow.archive_firstmatch):
                    archive_firstmatch_all_same = False
                else:
                    last_archive_firstmatch = curShow.archive_firstmatch

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

        archive_firstmatch_value = last_archive_firstmatch if archive_firstmatch_all_same else None
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

        return self.render("manage_massEdit.mako",
                           showList=toEdit,
                           showNames=showNames,
                           archive_firstmatch_value=archive_firstmatch_value,
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
                           title='Mass Edit',
                           header='Mass Edit',
                           topmenu='manage')

    def massEditSubmit(self, archive_firstmatch=None, paused=None, default_ep_status=None,
                       anime=None, sports=None, scene=None, flatten_folders=None, quality_preset=None,
                       subtitles=None, air_by_date=None, anyQualities=[], bestQualities=[], toEdit=None, *args,
                       **kwargs):
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
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(curShow))
            if not showObj:
                continue

            cur_root_dir = os.path.dirname(showObj.location)
            cur_show_dir = os.path.basename(showObj.location)
            if cur_root_dir in dir_map and cur_root_dir != dir_map[cur_root_dir]:
                new_show_dir = os.path.join(dir_map[cur_root_dir], cur_show_dir)
                sickrage.srLogger.info(
                    "For show " + showObj.name + " changing dir from " + showObj.location + " to " + new_show_dir)
            else:
                new_show_dir = showObj.location

            if archive_firstmatch == 'keep':
                new_archive_firstmatch = showObj.archive_firstmatch
            else:
                new_archive_firstmatch = True if archive_firstmatch == 'enable' else False
            new_archive_firstmatch = 'on' if new_archive_firstmatch else 'off'

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
                anyQualities, bestQualities = Quality.splitQuality(showObj.quality)
            elif tryInt(quality_preset, None):
                bestQualities = []

            exceptions_list = []

            curErrors += self.editShow(curShow, new_show_dir, anyQualities,
                                       bestQualities, exceptions_list,
                                       defaultEpStatus=new_default_ep_status,
                                       archive_firstmatch=new_archive_firstmatch,
                                       flatten_folders=new_flatten_folders,
                                       paused=new_paused, sports=new_sports,
                                       subtitles=new_subtitles, anime=new_anime,
                                       scene=new_scene, air_by_date=new_air_by_date,
                                       directCall=True)

            if curErrors:
                sickrage.srLogger.error("Errors: " + str(curErrors))
                errors.append('<b>%s:</b>\n<ul>' % showObj.name + ' '.join(
                    ['<li>%s</li>' % error for error in curErrors]) + "</ul>")

        if len(errors) > 0:
            notifications.error('%d error%s while saving changes:' % (len(errors), "" if len(errors) == 1 else "s"),
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

            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(curShowID))

            if showObj is None:
                continue

            if curShowID in toDelete:
                sickrage.srCore.SHOWQUEUE.removeShow(showObj, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in toRemove:
                sickrage.srCore.SHOWQUEUE.removeShow(showObj)
                # don't do anything else if it's being remove
                continue

            if curShowID in toUpdate:
                try:
                    sickrage.srCore.SHOWQUEUE.updateShow(showObj, True)
                    updates.append(showObj.name)
                except CantUpdateShowException as e:
                    errors.append("Unable to update show: {0}".format(str(e)))

            # don't bother refreshing shows that were updated anyway
            if curShowID in toRefresh and curShowID not in toUpdate:
                try:
                    sickrage.srCore.SHOWQUEUE.refreshShow(showObj)
                    refreshes.append(showObj.name)
                except CantRefreshShowException as e:
                    errors.append("Unable to refresh show " + showObj.name + ": {}".format(e.message))

            if curShowID in toRename:
                sickrage.srCore.SHOWQUEUE.renameShowEpisodes(showObj)
                renames.append(showObj.name)

            if curShowID in toSubtitle:
                sickrage.srCore.SHOWQUEUE.downloadSubtitles(showObj)
                subtitles.append(showObj.name)

        if errors:
            notifications.error("Errors encountered",
                                '<br >\n'.join(errors))

        messageDetail = ""

        if updates:
            messageDetail += "<br><b>Updates</b><br><ul><li>"
            messageDetail += "</li><li>".join(updates)
            messageDetail += "</li></ul>"

        if refreshes:
            messageDetail += "<br><b>Refreshes</b><br><ul><li>"
            messageDetail += "</li><li>".join(refreshes)
            messageDetail += "</li></ul>"

        if renames:
            messageDetail += "<br><b>Renames</b><br><ul><li>"
            messageDetail += "</li><li>".join(renames)
            messageDetail += "</li></ul>"

        if subtitles:
            messageDetail += "<br><b>Subtitles</b><br><ul><li>"
            messageDetail += "</li><li>".join(subtitles)
            messageDetail += "</li></ul>"

        if updates + refreshes + renames + subtitles:
            notifications.message("The following actions were queued:",
                                  messageDetail)

        return self.redirect("/manage/")

    def manageTorrents(self):
        info_download_station = ''

        if re.search('localhost', sickrage.srConfig.TORRENT_HOST):

            if sickrage.srConfig.LOCALHOST_IP == '':
                webui_url = re.sub('localhost', get_lan_ip(), sickrage.srConfig.TORRENT_HOST)
            else:
                webui_url = re.sub('localhost', sickrage.srConfig.LOCALHOST_IP,
                                   sickrage.srConfig.TORRENT_HOST)
        else:
            webui_url = sickrage.srConfig.TORRENT_HOST

        if sickrage.srConfig.TORRENT_METHOD == 'utorrent':
            webui_url = '/'.join(s.strip('/') for s in (webui_url, 'gui/'))
        if sickrage.srConfig.TORRENT_METHOD == 'download_station':
            if check_url(webui_url + 'download/'):
                webui_url += 'download/'
            else:
                info_download_station = '<p>To have a better experience please set the Download Station alias as <code>download</code>, you can check this setting in the Synology DSM <b>Control Panel</b> > <b>Application Portal</b>. Make sure you allow DSM to be embedded with iFrames too in <b>Control Panel</b> > <b>DSM Settings</b> > <b>Security</b>.</p><br><p>There is more information about this available <a href="https://github.com/midgetspy/Sick-Beard/pull/338">here</a>.</p><br>'

        if not sickrage.srConfig.TORRENT_PASSWORD == "" and not sickrage.srConfig.TORRENT_USERNAME == "":
            webui_url = re.sub('://',
                               '://' + str(sickrage.srConfig.TORRENT_USERNAME) + ':' + str(
                                   sickrage.srConfig.TORRENT_PASSWORD) + '@',
                               webui_url)

        return self.render("manage_torrents.mako",
                           webui_url=webui_url,
                           info_download_station=info_download_station,
                           title='Manage Torrents',
                           header='Manage Torrents',
                           topmenu='manage')

    def failedDownloads(self, limit=100, toRemove=None):
        if limit == "0":
            sqlResults = failed_db.FailedDB().select("SELECT * FROM failed")
        else:
            sqlResults = failed_db.FailedDB().select("SELECT * FROM failed LIMIT ?", [limit])

        toRemove = toRemove.split("|") if toRemove is not None else []

        for release in toRemove:
            main_db.MainDB().action("DELETE FROM failed WHERE failed.release = ?", [release])

        if toRemove:
            return self.redirect('/manage/failedDownloads/')

        return self.render("manage_failedDownloads.mako",
                           limit=limit,
                           failedResults=sqlResults,
                           title='Failed Downloads',
                           header='Failed Downloads',
                           topmenu='manage')


@Route('/manage/manageSearches(/?.*)')
class ManageSearches(Manage):
    def __init__(self, *args, **kwargs):
        super(ManageSearches, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("manage_manageSearches.mako",
                           backlogPaused=sickrage.srCore.SEARCHQUEUE.is_backlog_paused(),
                           backlogRunning=sickrage.srCore.SEARCHQUEUE.is_backlog_in_progress(),
                           dailySearchStatus=sickrage.srCore.DAILYSEARCHER.amActive,
                           findPropersStatus=sickrage.srCore.PROPERSEARCHER.amActive,
                           queueLength=sickrage.srCore.SEARCHQUEUE.queue_length(),
                           title='Manage Searches',
                           header='Manage Searches',
                           topmenu='manage')

    def forceBacklog(self):
        # force it to run the next time it looks
        result = sickrage.srCore.SCHEDULER.get_job('BACKLOG').func()
        if result:
            sickrage.srLogger.info("Backlog search forced")
            notifications.message('Backlog search started')

        return self.redirect("/manage/manageSearches/")

    def forceSearch(self):

        # force it to run the next time it looks
        result = sickrage.srCore.SCHEDULER.get_job('DAILYSEARCHER').func()
        if result:
            sickrage.srLogger.info("Daily search forced")
            notifications.message('Daily search started')

        return self.redirect("/manage/manageSearches/")

    def forceFindPropers(self):
        # force it to run the next time it looks
        result = sickrage.srCore.SCHEDULER.get_job('PROPERSEARCHER').func()
        if result:
            sickrage.srLogger.info("Find propers search forced")
            notifications.message('Find propers search started')

        return self.redirect("/manage/manageSearches/")

    def pauseBacklog(self, paused=None):
        if paused == "1":
            sickrage.srCore.SEARCHQUEUE.pause_backlog()
        else:
            sickrage.srCore.SEARCHQUEUE.unpause_backlog()

        return self.redirect("/manage/manageSearches/")


@Route('/history(/?.*)')
class History(WebRoot):
    def __init__(self, *args, **kwargs):
        super(History, self).__init__(*args, **kwargs)
        self.historyTool = HistoryTool()

    def index(self, limit=None):

        if limit is None:
            if sickrage.srConfig.HISTORY_LIMIT:
                limit = int(sickrage.srConfig.HISTORY_LIMIT)
            else:
                limit = 100
        else:
            limit = int(limit)

        sickrage.srConfig.HISTORY_LIMIT = limit

        sickrage.srConfig.save_config()

        compact = []
        data = self.historyTool.get(limit)

        for row in data:
            action = {
                'action': row[b'action'],
                'provider': row[b'provider'],
                'resource': row[b'resource'],
                'time': row[b'date']
            }

            if not any((history[b'show_id'] == row[b'show_id'] and
                                history[b'season'] == row[b'season'] and
                                history[b'episode'] == row[b'episode'] and
                                history[b'quality'] == row[b'quality']) for history in compact):
                history = {
                    'actions': [action],
                    'episode': row[b'episode'],
                    'quality': row[b'quality'],
                    'resource': row[b'resource'],
                    'season': row[b'season'],
                    'show_id': row[b'show_id'],
                    'show_name': row[b'show_name']
                }

                compact.append(history)
            else:
                index = [i for i, item in enumerate(compact)
                         if item[b'show_id'] == row[b'show_id'] and
                         item[b'season'] == row[b'season'] and
                         item[b'episode'] == row[b'episode'] and
                         item[b'quality'] == row[b'quality']][0]
                history = compact[index]
                history[b'actions'].append(action)
                history[b'actions'].sort(key=lambda x: x[b'time'], reverse=True)

        submenu = [
            {'title': 'Clear History', 'path': 'history/clearHistory', 'icon': 'ui-icon ui-icon-trash',
             'class': 'clearhistory', 'confirm': True},
            {'title': 'Trim History', 'path': 'history/trimHistory', 'icon': 'ui-icon ui-icon-trash',
             'class': 'trimhistory', 'confirm': True},
        ]

        return self.render("history.mako",
                           historyResults=data,
                           compactResults=compact,
                           limit=limit,
                           submenu=submenu,
                           title='History',
                           header='History',
                           topmenu="history")

    def clearHistory(self):
        self.historyTool.clear()

        notifications.message('History cleared')

        return self.redirect("/history/")

    def trimHistory(self):
        self.historyTool.trim()

        notifications.message('Removed history entries older than 30 days')

        return self.redirect("/history/")


@Route('/config(/?.*)')
class Config(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    @staticmethod
    def ConfigMenu():
        menu = [
            {'title': 'General', 'path': 'config/general/', 'icon': 'ui-icon ui-icon-gear'},
            {'title': 'Backup/Restore', 'path': 'config/backuprestore/', 'icon': 'ui-icon ui-icon-gear'},
            {'title': 'Search Settings', 'path': 'config/search/', 'icon': 'ui-icon ui-icon-search'},
            {'title': 'Search Providers', 'path': 'config/providers/', 'icon': 'ui-icon ui-icon-search'},
            {'title': 'Subtitles Settings', 'path': 'config/subtitles/', 'icon': 'ui-icon ui-icon-comment'},
            {'title': 'Post Processing', 'path': 'config/postProcessing/', 'icon': 'ui-icon ui-icon-folder-open'},
            {'title': 'Notifications', 'path': 'config/notifications/', 'icon': 'ui-icon ui-icon-note'},
            {'title': 'Anime', 'path': 'config/anime/', 'icon': 'submenu-icon-anime'},
        ]

        return menu

    def index(self):
        return self.render("config.mako",
                           submenu=self.ConfigMenu(),
                           title='Configuration',
                           header='Configuration',
                           topmenu="config")


@Route('/config/general(/?.*)')
class ConfigGeneral(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigGeneral, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_general.mako",
                           title='Config - General',
                           header='General Configuration',
                           topmenu='config',
                           submenu=self.ConfigMenu())

    @staticmethod
    def generateApiKey():
        return generateApiKey()

    @staticmethod
    def saveRootDirs(rootDirString=None):
        sickrage.srConfig.ROOT_DIRS = rootDirString

    @staticmethod
    def saveAddShowDefaults(defaultStatus, anyQualities, bestQualities, defaultFlattenFolders, subtitles=False,
                            anime=False, scene=False, defaultStatusAfter=WANTED, archive=False):

        if anyQualities:
            anyQualities = anyQualities.split(',')
        else:
            anyQualities = []

        if bestQualities:
            bestQualities = bestQualities.split(',')
        else:
            bestQualities = []

        newQuality = Quality.combineQualities(map(int, anyQualities), map(int, bestQualities))

        sickrage.srConfig.STATUS_DEFAULT = int(defaultStatus)
        sickrage.srConfig.STATUS_DEFAULT_AFTER = int(defaultStatusAfter)
        sickrage.srConfig.QUALITY_DEFAULT = int(newQuality)

        sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT = sickrage.srConfig.checkbox_to_value(defaultFlattenFolders)
        sickrage.srConfig.SUBTITLES_DEFAULT = sickrage.srConfig.checkbox_to_value(subtitles)

        sickrage.srConfig.ANIME_DEFAULT = sickrage.srConfig.checkbox_to_value(anime)
        sickrage.srConfig.SCENE_DEFAULT = sickrage.srConfig.checkbox_to_value(scene)
        sickrage.srConfig.ARCHIVE_DEFAULT = sickrage.srConfig.checkbox_to_value(archive)

        sickrage.srConfig.save_config()

    def saveGeneral(self, log_dir=None, log_nr=5, log_size=1048576, web_port=None, web_log=None,
                    encryption_version=None, web_ipv6=None,
                    trash_remove_show=None, trash_rotate_logs=None, update_frequency=None, skip_removed_files=None,
                    indexerDefaultLang='en', ep_default_deleted_status=None, launch_browser=None, showupdate_hour=3,
                    web_username=None,
                    api_key=None, indexer_default=None, timezone_display=None, cpu_preset='NORMAL',
                    web_password=None, version_notify=None, enable_https=None, https_cert=None, https_key=None,
                    handle_reverse_proxy=None, sort_article=None, auto_update=None, notify_on_update=None,
                    proxy_setting=None, proxy_indexers=None, anon_redirect=None, git_path=None, git_remote=None,
                    calendar_unprotected=None, calendar_icons=None, debug=None, ssl_verify=None, no_restart=None,
                    coming_eps_missed_range=None,
                    filter_row=None, fuzzy_dating=None, trim_zero=None, date_preset=None, date_preset_na=None,
                    time_preset=None,
                    indexer_timeout=None, download_url=None, rootDir=None, theme_name=None, default_page=None,
                    git_reset=None, git_username=None, git_password=None, git_autoissues=None,
                    display_all_seasons=None):

        results = []

        # Misc
        sickrage.srConfig.DOWNLOAD_URL = download_url
        sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE = indexerDefaultLang
        sickrage.srConfig.EP_DEFAULT_DELETED_STATUS = ep_default_deleted_status
        sickrage.srConfig.SKIP_REMOVED_FILES = sickrage.srConfig.checkbox_to_value(skip_removed_files)
        sickrage.srConfig.LAUNCH_BROWSER = sickrage.srConfig.checkbox_to_value(launch_browser)
        sickrage.srConfig.change_showupdate_hour(showupdate_hour)
        sickrage.srConfig.change_version_notify(sickrage.srConfig.checkbox_to_value(version_notify))
        sickrage.srConfig.AUTO_UPDATE = sickrage.srConfig.checkbox_to_value(auto_update)
        sickrage.srConfig.NOTIFY_ON_UPDATE = sickrage.srConfig.checkbox_to_value(notify_on_update)
        # sickrage.LOG_DIR is set in sickrage.CONFIG.change_log_dir()
        sickrage.srConfig.LOG_NR = log_nr
        sickrage.srConfig.LOG_SIZE = log_size

        sickrage.srConfig.TRASH_REMOVE_SHOW = sickrage.srConfig.checkbox_to_value(trash_remove_show)
        sickrage.srConfig.TRASH_ROTATE_LOGS = sickrage.srConfig.checkbox_to_value(trash_rotate_logs)
        sickrage.srConfig.change_updater_freq(update_frequency)
        sickrage.srConfig.LAUNCH_BROWSER = sickrage.srConfig.checkbox_to_value(launch_browser)
        sickrage.srConfig.SORT_ARTICLE = sickrage.srConfig.checkbox_to_value(sort_article)
        sickrage.srConfig.CPU_PRESET = cpu_preset
        sickrage.srConfig.ANON_REDIRECT = anon_redirect
        sickrage.srConfig.PROXY_SETTING = proxy_setting
        sickrage.srConfig.PROXY_INDEXERS = sickrage.srConfig.checkbox_to_value(proxy_indexers)
        sickrage.srConfig.GIT_USERNAME = git_username
        sickrage.srConfig.GIT_PASSWORD = git_password
        # sickrage.GIT_RESET = sickrage.CONFIG.checkbox_to_value(git_reset)
        # Force GIT_RESET
        sickrage.srConfig.GIT_RESET = 1
        sickrage.srConfig.GIT_AUTOISSUES = sickrage.srConfig.checkbox_to_value(git_autoissues)
        sickrage.srConfig.GIT_PATH = git_path
        sickrage.srConfig.GIT_REMOTE = git_remote
        sickrage.srConfig.CALENDAR_UNPROTECTED = sickrage.srConfig.checkbox_to_value(calendar_unprotected)
        sickrage.srConfig.CALENDAR_ICONS = sickrage.srConfig.checkbox_to_value(calendar_icons)
        sickrage.srConfig.NO_RESTART = sickrage.srConfig.checkbox_to_value(no_restart)
        sickrage.srConfig.DEBUG = sickrage.srConfig.checkbox_to_value(debug)
        sickrage.srConfig.SSL_VERIFY = sickrage.srConfig.checkbox_to_value(ssl_verify)
        # sickrage.LOG_DIR is set in sickrage.CONFIG.change_log_dir()
        sickrage.srConfig.COMING_EPS_MISSED_RANGE = sickrage.srConfig.to_int(coming_eps_missed_range,
                                                                                       default=7)
        sickrage.srConfig.DISPLAY_ALL_SEASONS = sickrage.srConfig.checkbox_to_value(display_all_seasons)

        sickrage.srConfig.WEB_PORT = sickrage.srConfig.to_int(web_port)
        sickrage.srConfig.WEB_IPV6 = sickrage.srConfig.checkbox_to_value(web_ipv6)
        # sickrage.WEB_LOG is set in sickrage.CONFIG.change_log_dir()
        if sickrage.srConfig.checkbox_to_value(encryption_version) == 1:
            sickrage.srConfig.ENCRYPTION_VERSION = 2
        else:
            sickrage.srConfig.ENCRYPTION_VERSION = 0
        sickrage.srConfig.WEB_USERNAME = web_username
        sickrage.srConfig.WEB_PASSWORD = web_password

        sickrage.srConfig.FILTER_ROW = sickrage.srConfig.checkbox_to_value(filter_row)
        sickrage.srConfig.FUZZY_DATING = sickrage.srConfig.checkbox_to_value(fuzzy_dating)
        sickrage.srConfig.TRIM_ZERO = sickrage.srConfig.checkbox_to_value(trim_zero)

        if date_preset:
            sickrage.srConfig.DATE_PRESET = date_preset

        if indexer_default:
            sickrage.srConfig.INDEXER_DEFAULT = sickrage.srConfig.to_int(indexer_default)

        if indexer_timeout:
            sickrage.srConfig.INDEXER_TIMEOUT = sickrage.srConfig.to_int(indexer_timeout)

        if time_preset:
            sickrage.srConfig.TIME_PRESET_W_SECONDS = time_preset
            sickrage.srConfig.TIME_PRESET = sickrage.srConfig.TIME_PRESET_W_SECONDS.replace(":%S", "")

        sickrage.srConfig.TIMEZONE_DISPLAY = timezone_display

        if not sickrage.srConfig.change_log_dir(os.path.abspath(os.path.join(sickrage.srCore.DATA_DIR, log_dir)),
                                                     web_log):
            results += ["Unable to create directory " + os.path.normpath(log_dir) + ", log directory not changed."]

        sickrage.srConfig.API_KEY = api_key

        sickrage.srConfig.ENABLE_HTTPS = sickrage.srConfig.checkbox_to_value(enable_https)

        if not sickrage.srConfig.change_https_cert(https_cert):
            results += [
                "Unable to create directory " + os.path.normpath(https_cert) + ", https cert directory not changed."]

        if not sickrage.srConfig.change_https_key(https_key):
            results += [
                "Unable to create directory " + os.path.normpath(https_key) + ", https key directory not changed."]

        sickrage.srConfig.HANDLE_REVERSE_PROXY = sickrage.srConfig.checkbox_to_value(handle_reverse_proxy)

        sickrage.srConfig.THEME_NAME = theme_name

        sickrage.srConfig.DEFAULT_PAGE = default_page

        sickrage.srConfig.save_config()

        if len(results) > 0:
            for x in results:
                sickrage.srLogger.error(x)
            notifications.error('Error(s) Saving Configuration',
                                '<br>\n'.join(results))
        else:
            notifications.message('Configuration Saved', os.path.join(sickrage.srConfig.CONFIG_FILE))

        return self.redirect("/config/general/")


@Route('/config/backuprestore(/?.*)')
class ConfigBackupRestore(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigBackupRestore, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_backuprestore.mako",
                           submenu=self.ConfigMenu(),
                           title='Config - Backup/Restore',
                           header='Backup/Restore',
                           topmenu='config')

    @staticmethod
    def backup(backupDir=None):
        finalResult = ''

        if backupDir:
            if backupAll(backupDir):
                finalResult += "Backup SUCCESSFUL"
            else:
                finalResult += "Backup FAILED!"
        else:
            finalResult += "You need to choose a folder to save your backup to first!"

        finalResult += "<br>\n"

        return finalResult

    @staticmethod
    def restore(backupFile=None):

        finalResult = ''

        if backupFile:
            source = backupFile
            target_dir = os.path.join(sickrage.srCore.DATA_DIR, 'restore')

            if restoreConfigZip(source, target_dir):
                finalResult += "Successfully extracted restore files to " + target_dir
                finalResult += "<br>Restart sickrage to complete the restore."
            else:
                finalResult += "Restore FAILED"
        else:
            finalResult += "You need to select a backup file to restore!"

        finalResult += "<br>\n"

        return finalResult


@Route('/config/search(/?.*)')
class ConfigSearch(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSearch, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_search.mako",
                           submenu=self.ConfigMenu(),
                           title='Config - Episode Search',
                           header='Search Settings',
                           topmenu='config')

    def saveSearch(self, use_nzbs=None, use_torrents=None, nzb_dir=None, sab_username=None, sab_password=None,
                   sab_apikey=None, sab_category=None, sab_category_anime=None, sab_category_backlog=None,
                   sab_category_anime_backlog=None, sab_host=None, nzbget_username=None,
                   nzbget_password=None, nzbget_category=None, nzbget_category_backlog=None, nzbget_category_anime=None,
                   nzbget_category_anime_backlog=None, nzbget_priority=None,
                   nzbget_host=None, nzbget_use_https=None, backlog_frequency=None,
                   dailysearch_frequency=None, nzb_method=None, torrent_method=None, usenet_retention=None,
                   download_propers=None, check_propers_interval=None, allow_high_priority=None, sab_forced=None,
                   randomize_providers=None, use_failed_downloads=None, delete_failed=None,
                   torrent_dir=None, torrent_username=None, torrent_password=None, torrent_host=None,
                   torrent_label=None, torrent_label_anime=None, torrent_path=None, torrent_verify_cert=None,
                   torrent_seed_time=None, torrent_paused=None, torrent_high_bandwidth=None,
                   torrent_rpcurl=None, torrent_auth_type=None, ignore_words=None, require_words=None,
                   ignored_subs_list=None):

        results = []

        if not sickrage.srConfig.change_nzb_dir(nzb_dir):
            results += ["Unable to create directory " + os.path.normpath(nzb_dir) + ", dir not changed."]

        if not sickrage.srConfig.change_torrent_dir(torrent_dir):
            results += ["Unable to create directory " + os.path.normpath(torrent_dir) + ", dir not changed."]

        sickrage.srConfig.change_daily_searcher_freq(dailysearch_frequency)

        sickrage.srConfig.change_backlog_searcher_freq(backlog_frequency)

        sickrage.srConfig.USE_NZBS = sickrage.srConfig.checkbox_to_value(use_nzbs)
        sickrage.srConfig.USE_TORRENTS = sickrage.srConfig.checkbox_to_value(use_torrents)

        sickrage.srConfig.NZB_METHOD = nzb_method
        sickrage.srConfig.TORRENT_METHOD = torrent_method
        sickrage.srConfig.USENET_RETENTION = sickrage.srConfig.to_int(usenet_retention, default=500)

        sickrage.srConfig.IGNORE_WORDS = ignore_words if ignore_words else ""
        sickrage.srConfig.REQUIRE_WORDS = require_words if require_words else ""
        sickrage.srConfig.IGNORED_SUBS_LIST = ignored_subs_list if ignored_subs_list else ""

        sickrage.srConfig.RANDOMIZE_PROVIDERS = sickrage.srConfig.checkbox_to_value(randomize_providers)

        sickrage.srConfig.change_download_propers(download_propers)

        sickrage.srConfig.PROPER_SEARCHER_INTERVAL = check_propers_interval

        sickrage.srConfig.ALLOW_HIGH_PRIORITY = sickrage.srConfig.checkbox_to_value(allow_high_priority)

        sickrage.srConfig.USE_FAILED_DOWNLOADS = sickrage.srConfig.checkbox_to_value(use_failed_downloads)
        sickrage.srConfig.DELETE_FAILED = sickrage.srConfig.checkbox_to_value(delete_failed)

        sickrage.srConfig.SAB_USERNAME = sab_username
        sickrage.srConfig.SAB_PASSWORD = sab_password
        sickrage.srConfig.SAB_APIKEY = sab_apikey.strip()
        sickrage.srConfig.SAB_CATEGORY = sab_category
        sickrage.srConfig.SAB_CATEGORY_BACKLOG = sab_category_backlog
        sickrage.srConfig.SAB_CATEGORY_ANIME = sab_category_anime
        sickrage.srConfig.SAB_CATEGORY_ANIME_BACKLOG = sab_category_anime_backlog
        sickrage.srConfig.SAB_HOST = sickrage.srConfig.clean_url(sab_host)
        sickrage.srConfig.SAB_FORCED = sickrage.srConfig.checkbox_to_value(sab_forced)

        sickrage.srConfig.NZBGET_USERNAME = nzbget_username
        sickrage.srConfig.NZBGET_PASSWORD = nzbget_password
        sickrage.srConfig.NZBGET_CATEGORY = nzbget_category
        sickrage.srConfig.NZBGET_CATEGORY_BACKLOG = nzbget_category_backlog
        sickrage.srConfig.NZBGET_CATEGORY_ANIME = nzbget_category_anime
        sickrage.srConfig.NZBGET_CATEGORY_ANIME_BACKLOG = nzbget_category_anime_backlog
        sickrage.srConfig.NZBGET_HOST = sickrage.srConfig.clean_host(nzbget_host)
        sickrage.srConfig.NZBGET_USE_HTTPS = sickrage.srConfig.checkbox_to_value(nzbget_use_https)
        sickrage.srConfig.NZBGET_PRIORITY = sickrage.srConfig.to_int(nzbget_priority, default=100)

        sickrage.srConfig.TORRENT_USERNAME = torrent_username
        sickrage.srConfig.TORRENT_PASSWORD = torrent_password
        sickrage.srConfig.TORRENT_LABEL = torrent_label
        sickrage.srConfig.TORRENT_LABEL_ANIME = torrent_label_anime
        sickrage.srConfig.TORRENT_VERIFY_CERT = sickrage.srConfig.checkbox_to_value(torrent_verify_cert)
        sickrage.srConfig.TORRENT_PATH = torrent_path.rstrip('/\\')
        sickrage.srConfig.TORRENT_SEED_TIME = torrent_seed_time
        sickrage.srConfig.TORRENT_PAUSED = sickrage.srConfig.checkbox_to_value(torrent_paused)
        sickrage.srConfig.TORRENT_HIGH_BANDWIDTH = sickrage.srConfig.checkbox_to_value(torrent_high_bandwidth)
        sickrage.srConfig.TORRENT_HOST = sickrage.srConfig.clean_url(torrent_host)
        sickrage.srConfig.TORRENT_RPCURL = torrent_rpcurl
        sickrage.srConfig.TORRENT_AUTH_TYPE = torrent_auth_type

        sickrage.srConfig.save_config()

        if len(results) > 0:
            for x in results:
                sickrage.srLogger.error(x)
            notifications.error('Error(s) Saving Configuration',
                                '<br>\n'.join(results))
        else:
            notifications.message('Configuration Saved', os.path.join(sickrage.srConfig.CONFIG_FILE))

        return self.redirect("/config/search/")


@Route('/config/postProcessing(/?.*)')
class ConfigPostProcessing(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigPostProcessing, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_postProcessing.mako",
                           submenu=self.ConfigMenu(),
                           title='Config - Post Processing',
                           header='Post Processing',
                           topmenu='config')

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
                           use_failed_downloads=None, delete_failed=None, extra_scripts=None,
                           naming_custom_sports=None, naming_sports_pattern=None,
                           naming_custom_anime=None, naming_anime_pattern=None,
                           naming_anime_multi_ep=None, autopostprocessor_frequency=None):

        results = []

        if not sickrage.srConfig.change_tv_download_dir(tv_download_dir):
            results += ["Unable to create directory " + os.path.normpath(tv_download_dir) + ", dir not changed."]

        sickrage.srConfig.change_autopostprocessor_freq(autopostprocessor_frequency)
        sickrage.srConfig.change_process_automatically(process_automatically)

        if unpack:
            if self.isRarSupported() != 'not supported':
                sickrage.srConfig.UNPACK = sickrage.srConfig.checkbox_to_value(unpack)
            else:
                sickrage.srConfig.UNPACK = 0
                results.append("Unpacking Not Supported, disabling unpack setting")
        else:
            sickrage.srConfig.UNPACK = sickrage.srConfig.checkbox_to_value(unpack)
        sickrage.srConfig.NO_DELETE = sickrage.srConfig.checkbox_to_value(no_delete)
        sickrage.srConfig.KEEP_PROCESSED_DIR = sickrage.srConfig.checkbox_to_value(keep_processed_dir)
        sickrage.srConfig.CREATE_MISSING_SHOW_DIRS = sickrage.srConfig.checkbox_to_value(
            create_missing_show_dirs)
        sickrage.srConfig.ADD_SHOWS_WO_DIR = sickrage.srConfig.checkbox_to_value(add_shows_wo_dir)
        sickrage.srConfig.PROCESS_METHOD = process_method
        sickrage.srConfig.DELRARCONTENTS = sickrage.srConfig.checkbox_to_value(del_rar_contents)
        sickrage.srConfig.EXTRA_SCRIPTS = [x.strip() for x in extra_scripts.split('|') if x.strip()]
        sickrage.srConfig.RENAME_EPISODES = sickrage.srConfig.checkbox_to_value(rename_episodes)
        sickrage.srConfig.AIRDATE_EPISODES = sickrage.srConfig.checkbox_to_value(airdate_episodes)
        sickrage.srConfig.FILE_TIMESTAMP_TIMEZONE = file_timestamp_timezone
        sickrage.srConfig.MOVE_ASSOCIATED_FILES = sickrage.srConfig.checkbox_to_value(move_associated_files)
        sickrage.srConfig.SYNC_FILES = sync_files
        sickrage.srConfig.POSTPONE_IF_SYNC_FILES = sickrage.srConfig.checkbox_to_value(postpone_if_sync_files)
        sickrage.srConfig.NAMING_CUSTOM_ABD = sickrage.srConfig.checkbox_to_value(naming_custom_abd)
        sickrage.srConfig.NAMING_CUSTOM_SPORTS = sickrage.srConfig.checkbox_to_value(naming_custom_sports)
        sickrage.srConfig.NAMING_CUSTOM_ANIME = sickrage.srConfig.checkbox_to_value(naming_custom_anime)
        sickrage.srConfig.NAMING_STRIP_YEAR = sickrage.srConfig.checkbox_to_value(naming_strip_year)
        sickrage.srConfig.USE_FAILED_DOWNLOADS = sickrage.srConfig.checkbox_to_value(use_failed_downloads)
        sickrage.srConfig.DELETE_FAILED = sickrage.srConfig.checkbox_to_value(delete_failed)
        sickrage.srConfig.NFO_RENAME = sickrage.srConfig.checkbox_to_value(nfo_rename)

        sickrage.srConfig.METADATA_KODI = kodi_data
        sickrage.srConfig.METADATA_KODI_12PLUS = kodi_12plus_data
        sickrage.srConfig.METADATA_MEDIABROWSER = mediabrowser_data
        sickrage.srConfig.METADATA_PS3 = sony_ps3_data
        sickrage.srConfig.METADATA_WDTV = wdtv_data
        sickrage.srConfig.METADATA_TIVO = tivo_data
        sickrage.srConfig.METADATA_MEDE8ER = mede8er_data

        sickrage.srCore.metadataProviderDict[b'KODI'].set_config(sickrage.srConfig.METADATA_KODI)
        sickrage.srCore.metadataProviderDict[b'KODI 12+'].set_config(sickrage.srConfig.METADATA_KODI_12PLUS)
        sickrage.srCore.metadataProviderDict[b'MediaBrowser'].set_config(sickrage.srConfig.METADATA_MEDIABROWSER)
        sickrage.srCore.metadataProviderDict[b'Sony PS3'].set_config(sickrage.srConfig.METADATA_PS3)
        sickrage.srCore.metadataProviderDict[b'WDTV'].set_config(sickrage.srConfig.METADATA_WDTV)
        sickrage.srCore.metadataProviderDict[b'TIVO'].set_config(sickrage.srConfig.METADATA_TIVO)
        sickrage.srCore.metadataProviderDict[b'Mede8er'].set_config(sickrage.srConfig.METADATA_MEDE8ER)

        if self.isNamingValid(naming_pattern, naming_multi_ep, anime_type=naming_anime) != "invalid":
            sickrage.srConfig.NAMING_PATTERN = naming_pattern
            sickrage.srConfig.NAMING_MULTI_EP = int(naming_multi_ep)
            sickrage.srConfig.NAMING_ANIME = int(naming_anime)
            sickrage.srConfig.NAMING_FORCE_FOLDERS = validator.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append("You tried saving an invalid anime naming config, not saving your naming settings")
            else:
                results.append("You tried saving an invalid naming config, not saving your naming settings")

        if self.isNamingValid(naming_anime_pattern, naming_anime_multi_ep, anime_type=naming_anime) != "invalid":
            sickrage.srConfig.NAMING_ANIME_PATTERN = naming_anime_pattern
            sickrage.srConfig.NAMING_ANIME_MULTI_EP = int(naming_anime_multi_ep)
            sickrage.srConfig.NAMING_ANIME = int(naming_anime)
            sickrage.srConfig.NAMING_FORCE_FOLDERS = validator.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append("You tried saving an invalid anime naming config, not saving your naming settings")
            else:
                results.append("You tried saving an invalid naming config, not saving your naming settings")

        if self.isNamingValid(naming_abd_pattern, None, abd=True) != "invalid":
            sickrage.srConfig.NAMING_ABD_PATTERN = naming_abd_pattern
        else:
            results.append(
                "You tried saving an invalid air-by-date naming config, not saving your air-by-date settings")

        if self.isNamingValid(naming_sports_pattern, None, sports=True) != "invalid":
            sickrage.srConfig.NAMING_SPORTS_PATTERN = naming_sports_pattern
        else:
            results.append(
                "You tried saving an invalid sports naming config, not saving your sports settings")

        sickrage.srConfig.save_config()

        if len(results) > 0:
            for x in results:
                sickrage.srLogger.warning(x)
            notifications.error('Error(s) Saving Configuration',
                                '<br>\n'.join(results))
        else:
            notifications.message('Configuration Saved', os.path.join(sickrage.srConfig.CONFIG_FILE))

        return self.redirect("/config/postProcessing/")

    @staticmethod
    def testNaming(pattern=None, multi=None, abd=False, sports=False, anime_type=None):

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        result = validator.test_name(pattern, multi, abd, sports, anime_type)

        result = os.path.join(result[b'dir'], result[b'name'])

        return result

    @staticmethod
    def isNamingValid(pattern=None, multi=None, abd=False, sports=False, anime_type=None):
        if pattern is None:
            return "invalid"

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
            return "valid"
        elif is_valid and require_season_folders:
            return "seasonfolders"
        else:
            return "invalid"

    @staticmethod
    def isRarSupported():
        """
        Test Packing Support:
            - Simulating in memory rar extraction on test.rar file
        """

        try:
            rar_path = os.path.join(sickrage.srCore.PROG_DIR, 'unrar2', 'test.rar')
            testing = RarFile(rar_path).read_files('*test.txt')
            if testing[0][1] == 'This is only a test.':
                return 'supported'
            sickrage.srLogger.error('Rar Not Supported: Can not read the content of test file')
            return 'not supported'
        except Exception as e:
            sickrage.srLogger.error('Rar Not Supported: {}'.format(e.message))
            return 'not supported'


@Route('/config/providers(/?.*)')
class ConfigProviders(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigProviders, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_providers.mako",
                           submenu=self.ConfigMenu(),
                           title='Config - Providers',
                           header='Search Providers',
                           topmenu='config')

    @staticmethod
    def canAddNewznabProvider(name):

        if not name:
            return json_encode({'error': 'No Provider Name specified'})

        providerDict = dict(
            zip([x.id for x in sickrage.srCore.newznabProviderList], sickrage.srCore.newznabProviderList))

        tempProvider = NewznabProvider(name, '')

        if tempProvider.id in providerDict:
            return json_encode({'error': 'Provider Name already exists as ' + providerDict[tempProvider.id].name})
        else:
            return json_encode({'success': tempProvider.id})

    @staticmethod
    def saveNewznabProvider(name, url, key=''):

        if not name or not url:
            return '0'

        providerDict = dict(
            zip([x.name for x in sickrage.srCore.newznabProviderList], sickrage.srCore.newznabProviderList))

        if name in providerDict:
            if not providerDict[name].default:
                providerDict[name].name = name
                providerDict[name].url = sickrage.srConfig.clean_url(url)

            providerDict[name].key = key
            # a 0 in the key spot indicates that no key is needed
            if key == '0':
                providerDict[name].needs_auth = False
            else:
                providerDict[name].needs_auth = True

            return providerDict[name].id + '|' + providerDict[name].configStr()

        else:
            newProvider = NewznabProvider(name, url, key=key)
            sickrage.srCore.newznabProviderList.append(newProvider)
            return newProvider.id + '|' + newProvider.configStr()

    @staticmethod
    def getNewznabCategories(name, url, key):
        """
        Retrieves a list of possible categories with category id's
        Using the default url/api?cat
        http://yournewznaburl.com/api?t=caps&apikey=yourapikey
        """
        error = ""
        success = False

        if not name:
            error += "\nNo Provider Name specified"
        if not url:
            error += "\nNo Provider Url specified"
        if not key:
            error += "\nNo Provider Api key specified"

        if error != "":
            return json_encode({'success': False, 'error': error})

        # Get list with Newznabproviders
        # providerDict = dict(zip([x.id for x in sickrage.newznabProviderList], sickrage.newznabProviderList))

        # Get newznabprovider obj with provided name
        tempProvider = NewznabProvider(name, url, key)

        success, tv_categories, error = tempProvider.get_newznab_categories()

        return json_encode({'success': success, 'tv_categories': tv_categories, 'error': error})

    @staticmethod
    def deleteNewznabProvider(nnid):

        providerDict = dict(
            zip([x.id for x in sickrage.srCore.newznabProviderList], sickrage.srCore.newznabProviderList))

        if nnid not in providerDict or providerDict[nnid].default:
            return '0'

        # delete it from the list
        sickrage.srCore.newznabProviderList.remove(providerDict[nnid])

        if nnid in sickrage.srConfig.PROVIDER_ORDER:
            sickrage.srConfig.PROVIDER_ORDER.remove(nnid)

        return '1'

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, titleTAG):

        if not name:
            return json_encode({'error': 'Invalid name specified'})

        providerDict = dict(
            zip([x.id for x in sickrage.srCore.torrentRssProviderList], sickrage.srCore.torrentRssProviderList))

        tempProvider = TorrentRssProvider(name, url, cookies, titleTAG)

        if tempProvider.id in providerDict:
            return json_encode({'error': 'Exists as ' + providerDict[tempProvider.id].name})
        else:
            (succ, errMsg) = tempProvider.validateRSS()
            if succ:
                return json_encode({'success': tempProvider.id})
            else:
                return json_encode({'error': errMsg})

    @staticmethod
    def saveTorrentRssProvider(name, url, cookies, titleTAG):

        if not name or not url:
            return '0'

        providerDict = dict(zip([x.name for x in sickrage.srCore.torrentRssProviderList],
                                sickrage.srCore.torrentRssProviderList))

        if name in providerDict:
            providerDict[name].name = name
            providerDict[name].url = sickrage.srConfig.clean_url(url)
            providerDict[name].cookies = cookies
            providerDict[name].titleTAG = titleTAG

            return providerDict[name].id + '|' + providerDict[name].configStr()

        else:
            newProvider = TorrentRssProvider(name, url, cookies, titleTAG)
            sickrage.srCore.torrentRssProviderList.append(newProvider)
            return newProvider.id + '|' + newProvider.configStr()

    @staticmethod
    def deleteTorrentRssProvider(id):

        providerDict = dict(
            zip([x.id for x in sickrage.srCore.torrentRssProviderList], sickrage.srCore.torrentRssProviderList))

        if id not in providerDict:
            return '0'

        # delete it from the list
        sickrage.srCore.torrentRssProviderList.remove(providerDict[id])

        if id in sickrage.srConfig.PROVIDER_ORDER:
            sickrage.srConfig.PROVIDER_ORDER.remove(id)

        return '1'

    def saveProviders(self, newznab_string='', torrentrss_string='', provider_order=None, **kwargs):
        results = []

        provider_str_list = provider_order.split() or []

        newznabProviderDict = dict(
            zip([x.id for x in sickrage.srCore.newznabProviderList], sickrage.srCore.newznabProviderList))

        torrentRssProviderDict = dict(
            zip([x.id for x in sickrage.srCore.torrentRssProviderList], sickrage.srCore.torrentRssProviderList))

        # do the enable/disable
        providers_reordered = []
        sorted_providers = sortedProviderDict()
        for curProviderStr in provider_str_list:
            curProvider, curEnabled = curProviderStr.split(':')
            curEnabled = bool(sickrage.srConfig.to_int(curEnabled))

            try:
                curProvObj = sorted_providers[curProvider]
                curProvObj.enabled = curEnabled
                if curEnabled:
                    providers_reordered.insert(0, curProvider)
                else:
                    providers_reordered.append(curProvider)
            except:
                continue

            if curProvider in newznabProviderDict:
                newznabProviderDict[curProvider].enabled = curEnabled
            elif curProvider in torrentRssProviderDict:
                torrentRssProviderDict[curProvider].enabled = curEnabled
        sickrage.srConfig.PROVIDER_ORDER = providers_reordered
        del providers_reordered, sorted_providers

        # add all the newznab info we got into our list
        finishedNames = []
        if newznab_string:
            for curNewznabProviderStr in newznab_string.split('!!!'):

                if not curNewznabProviderStr:
                    continue

                cur_name, cur_url, cur_key, cur_cat = curNewznabProviderStr.split('|')
                cur_url = sickrage.srConfig.clean_url(cur_url)

                newProvider = NewznabProvider(cur_name, cur_url, key=cur_key)

                cur_id = newProvider.id

                # if it already exists then update it
                if cur_id in newznabProviderDict:
                    newznabProviderDict[cur_id].name = cur_name
                    newznabProviderDict[cur_id].url = cur_url
                    newznabProviderDict[cur_id].key = cur_key
                    newznabProviderDict[cur_id].catIDs = cur_cat
                    # a 0 in the key spot indicates that no key is needed
                    if cur_key == '0':
                        newznabProviderDict[cur_id].needs_auth = False
                    else:
                        newznabProviderDict[cur_id].needs_auth = True

                    try:
                        newznabProviderDict[cur_id].search_mode = str(kwargs[cur_id + '_search_mode']).strip()
                    except Exception:
                        pass

                    try:
                        newznabProviderDict[cur_id].search_fallback = sickrage.srConfig.checkbox_to_value(
                            kwargs[cur_id + '_search_fallback'])
                    except Exception:
                        newznabProviderDict[cur_id].search_fallback = 0

                    try:
                        newznabProviderDict[cur_id].enable_daily = sickrage.srConfig.checkbox_to_value(
                            kwargs[cur_id + '_enable_daily'])
                    except Exception:
                        newznabProviderDict[cur_id].enable_daily = 0

                    try:
                        newznabProviderDict[cur_id].enable_backlog = sickrage.srConfig.checkbox_to_value(
                            kwargs[cur_id + '_enable_backlog'])
                    except Exception:
                        newznabProviderDict[cur_id].enable_backlog = 0
                else:
                    sickrage.srCore.newznabProviderList.append(newProvider)

                finishedNames.append(cur_id)

        if torrentrss_string:
            for curTorrentRssProviderStr in torrentrss_string.split('!!!'):

                if not curTorrentRssProviderStr:
                    continue

                curName, curURL, curCookies, curTitleTAG = curTorrentRssProviderStr.split('|')
                curURL = sickrage.srConfig.clean_url(curURL)

                newProvider = TorrentRssProvider(curName, curURL, curCookies, curTitleTAG)

                curID = newProvider.id

                # if it already exists then update it
                if curID in torrentRssProviderDict:
                    torrentRssProviderDict[curID].name = curName
                    torrentRssProviderDict[curID].url = curURL
                    torrentRssProviderDict[curID].cookies = curCookies
                    torrentRssProviderDict[curID].curTitleTAG = curTitleTAG
                else:
                    sickrage.srCore.torrentRssProviderList.append(newProvider)

                finishedNames.append(curID)

        # delete anything that is missing
        for curProvider in sickrage.srCore.torrentRssProviderList + sickrage.srCore.newznabProviderList:
            if curProvider.id in finishedNames:
                finishedNames.pop(finishedNames.index(curProvider.id))
                continue

            if curProvider.type == GenericProvider.NZB:
                sickrage.srCore.newznabProviderList.remove(curProvider)
            elif curProvider.type == GenericProvider.TORRENT:
                sickrage.srCore.torrentRssProviderList.remove(curProvider)

        # dynamically load provider settings
        for providerID, providerObj in sickrage.srCore.providersDict[GenericProvider.TORRENT].items():

            if hasattr(providerObj, 'minseed'):
                try:
                    providerObj.minseed = int(str(kwargs[providerID + '_minseed']).strip())
                except Exception:
                    providerObj.minseed = 0

            if hasattr(providerObj, 'minleech'):
                try:
                    providerObj.minleech = int(str(kwargs[providerID + '_minleech']).strip())
                except Exception:
                    providerObj.minleech = 0

            if hasattr(providerObj, 'ratio'):
                try:
                    providerObj.ratio = str(kwargs[providerID + '_ratio']).strip()
                except Exception:
                    providerObj.ratio = None

            if hasattr(providerObj, 'digest'):
                try:
                    providerObj.digest = str(kwargs[providerID + '_digest']).strip()
                except Exception:
                    providerObj.digest = None

            if hasattr(providerObj, 'hash'):
                try:
                    providerObj.hash = str(kwargs[providerID + '_hash']).strip()
                except Exception:
                    providerObj.hash = None

            if hasattr(providerObj, 'api_key'):
                try:
                    providerObj.api_key = str(kwargs[providerID + '_api_key']).strip()
                except Exception:
                    providerObj.api_key = None

            if hasattr(providerObj, 'username'):
                try:
                    providerObj.username = str(kwargs[providerID + '_username']).strip()
                except Exception:
                    providerObj.username = None

            if hasattr(providerObj, 'password'):
                try:
                    providerObj.password = str(kwargs[providerID + '_password']).strip()
                except Exception:
                    providerObj.password = None

            if hasattr(providerObj, 'passkey'):
                try:
                    providerObj.passkey = str(kwargs[providerID + '_passkey']).strip()
                except Exception:
                    providerObj.passkey = None

            if hasattr(providerObj, 'pin'):
                try:
                    providerObj.pin = str(kwargs[providerID + '_pin']).strip()
                except Exception:
                    providerObj.pin = None

            if hasattr(providerObj, 'confirmed'):
                try:
                    providerObj.confirmed = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_confirmed'])
                except Exception:
                    providerObj.confirmed = 0

            if hasattr(providerObj, 'ranked'):
                try:
                    providerObj.ranked = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_ranked'])
                except Exception:
                    providerObj.ranked = 0

            if hasattr(providerObj, 'engrelease'):
                try:
                    providerObj.engrelease = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_engrelease'])
                except Exception:
                    providerObj.engrelease = 0

            if hasattr(providerObj, 'onlyspasearch'):
                try:
                    providerObj.onlyspasearch = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_onlyspasearch'])
                except:
                    providerObj.onlyspasearch = 0

            if hasattr(providerObj, 'sorting'):
                try:
                    providerObj.sorting = str(kwargs[providerID + '_sorting']).strip()
                except Exception:
                    providerObj.sorting = 'seeders'

            if hasattr(providerObj, 'freeleech'):
                try:
                    providerObj.freeleech = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_freeleech'])
                except Exception:
                    providerObj.freeleech = 0

            if hasattr(providerObj, 'search_mode'):
                try:
                    providerObj.search_mode = str(kwargs[providerID + '_search_mode']).strip()
                except Exception:
                    providerObj.search_mode = 'eponly'

            if hasattr(providerObj, 'search_fallback'):
                try:
                    providerObj.search_fallback = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_search_fallback'])
                except Exception:
                    providerObj.search_fallback = 0  # these exceptions are catching unselected checkboxes

            if hasattr(providerObj, 'enable_daily'):
                try:
                    providerObj.enable_daily = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_enable_daily'])
                except Exception:
                    providerObj.enable_daily = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(providerObj, 'enable_backlog'):
                try:
                    providerObj.enable_backlog = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_enable_backlog'])
                except Exception:
                    providerObj.enable_backlog = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(providerObj, 'cat'):
                try:
                    providerObj.cat = int(str(kwargs[providerID + '_cat']).strip())
                except Exception:
                    providerObj.cat = 0

            if hasattr(providerObj, 'subtitle'):
                try:
                    providerObj.subtitle = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_subtitle'])
                except Exception:
                    providerObj.subtitle = 0

        for providerID, providerObj in sickrage.srCore.providersDict[GenericProvider.NZB].items():

            if hasattr(providerObj, 'api_key'):
                try:
                    providerObj.api_key = str(kwargs[providerID + '_api_key']).strip()
                except Exception:
                    providerObj.api_key = None

            if hasattr(providerObj, 'username'):
                try:
                    providerObj.username = str(kwargs[providerID + '_username']).strip()
                except Exception:
                    providerObj.username = None

            if hasattr(providerObj, 'search_mode'):
                try:
                    providerObj.search_mode = str(kwargs[providerID + '_search_mode']).strip()
                except Exception:
                    providerObj.search_mode = 'eponly'

            if hasattr(providerObj, 'search_fallback'):
                try:
                    providerObj.search_fallback = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_search_fallback'])
                except Exception:
                    providerObj.search_fallback = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(providerObj, 'enable_daily'):
                try:
                    providerObj.enable_daily = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_enable_daily'])
                except Exception:
                    providerObj.enable_daily = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(providerObj, 'enable_backlog'):
                try:
                    providerObj.enable_backlog = sickrage.srConfig.checkbox_to_value(
                        kwargs[providerID + '_enable_backlog'])
                except Exception:
                    providerObj.enable_backlog = 0  # these exceptions are actually catching unselected checkboxes

        sickrage.srConfig.NEWZNAB_DATA = '!!!'.join([x.configStr() for x in sickrage.srCore.newznabProviderList])
        sickrage.srConfig.save_config()

        if len(results) > 0:
            for x in results:
                sickrage.srLogger.error(x)
            notifications.error('Error(s) Saving Configuration',
                                '<br>\n'.join(results))
        else:
            notifications.message('Configuration Saved', os.path.join(sickrage.srConfig.CONFIG_FILE))

        return self.redirect("/config/providers/")


@Route('/config/notifications(/?.*)')
class ConfigNotifications(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigNotifications, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_notifications.mako",
                           submenu=self.ConfigMenu(),
                           title='Config - Notifications',
                           header='Notifications',
                           topmenu='config')

    def saveNotifications(self, use_kodi=None, kodi_always_on=None, kodi_notify_onsnatch=None,
                          kodi_notify_ondownload=None,
                          kodi_notify_onsubtitledownload=None, kodi_update_onlyfirst=None,
                          kodi_update_library=None, kodi_update_full=None, kodi_host=None, kodi_username=None,
                          kodi_password=None,
                          use_plex=None, plex_notify_onsnatch=None, plex_notify_ondownload=None,
                          plex_notify_onsubtitledownload=None, plex_update_library=None,
                          plex_server_host=None, plex_server_token=None, plex_host=None, plex_username=None,
                          plex_password=None,
                          use_plex_client=None, plex_client_username=None, plex_client_password=None,
                          use_emby=None, emby_host=None, emby_apikey=None,
                          use_growl=None, growl_notify_onsnatch=None, growl_notify_ondownload=None,
                          growl_notify_onsubtitledownload=None, growl_host=None, growl_password=None,
                          use_freemobile=None, freemobile_notify_onsnatch=None, freemobile_notify_ondownload=None,
                          freemobile_notify_onsubtitledownload=None, freemobile_id=None, freemobile_apikey=None,
                          use_prowl=None, prowl_notify_onsnatch=None, prowl_notify_ondownload=None,
                          prowl_notify_onsubtitledownload=None, prowl_api=None, prowl_priority=0,
                          use_twitter=None, twitter_notify_onsnatch=None, twitter_notify_ondownload=None,
                          twitter_notify_onsubtitledownload=None, twitter_usedm=None, twitter_dmto=None,
                          use_boxcar=None, boxcar_notify_onsnatch=None, boxcar_notify_ondownload=None,
                          boxcar_notify_onsubtitledownload=None, boxcar_username=None,
                          use_boxcar2=None, boxcar2_notify_onsnatch=None, boxcar2_notify_ondownload=None,
                          boxcar2_notify_onsubtitledownload=None, boxcar2_accesstoken=None,
                          use_pushover=None, pushover_notify_onsnatch=None, pushover_notify_ondownload=None,
                          pushover_notify_onsubtitledownload=None, pushover_userkey=None, pushover_apikey=None,
                          pushover_device=None, pushover_sound=None,
                          use_libnotify=None, libnotify_notify_onsnatch=None, libnotify_notify_ondownload=None,
                          libnotify_notify_onsubtitledownload=None,
                          use_nmj=None, nmj_host=None, nmj_database=None, nmj_mount=None, use_synoindex=None,
                          use_nmjv2=None, nmjv2_host=None, nmjv2_dbloc=None, nmjv2_database=None,
                          use_trakt=None, trakt_username=None, trakt_pin=None,
                          trakt_remove_watchlist=None, trakt_sync_watchlist=None, trakt_remove_show_from_sickrage=None,
                          trakt_method_add=None,
                          trakt_start_paused=None, trakt_use_recommended=None, trakt_sync=None, trakt_sync_remove=None,
                          trakt_default_indexer=None, trakt_remove_serieslist=None, trakt_timeout=None,
                          trakt_blacklist_name=None,
                          use_synologynotifier=None, synologynotifier_notify_onsnatch=None,
                          synologynotifier_notify_ondownload=None, synologynotifier_notify_onsubtitledownload=None,
                          use_pytivo=None, pytivo_notify_onsnatch=None, pytivo_notify_ondownload=None,
                          pytivo_notify_onsubtitledownload=None, pytivo_update_library=None,
                          pytivo_host=None, pytivo_share_name=None, pytivo_tivo_name=None,
                          use_nma=None, nma_notify_onsnatch=None, nma_notify_ondownload=None,
                          nma_notify_onsubtitledownload=None, nma_api=None, nma_priority=0,
                          use_pushalot=None, pushalot_notify_onsnatch=None, pushalot_notify_ondownload=None,
                          pushalot_notify_onsubtitledownload=None, pushalot_authorizationtoken=None,
                          use_pushbullet=None, pushbullet_notify_onsnatch=None, pushbullet_notify_ondownload=None,
                          pushbullet_notify_onsubtitledownload=None, pushbullet_api=None, pushbullet_device=None,
                          pushbullet_device_list=None,
                          use_email=None, email_notify_onsnatch=None, email_notify_ondownload=None,
                          email_notify_onsubtitledownload=None, email_host=None, email_port=25, email_from=None,
                          email_tls=None, email_user=None, email_password=None, email_list=None, email_show_list=None,
                          email_show=None):

        results = []

        sickrage.srConfig.USE_KODI = sickrage.srConfig.checkbox_to_value(use_kodi)
        sickrage.srConfig.KODI_ALWAYS_ON = sickrage.srConfig.checkbox_to_value(kodi_always_on)
        sickrage.srConfig.KODI_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(kodi_notify_onsnatch)
        sickrage.srConfig.KODI_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(kodi_notify_ondownload)
        sickrage.srConfig.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            kodi_notify_onsubtitledownload)
        sickrage.srConfig.KODI_UPDATE_LIBRARY = sickrage.srConfig.checkbox_to_value(kodi_update_library)
        sickrage.srConfig.KODI_UPDATE_FULL = sickrage.srConfig.checkbox_to_value(kodi_update_full)
        sickrage.srConfig.KODI_UPDATE_ONLYFIRST = sickrage.srConfig.checkbox_to_value(kodi_update_onlyfirst)
        sickrage.srConfig.KODI_HOST = sickrage.srConfig.clean_hosts(kodi_host)
        sickrage.srConfig.KODI_USERNAME = kodi_username
        sickrage.srConfig.KODI_PASSWORD = kodi_password

        sickrage.srConfig.USE_PLEX = sickrage.srConfig.checkbox_to_value(use_plex)
        sickrage.srConfig.PLEX_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(plex_notify_onsnatch)
        sickrage.srConfig.PLEX_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(plex_notify_ondownload)
        sickrage.srConfig.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            plex_notify_onsubtitledownload)
        sickrage.srConfig.PLEX_UPDATE_LIBRARY = sickrage.srConfig.checkbox_to_value(plex_update_library)
        sickrage.srConfig.PLEX_HOST = sickrage.srConfig.clean_hosts(plex_host)
        sickrage.srConfig.PLEX_SERVER_HOST = sickrage.srConfig.clean_hosts(plex_server_host)
        sickrage.srConfig.PLEX_SERVER_TOKEN = sickrage.srConfig.clean_host(plex_server_token)
        sickrage.srConfig.PLEX_USERNAME = plex_username
        sickrage.srConfig.PLEX_PASSWORD = plex_password
        sickrage.srConfig.USE_PLEX_CLIENT = sickrage.srConfig.checkbox_to_value(use_plex)
        sickrage.srConfig.PLEX_CLIENT_USERNAME = plex_username
        sickrage.srConfig.PLEX_CLIENT_PASSWORD = plex_password

        sickrage.srConfig.USE_EMBY = sickrage.srConfig.checkbox_to_value(use_emby)
        sickrage.srConfig.EMBY_HOST = sickrage.srConfig.clean_host(emby_host)
        sickrage.srConfig.EMBY_APIKEY = emby_apikey

        sickrage.srConfig.USE_GROWL = sickrage.srConfig.checkbox_to_value(use_growl)
        sickrage.srConfig.GROWL_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(growl_notify_onsnatch)
        sickrage.srConfig.GROWL_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            growl_notify_ondownload)
        sickrage.srConfig.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            growl_notify_onsubtitledownload)
        sickrage.srConfig.GROWL_HOST = sickrage.srConfig.clean_host(growl_host, default_port=23053)
        sickrage.srConfig.GROWL_PASSWORD = growl_password

        sickrage.srConfig.USE_FREEMOBILE = sickrage.srConfig.checkbox_to_value(use_freemobile)
        sickrage.srConfig.FREEMOBILE_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            freemobile_notify_onsnatch)
        sickrage.srConfig.FREEMOBILE_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            freemobile_notify_ondownload)
        sickrage.srConfig.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            freemobile_notify_onsubtitledownload)
        sickrage.srConfig.FREEMOBILE_ID = freemobile_id
        sickrage.srConfig.FREEMOBILE_APIKEY = freemobile_apikey

        sickrage.srConfig.USE_PROWL = sickrage.srConfig.checkbox_to_value(use_prowl)
        sickrage.srConfig.PROWL_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(prowl_notify_onsnatch)
        sickrage.srConfig.PROWL_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            prowl_notify_ondownload)
        sickrage.srConfig.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            prowl_notify_onsubtitledownload)
        sickrage.srConfig.PROWL_API = prowl_api
        sickrage.srConfig.PROWL_PRIORITY = prowl_priority

        sickrage.srConfig.USE_TWITTER = sickrage.srConfig.checkbox_to_value(use_twitter)
        sickrage.srConfig.TWITTER_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            twitter_notify_onsnatch)
        sickrage.srConfig.TWITTER_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            twitter_notify_ondownload)
        sickrage.srConfig.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            twitter_notify_onsubtitledownload)
        sickrage.srConfig.TWITTER_USEDM = sickrage.srConfig.checkbox_to_value(twitter_usedm)
        sickrage.srConfig.TWITTER_DMTO = twitter_dmto

        sickrage.srConfig.USE_BOXCAR = sickrage.srConfig.checkbox_to_value(use_boxcar)
        sickrage.srConfig.BOXCAR_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(boxcar_notify_onsnatch)
        sickrage.srConfig.BOXCAR_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            boxcar_notify_ondownload)
        sickrage.srConfig.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            boxcar_notify_onsubtitledownload)
        sickrage.srConfig.BOXCAR_USERNAME = boxcar_username

        sickrage.srConfig.USE_BOXCAR2 = sickrage.srConfig.checkbox_to_value(use_boxcar2)
        sickrage.srConfig.BOXCAR2_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            boxcar2_notify_onsnatch)
        sickrage.srConfig.BOXCAR2_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            boxcar2_notify_ondownload)
        sickrage.srConfig.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            boxcar2_notify_onsubtitledownload)
        sickrage.srConfig.BOXCAR2_ACCESSTOKEN = boxcar2_accesstoken

        sickrage.srConfig.USE_PUSHOVER = sickrage.srConfig.checkbox_to_value(use_pushover)
        sickrage.srConfig.PUSHOVER_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            pushover_notify_onsnatch)
        sickrage.srConfig.PUSHOVER_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pushover_notify_ondownload)
        sickrage.srConfig.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pushover_notify_onsubtitledownload)
        sickrage.srConfig.PUSHOVER_USERKEY = pushover_userkey
        sickrage.srConfig.PUSHOVER_APIKEY = pushover_apikey
        sickrage.srConfig.PUSHOVER_DEVICE = pushover_device
        sickrage.srConfig.PUSHOVER_SOUND = pushover_sound

        sickrage.srConfig.USE_LIBNOTIFY = sickrage.srConfig.checkbox_to_value(use_libnotify)
        sickrage.srConfig.LIBNOTIFY_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            libnotify_notify_onsnatch)
        sickrage.srConfig.LIBNOTIFY_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            libnotify_notify_ondownload)
        sickrage.srConfig.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            libnotify_notify_onsubtitledownload)

        sickrage.srConfig.USE_NMJ = sickrage.srConfig.checkbox_to_value(use_nmj)
        sickrage.srConfig.NMJ_HOST = sickrage.srConfig.clean_host(nmj_host)
        sickrage.srConfig.NMJ_DATABASE = nmj_database
        sickrage.srConfig.NMJ_MOUNT = nmj_mount

        sickrage.srConfig.USE_NMJv2 = sickrage.srConfig.checkbox_to_value(use_nmjv2)
        sickrage.srConfig.NMJv2_HOST = sickrage.srConfig.clean_host(nmjv2_host)
        sickrage.srConfig.NMJv2_DATABASE = nmjv2_database
        sickrage.srConfig.NMJv2_DBLOC = nmjv2_dbloc

        sickrage.srConfig.USE_SYNOINDEX = sickrage.srConfig.checkbox_to_value(use_synoindex)

        sickrage.srConfig.USE_SYNOLOGYNOTIFIER = sickrage.srConfig.checkbox_to_value(use_synologynotifier)
        sickrage.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            synologynotifier_notify_onsnatch)
        sickrage.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            synologynotifier_notify_ondownload)
        sickrage.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            synologynotifier_notify_onsubtitledownload)

        sickrage.srConfig.change_use_trakt(use_trakt)
        sickrage.srConfig.TRAKT_USERNAME = trakt_username
        sickrage.srConfig.TRAKT_REMOVE_WATCHLIST = sickrage.srConfig.checkbox_to_value(trakt_remove_watchlist)
        sickrage.srConfig.TRAKT_REMOVE_SERIESLIST = sickrage.srConfig.checkbox_to_value(
            trakt_remove_serieslist)
        sickrage.srConfig.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = sickrage.srConfig.checkbox_to_value(
            trakt_remove_show_from_sickrage)
        sickrage.srConfig.TRAKT_SYNC_WATCHLIST = sickrage.srConfig.checkbox_to_value(trakt_sync_watchlist)
        sickrage.srConfig.TRAKT_METHOD_ADD = int(trakt_method_add)
        sickrage.srConfig.TRAKT_START_PAUSED = sickrage.srConfig.checkbox_to_value(trakt_start_paused)
        sickrage.srConfig.TRAKT_USE_RECOMMENDED = sickrage.srConfig.checkbox_to_value(trakt_use_recommended)
        sickrage.srConfig.TRAKT_SYNC = sickrage.srConfig.checkbox_to_value(trakt_sync)
        sickrage.srConfig.TRAKT_SYNC_REMOVE = sickrage.srConfig.checkbox_to_value(trakt_sync_remove)
        sickrage.srConfig.TRAKT_DEFAULT_INDEXER = int(trakt_default_indexer)
        sickrage.srConfig.TRAKT_TIMEOUT = int(trakt_timeout)
        sickrage.srConfig.TRAKT_BLACKLIST_NAME = trakt_blacklist_name

        sickrage.srConfig.USE_EMAIL = sickrage.srConfig.checkbox_to_value(use_email)
        sickrage.srConfig.EMAIL_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(email_notify_onsnatch)
        sickrage.srConfig.EMAIL_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            email_notify_ondownload)
        sickrage.srConfig.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            email_notify_onsubtitledownload)
        sickrage.srConfig.EMAIL_HOST = sickrage.srConfig.clean_host(email_host)
        sickrage.srConfig.EMAIL_PORT = sickrage.srConfig.to_int(email_port, default=25)
        sickrage.srConfig.EMAIL_FROM = email_from
        sickrage.srConfig.EMAIL_TLS = sickrage.srConfig.checkbox_to_value(email_tls)
        sickrage.srConfig.EMAIL_USER = email_user
        sickrage.srConfig.EMAIL_PASSWORD = email_password
        sickrage.srConfig.EMAIL_LIST = email_list

        sickrage.srConfig.USE_PYTIVO = sickrage.srConfig.checkbox_to_value(use_pytivo)
        sickrage.srConfig.PYTIVO_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(pytivo_notify_onsnatch)
        sickrage.srConfig.PYTIVO_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pytivo_notify_ondownload)
        sickrage.srConfig.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pytivo_notify_onsubtitledownload)
        sickrage.srConfig.PYTIVO_UPDATE_LIBRARY = sickrage.srConfig.checkbox_to_value(pytivo_update_library)
        sickrage.srConfig.PYTIVO_HOST = sickrage.srConfig.clean_host(pytivo_host)
        sickrage.srConfig.PYTIVO_SHARE_NAME = pytivo_share_name
        sickrage.srConfig.PYTIVO_TIVO_NAME = pytivo_tivo_name

        sickrage.srConfig.USE_NMA = sickrage.srConfig.checkbox_to_value(use_nma)
        sickrage.srConfig.NMA_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(nma_notify_onsnatch)
        sickrage.srConfig.NMA_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(nma_notify_ondownload)
        sickrage.srConfig.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            nma_notify_onsubtitledownload)
        sickrage.srConfig.NMA_API = nma_api
        sickrage.srConfig.NMA_PRIORITY = nma_priority

        sickrage.srConfig.USE_PUSHALOT = sickrage.srConfig.checkbox_to_value(use_pushalot)
        sickrage.srConfig.PUSHALOT_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            pushalot_notify_onsnatch)
        sickrage.srConfig.PUSHALOT_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pushalot_notify_ondownload)
        sickrage.srConfig.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pushalot_notify_onsubtitledownload)
        sickrage.srConfig.PUSHALOT_AUTHORIZATIONTOKEN = pushalot_authorizationtoken

        sickrage.srConfig.USE_PUSHBULLET = sickrage.srConfig.checkbox_to_value(use_pushbullet)
        sickrage.srConfig.PUSHBULLET_NOTIFY_ONSNATCH = sickrage.srConfig.checkbox_to_value(
            pushbullet_notify_onsnatch)
        sickrage.srConfig.PUSHBULLET_NOTIFY_ONDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pushbullet_notify_ondownload)
        sickrage.srConfig.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srConfig.checkbox_to_value(
            pushbullet_notify_onsubtitledownload)
        sickrage.srConfig.PUSHBULLET_API = pushbullet_api
        sickrage.srConfig.PUSHBULLET_DEVICE = pushbullet_device_list

        sickrage.srConfig.save_config()

        if len(results) > 0:
            for x in results:
                sickrage.srLogger.error(x)
            notifications.error('Error(s) Saving Configuration',
                                '<br>\n'.join(results))
        else:
            notifications.message('Configuration Saved', os.path.join(sickrage.srConfig.CONFIG_FILE))

        return self.redirect("/config/notifications/")


@Route('/config/subtitles(/?.*)')
class ConfigSubtitles(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSubtitles, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_subtitles.mako",
                           submenu=self.ConfigMenu(),
                           title='Config - Subtitles',
                           header='Subtitles',
                           topmenu='config')

    def saveSubtitles(self, use_subtitles=None, subtitles_plugins=None, subtitles_languages=None, subtitles_dir=None,
                      service_order=None, subtitles_history=None, subtitles_finder_frequency=None,
                      subtitles_multi=None, embedded_subtitles_all=None, subtitles_extra_scripts=None,
                      subtitles_hearing_impaired=None,
                      addic7ed_user=None, addic7ed_pass=None, legendastv_user=None, legendastv_pass=None,
                      opensubtitles_user=None, opensubtitles_pass=None):

        results = []

        sickrage.srConfig.change_subtitle_searcher_freq(subtitles_finder_frequency)
        sickrage.srConfig.change_use_subtitles(use_subtitles)

        sickrage.srConfig.SUBTITLES_LANGUAGES = [lang.strip() for lang in subtitles_languages.split(',') if
                                                      subtitle_searcher.isValidLanguage(
                                                          lang.strip())] if subtitles_languages else []
        sickrage.srConfig.SUBTITLES_DIR = subtitles_dir
        sickrage.srConfig.SUBTITLES_HISTORY = sickrage.srConfig.checkbox_to_value(subtitles_history)
        sickrage.srConfig.EMBEDDED_SUBTITLES_ALL = sickrage.srConfig.checkbox_to_value(embedded_subtitles_all)
        sickrage.srConfig.SUBTITLES_HEARING_IMPAIRED = sickrage.srConfig.checkbox_to_value(
            subtitles_hearing_impaired)
        sickrage.srConfig.SUBTITLES_MULTI = sickrage.srConfig.checkbox_to_value(subtitles_multi)
        sickrage.srConfig.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in subtitles_extra_scripts.split('|') if
                                                          x.strip()]

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            curService, curEnabled = curServiceStr.split(':')
            subtitles_services_list.append(curService)
            subtitles_services_enabled.append(int(curEnabled))

        sickrage.srConfig.SUBTITLES_SERVICES_LIST = subtitles_services_list
        sickrage.srConfig.SUBTITLES_SERVICES_ENABLED = subtitles_services_enabled

        sickrage.srConfig.ADDIC7ED_USER = addic7ed_user or ''
        sickrage.srConfig.ADDIC7ED_PASS = addic7ed_pass or ''
        sickrage.srConfig.LEGENDASTV_USER = legendastv_user or ''
        sickrage.srConfig.LEGENDASTV_PASS = legendastv_pass or ''
        sickrage.srConfig.OPENSUBTITLES_USER = opensubtitles_user or ''
        sickrage.srConfig.OPENSUBTITLES_PASS = opensubtitles_pass or ''

        sickrage.srConfig.save_config()

        if len(results) > 0:
            for x in results:
                sickrage.srLogger.error(x)
            notifications.error('Error(s) Saving Configuration',
                                '<br>\n'.join(results))
        else:
            notifications.message('Configuration Saved', os.path.join(sickrage.srConfig.CONFIG_FILE))

        return self.redirect("/config/subtitles/")


@Route('/config/anime(/?.*)')
class ConfigAnime(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigAnime, self).__init__(*args, **kwargs)

    def index(self):
        return self.render("config_anime.mako",
                           submenu=self.ConfigMenu(),
                           title='Config - Anime',
                           header='Anime',
                           topmenu='config')

    def saveAnime(self, use_anidb=None, anidb_username=None, anidb_password=None, anidb_use_mylist=None,
                  split_home=None):

        results = []

        sickrage.srConfig.USE_ANIDB = sickrage.srConfig.checkbox_to_value(use_anidb)
        sickrage.srConfig.ANIDB_USERNAME = anidb_username
        sickrage.srConfig.ANIDB_PASSWORD = anidb_password
        sickrage.srConfig.ANIDB_USE_MYLIST = sickrage.srConfig.checkbox_to_value(anidb_use_mylist)
        sickrage.srConfig.ANIME_SPLIT_HOME = sickrage.srConfig.checkbox_to_value(split_home)

        sickrage.srConfig.save_config()

        if len(results) > 0:
            for x in results:
                sickrage.srLogger.error(x)
            notifications.error('Error(s) Saving Configuration',
                                '<br>\n'.join(results))
        else:
            notifications.message('Configuration Saved', os.path.join(sickrage.srConfig.CONFIG_FILE))

        return self.redirect("/config/anime/")


@Route('/errorlogs(/?.*)')
class ErrorLogs(WebRoot):
    def __init__(self, *args, **kwargs):
        super(ErrorLogs, self).__init__(*args, **kwargs)

    def ErrorLogsMenu(self, level):
        menu = [
            {'title': 'Clear Errors', 'path': 'errorlogs/clearerrors/',
             'requires': self.haveErrors() and level == sickrage.srLogger.ERROR, 'icon': 'ui-icon ui-icon-trash'},
            {'title': 'Clear Warnings', 'path': 'errorlogs/clearerrors/?level=' + str(sickrage.srLogger.WARNING),
             'requires': self.haveWarnings() and level == sickrage.srLogger.WARNING,
             'icon': 'ui-icon ui-icon-trash'},
        ]

        return menu

    def index(self, level=None):
        level = int(level or sickrage.srLogger.ERROR)
        return self.render("errorlogs.mako",
                           header="Logs &amp; Errors",
                           title="Logs &amp; Errors",
                           topmenu="system",
                           submenu=self.ErrorLogsMenu(level),
                           logLevel=level)

    @staticmethod
    def haveErrors():
        if len(ErrorViewer.errors) > 0:
            return True

    @staticmethod
    def haveWarnings():
        if len(WarningViewer.errors) > 0:
            return True

    def clearerrors(self, level=None):
        if int(level or sickrage.srLogger.ERROR) == sickrage.srLogger.WARNING:
            WarningViewer.clear()
        else:
            ErrorViewer.clear()

        return self.redirect("/errorlogs/viewlog/")

    def viewlog(self, minLevel=None, logFilter='', logSearch='', maxLines=500):
        minLevel = minLevel or sickrage.srLogger.INFO

        logFiles = [sickrage.srConfig.LOG_FILE] + ["{}.{}".format(sickrage.srConfig.LOG_FILE, x) for x in
                                                        xrange(int(
                                                            sickrage.srConfig.LOG_NR))]

        levelsFiltered = b'|'.join(
            [x for x in sickrage.srLogger.logLevels.keys() if
             sickrage.srLogger.logLevels[x] >= int(minLevel)])

        logRegex = re.compile(
            r"(^\d+\-\d+\-\d+\s*\d+\:\d+\:\d+\s*(?:{}.+?)\:\:(?:{}.+?)\:\:.+?$)".format(levelsFiltered, logFilter)
            , re.S + re.M + re.I
        )

        data = ""

        try:
            for logFile in [x for x in logFiles if os.path.isfile(x)]:
                data += "\n".join(logRegex.findall(
                    "\n".join(re.findall(
                        "((?:^.+?{}.+?$))".format(logSearch),
                        "\n".join(next(readFileBuffered(
                            logFile, reverse=True)).splitlines(True)[::-1]),
                        re.S + re.M + re.I)))[:maxLines])

                maxLines -= len(data)
                if len(data) == maxLines:
                    raise StopIteration

        except StopIteration:
            pass
        except Exception as e:
            pass

        return self.render("viewlogs.mako",
                           header="Log File",
                           title="Logs",
                           topmenu="system",
                           logLines=data,
                           minLevel=int(minLevel),
                           logNameFilters=sickrage.srLogger.logNameFilters,
                           logFilter=logFilter,
                           logSearch=logSearch)

    def submit_errors(self):
        # submitter_result, issue_id = logging.submit_errors()
        # LOGGER.warning(submitter_result, [issue_id is None])
        # submitter_notification = notifications.error if issue_id is None else notifications.message
        # submitter_notification(submitter_result)

        return self.redirect("/errorlogs/")
