# Author: echel0n <echel0n@sickrage.ca>
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

import datetime
import os
import re
import threading
import time
import traceback
import urllib

import markdown2
from UnRAR2 import RarFile
from dateutil import tz
from mako.exceptions import html_error_template, RichTraceback
from mako.lookup import TemplateLookup
from tornado.concurrent import run_on_executor
from tornado.escape import json_encode, recursive_unicode, json_decode
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, authenticated

try:
    from futures import ThreadPoolExecutor
except ImportError:
    from concurrent.futures import ThreadPoolExecutor

import sickrage
from sickrage.clients import getClientIstance
from sickrage.clients.sabnzbd import SabNZBd
from sickrage.core.blackandwhitelist import BlackAndWhiteList, \
    short_group_names
from sickrage.core.classes import ErrorViewer, AllShowsListUI, AttrDict
from sickrage.core.classes import WarningViewer
from sickrage.core.common import FAILED, IGNORED, Overview, Quality, SKIPPED, \
    SNATCHED, UNAIRED, WANTED, cpu_presets, statusStrings
from sickrage.core.databases import failed_db, main_db
from sickrage.core.exceptions import CantRefreshShowException, \
    CantUpdateShowException, EpisodeDeletedException, \
    MultipleShowObjectsException, NoNFOException, \
    ShowDirectoryNotFoundException
from sickrage.core.helpers import argToBool, backupSR, check_url, \
    chmodAsParent, findCertainShow, generateApiKey, getDiskSpaceUsage, get_lan_ip, makeDir, readFileBuffered, \
    remove_article, restoreConfigZip, \
    sanitizeFileName, tryInt
from sickrage.core.helpers.browser import foldersAtPath
from sickrage.core.helpers.compat import cmp
from sickrage.core.imdb_popular import imdbPopular
from sickrage.core.nameparser import validator
from sickrage.core.process_tv import processDir
from sickrage.core.queues.search import BacklogQueueItem, FailedQueueItem, \
    MANUAL_SEARCH_HISTORY, ManualSearchQueueItem
from sickrage.core.scene_exceptions import get_all_scene_exceptions, \
    get_scene_exceptions, update_scene_exceptions
from sickrage.core.scene_numbering import get_scene_absolute_numbering, \
    get_scene_absolute_numbering_for_show, get_scene_numbering, \
    get_scene_numbering_for_show, get_xem_absolute_numbering_for_show, \
    get_xem_numbering_for_show, set_scene_numbering, xem_refresh
from sickrage.core.searchers import subtitle_searcher
from sickrage.core.trakt import TraktAPI, traktException
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show import TVShow
from sickrage.core.tv.show.coming_episodes import ComingEpisodes
from sickrage.core.tv.show.history import History as HistoryTool
from sickrage.core.updaters import tz_updater
from sickrage.core.webserver.routes import Route
from sickrage.indexers import srIndexerApi
from sickrage.indexers.adba import aniDBAbstracter
from sickrage.providers import NewznabProvider, TorrentRssProvider


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)

        # template settings
        self.mako_lookup = TemplateLookup(
            directories=[os.path.join(sickrage.srCore.srConfig.GUI_DIR, 'views{}'.format(os.sep))],
            module_directory=os.path.join(sickrage.srCore.srConfig.CACHE_DIR, 'mako{}'.format(os.sep)),
            format_exceptions=False,
            strict_undefined=True,
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace',
            future_imports=['unicode_literals']
        )

        # start time
        self.startTime = time.time()

    def initialize(self):
        self.io_loop = IOLoop.current()
        self.executor = ThreadPoolExecutor(max_workers=10)

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if sickrage.srCore.srConfig.WEB_ROOT and self.request.uri.startswith(sickrage.srCore.srConfig.WEB_ROOT):
                url = url[len(sickrage.srCore.srConfig.WEB_ROOT) + 1:]

            if url[:3] != 'api':
                return self.finish(self.render(
                    '/errors/404.mako',
                    title='HTTP Error 404',
                    header='HTTP Error 404')
                )
            else:
                self.write('Wrong API key used')

        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br>" % line for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br>" % (k, self.request.__dict__[k]) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.write("""<html>
                                 <title>{}</title>
                                 <body>
                                    <h2>Error</h2>
                                    <p>{}</p>
                                    <h2>Traceback</h2>
                                    <p>{}</p>
                                    <h2>Request Info</h2>
                                    <p>{}</p>
                                    <button onclick="window.location='{}/logs/';">View Log(Errors)</button>
                                 </body>
                               </html>""".format(error, error, trace_info, request_info,
                                                 sickrage.srCore.srConfig.WEB_ROOT))

    def redirect(self, url, *args, **kwargs):
        if not url.startswith(sickrage.srCore.srConfig.WEB_ROOT):
            url = sickrage.srCore.srConfig.WEB_ROOT + url
        super(BaseHandler, self).redirect(url, *args, **kwargs)

    def get_current_user(self):
        return self.get_secure_cookie('user')

    def render_string(self, template_name, **kwargs):
        template_kwargs = {
            'title': "",
            'header': "",
            'topmenu': "",
            'submenu': "",
            'controller': "home",
            'action': "index",
            'srPID': sickrage.srCore.PID,
            'srHttpsEnabled': sickrage.srCore.srConfig.ENABLE_HTTPS or bool(
                self.request.headers.get('X-Forwarded-Proto') == 'https'),
            'srHost': self.request.headers.get('X-Forwarded-Host', self.request.host.split(':')[0]),
            'srHttpPort': self.request.headers.get('X-Forwarded-Port', sickrage.srCore.srConfig.WEB_PORT),
            'srHttpsPort': sickrage.srCore.srConfig.WEB_PORT,
            'srHandleReverseProxy': sickrage.srCore.srConfig.HANDLE_REVERSE_PROXY,
            'srThemeName': sickrage.srCore.srConfig.THEME_NAME,
            'srDefaultPage': sickrage.srCore.srConfig.DEFAULT_PAGE,
            'numErrors': len(ErrorViewer.errors),
            'numWarnings': len(WarningViewer.errors),
            'srStartTime': self.startTime,
            'makoStartTime': time.time(),
            'application': self.application,
            'request': self.request
        }

        template_kwargs.update(self.get_template_namespace())
        template_kwargs.update(kwargs)

        try:
            return self.mako_lookup.get_template(template_name).render_unicode(**template_kwargs)
        except Exception:
            kwargs['title'] = 'HTTP Error 500'
            kwargs['header'] = 'HTTP Error 500'
            kwargs['backtrace'] = RichTraceback()
            template_kwargs.update(kwargs)
            return self.mako_lookup.get_template('/errors/500.mako').render_unicode(**template_kwargs)

    def render(self, template_name, **kwargs):
        return self.render_string(template_name, **kwargs)

    @run_on_executor
    def callback(self, function, **kwargs):
        threading.currentThread().setName('WEB')
        return recursive_unicode(function(
            **dict([(k, (v, ''.join(v))[isinstance(v, list) and len(v) == 1]) for k, v in
                    recursive_unicode(kwargs.items())])
        ))


class WebHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(WebHandler, self).__init__(*args, **kwargs)

    @coroutine
    @authenticated
    def prepare(self, *args, **kwargs):
        # route -> method obj
        method = getattr(self, self.request.path.strip('/').split('/')[::-1][0].replace('.', '_'),
                         getattr(self, 'index'))

        result = yield self.callback(method, **self.request.arguments)
        self.finish(result)


class LoginHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(LoginHandler, self).__init__(*args, **kwargs)

    @coroutine
    def prepare(self, *args, **kwargs):
        result = yield self.callback(self.checkAuth)
        self.finish(result)

    def checkAuth(self):
        try:
            username = self.get_argument('username', '')
            password = self.get_argument('password', '')

            if cmp([username, password],
                   [sickrage.srCore.srConfig.WEB_USERNAME, sickrage.srCore.srConfig.WEB_PASSWORD]) == 0:
                remember_me = int(self.get_argument('remember_me', default=0))
                self.set_secure_cookie('user', json_encode(sickrage.srCore.srConfig.API_KEY),
                                       expires_days=30 if remember_me > 0 else None)
                sickrage.srCore.srLogger.debug('User logged into the SiCKRAGE web interface')
                return self.redirect(self.get_argument("next", "/"))
            elif username and password:
                sickrage.srCore.srLogger.warning(
                    'User attempted a failed login to the SiCKRAGE web interface from IP: {}'.format(
                        self.request.remote_ip)
                )

            return self.render(
                "/login.mako",
                title="Login",
                header="Login",
                topmenu="login",
                controller='root',
                action='login'
            )
        except Exception:
            sickrage.srCore.srLogger.debug(
                'Failed doing webui login callback [{}]: {}'.format(self.request.uri, traceback.format_exc()))
            return html_error_template().render_unicode()


class LogoutHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(LogoutHandler, self).__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        self.clear_cookie("user")
        return self.redirect(self.get_argument("next", "/"))


class CalendarHandler(BaseHandler):
    def prepare(self, *args, **kwargs):
        if sickrage.srCore.srConfig.CALENDAR_UNPROTECTED:
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

        sickrage.srCore.srLogger.info("Receiving iCal request from %s" % self.request.remote_ip)

        # Create a iCal string
        ical = 'BEGIN:VCALENDAR\r\n'
        ical += 'VERSION:2.0\r\n'
        ical += 'X-WR-CALNAME:SiCKRAGE\r\n'
        ical += 'X-WR-CALDESC:SiCKRAGE\r\n'
        ical += 'PRODID://Sick-Beard Upcoming Episodes//\r\n'

        # Limit dates
        past_date = (datetime.date.today() + datetime.timedelta(weeks=-52)).toordinal()
        future_date = (datetime.date.today() + datetime.timedelta(weeks=52)).toordinal()

        # Get all the shows that are not paused and are currently on air (from kjoconnor Fork)
        calendar_shows = main_db.MainDB().select(
            "SELECT show_name, indexer_id, network, airs, runtime FROM tv_shows WHERE ( status = 'Continuing' OR status = 'Returning Series' ) AND paused != '1'")
        for show in calendar_shows:
            # Get all episodes of this show airing between today and next month
            episode_list = main_db.MainDB().select(
                "SELECT indexerid, name, season, episode, description, airdate FROM tv_episodes WHERE airdate >= ? AND airdate < ? AND showid = ?",
                (past_date, future_date, int(show["indexer_id"])))

            utc = tz.gettz('GMT')

            for episode in episode_list:

                air_date_time = tz_updater.parse_date_time(episode['airdate'], show["airs"],
                                                           show['network']).astimezone(utc)
                air_date_time_end = air_date_time + datetime.timedelta(
                    minutes=tryInt(show["runtime"], 60))

                # Create event for episode
                ical += 'BEGIN:VEVENT\r\n'
                ical += 'DTSTART:' + air_date_time.strftime("%Y%m%d") + 'T' + air_date_time.strftime(
                    "%H%M%S") + 'Z\r\n'
                ical += 'DTEND:' + air_date_time_end.strftime(
                    "%Y%m%d") + 'T' + air_date_time_end.strftime(
                    "%H%M%S") + 'Z\r\n'
                if sickrage.srCore.srConfig.CALENDAR_ICONS:
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-ICON:http://www.sickrage.ca/favicon.ico\r\n'
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-DISPLAY:CHIP\r\n'
                ical += 'SUMMARY: {0} - {1}x{2} - {3}\r\n'.format(
                    show['show_name'], episode['season'], episode['episode'], episode['name']
                )
                ical += 'UID:SiCKRAGE-' + str(datetime.date.today().isoformat()) + '-' + \
                        show['show_name'].replace(" ", "-") + '-E' + str(episode['episode']) + \
                        'S' + str(episode['season']) + '\r\n'
                if episode['description']:
                    ical += 'DESCRIPTION: {0} on {1} \\n\\n {2}\r\n'.format(
                        (show['airs'] or '(Unknown airs)'),
                        (show['network'] or 'Unknown network'),
                        episode['description'].splitlines()[0])
                else:
                    ical += 'DESCRIPTION:' + (show['airs'] or '(Unknown airs)') + ' on ' + (
                        show['network'] or 'Unknown network') + '\r\n'

                ical += 'END:VEVENT\r\n'

        # Ending the iCal
        ical += 'END:VCALENDAR'

        return ical


@Route('(.*)(/?)')
class WebRoot(WebHandler):
    def __init__(self, *args, **kwargs):
        super(WebRoot, self).__init__(*args, **kwargs)

    def index(self):
        return self.redirect('/' + sickrage.srCore.srConfig.DEFAULT_PAGE + '/')

    def robots_txt(self):
        """ Keep web crawlers out """
        self.set_header('Content-Type', 'text/plain')
        return "User-agent: *\nDisallow: /"

    def apibuilder(self):
        def titler(x):
            return (remove_article(x), x)[not x or sickrage.srCore.srConfig.SORT_ARTICLE]

        myDB = main_db.MainDB(row_type='dict')
        shows = sorted(sickrage.srCore.SHOWLIST, lambda x, y: cmp(titler(x.name), titler(y.name)))
        episodes = {}

        results = myDB.select(
            'SELECT episode, season, showid '
            'FROM tv_episodes '
            'ORDER BY season ASC, episode ASC'
        )

        for result in results:
            if result['showid'] not in episodes:
                episodes[result['showid']] = {}

            if result['season'] not in episodes[result['showid']]:
                episodes[result['showid']][result['season']] = []

            episodes[result['showid']][result['season']].append(result['episode'])

        if len(sickrage.srCore.srConfig.API_KEY) == 32:
            apikey = sickrage.srCore.srConfig.API_KEY
        else:
            apikey = 'API Key not generated'

        return self.render(
            'api_builder.mako',
            title='API Builder',
            header='API Builder',
            shows=shows,
            episodes=episodes,
            apikey=apikey,
            controller='root',
            action='api_builder'
        )

    def setHomeLayout(self, layout):
        if layout not in ('poster', 'small', 'banner', 'simple', 'coverflow'):
            layout = 'poster'

        sickrage.srCore.srConfig.HOME_LAYOUT = layout

        # Don't redirect to default page so user can see new layout
        return self.redirect("/home/")

    @staticmethod
    def setPosterSortBy(sort):

        if sort not in ('name', 'date', 'network', 'progress'):
            sort = 'name'

        sickrage.srCore.srConfig.POSTER_SORTBY = sort
        sickrage.srCore.srConfig.save()

    @staticmethod
    def setPosterSortDir(direction):

        sickrage.srCore.srConfig.POSTER_SORTDIR = int(direction)
        sickrage.srCore.srConfig.save()

    def setHistoryLayout(self, layout):

        if layout not in ('compact', 'detailed'):
            layout = 'detailed'

        sickrage.srCore.srConfig.HISTORY_LAYOUT = layout

        return self.redirect("/history/")

    def toggleDisplayShowSpecials(self, show):

        sickrage.srCore.srConfig.DISPLAY_SHOW_SPECIALS = not sickrage.srCore.srConfig.DISPLAY_SHOW_SPECIALS

        return self.redirect("/home/displayShow?show=" + show)

    def setScheduleLayout(self, layout):
        if layout not in ('poster', 'banner', 'list', 'calendar'):
            layout = 'banner'

        if layout == 'calendar':
            sickrage.srCore.srConfig.COMING_EPS_SORT = 'date'

        sickrage.srCore.srConfig.COMING_EPS_LAYOUT = layout

        return self.redirect("/schedule/")

    def toggleScheduleDisplayPaused(self):

        sickrage.srCore.srConfig.COMING_EPS_DISPLAY_PAUSED = not sickrage.srCore.srConfig.COMING_EPS_DISPLAY_PAUSED

        return self.redirect("/schedule/")

    def setScheduleSort(self, sort):
        if sort not in ('date', 'network', 'show'):
            sort = 'date'

        if sickrage.srCore.srConfig.COMING_EPS_LAYOUT == 'calendar':
            sort \
                = 'date'

        sickrage.srCore.srConfig.COMING_EPS_SORT = sort

        return self.redirect("/schedule/")

    def schedule(self, layout=None):
        next_week = datetime.date.today() + datetime.timedelta(days=7)
        next_week1 = datetime.datetime.combine(next_week,
                                               datetime.datetime.now().time().replace(tzinfo=tz_updater.sr_timezone))
        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories,
                                                     sickrage.srCore.srConfig.COMING_EPS_SORT,
                                                     False)
        today = datetime.datetime.now().replace(tzinfo=tz_updater.sr_timezone)

        submenu = [
            {
                'title': 'Sort by:',
                'path': {
                    'Date': '/setScheduleSort/?sort=date',
                    'Show': '/setScheduleSort/?sort=show',
                    'Network': '/setScheduleSort/?sort=network',
                }
            },
            {
                'title': 'Layout:',
                'path': {
                    'Banner': '/setScheduleLayout/?layout=banner',
                    'Poster': '/setScheduleLayout/?layout=poster',
                    'List': '/setScheduleLayout/?layout=list',
                    'Calendar': '/setScheduleLayout/?layout=calendar',
                }
            },
            {
                'title': 'View Paused:',
                'path': {
                    'Hide': '/toggleScheduleDisplayPaused'
                } if sickrage.srCore.srConfig.COMING_EPS_DISPLAY_PAUSED else {
                    'Show': '/toggleScheduleDisplayPaused'
                }
            },
        ]

        # Allow local overriding of layout parameter
        if layout and layout in ('poster', 'banner', 'list', 'calendar'):
            layout = layout
        else:
            layout = sickrage.srCore.srConfig.COMING_EPS_LAYOUT

        return self.render(
            'schedule.mako',
            submenu=submenu,
            next_week=next_week1,
            today=today,
            results=results,
            layout=layout,
            title='Schedule',
            header='Schedule',
            topmenu='schedule',
            controller='root',
            action='schedule'
        )


@Route('/google(/?.*)')
class GoogleAuth(WebRoot):
    def __init__(self, *args, **kwargs):
        super(GoogleAuth, self).__init__(*args, **kwargs)

    def get_user_code(self):
        data = sickrage.srCore.googleAuth.get_user_code()
        return json_encode({field: str(getattr(data, field)) for field in data._fields})

    def get_credentials(self, flow_info):
        try:
            data = sickrage.srCore.googleAuth.get_credentials(AttrDict(json_decode(flow_info)))
            return json_encode(data.token_response)
        except Exception as e:
            return json_encode({'error': e.message})

    def refresh_credentials(self):
        sickrage.srCore.googleAuth.refresh_credentials()

    def logout(self):
        sickrage.srCore.googleAuth.logout()


@Route('/ui(/?.*)')
class UI(WebRoot):
    def __init__(self, *args, **kwargs):
        super(UI, self).__init__(*args, **kwargs)
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")

    @staticmethod
    def add_message():
        sickrage.srCore.srNotifications.message('Test 1', 'This is test number 1')
        sickrage.srCore.srNotifications.error('Test 2', 'This is test number 2')
        return "ok"

    def get_messages(self):
        messages = {}
        cur_notification_num = 0
        for cur_notification in sickrage.srCore.srNotifications.get_notifications(self.request.remote_ip):
            cur_notification_num += 1
            messages['notification-{}'.format(cur_notification_num)] = {
                'title': cur_notification.title,
                'message': cur_notification.message or "",
                'type': cur_notification.type
            }

        if messages:
            return json_encode(messages)


@Route('/browser(/?.*)')
class WebFileBrowser(WebRoot):
    def __init__(self, *args, **kwargs):
        super(WebFileBrowser, self).__init__(*args, **kwargs)

    def index(self, path='', includeFiles=False, *args, **kwargs):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")
        return json_encode(foldersAtPath(path, True, bool(int(includeFiles))))

    def complete(self, term, includeFiles=0):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")
        paths = [entry['path'] for entry in
                 foldersAtPath(os.path.dirname(term), includeFiles=bool(int(includeFiles))) if 'path' in entry]

        return json_encode(paths)


@Route('/home(/?.*)')
class Home(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Home, self).__init__(*args, **kwargs)

    def _genericMessage(self, subject, message):
        return self.render(
            "/generic_message.mako",
            message=message,
            subject=subject,
            topmenu="home",
            title="",
            controller='home',
            action='genericmessage'
        )

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
        if not len(sickrage.srCore.SHOWLIST):
            return self.redirect('/home/addShows/')

        if sickrage.srCore.srConfig.ANIME_SPLIT_HOME:
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
        return self.render(
            "/home/index.mako",
            title="Home",
            header="Show List",
            topmenu="home",
            showlists=showlists,
            show_stat=stats[0],
            max_download_count=stats[1],
            controller='home',
            action='index'
        )

    @staticmethod
    def show_statistics():
        today = str(datetime.date.today().toordinal())

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
            show_stat[cur_result['showid']] = cur_result
            if cur_result['ep_total'] > max_download_count:
                max_download_count = cur_result['ep_total']

        max_download_count *= 100

        return show_stat, max_download_count

    def is_alive(self, *args, **kwargs):
        if not all([kwargs.get('srcallback'), kwargs.get('_')]):
            return "Error: Unsupported Request. Send jsonp request with 'srcallback' variable in the query string."

        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header('Content-Type', 'text/javascript')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with')

        return "%s({'msg':%s})" % (kwargs['srcallback'], str(sickrage.srCore.PID))

    @staticmethod
    def haveKODI():
        return sickrage.srCore.srConfig.USE_KODI and sickrage.srCore.srConfig.KODI_UPDATE_LIBRARY

    @staticmethod
    def havePLEX():
        return sickrage.srCore.srConfig.USE_PLEX and sickrage.srCore.srConfig.PLEX_UPDATE_LIBRARY

    @staticmethod
    def haveEMBY():
        return sickrage.srCore.srConfig.USE_EMBY

    @staticmethod
    def haveTORRENT():
        if sickrage.srCore.srConfig.USE_TORRENTS and sickrage.srCore.srConfig.TORRENT_METHOD != 'blackhole' and \
                (sickrage.srCore.srConfig.ENABLE_HTTPS and sickrage.srCore.srConfig.TORRENT_HOST[:5] == 'https' or not
                sickrage.srCore.srConfig.ENABLE_HTTPS and sickrage.srCore.srConfig.TORRENT_HOST[:5] == 'http:'):
            return True
        else:
            return False

    @staticmethod
    def testSABnzbd(host=None, username=None, password=None, apikey=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = sickrage.srCore.srConfig.clean_url(host)

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

        host = sickrage.srCore.srConfig.clean_url(host)

        client = getClientIstance(torrent_method)

        _, accesMsg = client(host, username, password).testAuthentication()

        return accesMsg

    @staticmethod
    def testFreeMobile(freemobile_id=None, freemobile_apikey=None):

        result, message = sickrage.srCore.notifiersDict.freemobile_notifier.test_notify(freemobile_id,
                                                                                        freemobile_apikey)
        if result:
            return "SMS sent successfully"
        else:
            return "Problem sending SMS: " + message

    @staticmethod
    def testGrowl(host=None, password=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = sickrage.srCore.srConfig.clean_host(host, default_port=23053)

        result = sickrage.srCore.notifiersDict.growl_notifier.test_notify(host, password)
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

        result = sickrage.srCore.notifiersDict.prowl_notifier.test_notify(prowl_api, prowl_priority)
        if result:
            return "Test prowl notice sent successfully"
        else:
            return "Test prowl notice failed"

    @staticmethod
    def testBoxcar(username=None):

        result = sickrage.srCore.notifiersDict.boxcar_notifier.test_notify(username)
        if result:
            return "Boxcar notification succeeded. Check your Boxcar clients to make sure it worked"
        else:
            return "Error sending Boxcar notification"

    @staticmethod
    def testBoxcar2(accesstoken=None):

        result = sickrage.srCore.notifiersDict.boxcar2_notifier.test_notify(accesstoken)
        if result:
            return "Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked"
        else:
            return "Error sending Boxcar2 notification"

    @staticmethod
    def testPushover(userKey=None, apiKey=None):

        result = sickrage.srCore.notifiersDict.pushover_notifier.test_notify(userKey, apiKey)
        if result:
            return "Pushover notification succeeded. Check your Pushover clients to make sure it worked"
        else:
            return "Error sending Pushover notification"

    @staticmethod
    def twitterStep1():
        return sickrage.srCore.notifiersDict.twitter_notifier._get_authorization()

    @staticmethod
    def twitterStep2(key):

        result = sickrage.srCore.notifiersDict.twitter_notifier._get_credentials(key)
        sickrage.srCore.srLogger.info("result: " + str(result))
        if result:
            return "Key verification successful"
        else:
            return "Unable to verify key"

    @staticmethod
    def testTwitter():

        result = sickrage.srCore.notifiersDict.twitter_notifier.test_notify()
        if result:
            return "Tweet successful, check your twitter to make sure it worked"
        else:
            return "Error sending tweet"

    @staticmethod
    def testKODI(host=None, username=None, password=None):

        host = sickrage.srCore.srConfig.clean_hosts(host)
        finalResult = ''
        for curHost in [x.strip() for x in host.split(",")]:
            curResult = sickrage.srCore.notifiersDict.kodi_notifier.test_notify(urllib.unquote_plus(curHost), username,
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
            password = sickrage.srCore.srConfig.PLEX_CLIENT_PASSWORD

        finalResult = ''
        for curHost in [x.strip() for x in host.split(',')]:
            curResult = sickrage.srCore.notifiersDict.plex_notifier.test_notify_pmc(urllib.unquote_plus(curHost),
                                                                                    username,
                                                                                    password)
            if len(curResult.split(':')) > 2 and 'OK' in curResult.split(':')[2]:
                finalResult += 'Successful test notice sent to Plex client ... ' + urllib.unquote_plus(curHost)
            else:
                finalResult += 'Test failed for Plex client ... ' + urllib.unquote_plus(curHost)
            finalResult += '<br>' + '\n'

        sickrage.srCore.srNotifications.message('Tested Plex client(s): ', urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    def testPMS(self, host=None, username=None, password=None, plex_server_token=None):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if password is not None and set('*') == set(password):
            password = sickrage.srCore.srConfig.PLEX_PASSWORD

        finalResult = ''

        curResult = sickrage.srCore.notifiersDict.plex_notifier.test_notify_pms(urllib.unquote_plus(host), username,
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

        sickrage.srCore.srNotifications.message('Tested Plex Media Server host(s): ',
                                                urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    @staticmethod
    def testLibnotify():

        if sickrage.srCore.notifiersDict.libnotify_notifier.test_notify():
            return "Tried sending desktop notification via libnotify"
        else:
            return sickrage.srCore.notifiersDict.libnotify.diagnose()

    @staticmethod
    def testEMBY(host=None, emby_apikey=None):

        host = sickrage.srCore.srConfig.clean_host(host)
        result = sickrage.srCore.notifiersDict.emby_notifier.test_notify(urllib.unquote_plus(host), emby_apikey)
        if result:
            return "Test notice sent successfully to " + urllib.unquote_plus(host)
        else:
            return "Test notice failed to " + urllib.unquote_plus(host)

    @staticmethod
    def testNMJ(host=None, database=None, mount=None):

        host = sickrage.srCore.srConfig.clean_host(host)
        result = sickrage.srCore.notifiersDict.nmj_notifier.test_notify(urllib.unquote_plus(host), database, mount)
        if result:
            return "Successfully started the scan update"
        else:
            return "Test failed to start the scan update"

    @staticmethod
    def settingsNMJ(host=None):

        host = sickrage.srCore.srConfig.clean_host(host)
        result = sickrage.srCore.notifiersDict.nmj_notifier.notify_settings(urllib.unquote_plus(host))
        if result:
            return '{"message": "Got settings from %(host)s", "database": "%(database)s", "mount": "%(mount)s"}' % {
                "host": host, "database": sickrage.srCore.srConfig.NMJ_DATABASE,
                "mount": sickrage.srCore.srConfig.NMJ_MOUNT}
        else:
            return '{"message": "Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for detailed info)", "database": "", "mount": ""}'

    @staticmethod
    def testNMJv2(host=None):

        host = sickrage.srCore.srConfig.clean_host(host)
        result = sickrage.srCore.notifiersDict.nmjv2_notifier.test_notify(urllib.unquote_plus(host))
        if result:
            return "Test notice sent successfully to " + urllib.unquote_plus(host)
        else:
            return "Test notice failed to " + urllib.unquote_plus(host)

    @staticmethod
    def settingsNMJv2(host=None, dbloc=None, instance=None):

        host = sickrage.srCore.srConfig.clean_host(host)
        result = sickrage.srCore.notifiersDict.nmjv2_notifier.notify_settings(urllib.unquote_plus(host), dbloc,
                                                                              instance)
        if result:
            return '{"message": "NMJ Database found at: %(host)s", "database": "%(database)s"}' % {"host": host,
                                                                                                   "database": sickrage.srCore.srConfig.NMJv2_DATABASE}
        else:
            return '{"message": "Unable to find NMJ Database at location: %(dbloc)s. Is the right location selected and PCH running?", "database": ""}' % {
                "dbloc": dbloc}

    @staticmethod
    def getTraktToken(trakt_pin=None):

        trakt_api = TraktAPI(sickrage.srCore.srConfig.SSL_VERIFY, sickrage.srCore.srConfig.TRAKT_TIMEOUT)
        response = trakt_api.traktToken(trakt_pin)
        if response:
            return "Trakt Authorized"
        return "Trakt Not Authorized!"

    @staticmethod
    def testTrakt(username=None, blacklist_name=None):
        return sickrage.srCore.notifiersDict.trakt_notifier.test_notify(username, blacklist_name)

    @staticmethod
    def loadShowNotifyLists():

        rows = main_db.MainDB().select("SELECT show_id, show_name, notify_list FROM tv_shows ORDER BY show_name ASC")

        data = {}
        size = 0
        for r in rows:
            data[r['show_id']] = {'id': r['show_id'], 'name': r['show_name'], 'list': r['notify_list']}
            size += 1
        data['_size'] = size
        return json_encode(data)

    @staticmethod
    def saveShowNotifyList(show=None, emails=None):

        if main_db.MainDB().action("UPDATE tv_shows SET notify_list = ? WHERE show_id = ?", [emails, show]):
            return 'OK'
        else:
            return 'ERROR'

    @staticmethod
    def testEmail(host=None, port=None, smtp_from=None, use_tls=None, user=None, pwd=None, to=None):

        host = sickrage.srCore.srConfig.clean_host(host)
        if sickrage.srCore.notifiersDict.email_notifier.test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return 'Test email sent successfully! Check inbox.'
        else:
            return 'ERROR: %s' % sickrage.srCore.notifiersDict.email_notifier.last_err

    @staticmethod
    def testNMA(nma_api=None, nma_priority=0):

        result = sickrage.srCore.notifiersDict.nma_notifier.test_notify(nma_api, nma_priority)
        if result:
            return "Test NMA notice sent successfully"
        else:
            return "Test NMA notice failed"

    @staticmethod
    def testPushalot(authorizationToken=None):

        result = sickrage.srCore.notifiersDict.pushalot_notifier.test_notify(authorizationToken)
        if result:
            return "Pushalot notification succeeded. Check your Pushalot clients to make sure it worked"
        else:
            return "Error sending Pushalot notification"

    @staticmethod
    def testPushbullet(api=None):

        result = sickrage.srCore.notifiersDict.pushbullet_notifier.test_notify(api)
        if result:
            return "Pushbullet notification succeeded. Check your device to make sure it worked"
        else:
            return "Error sending Pushbullet notification"

    @staticmethod
    def getPushbulletDevices(api=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = sickrage.srCore.notifiersDict.pushbullet_notifier.get_devices(api)
        if result:
            return result
        else:
            return "Error sending Pushbullet notification"

    def status(self):
        tvdirFree = getDiskSpaceUsage(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR)
        rootDir = {}
        if sickrage.srCore.srConfig.ROOT_DIRS:
            backend_pieces = sickrage.srCore.srConfig.ROOT_DIRS.split('|')
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if len(backend_dirs):
            for subject in backend_dirs:
                rootDir[subject] = getDiskSpaceUsage(subject)

        return self.render(
            "/home/status.mako",
            title='Status',
            header='Status',
            topmenu='system',
            tvdirFree=tvdirFree,
            rootDir=rootDir,
            controller='home',
            action='status'
        )

    def shutdown(self, pid=None):
        if str(pid) != str(sickrage.srCore.PID):
            return self.redirect('/home/')

        self._genericMessage("Shutting down", "SiCKRAGE is shutting down")
        sickrage.srCore.shutdown()

    def restart(self, pid=None):
        if str(pid) != str(sickrage.srCore.PID):
            return self.redirect('/home/')

        self._genericMessage("Restarting", "SiCKRAGE is restarting")

        self.io_loop.add_timeout(
            datetime.timedelta(seconds=10),
            lambda: sickrage.srCore.shutdown(restart=True))

        return self.render(
            "/home/restart.mako",
            title="Home",
            header="Restarting SiCKRAGE",
            topmenu="system",
            controller='home',
            action="restart"
        )

    def updateCheck(self, pid=None):
        if str(pid) != str(sickrage.srCore.PID):
            return self.redirect('/home/')

        # check for news updates
        sickrage.srCore.VERSIONUPDATER.check_for_new_news()

        # check for new app updates
        sickrage.srCore.srNotifications.message('Checking for new updates ...')
        if sickrage.srCore.VERSIONUPDATER.check_for_new_version(True):
            sickrage.srCore.srNotifications.message('New update found for SiCKRAGE, starting auto-updater')
            return self.update(pid)
        else:
            sickrage.srCore.srNotifications.message('No updates found for SiCKRAGE!')
            return self.redirect('/' + sickrage.srCore.srConfig.DEFAULT_PAGE + '/')

    def update(self, pid=None):
        if str(pid) != str(sickrage.srCore.PID):
            return self.redirect('/home/')

        if sickrage.srCore.VERSIONUPDATER._runbackup() is True:
            if sickrage.srCore.VERSIONUPDATER.update():
                return self.restart(pid)
            else:
                return self._genericMessage("Update Failed",
                                            "Update wasn't successful, not restarting. Check your log for more information.")
        else:
            return self.redirect('/' + sickrage.srCore.srConfig.DEFAULT_PAGE + '/')

    def branchCheckout(self, branch):
        if branch and sickrage.srCore.VERSIONUPDATER.updater.current_branch != branch:
            sickrage.srCore.srNotifications.message('Checking out branch: ', branch)
            if sickrage.srCore.VERSIONUPDATER.updater.checkout_branch(branch):
                sickrage.srCore.srNotifications.message('Branch checkout successful, restarting: ', branch)
                return self.restart(sickrage.srCore.PID)
        else:
            sickrage.srCore.srNotifications.message('Already on branch: ', branch)

        return self.redirect('/' + sickrage.srCore.srConfig.DEFAULT_PAGE + '/')

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

        episodeResults = main_db.MainDB().select(
            "SELECT * FROM tv_episodes WHERE showid = ? ORDER BY season DESC, episode DESC",
            [showObj.indexerid]
        )

        submenu = [
            {'title': 'Edit', 'path': '/home/editShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-pencil'}]

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
                    submenu.append({'title': 'Resume', 'path': '/home/togglePause?show=%d' % showObj.indexerid,
                                    'icon': 'ui-icon ui-icon-play'})
                else:
                    submenu.append({'title': 'Pause', 'path': '/home/togglePause?show=%d' % showObj.indexerid,
                                    'icon': 'ui-icon ui-icon-pause'})

                submenu.append({'title': 'Remove', 'path': '/home/deleteShow?show=%d' % showObj.indexerid,
                                'class': 'removeshow', 'confirm': True, 'icon': 'ui-icon ui-icon-trash'})
                submenu.append({'title': 'Re-scan files', 'path': '/home/refreshShow?show=%d' % showObj.indexerid,
                                'icon': 'ui-icon ui-icon-refresh'})
                submenu.append({'title': 'Force Full Update',
                                'path': '/home/updateShow?show=%d&amp;force=1' % showObj.indexerid,
                                'icon': 'ui-icon ui-icon-transfer-e-w'})
                submenu.append({'title': 'Update show in KODI', 'path': '/home/updateKODI?show=%d' % showObj.indexerid,
                                'requires': self.haveKODI(), 'icon': 'submenu-icon-kodi'})
                submenu.append({'title': 'Update show in Emby', 'path': '/home/updateEMBY?show=%d' % showObj.indexerid,
                                'requires': self.haveEMBY(), 'icon': 'ui-icon ui-icon-refresh'})
                submenu.append({'title': 'Preview Rename', 'path': '/home/testRename?show=%d' % showObj.indexerid,
                                'icon': 'ui-icon ui-icon-tag'})

                if sickrage.srCore.srConfig.USE_SUBTITLES and not sickrage.srCore.SHOWQUEUE.isBeingSubtitled(
                        showObj) and showObj.subtitles:
                    submenu.append(
                        {'title': 'Download Subtitles', 'path': '/home/subtitleShow?show=%d' % showObj.indexerid,
                         'icon': 'ui-icon ui-icon-comment'})

        epCounts = {}
        epCats = {}
        epCounts[Overview.SKIPPED] = 0
        epCounts[Overview.WANTED] = 0
        epCounts[Overview.QUAL] = 0
        epCounts[Overview.GOOD] = 0
        epCounts[Overview.UNAIRED] = 0
        epCounts[Overview.SNATCHED] = 0

        for curEp in episodeResults:
            curEpCat = showObj.getOverview(int(curEp["status"] or -1))
            if curEpCat:
                epCats[str(curEp["season"]) + "x" + str(curEp["episode"])] = curEpCat
                epCounts[curEpCat] += 1

        def titler(x):
            return (remove_article(x), x)[not x or sickrage.srCore.srConfig.SORT_ARTICLE]

        if sickrage.srCore.srConfig.ANIME_SPLIT_HOME:
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
        for index, recentShow in enumerate(sickrage.srCore.srConfig.SHOWS_RECENT):
            if recentShow['indexerid'] == indexerid:
                del sickrage.srCore.srConfig.SHOWS_RECENT[index]

        # Only track 5 most recent shows
        del sickrage.srCore.srConfig.SHOWS_RECENT[4:]

        # Insert most recent show
        sickrage.srCore.srConfig.SHOWS_RECENT.insert(0, {
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

    @staticmethod
    def plotDetails(show, season, episode):

        try:
            result = main_db.MainDB().select(
                "SELECT description FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                (int(show), int(season), int(episode)))[0]['description']
        except:
            result = 'Episode not found.'
        return result

    @staticmethod
    def sceneExceptions(show):
        exceptionsList = get_all_scene_exceptions(show)
        if not exceptionsList:
            return "No scene exceptions"

        out = []
        for season, names in iter(sorted(exceptionsList.items())):
            if season == -1:
                season = "*"
            out.append("S" + str(season) + ": " + ", ".join(names))
        return "<br>".join(out)

    def editShow(self, show=None, location=None, anyQualities=None, bestQualities=None, exceptions_list=None,
                 flatten_folders=None, paused=None, directCall=False, air_by_date=None, sports=None, dvdorder=None,
                 indexerLang=None, subtitles=None, archive_firstmatch=None, rls_ignore_words=None,
                 rls_require_words=None, anime=None, blacklist=None, whitelist=None,
                 scene=None, defaultEpStatus=None, quality_preset=None):

        if exceptions_list is None:
            exceptions_list = []
        if bestQualities is None:
            bestQualities = []
        if anyQualities is None:
            anyQualities = []

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

                if sickrage.srCore.ADBA_CONNECTION and not anidb_failed:
                    try:
                        anime = aniDBAbstracter.Anime(sickrage.srCore.ADBA_CONNECTION, name=showObj.name)
                        groups = anime.get_groups()
                    except Exception as e:
                        anidb_failed = True
                        sickrage.srCore.srNotifications.error('Unable to retreive Fansub Groups from AniDB.')
                        sickrage.srCore.srLogger.debug(
                            'Unable to retreive Fansub Groups from AniDB. Error is {}'.format(str(e)))

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
                    title='Edit Show',
                    header='Edit Show',
                    controller='home',
                    action="edit_show"
                )
            else:
                return self.render(
                    "/home/edit_show.mako",
                    show=showObj,
                    quality=showObj.quality,
                    scene_exceptions=scene_exceptions,
                    title='Edit Show',
                    header='Edit Show',
                    controller='home',
                    action="edit_show"
                )

        flatten_folders = not sickrage.srCore.srConfig.checkbox_to_value(flatten_folders)  # UI inverts this value
        dvdorder = sickrage.srCore.srConfig.checkbox_to_value(dvdorder)
        archive_firstmatch = sickrage.srCore.srConfig.checkbox_to_value(archive_firstmatch)
        paused = sickrage.srCore.srConfig.checkbox_to_value(paused)
        air_by_date = sickrage.srCore.srConfig.checkbox_to_value(air_by_date)
        scene = sickrage.srCore.srConfig.checkbox_to_value(scene)
        sports = sickrage.srCore.srConfig.checkbox_to_value(sports)
        anime = sickrage.srCore.srConfig.checkbox_to_value(anime)
        subtitles = sickrage.srCore.srConfig.checkbox_to_value(subtitles)

        if indexerLang and indexerLang in srIndexerApi(showObj.indexer).indexer().config[
            'valid_languages']:
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
                newQuality = Quality.combineQualities(map(int, anyQualities), map(int, bestQualities))

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
                sickrage.srCore.srLogger.debug(os.path.normpath(showObj.location) + " != " + os.path.normpath(location))
                if not os.path.isdir(location) and not sickrage.srCore.srConfig.CREATE_MISSING_SHOW_DIRS:
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
                time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append("Unable to update show: {0}".format(str(e)))

        if do_update_exceptions:
            try:
                update_scene_exceptions(showObj.indexerid,
                                        exceptions_list)  # @UndefinedVdexerid)
                time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append("Unable to force an update on scene exceptions of the show.")

        if do_update_scene_numbering:
            try:
                xem_refresh(showObj.indexerid, showObj.indexer)
                time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append("Unable to force an update on scene numbering of the show.")

        if directCall:
            return errors

        if len(errors) > 0:
            sickrage.srCore.srNotifications.error(
                '%d error%s while saving changes:' % (len(errors), "" if len(errors) == 1 else "s"),
                '<ul>' + '\n'.join(['<li>%s</li>' % error for error in errors]) + "</ul>")

        return self.redirect("/home/displayShow?show=" + show)

    def togglePause(self, show=None):
        error, show = TVShow.pause(show)

        if error is not None:
            return self._genericMessage('Error', error)

        sickrage.srCore.srNotifications.message('%s has been %s' % (show.name, ('resumed', 'paused')[show.paused]))

        return self.redirect("/home/displayShow?show=%i" % show.indexerid)

    def deleteShow(self, show=None, full=0):
        if show:
            error, show = TVShow.delete(show, full)

            if error is not None:
                return self._genericMessage('Error', error)

            sickrage.srCore.srNotifications.message(
                '%s has been %s %s' %
                (
                    show.name,
                    ('deleted', 'trashed')[bool(sickrage.srCore.srConfig.TRASH_REMOVE_SHOW)],
                    ('(media untouched)', '(with all related media)')[bool(full)]
                )
            )

            time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')

    def refreshShow(self, show=None):
        error, show = TVShow.refresh(show)

        # This is a show validation error
        if error is not None and show is None:
            return self._genericMessage('Error', error)

        # This is a refresh error
        if error is not None:
            sickrage.srCore.srNotifications.error('Unable to refresh this show.', error)

        time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])

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
            sickrage.srCore.srNotifications.error("Unable to update this show.", e.message)

        # just give it some time
        time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def subtitleShow(self, show=None, force=0):

        if show is None:
            return self._genericMessage("Error", "Invalid show ID")

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if showObj is None:
            return self._genericMessage("Error", "Unable to find the specified show")

        # search and download subtitles
        sickrage.srCore.SHOWQUEUE.downloadSubtitles(showObj, bool(force))

        time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def updateKODI(self, show=None):
        showName = None
        showObj = None

        if show:
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))
            if showObj:
                showName = urllib.quote_plus(showObj.name.encode('utf-8'))

        if sickrage.srCore.srConfig.KODI_UPDATE_ONLYFIRST:
            host = sickrage.srCore.srConfig.KODI_HOST.split(",")[0].strip()
        else:
            host = sickrage.srCore.srConfig.KODI_HOST

        if sickrage.srCore.notifiersDict.kodi_notifier.update_library(showName=showName):
            sickrage.srCore.srNotifications.message("Library update command sent to KODI host(s): " + host)
        else:
            sickrage.srCore.srNotifications.error("Unable to contact one or more KODI host(s): " + host)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def updatePLEX(self):
        if None is sickrage.srCore.notifiersDict.plex_notifier.update_library():
            sickrage.srCore.srNotifications.message(
                "Library update command sent to Plex Media Server host: " + sickrage.srCore.srConfig.PLEX_SERVER_HOST)
        else:
            sickrage.srCore.srNotifications.error(
                "Unable to contact Plex Media Server host: " + sickrage.srCore.srConfig.PLEX_SERVER_HOST)
        return self.redirect('/home/')

    def updateEMBY(self, show=None):
        showObj = None

        if show:
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if sickrage.srCore.notifiersDict.emby_notifier.update_library(showObj):
            sickrage.srCore.srNotifications.message(
                "Library update command sent to Emby host: " + sickrage.srCore.srConfig.EMBY_HOST)
        else:
            sickrage.srCore.srNotifications.error("Unable to contact Emby host: " + sickrage.srCore.srConfig.EMBY_HOST)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def deleteEpisode(self, show=None, eps=None, direct=False):
        if not all([show, eps]):
            errMsg = "You must specify a show and at least one episode"
            if direct:
                sickrage.srCore.srNotifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))
        if not showObj:
            errMsg = "Error", "Show not in show list"
            if direct:
                sickrage.srCore.srNotifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        if eps:
            for curEp in eps.split('|'):
                if not curEp:
                    sickrage.srCore.srLogger.debug("curEp was empty when trying to deleteEpisode")

                sickrage.srCore.srLogger.debug("Attempting to delete episode " + curEp)

                epInfo = curEp.split('x')

                if not all(epInfo):
                    sickrage.srCore.srLogger.debug(
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
                sickrage.srCore.srNotifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        if not statusStrings.has_key(int(status)):
            errMsg = "Invalid status"
            if direct:
                sickrage.srCore.srNotifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(show))

        if not showObj:
            errMsg = "Error", "Show not in show list"
            if direct:
                sickrage.srCore.srNotifications.error('Error', errMsg)
                return json_encode({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        segments = {}
        trakt_data = []
        if eps:
            sql_l = []
            for curEp in eps.split('|'):

                if not curEp:
                    sickrage.srCore.srLogger.debug("curEp was empty when trying to setStatus")

                sickrage.srCore.srLogger.debug("Attempting to set status on episode " + curEp + " to " + status)

                epInfo = curEp.split('x')

                if not all(epInfo):
                    sickrage.srCore.srLogger.debug(
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
                        sickrage.srCore.srLogger.warning(
                            "Refusing to change status of " + curEp + " because it is UNAIRED")
                        continue

                    if int(status) in Quality.DOWNLOADED and epObj.status not in Quality.SNATCHED + \
                            Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + [
                        IGNORED] and not os.path.isfile(epObj.location):
                        sickrage.srCore.srLogger.warning(
                            "Refusing to change status of " + curEp + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if int(status) == FAILED and epObj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + \
                            Quality.SNATCHED_BEST + Quality.DOWNLOADED + Quality.ARCHIVED:
                        sickrage.srCore.srLogger.warning(
                            "Refusing to change status of " + curEp + " to FAILED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if epObj.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        sickrage.srCore.srLogger.info(
                            "Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced")
                        epObj.release_name = ""

                    epObj.status = int(status)

                    # mass add to database
                    sql_q = epObj.saveToDB(False)
                    if sql_q:
                        sql_l.append(sql_q)

                    trakt_data.append((epObj.season, epObj.episode))

            data = sickrage.srCore.notifiersDict.trakt_notifier.trakt_episode_data_generate(trakt_data)
            if data and sickrage.srCore.srConfig.USE_TRAKT and sickrage.srCore.srConfig.TRAKT_SYNC_WATCHLIST:
                if int(status) in [WANTED, FAILED]:
                    sickrage.srCore.srLogger.debug(
                        "Add episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(
                            showObj.name) + " to Watchlist")
                    sickrage.srCore.notifiersDict.trakt_notifier.update_watchlist(showObj, data_episode=data,
                                                                                  update="add")
                elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                    sickrage.srCore.srLogger.debug(
                        "Remove episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(
                            showObj.name) + " from Watchlist")
                    sickrage.srCore.notifiersDict.trakt_notifier.update_watchlist(showObj, data_episode=data,
                                                                                  update="remove")

            if len(sql_l) > 0:
                main_db.MainDB().mass_upsert(sql_l)
                del sql_l  # cleanup

        if int(status) == WANTED and not showObj.paused:
            msg = "Backlog was automatically started for the following seasons of <b>" + showObj.name + "</b>:<br>"
            msg += '<ul>'

            for season, segment in segments.items():
                sickrage.srCore.SEARCHQUEUE.put(BacklogQueueItem(showObj, segment))

                msg += "<li>Season " + str(season) + "</li>"
                sickrage.srCore.srLogger.info("Sending backlog for " + showObj.name + " season " + str(
                    season) + " because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                sickrage.srCore.srNotifications.message("Backlog started", msg)
        elif int(status) == WANTED and showObj.paused:
            sickrage.srCore.srLogger.info(
                "Some episodes were set to wanted, but " + showObj.name + " is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = "Retrying Search was automatically started for the following season of <b>" + showObj.name + "</b>:<br>"
            msg += '<ul>'

            for season, segment in segments.items():
                sickrage.srCore.SEARCHQUEUE.put(FailedQueueItem(showObj, segment))

                msg += "<li>Season " + str(season) + "</li>"
                sickrage.srCore.srLogger.info("Retrying Search for " + showObj.name + " season " + str(
                    season) + " because some eps were set to failed")

            msg += "</ul>"

            if segments:
                sickrage.srCore.srNotifications.message("Retry Search started", msg)

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
            {'title': 'Edit', 'path': '/home/editShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-pencil'}]

        return self.render(
            "/home/test_renaming.mako",
            submenu=submenu,
            ep_obj_list=ep_obj_rename_list,
            show=showObj,
            title='Preview Rename',
            header='Preview Rename',
            controller='home',
            action="test_renaming"
        )

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
                sickrage.srCore.srLogger.warning("Unable to find an episode for " + curEp + ", skipping")
                continue
            related_eps_result = main_db.MainDB().select(
                "SELECT * FROM tv_episodes WHERE location = ? AND episode != ?",
                [ep_result[0]["location"], epInfo[1]])

            root_ep_obj = show_obj.getEpisode(int(epInfo[0]), int(epInfo[1]))
            root_ep_obj.relatedEps = []

            for cur_related_ep in related_eps_result:
                related_ep_obj = show_obj.getEpisode(int(cur_related_ep["season"]), int(cur_related_ep["episode"]))
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

            sickrage.srCore.SEARCHQUEUE.put(ep_queue_item)
            if not all([ep_queue_item.started, ep_queue_item.success]):
                return json_encode({'result': 'success'})
        return json_encode({'result': 'failure'})

    ### Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self, show=None):
        def getEpisodes(searchThread, searchstatus):
            results = []
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(searchThread.show.indexerid))

            if not showObj:
                sickrage.srCore.srLogger.error(
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
            sickrage.srCore.srNotifications.message(ep_obj.show.name, status)
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
            result['success'] = False
            result['errorMessage'] = ep_obj
        elif showObj.is_anime:
            sickrage.srCore.srLogger.debug("setAbsoluteSceneNumbering for %s from %s to %s" %
                                           (show, forAbsolute, sceneAbsolute))

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None:
                sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            sickrage.srCore.srLogger.debug("setEpisodeSceneNumbering for %s from %sx%s to %sx%s" %
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

            sickrage.srCore.SEARCHQUEUE.put(ep_queue_item)
            if not all([ep_queue_item.started, ep_queue_item.success]):
                return json_encode({'result': 'success'})
        return json_encode({'result': 'failure'})

    @staticmethod
    def fetch_releasegroups(show_name):
        sickrage.srCore.srLogger.info('ReleaseGroups: %s' % show_name)
        if sickrage.srCore.ADBA_CONNECTION:
            anime = aniDBAbstracter.Anime(sickrage.srCore.ADBA_CONNECTION, name=show_name)
            groups = anime.get_groups()
            sickrage.srCore.srLogger.info('ReleaseGroups: %s' % groups)
            return json_encode({'result': 'success', 'groups': groups})

        return json_encode({'result': 'failure'})


@Route('/IRC(/?.*)')
class irc(WebRoot):
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


@Route('/news(/?.*)')
class news(WebRoot):
    def __init__(self, *args, **kwargs):
        super(news, self).__init__(*args, **kwargs)

    def index(self):
        try:
            news = sickrage.srCore.VERSIONUPDATER.check_for_new_news(force=True)
        except Exception:
            sickrage.srCore.srLogger.debug('Could not load news from repo, giving a link!')
            news = 'Could not load news from the repo. [Click here for news.md](' + sickrage.srCore.srConfig.NEWS_URL + ')'

        sickrage.srCore.srConfig.NEWS_LAST_READ = sickrage.srCore.srConfig.NEWS_LATEST
        sickrage.srCore.srConfig.NEWS_UNREAD = 0
        sickrage.srCore.srConfig.save()

        data = markdown2.markdown(
            news if news else "The was a problem connecting to github, please refresh and try again",
            extras=['header-ids'])

        return self.render(
            "/markdown.mako",
            title="News",
            header="News",
            topmenu="system",
            data=data,
            controller='root',
            action='news'
        )


@Route('/changes(/?.*)')
class changelog(WebRoot):
    def __init__(self, *args, **kwargs):
        super(changelog, self).__init__(*args, **kwargs)

    def index(self):
        try:
            changes = sickrage.srCore.srWebSession.get(sickrage.srCore.srConfig.CHANGES_URL).text
        except Exception:
            sickrage.srCore.srLogger.debug('Could not load changes from repo, giving a link!')
            changes = 'Could not load changes from the repo. [Click here for CHANGES.md]({})'.format(
                sickrage.srCore.srConfig.CHANGES_URL)

        data = markdown2.markdown(
            changes if changes else "The was a problem connecting to github, please refresh and try again",
            extras=['header-ids'])

        return self.render(
            "/markdown.mako",
            title="Changelog",
            header="Changelog",
            topmenu="system",
            data=data,
            controller='root',
            action='changelog'
        )


@Route('/home/postprocess(/?.*)')
class HomePostProcess(Home):
    def __init__(self, *args, **kwargs):
        super(HomePostProcess, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/home/postprocess.mako",
            title='Post Processing',
            header='Post Processing',
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

        if not pp_options.has_key('proc_dir'):
            return self.redirect("/home/postprocess/")

        result = processDir(pp_options["proc_dir"], **pp_options)
        if pp_options.get("quiet", None):
            return result

        return self._genericMessage("Postprocessing results", result.replace("\n", "<br>\n"))


@Route('/home/addShows(/?.*)')
class HomeAddShows(Home):
    def __init__(self, *args, **kwargs):
        super(HomeAddShows, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/home/add_shows.mako",
            title='Add Shows',
            header='Add Shows',
            topmenu='home',
            controller='home',
            action='add_shows'
        )

    @staticmethod
    def getIndexerLanguages():
        result = srIndexerApi().config['valid_languages']

        return json_encode({'results': result})

    @staticmethod
    def sanitizeFileName(name):
        return sanitizeFileName(name)

    @staticmethod
    def searchIndexersForShowName(search_term, lang=None, indexer=None):
        if not lang or lang == 'null':
            lang = sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE

        results = {}
        final_results = []

        # Query Indexers for each search term and build the list of results
        for indexer in srIndexerApi().indexers if not int(indexer) else [int(indexer)]:
            lINDEXER_API_PARMS = srIndexerApi(indexer).api_params.copy()
            lINDEXER_API_PARMS['language'] = lang
            lINDEXER_API_PARMS['custom_ui'] = AllShowsListUI
            t = srIndexerApi(indexer).indexer(**lINDEXER_API_PARMS)

            sickrage.srCore.srLogger.debug("Searching for Show with searchterm: %s on Indexer: %s" % (
                search_term, srIndexerApi(indexer).name))

            try:
                # search via seriesname
                results.setdefault(indexer, []).extend(t[search_term])
            except Exception:
                continue

        for i, shows in results.items():
            final_results.extend(
                [[srIndexerApi(i).name, i, srIndexerApi(i).config["show_url"],
                  int(show['id']), show['seriesname'], show['firstaired']] for show in shows])

        lang_id = srIndexerApi().config['langabbv_to_id'][lang]
        return json_encode({'results': final_results, 'langid': lang_id})

    def massAddTable(self, rootDir=None):
        if not rootDir:
            return "No folders selected."
        elif not isinstance(rootDir, list):
            root_dirs = [rootDir]
        else:
            root_dirs = rootDir

        root_dirs = [urllib.unquote_plus(x) for x in root_dirs]

        if sickrage.srCore.srConfig.ROOT_DIRS:
            default_index = int(sickrage.srCore.srConfig.ROOT_DIRS.split('|')[0])
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
                    cur_dir['added_already'] = True
                else:
                    cur_dir['added_already'] = False

                dir_list.append(cur_dir)

                showid = show_name = indexer = None
                for cur_provider in sickrage.srCore.metadataProviderDict.values():
                    if not cur_provider.enabled:
                        continue

                    if not (showid and show_name):
                        (showid, show_name, indexer) = cur_provider.retrieveShowMetadata(cur_path)

                        # default to TVDB if indexer was not detected
                        if show_name and not (indexer or showid):
                            (sn, idxr, i) = srIndexerApi(indexer).searchForShowID(show_name, showid)

                            # set indexer and indexer_id from found info
                            if not indexer and idxr:
                                indexer = idxr

                            if not showid and i:
                                showid = i

                cur_dir['existing_info'] = (showid, show_name, indexer)

                if showid and findCertainShow(sickrage.srCore.SHOWLIST, showid):
                    cur_dir['added_already'] = True

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

        provided_indexer = int(indexer or sickrage.srCore.srConfig.INDEXER_DEFAULT)

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
            indexers=srIndexerApi().indexers,
            quality=sickrage.srCore.srConfig.QUALITY_DEFAULT,
            whitelist=[],
            blacklist=[],
            groups=[],
            title='New Show',
            header='New Show',
            topmenu='home',
            controller='home',
            action="new_show"
        )

    def recommendedShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        return self.render(
            "/home/recommended_shows.mako",
            title="Recommended Shows",
            header="Recommended Shows",
            enable_anime_options=False,
            controller='home',
            action="recommended_shows"
        )

    def getRecommendedShows(self):
        blacklist = False
        recommended_shows = []
        trakt_api = TraktAPI(sickrage.srCore.srConfig.SSL_VERIFY, sickrage.srCore.srConfig.TRAKT_TIMEOUT)

        try:
            shows = trakt_api.traktRequest("recommendations/shows?extended=full,images") or []
            for show in shows:
                show = {'show': show}
                show_id = int(show['show']['ids']['tvdb']) or None

                try:
                    if not findCertainShow(sickrage.srCore.SHOWLIST, [show_id]):
                        library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
                        if show_id in (lshow['show']['ids']['tvdb'] for lshow in library_shows):
                            continue

                    if sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME is not None and sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME:
                        not_liked_show = trakt_api.traktRequest(
                            "users/{}/lists/{}/items".format(sickrage.srCore.srConfig.TRAKT_USERNAME,
                                                             sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME))
                        if not_liked_show and [nlshow for nlshow in not_liked_show if (
                                        show_id == nlshow['show']['ids']['tvdb'] and nlshow['type'] == 'show')]:
                            continue

                        recommended_shows += [show]
                except MultipleShowObjectsException:
                    continue

            if sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME != '':
                blacklist = True

        except traktException as e:
            sickrage.srCore.srLogger.warning("Could not connect to Trakt service: %s" % e)

        return self.render(
            "/home/recommended_shows.mako",
            title="Recommended Shows",
            header="Recommended Shows",
            trending_shows=recommended_shows,
            blacklist=blacklist,
            controller='home',
            action="recommended_shows"
        )

    def trendingShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        return self.render(
            "/home/trending_shows.mako",
            title="Trending Shows",
            header="Trending Shows",
            enable_anime_options=False,
            controller='home',
            action="trending_shows"
        )

    def getTrendingShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """

        blacklist = False
        trending_shows = []
        trakt_api = TraktAPI(sickrage.srCore.srConfig.SSL_VERIFY, sickrage.srCore.srConfig.TRAKT_TIMEOUT)

        try:
            not_liked_show = ""
            if sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME is not None and sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME:
                not_liked_show = trakt_api.traktRequest(
                    "users/" + sickrage.srCore.srConfig.TRAKT_USERNAME + "/lists/" + sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME + "/items") or []
            else:
                sickrage.srCore.srLogger.debug("trending blacklist name is empty")

            limit_show = 50 + len(not_liked_show)

            shows = trakt_api.traktRequest("shows/trending?limit=" + str(limit_show) + "&extended=full,images") or []

            library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
            for show in shows:
                show = {'show': show}
                show_id = show['show']['ids']['tvdb']

                try:
                    if not findCertainShow(sickrage.srCore.SHOWLIST, [int(show['show']['ids']['tvdb'])]):
                        if show_id not in [lshow['show']['ids']['tvdb'] for lshow in library_shows]:
                            if sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME:
                                not_liked_show = trakt_api.traktRequest(
                                    "users/{}/lists/{}/items".format(sickrage.srCore.srConfig.TRAKT_USERNAME,
                                                                     sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME))
                                if not_liked_show and [nlshow for nlshow in not_liked_show if (
                                                show_id == nlshow['show']['ids']['tvdb'] and nlshow[
                                            'type'] == 'show')]:
                                    continue

                                trending_shows += [show]
                            else:
                                trending_shows += [show]

                except MultipleShowObjectsException:
                    continue

            if sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME != '':
                blacklist = True

        except traktException as e:
            sickrage.srCore.srLogger.warning("Could not connect to Trakt service: %s" % e)

        return self.render(
            "/home/trending_shows.mako",
            blacklist=blacklist,
            trending_shows=trending_shows,
            controller='home',
            action="trending_shows"
        )

    def popularShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        e = None

        try:
            popular_shows = imdbPopular().fetch_popular_shows()
        except Exception as e:
            popular_shows = None

        return self.render("/home/popular_shows.mako",
                           title="Popular Shows",
                           header="Popular Shows",
                           popular_shows=popular_shows,
                           imdb_exception=e,
                           topmenu="home",
                           controller='home',
                           action="popular_shows"
                           )

    def addShowToBlacklist(self, indexer_id):
        # URL parameters
        data = {'shows': [{'ids': {'tvdb': indexer_id}}]}

        trakt_api = TraktAPI(sickrage.srCore.srConfig.SSL_VERIFY, sickrage.srCore.srConfig.TRAKT_TIMEOUT)

        trakt_api.traktRequest(
            "users/" + sickrage.srCore.srConfig.TRAKT_USERNAME + "/lists/" + sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME + "/items",
            data,
            method='POST')

        return self.redirect('/home/addShows/trendingShows/')

    def existingShows(self):
        """
        Prints out the page to add existing shows from a root dir
        """
        return self.render("/home/add_existing_shows.mako",
                           enable_anime_options=False,
                           quality=sickrage.srCore.srConfig.QUALITY_DEFAULT,
                           title='Existing Show',
                           header='Existing Show',
                           topmenu="home",
                           controller='home',
                           action="add_existing_shows"
                           )

    def addTraktShow(self, indexer_id, showName):
        if findCertainShow(sickrage.srCore.SHOWLIST, int(indexer_id)):
            return

        if sickrage.srCore.srConfig.ROOT_DIRS:
            root_dirs = sickrage.srCore.srConfig.ROOT_DIRS.split('|')
            location = root_dirs[int(root_dirs[0]) + 1]
        else:
            location = None

        if location:
            show_dir = os.path.join(location, sanitizeFileName(showName))
            dir_exists = makeDir(show_dir)
            if not dir_exists:
                sickrage.srCore.srLogger.error("Unable to create the folder " + show_dir + ", can't add the show")
                return
            else:
                chmodAsParent(show_dir)

            sickrage.srCore.SHOWQUEUE.addShow(1, int(indexer_id), show_dir,
                                              default_status=sickrage.srCore.srConfig.STATUS_DEFAULT,
                                              quality=sickrage.srCore.srConfig.QUALITY_DEFAULT,
                                              flatten_folders=sickrage.srCore.srConfig.FLATTEN_FOLDERS_DEFAULT,
                                              subtitles=sickrage.srCore.srConfig.SUBTITLES_DEFAULT,
                                              anime=sickrage.srCore.srConfig.ANIME_DEFAULT,
                                              scene=sickrage.srCore.srConfig.SCENE_DEFAULT,
                                              default_status_after=sickrage.srCore.srConfig.STATUS_DEFAULT_AFTER,
                                              archive=sickrage.srCore.srConfig.ARCHIVE_DEFAULT)

            sickrage.srCore.srNotifications.message('Adding Show', 'Adding the specified show into ' + show_dir)
        else:
            sickrage.srCore.srLogger.error("There was an error creating the show, no root directory setting found")
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
            indexerLang = sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE

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
                sickrage.srCore.srLogger.error(
                    "Unable to add show due to show selection. Not anough arguments: %s" % (repr(series_pieces)))
                sickrage.srCore.srNotifications.error(
                    "Unknown error. Unable to add show due to problem with show selection.")
                return self.redirect('/home/addShows/existingShows/')

            indexer = int(series_pieces[1])
            indexer_id = int(series_pieces[3])
            # Show name was sent in UTF-8 in the form
            show_name = series_pieces[4].decode('utf-8')
        else:
            # if no indexer was provided use the default indexer set in General settings
            if not providedIndexer:
                providedIndexer = sickrage.srCore.srConfig.INDEXER_DEFAULT

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
            sickrage.srCore.srNotifications.error("Unable to add show", "Folder " + show_dir + " exists already")
            return self.redirect('/home/addShows/existingShows/')

        # don't create show dir if config says not to
        if sickrage.srCore.srConfig.ADD_SHOWS_WO_DIR:
            sickrage.srCore.srLogger.info(
                "Skipping initial creation of " + show_dir + " due to sickrage.CONFIG.ini setting")
        else:
            dir_exists = makeDir(show_dir)
            if not dir_exists:
                sickrage.srCore.srLogger.error("Unable to create the folder " + show_dir + ", can't add the show")
                sickrage.srCore.srNotifications.error("Unable to add show",
                                                      "Unable to create the folder " + show_dir + ", can't add the show")
                # Don't redirect to default page because user wants to see the new show
                return self.redirect("/home/")
            else:
                chmodAsParent(show_dir)

        # prepare the inputs for passing along
        scene = sickrage.srCore.srConfig.checkbox_to_value(scene)
        anime = sickrage.srCore.srConfig.checkbox_to_value(anime)
        flatten_folders = sickrage.srCore.srConfig.checkbox_to_value(flatten_folders)
        subtitles = sickrage.srCore.srConfig.checkbox_to_value(subtitles)
        archive = sickrage.srCore.srConfig.checkbox_to_value(archive)

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

        newQuality = tryInt(quality_preset, None)
        if not newQuality:
            newQuality = Quality.combineQualities(map(int, anyQualities), map(int, bestQualities))

        # add the show
        sickrage.srCore.SHOWQUEUE.addShow(indexer, indexer_id, show_dir, int(defaultStatus), newQuality,
                                          flatten_folders, indexerLang, subtitles, anime,
                                          scene, None, blacklist, whitelist, int(defaultStatusAfter), archive)
        sickrage.srCore.srNotifications.message('Adding Show', 'Adding the specified show into ' + show_dir)

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

        promptForSettings = sickrage.srCore.srConfig.checkbox_to_value(promptForSettings)

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
                sickrage.srCore.SHOWQUEUE.addShow(indexer, indexer_id, show_dir,
                                                  default_status=sickrage.srCore.srConfig.STATUS_DEFAULT,
                                                  quality=sickrage.srCore.srConfig.QUALITY_DEFAULT,
                                                  flatten_folders=sickrage.srCore.srConfig.FLATTEN_FOLDERS_DEFAULT,
                                                  subtitles=sickrage.srCore.srConfig.SUBTITLES_DEFAULT,
                                                  anime=sickrage.srCore.srConfig.ANIME_DEFAULT,
                                                  scene=sickrage.srCore.srConfig.SCENE_DEFAULT,
                                                  default_status_after=sickrage.srCore.srConfig.STATUS_DEFAULT_AFTER,
                                                  archive=sickrage.srCore.srConfig.ARCHIVE_DEFAULT)
                num_added += 1

        if num_added:
            sickrage.srCore.srNotifications.message("Shows Added",
                                                    "Automatically added " + str(
                                                        num_added) + " from their existing metadata files")

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

        cur_show_results = main_db.MainDB().select(
            "SELECT season, episode, name FROM tv_episodes WHERE showid = ? AND season != 0 AND status IN (" + ','.join(
                ['?'] * len(status_list)) + ")", [int(indexer_id)] + status_list)

        result = {}
        for cur_result in cur_show_results:
            cur_season = int(cur_result["season"])
            cur_episode = int(cur_result["episode"])

            if cur_season not in result:
                result[cur_season] = {}

            result[cur_season][cur_episode] = cur_result["name"]

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
                cur_indexer_id = int(cur_status_result["indexer_id"])
                if cur_indexer_id not in ep_counts:
                    ep_counts[cur_indexer_id] = 1
                else:
                    ep_counts[cur_indexer_id] += 1

                show_names[cur_indexer_id] = cur_status_result["show_name"]
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
                all_eps_results = main_db.MainDB().select(
                    "SELECT season, episode FROM tv_episodes WHERE status IN (" + ','.join(
                        ['?'] * len(status_list)) + ") AND season != 0 AND showid = ?",
                    status_list + [cur_indexer_id])
                all_eps = [str(x["season"]) + 'x' + str(x["episode"]) for x in all_eps_results]
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
                if not frozenset(subtitle_searcher.wantedLanguages()).difference(cur_result["subtitles"].split(',')):
                    continue
            elif whichSubs in cur_result["subtitles"]:
                continue

            cur_season = int(cur_result["season"])
            cur_episode = int(cur_result["episode"])

            if cur_season not in result:
                result[cur_season] = {}

            if cur_episode not in result[cur_season]:
                result[cur_season][cur_episode] = {}

            result[cur_season][cur_episode]["name"] = cur_result["name"]

            result[cur_season][cur_episode]["subtitles"] = cur_result["subtitles"]

        return json_encode(result)

    def subtitleMissed(self, whichSubs=None):
        if not whichSubs:
            return self.render(
                "/manage/subtitles_missed.mako",
                whichSubs=whichSubs,
                title='Episode Overview',
                header='Episode Overview',
                topmenu='manage',
                controller='manage',
                action='subtitles_missed'
            )

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
            title='Missing Subtitles',
            header='Missing Subtitles',
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
                all_eps_results = main_db.MainDB().select(
                    "SELECT season, episode FROM tv_episodes WHERE status LIKE '%4' AND season != 0 AND showid = ?",
                    [cur_indexer_id])
                to_download[cur_indexer_id] = [str(x["season"]) + 'x' + str(x["episode"]) for x in all_eps_results]

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
                curEpCat = curShow.getOverview(int(curResult["status"] or -1))
                if curEpCat:
                    epCats[str(curResult["season"]) + "x" + str(curResult["episode"])] = curEpCat
                    epCounts[curEpCat] += 1

            showCounts[curShow.indexerid] = epCounts
            showCats[curShow.indexerid] = epCats
            showSQLResults[curShow.indexerid] = sqlResults

        return self.render(
            "/manage/backlog_overview.mako",
            showCounts=showCounts,
            showCats=showCats,
            showSQLResults=showSQLResults,
            title='Backlog Overview',
            header='Backlog Overview',
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

        return self.render(
            "/manage/mass_edit.mako",
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
            topmenu='manage',
            controller='manage',
            action='mass_edit'
        )

    def massEditSubmit(self, archive_firstmatch=None, paused=None, default_ep_status=None,
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
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(curShow))
            if not showObj:
                continue

            cur_root_dir = os.path.dirname(showObj.location)
            cur_show_dir = os.path.basename(showObj.location)
            if cur_root_dir in dir_map and cur_root_dir != dir_map[cur_root_dir]:
                new_show_dir = os.path.join(dir_map[cur_root_dir], cur_show_dir)
                sickrage.srCore.srLogger.info(
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
                sickrage.srCore.srLogger.error("Errors: " + str(curErrors))
                errors.append('<b>%s:</b>\n<ul>' % showObj.name + ' '.join(
                    ['<li>%s</li>' % error for error in curErrors]) + "</ul>")

        if len(errors) > 0:
            sickrage.srCore.srNotifications.error(
                '%d error%s while saving changes:' % (len(errors), "" if len(errors) == 1 else "s"),
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
            sickrage.srCore.srNotifications.error("Errors encountered",
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
            sickrage.srCore.srNotifications.message("The following actions were queued:",
                                                    messageDetail)

        return self.render(
            '/manage/mass_update.mako',
            title='Mass Update',
            header='Mass Update',
            topmenu='manage',
            controller='manage',
            action='mass_update'
        )

    def manageTorrents(self):
        info_download_station = ''

        if re.search('localhost', sickrage.srCore.srConfig.TORRENT_HOST):

            if sickrage.srCore.srConfig.LOCALHOST_IP == '':
                webui_url = re.sub('localhost', get_lan_ip(), sickrage.srCore.srConfig.TORRENT_HOST)
            else:
                webui_url = re.sub('localhost', sickrage.srCore.srConfig.LOCALHOST_IP,
                                   sickrage.srCore.srConfig.TORRENT_HOST)
        else:
            webui_url = sickrage.srCore.srConfig.TORRENT_HOST

        if sickrage.srCore.srConfig.TORRENT_METHOD == 'utorrent':
            webui_url = '/'.join(s.strip('/') for s in (webui_url, 'gui/'))
        if sickrage.srCore.srConfig.TORRENT_METHOD == 'download_station':
            if check_url(webui_url + 'download/'):
                webui_url += 'download/'
            else:
                info_download_station = '<p>To have a better experience please set the Download Station alias as <code>download</code>, you can check this setting in the Synology DSM <b>Control Panel</b> > <b>Application Portal</b>. Make sure you allow DSM to be embedded with iFrames too in <b>Control Panel</b> > <b>DSM Settings</b> > <b>Security</b>.</p><br><p>There is more information about this available <a href="https://github.com/midgetspy/Sick-Beard/pull/338">here</a>.</p><br>'

        if not sickrage.srCore.srConfig.TORRENT_PASSWORD == "" and not sickrage.srCore.srConfig.TORRENT_USERNAME == "":
            webui_url = re.sub('://',
                               '://' + str(sickrage.srCore.srConfig.TORRENT_USERNAME) + ':' + str(
                                   sickrage.srCore.srConfig.TORRENT_PASSWORD) + '@',
                               webui_url)

        return self.render(
            "/manage/torrents.mako",
            webui_url=webui_url,
            info_download_station=info_download_station,
            title='Manage Torrents',
            header='Manage Torrents',
            topmenu='manage',
            controller='manage',
            action='torrents'
        )

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

        return self.render(
            "/manage/failed_downloads.mako",
            limit=limit,
            failedResults=sqlResults,
            title='Failed Downloads',
            header='Failed Downloads',
            topmenu='manage',
            controller='manage',
            action='failed_downloads'
        )


@Route('/manage/manageSearches(/?.*)')
class ManageSearches(Manage):
    def __init__(self, *args, **kwargs):
        super(ManageSearches, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/manage/searches.mako",
            backlogPaused=sickrage.srCore.SEARCHQUEUE.is_backlog_paused(),
            backlogRunning=sickrage.srCore.SEARCHQUEUE.is_backlog_in_progress(),
            dailySearchStatus=sickrage.srCore.DAILYSEARCHER.amActive,
            findPropersStatus=sickrage.srCore.PROPERSEARCHER.amActive,
            queueLength=sickrage.srCore.SEARCHQUEUE.queue_length(),
            title='Manage Searches',
            header='Manage Searches',
            topmenu='manage',
            controller='manage',
            action='searches'
        )

    def forceBacklog(self):
        # force it to run the next time it looks
        if sickrage.srCore.srScheduler.get_job('BACKLOG').func():
            sickrage.srCore.srLogger.info("Backlog search forced")
            sickrage.srCore.srNotifications.message('Backlog search started')

        return self.redirect("/manage/manageSearches/")

    def forceSearch(self):
        # force it to run the next time it looks
        if sickrage.srCore.srScheduler.get_job('DAILYSEARCHER').func():
            sickrage.srCore.srLogger.info("Daily search forced")
            sickrage.srCore.srNotifications.message('Daily search started')

        return self.redirect("/manage/manageSearches/")

    def forceFindPropers(self):
        # force it to run the next time it looks
        if sickrage.srCore.srScheduler.get_job('PROPERSEARCHER').func():
            sickrage.srCore.srLogger.info("Find propers search forced")
            sickrage.srCore.srNotifications.message('Find propers search started')

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
            if sickrage.srCore.srConfig.HISTORY_LIMIT:
                limit = int(sickrage.srCore.srConfig.HISTORY_LIMIT)
            else:
                limit = 100
        else:
            limit = int(limit)

        sickrage.srCore.srConfig.HISTORY_LIMIT = limit

        sickrage.srCore.srConfig.save()

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
                history['actions'].sort(key=lambda x: x['time'], reverse=True)

        submenu = [
            {'title': 'Clear History', 'path': '/history/clearHistory', 'icon': 'ui-icon ui-icon-trash',
             'class': 'clearhistory', 'confirm': True},
            {'title': 'Trim History', 'path': '/history/trimHistory', 'icon': 'ui-icon ui-icon-trash',
             'class': 'trimhistory', 'confirm': True},
        ]

        return self.render(
            "/history.mako",
            historyResults=data,
            compactResults=compact,
            limit=limit,
            submenu=submenu,
            title='History',
            header='History',
            topmenu="history",
            controller='root',
            action='history'
        )

    def clearHistory(self):
        self.historyTool.clear()

        sickrage.srCore.srNotifications.message('History cleared')

        return self.redirect("/history/")

    def trimHistory(self):
        self.historyTool.trim()

        sickrage.srCore.srNotifications.message('Removed history entries older than 30 days')

        return self.redirect("/history/")


@Route('/config(/?.*)')
class Config(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    @staticmethod
    def ConfigMenu():
        menu = [
            {'title': 'General', 'path': '/config/general/', 'icon': 'ui-icon ui-icon-gear'},
            {'title': 'Backup/Restore', 'path': '/config/backuprestore/', 'icon': 'ui-icon ui-icon-gear'},
            {'title': 'Search Clients', 'path': '/config/search/', 'icon': 'ui-icon ui-icon-search'},
            {'title': 'Search Providers', 'path': '/config/providers/', 'icon': 'ui-icon ui-icon-search'},
            {'title': 'Subtitles Settings', 'path': '/config/subtitles/', 'icon': 'ui-icon ui-icon-comment'},
            {'title': 'Post Processing', 'path': '/config/postProcessing/', 'icon': 'ui-icon ui-icon-folder-open'},
            {'title': 'Notifications', 'path': '/config/notifications/', 'icon': 'ui-icon ui-icon-note'},
            {'title': 'Anime', 'path': '/config/anime/', 'icon': 'submenu-icon-anime'},
        ]

        return menu

    def index(self):
        return self.render(
            "/config/index.mako",
            submenu=self.ConfigMenu(),
            title='Configuration',
            header='Configuration',
            topmenu="config",
            controller='config',
            action='index'
        )


@Route('/config/general(/?.*)')
class ConfigGeneral(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigGeneral, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/general.mako",
            title='Config - General',
            header='General Configuration',
            topmenu='config',
            submenu=self.ConfigMenu(),
            controller='config',
            action='general'
        )

    @staticmethod
    def generateApiKey():
        return generateApiKey()

    @staticmethod
    def saveRootDirs(rootDirString=None):
        sickrage.srCore.srConfig.ROOT_DIRS = rootDirString

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

        sickrage.srCore.srConfig.STATUS_DEFAULT = int(defaultStatus)
        sickrage.srCore.srConfig.STATUS_DEFAULT_AFTER = int(defaultStatusAfter)
        sickrage.srCore.srConfig.QUALITY_DEFAULT = int(newQuality)

        sickrage.srCore.srConfig.FLATTEN_FOLDERS_DEFAULT = sickrage.srCore.srConfig.checkbox_to_value(
            defaultFlattenFolders)
        sickrage.srCore.srConfig.SUBTITLES_DEFAULT = sickrage.srCore.srConfig.checkbox_to_value(subtitles)

        sickrage.srCore.srConfig.ANIME_DEFAULT = sickrage.srCore.srConfig.checkbox_to_value(anime)
        sickrage.srCore.srConfig.SCENE_DEFAULT = sickrage.srCore.srConfig.checkbox_to_value(scene)
        sickrage.srCore.srConfig.ARCHIVE_DEFAULT = sickrage.srCore.srConfig.checkbox_to_value(archive)

        sickrage.srCore.srConfig.save()

    def saveGeneral(self, log_dir=None, log_nr=5, log_size=1048576, web_port=None, web_log=None,
                    encryption_version=None, web_ipv6=None, trash_remove_show=None, trash_rotate_logs=None,
                    update_frequency=None, skip_removed_files=None, indexerDefaultLang='en',
                    ep_default_deleted_status=None, launch_browser=None, showupdate_hour=3, web_username=None,
                    api_key=None, indexer_default=None, timezone_display=None, cpu_preset='NORMAL', web_password=None,
                    version_notify=None, enable_https=None, https_cert=None, https_key=None, handle_reverse_proxy=None,
                    sort_article=None, auto_update=None, notify_on_update=None, proxy_setting=None, proxy_indexers=None,
                    anon_redirect=None, git_path=None, git_remote=None, calendar_unprotected=None, calendar_icons=None,
                    debug=None, ssl_verify=None, no_restart=None, coming_eps_missed_range=None, filter_row=None,
                    fuzzy_dating=None, trim_zero=None, date_preset=None, date_preset_na=None, time_preset=None,
                    indexer_timeout=None, download_url=None, rootDir=None, theme_name=None, default_page=None,
                    git_reset=None, git_username=None, git_password=None, git_autoissues=None,
                    display_all_seasons=None, showupdate_stale=None, **kwargs):

        results = []

        # Misc
        sickrage.srCore.srConfig.DOWNLOAD_URL = download_url
        sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE = indexerDefaultLang
        sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS = ep_default_deleted_status
        sickrage.srCore.srConfig.SKIP_REMOVED_FILES = sickrage.srCore.srConfig.checkbox_to_value(skip_removed_files)
        sickrage.srCore.srConfig.LAUNCH_BROWSER = sickrage.srCore.srConfig.checkbox_to_value(launch_browser)
        sickrage.srCore.srConfig.change_showupdate_hour(showupdate_hour)
        sickrage.srCore.srConfig.change_version_notify(sickrage.srCore.srConfig.checkbox_to_value(version_notify))
        sickrage.srCore.srConfig.AUTO_UPDATE = sickrage.srCore.srConfig.checkbox_to_value(auto_update)
        sickrage.srCore.srConfig.NOTIFY_ON_UPDATE = sickrage.srCore.srConfig.checkbox_to_value(notify_on_update)
        sickrage.srCore.srConfig.SHOWUPDATE_STALE = sickrage.srCore.srConfig.checkbox_to_value(showupdate_stale)
        sickrage.srCore.srConfig.LOG_NR = log_nr
        sickrage.srCore.srConfig.LOG_SIZE = log_size

        sickrage.srCore.srConfig.TRASH_REMOVE_SHOW = sickrage.srCore.srConfig.checkbox_to_value(trash_remove_show)
        sickrage.srCore.srConfig.TRASH_ROTATE_LOGS = sickrage.srCore.srConfig.checkbox_to_value(trash_rotate_logs)
        sickrage.srCore.srConfig.change_updater_freq(update_frequency)
        sickrage.srCore.srConfig.LAUNCH_BROWSER = sickrage.srCore.srConfig.checkbox_to_value(launch_browser)
        sickrage.srCore.srConfig.SORT_ARTICLE = sickrage.srCore.srConfig.checkbox_to_value(sort_article)
        sickrage.srCore.srConfig.CPU_PRESET = cpu_preset
        sickrage.srCore.srConfig.ANON_REDIRECT = anon_redirect
        sickrage.srCore.srConfig.PROXY_SETTING = proxy_setting
        sickrage.srCore.srConfig.PROXY_INDEXERS = sickrage.srCore.srConfig.checkbox_to_value(proxy_indexers)
        sickrage.srCore.srConfig.GIT_USERNAME = git_username
        sickrage.srCore.srConfig.GIT_PASSWORD = git_password
        # sickrage.GIT_RESET = sickrage.CONFIG.checkbox_to_value(git_reset)
        # Force GIT_RESET
        sickrage.srCore.srConfig.GIT_RESET = 1
        sickrage.srCore.srConfig.GIT_AUTOISSUES = sickrage.srCore.srConfig.checkbox_to_value(git_autoissues)
        sickrage.srCore.srConfig.GIT_PATH = git_path
        sickrage.srCore.srConfig.GIT_REMOTE = git_remote
        sickrage.srCore.srConfig.CALENDAR_UNPROTECTED = sickrage.srCore.srConfig.checkbox_to_value(calendar_unprotected)
        sickrage.srCore.srConfig.CALENDAR_ICONS = sickrage.srCore.srConfig.checkbox_to_value(calendar_icons)
        sickrage.srCore.srConfig.NO_RESTART = sickrage.srCore.srConfig.checkbox_to_value(no_restart)
        sickrage.DEBUG = sickrage.srCore.srConfig.checkbox_to_value(debug)
        sickrage.srCore.srConfig.SSL_VERIFY = sickrage.srCore.srConfig.checkbox_to_value(ssl_verify)
        # sickrage.LOG_DIR is set in sickrage.CONFIG.change_log_dir()
        sickrage.srCore.srConfig.COMING_EPS_MISSED_RANGE = sickrage.srCore.srConfig.to_int(coming_eps_missed_range,
                                                                                           default=7)
        sickrage.srCore.srConfig.DISPLAY_ALL_SEASONS = sickrage.srCore.srConfig.checkbox_to_value(display_all_seasons)

        sickrage.srCore.srConfig.WEB_PORT = sickrage.srCore.srConfig.to_int(web_port)
        sickrage.srCore.srConfig.WEB_IPV6 = sickrage.srCore.srConfig.checkbox_to_value(web_ipv6)
        # sickrage.WEB_LOG is set in sickrage.CONFIG.change_log_dir()
        if sickrage.srCore.srConfig.checkbox_to_value(encryption_version) == 1:
            sickrage.srCore.srConfig.ENCRYPTION_VERSION = 2
        else:
            sickrage.srCore.srConfig.ENCRYPTION_VERSION = 0
        sickrage.srCore.srConfig.WEB_USERNAME = web_username
        sickrage.srCore.srConfig.WEB_PASSWORD = web_password

        sickrage.srCore.srConfig.FILTER_ROW = sickrage.srCore.srConfig.checkbox_to_value(filter_row)
        sickrage.srCore.srConfig.FUZZY_DATING = sickrage.srCore.srConfig.checkbox_to_value(fuzzy_dating)
        sickrage.srCore.srConfig.TRIM_ZERO = sickrage.srCore.srConfig.checkbox_to_value(trim_zero)

        if date_preset:
            sickrage.srCore.srConfig.DATE_PRESET = date_preset

        if indexer_default:
            sickrage.srCore.srConfig.INDEXER_DEFAULT = sickrage.srCore.srConfig.to_int(indexer_default)

        if indexer_timeout:
            sickrage.srCore.srConfig.INDEXER_TIMEOUT = sickrage.srCore.srConfig.to_int(indexer_timeout)

        if time_preset:
            sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS = time_preset
            sickrage.srCore.srConfig.TIME_PRESET = sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS.replace(":%S", "")

        sickrage.srCore.srConfig.TIMEZONE_DISPLAY = timezone_display

        if not sickrage.srCore.srConfig.change_log_dir(os.path.abspath(os.path.join(sickrage.DATA_DIR, log_dir)),
                                                       web_log):
            results += ["Unable to create directory " + os.path.normpath(log_dir) + ", log directory not changed."]

        sickrage.srCore.srConfig.API_KEY = api_key

        sickrage.srCore.srConfig.ENABLE_HTTPS = sickrage.srCore.srConfig.checkbox_to_value(enable_https)

        if not sickrage.srCore.srConfig.change_https_cert(https_cert):
            results += [
                "Unable to create directory " + os.path.normpath(https_cert) + ", https cert directory not changed."]

        if not sickrage.srCore.srConfig.change_https_key(https_key):
            results += [
                "Unable to create directory " + os.path.normpath(https_key) + ", https key directory not changed."]

        sickrage.srCore.srConfig.HANDLE_REVERSE_PROXY = sickrage.srCore.srConfig.checkbox_to_value(handle_reverse_proxy)

        sickrage.srCore.srConfig.THEME_NAME = theme_name

        sickrage.srCore.srConfig.DEFAULT_PAGE = default_page

        sickrage.srCore.srConfig.save()

        if len(results) > 0:
            for x in results:
                sickrage.srCore.srLogger.error(x)
            sickrage.srCore.srNotifications.error('Error(s) Saving Configuration',
                                                  '<br>\n'.join(results))
        else:
            sickrage.srCore.srNotifications.message('[GENERAL] Configuration Saved', os.path.join(sickrage.CONFIG_FILE))

        return self.redirect("/config/general/")


@Route('/config/backuprestore(/?.*)')
class ConfigBackupRestore(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigBackupRestore, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/backup_restore.mako",
            submenu=self.ConfigMenu(),
            title='Config - Backup/Restore',
            header='Backup/Restore',
            topmenu='config',
            controller='config',
            action='backup_restore'
        )

    @staticmethod
    def backup(backupDir=None):
        finalResult = ''

        if backupDir:
            if backupSR(backupDir):
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
            target_dir = os.path.join(sickrage.DATA_DIR, 'restore')

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
        return self.render(
            "/config/search.mako",
            submenu=self.ConfigMenu(),
            title='Config - Episode Search',
            header='Search Clients',
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
                   randomize_providers=None, use_failed_downloads=None, delete_failed=None,
                   torrent_dir=None, torrent_username=None, torrent_password=None, torrent_host=None,
                   torrent_label=None, torrent_label_anime=None, torrent_path=None, torrent_verify_cert=None,
                   torrent_seed_time=None, torrent_paused=None, torrent_high_bandwidth=None,
                   torrent_rpcurl=None, torrent_auth_type=None, ignore_words=None, require_words=None,
                   ignored_subs_list=None, torrent_trackers=None):

        results = []

        if not sickrage.srCore.srConfig.change_nzb_dir(nzb_dir):
            results += ["Unable to create directory " + os.path.normpath(nzb_dir) + ", dir not changed."]

        if not sickrage.srCore.srConfig.change_torrent_dir(torrent_dir):
            results += ["Unable to create directory " + os.path.normpath(torrent_dir) + ", dir not changed."]

        sickrage.srCore.srConfig.change_daily_searcher_freq(dailysearch_frequency)

        sickrage.srCore.srConfig.change_backlog_searcher_freq(backlog_frequency)

        sickrage.srCore.srConfig.USE_NZBS = sickrage.srCore.srConfig.checkbox_to_value(use_nzbs)
        sickrage.srCore.srConfig.USE_TORRENTS = sickrage.srCore.srConfig.checkbox_to_value(use_torrents)

        sickrage.srCore.srConfig.NZB_METHOD = nzb_method
        sickrage.srCore.srConfig.TORRENT_METHOD = torrent_method
        sickrage.srCore.srConfig.USENET_RETENTION = sickrage.srCore.srConfig.to_int(usenet_retention, default=500)

        sickrage.srCore.srConfig.TORRENT_TRACKERS = torrent_trackers if torrent_trackers else ""
        sickrage.srCore.srConfig.IGNORE_WORDS = ignore_words if ignore_words else ""
        sickrage.srCore.srConfig.REQUIRE_WORDS = require_words if require_words else ""
        sickrage.srCore.srConfig.IGNORED_SUBS_LIST = ignored_subs_list if ignored_subs_list else ""

        sickrage.srCore.srConfig.RANDOMIZE_PROVIDERS = sickrage.srCore.srConfig.checkbox_to_value(randomize_providers)

        sickrage.srCore.srConfig.change_download_propers(download_propers)

        sickrage.srCore.srConfig.PROPER_SEARCHER_INTERVAL = check_propers_interval

        sickrage.srCore.srConfig.ALLOW_HIGH_PRIORITY = sickrage.srCore.srConfig.checkbox_to_value(allow_high_priority)

        sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS = sickrage.srCore.srConfig.checkbox_to_value(use_failed_downloads)
        sickrage.srCore.srConfig.DELETE_FAILED = sickrage.srCore.srConfig.checkbox_to_value(delete_failed)

        sickrage.srCore.srConfig.SAB_USERNAME = sab_username
        sickrage.srCore.srConfig.SAB_PASSWORD = sab_password
        sickrage.srCore.srConfig.SAB_APIKEY = sab_apikey.strip()
        sickrage.srCore.srConfig.SAB_CATEGORY = sab_category
        sickrage.srCore.srConfig.SAB_CATEGORY_BACKLOG = sab_category_backlog
        sickrage.srCore.srConfig.SAB_CATEGORY_ANIME = sab_category_anime
        sickrage.srCore.srConfig.SAB_CATEGORY_ANIME_BACKLOG = sab_category_anime_backlog
        sickrage.srCore.srConfig.SAB_HOST = sickrage.srCore.srConfig.clean_url(sab_host)
        sickrage.srCore.srConfig.SAB_FORCED = sickrage.srCore.srConfig.checkbox_to_value(sab_forced)

        sickrage.srCore.srConfig.NZBGET_USERNAME = nzbget_username
        sickrage.srCore.srConfig.NZBGET_PASSWORD = nzbget_password
        sickrage.srCore.srConfig.NZBGET_CATEGORY = nzbget_category
        sickrage.srCore.srConfig.NZBGET_CATEGORY_BACKLOG = nzbget_category_backlog
        sickrage.srCore.srConfig.NZBGET_CATEGORY_ANIME = nzbget_category_anime
        sickrage.srCore.srConfig.NZBGET_CATEGORY_ANIME_BACKLOG = nzbget_category_anime_backlog
        sickrage.srCore.srConfig.NZBGET_HOST = sickrage.srCore.srConfig.clean_host(nzbget_host)
        sickrage.srCore.srConfig.NZBGET_USE_HTTPS = sickrage.srCore.srConfig.checkbox_to_value(nzbget_use_https)
        sickrage.srCore.srConfig.NZBGET_PRIORITY = sickrage.srCore.srConfig.to_int(nzbget_priority, default=100)

        sickrage.srCore.srConfig.TORRENT_USERNAME = torrent_username
        sickrage.srCore.srConfig.TORRENT_PASSWORD = torrent_password
        sickrage.srCore.srConfig.TORRENT_LABEL = torrent_label
        sickrage.srCore.srConfig.TORRENT_LABEL_ANIME = torrent_label_anime
        sickrage.srCore.srConfig.TORRENT_VERIFY_CERT = sickrage.srCore.srConfig.checkbox_to_value(torrent_verify_cert)
        sickrage.srCore.srConfig.TORRENT_PATH = torrent_path.rstrip('/\\')
        sickrage.srCore.srConfig.TORRENT_SEED_TIME = torrent_seed_time
        sickrage.srCore.srConfig.TORRENT_PAUSED = sickrage.srCore.srConfig.checkbox_to_value(torrent_paused)
        sickrage.srCore.srConfig.TORRENT_HIGH_BANDWIDTH = sickrage.srCore.srConfig.checkbox_to_value(
            torrent_high_bandwidth)
        sickrage.srCore.srConfig.TORRENT_HOST = sickrage.srCore.srConfig.clean_url(torrent_host)
        sickrage.srCore.srConfig.TORRENT_RPCURL = torrent_rpcurl
        sickrage.srCore.srConfig.TORRENT_AUTH_TYPE = torrent_auth_type

        sickrage.srCore.srConfig.save()

        if len(results) > 0:
            for x in results:
                sickrage.srCore.srLogger.error(x)
            sickrage.srCore.srNotifications.error('Error(s) Saving Configuration',
                                                  '<br>\n'.join(results))
        else:
            sickrage.srCore.srNotifications.message('[SEARCH] Configuration Saved', os.path.join(sickrage.CONFIG_FILE))

        return self.redirect("/config/search/")


@Route('/config/postProcessing(/?.*)')
class ConfigPostProcessing(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigPostProcessing, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/postprocessing.mako",
            submenu=self.ConfigMenu(),
            title='Config - Post Processing',
            header='Post Processing',
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
                           use_failed_downloads=None, delete_failed=None, extra_scripts=None,
                           naming_custom_sports=None, naming_sports_pattern=None,
                           naming_custom_anime=None, naming_anime_pattern=None,
                           naming_anime_multi_ep=None, autopostprocessor_frequency=None):

        results = []

        if not sickrage.srCore.srConfig.change_tv_download_dir(tv_download_dir):
            results += ["Unable to create directory " + os.path.normpath(tv_download_dir) + ", dir not changed."]

        sickrage.srCore.srConfig.change_autopostprocessor_freq(autopostprocessor_frequency)
        sickrage.srCore.srConfig.change_process_automatically(process_automatically)

        if unpack:
            if self.isRarSupported() != 'not supported':
                sickrage.srCore.srConfig.UNPACK = sickrage.srCore.srConfig.checkbox_to_value(unpack)
            else:
                sickrage.srCore.srConfig.UNPACK = 0
                results.append("Unpacking Not Supported, disabling unpack setting")
        else:
            sickrage.srCore.srConfig.UNPACK = sickrage.srCore.srConfig.checkbox_to_value(unpack)
        sickrage.srCore.srConfig.NO_DELETE = sickrage.srCore.srConfig.checkbox_to_value(no_delete)
        sickrage.srCore.srConfig.KEEP_PROCESSED_DIR = sickrage.srCore.srConfig.checkbox_to_value(keep_processed_dir)
        sickrage.srCore.srConfig.CREATE_MISSING_SHOW_DIRS = sickrage.srCore.srConfig.checkbox_to_value(
            create_missing_show_dirs)
        sickrage.srCore.srConfig.ADD_SHOWS_WO_DIR = sickrage.srCore.srConfig.checkbox_to_value(add_shows_wo_dir)
        sickrage.srCore.srConfig.PROCESS_METHOD = process_method
        sickrage.srCore.srConfig.DELRARCONTENTS = sickrage.srCore.srConfig.checkbox_to_value(del_rar_contents)
        sickrage.srCore.srConfig.EXTRA_SCRIPTS = [x.strip() for x in extra_scripts.split('|') if x.strip()]
        sickrage.srCore.srConfig.RENAME_EPISODES = sickrage.srCore.srConfig.checkbox_to_value(rename_episodes)
        sickrage.srCore.srConfig.AIRDATE_EPISODES = sickrage.srCore.srConfig.checkbox_to_value(airdate_episodes)
        sickrage.srCore.srConfig.FILE_TIMESTAMP_TIMEZONE = file_timestamp_timezone
        sickrage.srCore.srConfig.MOVE_ASSOCIATED_FILES = sickrage.srCore.srConfig.checkbox_to_value(
            move_associated_files)
        sickrage.srCore.srConfig.SYNC_FILES = sync_files
        sickrage.srCore.srConfig.POSTPONE_IF_SYNC_FILES = sickrage.srCore.srConfig.checkbox_to_value(
            postpone_if_sync_files)
        sickrage.srCore.srConfig.NAMING_CUSTOM_ABD = sickrage.srCore.srConfig.checkbox_to_value(naming_custom_abd)
        sickrage.srCore.srConfig.NAMING_CUSTOM_SPORTS = sickrage.srCore.srConfig.checkbox_to_value(naming_custom_sports)
        sickrage.srCore.srConfig.NAMING_CUSTOM_ANIME = sickrage.srCore.srConfig.checkbox_to_value(naming_custom_anime)
        sickrage.srCore.srConfig.NAMING_STRIP_YEAR = sickrage.srCore.srConfig.checkbox_to_value(naming_strip_year)
        sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS = sickrage.srCore.srConfig.checkbox_to_value(use_failed_downloads)
        sickrage.srCore.srConfig.DELETE_FAILED = sickrage.srCore.srConfig.checkbox_to_value(delete_failed)
        sickrage.srCore.srConfig.NFO_RENAME = sickrage.srCore.srConfig.checkbox_to_value(nfo_rename)

        sickrage.srCore.srConfig.METADATA_KODI = kodi_data
        sickrage.srCore.srConfig.METADATA_KODI_12PLUS = kodi_12plus_data
        sickrage.srCore.srConfig.METADATA_MEDIABROWSER = mediabrowser_data
        sickrage.srCore.srConfig.METADATA_PS3 = sony_ps3_data
        sickrage.srCore.srConfig.METADATA_WDTV = wdtv_data
        sickrage.srCore.srConfig.METADATA_TIVO = tivo_data
        sickrage.srCore.srConfig.METADATA_MEDE8ER = mede8er_data

        sickrage.srCore.metadataProviderDict['KODI'].set_config(sickrage.srCore.srConfig.METADATA_KODI)
        sickrage.srCore.metadataProviderDict['KODI 12+'].set_config(sickrage.srCore.srConfig.METADATA_KODI_12PLUS)
        sickrage.srCore.metadataProviderDict['MediaBrowser'].set_config(sickrage.srCore.srConfig.METADATA_MEDIABROWSER)
        sickrage.srCore.metadataProviderDict['Sony PS3'].set_config(sickrage.srCore.srConfig.METADATA_PS3)
        sickrage.srCore.metadataProviderDict['WDTV'].set_config(sickrage.srCore.srConfig.METADATA_WDTV)
        sickrage.srCore.metadataProviderDict['TIVO'].set_config(sickrage.srCore.srConfig.METADATA_TIVO)
        sickrage.srCore.metadataProviderDict['Mede8er'].set_config(sickrage.srCore.srConfig.METADATA_MEDE8ER)

        if self.isNamingValid(naming_pattern, naming_multi_ep, anime_type=naming_anime) != "invalid":
            sickrage.srCore.srConfig.NAMING_PATTERN = naming_pattern
            sickrage.srCore.srConfig.NAMING_MULTI_EP = int(naming_multi_ep)
            sickrage.srCore.srConfig.NAMING_ANIME = int(naming_anime)
            sickrage.srCore.srConfig.NAMING_FORCE_FOLDERS = validator.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append("You tried saving an invalid anime naming config, not saving your naming settings")
            else:
                results.append("You tried saving an invalid naming config, not saving your naming settings")

        if self.isNamingValid(naming_anime_pattern, naming_anime_multi_ep, anime_type=naming_anime) != "invalid":
            sickrage.srCore.srConfig.NAMING_ANIME_PATTERN = naming_anime_pattern
            sickrage.srCore.srConfig.NAMING_ANIME_MULTI_EP = int(naming_anime_multi_ep)
            sickrage.srCore.srConfig.NAMING_ANIME = int(naming_anime)
            sickrage.srCore.srConfig.NAMING_FORCE_FOLDERS = validator.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append("You tried saving an invalid anime naming config, not saving your naming settings")
            else:
                results.append("You tried saving an invalid naming config, not saving your naming settings")

        if self.isNamingValid(naming_abd_pattern, None, abd=True) != "invalid":
            sickrage.srCore.srConfig.NAMING_ABD_PATTERN = naming_abd_pattern
        else:
            results.append(
                "You tried saving an invalid air-by-date naming config, not saving your air-by-date settings")

        if self.isNamingValid(naming_sports_pattern, None, sports=True) != "invalid":
            sickrage.srCore.srConfig.NAMING_SPORTS_PATTERN = naming_sports_pattern
        else:
            results.append(
                "You tried saving an invalid sports naming config, not saving your sports settings")

        sickrage.srCore.srConfig.save()

        if len(results) > 0:
            for x in results:
                sickrage.srCore.srLogger.warning(x)
            sickrage.srCore.srNotifications.error('Error(s) Saving Configuration',
                                                  '<br>\n'.join(results))
        else:
            sickrage.srCore.srNotifications.message('[POST-PROCESSING] Configuration Saved',
                                                    os.path.join(sickrage.CONFIG_FILE))

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
            rar_path = os.path.join(sickrage.PROG_DIR, 'unrar2', 'test.rar')
            testing = RarFile(rar_path).read_files('*test.txt')
            if testing[0][1] == 'This is only a test.':
                return 'supported'
            sickrage.srCore.srLogger.error('Rar Not Supported: Can not read the content of test file')
            return 'not supported'
        except Exception as e:
            sickrage.srCore.srLogger.error('Rar Not Supported: {}'.format(e.message))
            return 'not supported'


@Route('/config/providers(/?.*)')
class ConfigProviders(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigProviders, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/providers.mako",
            submenu=self.ConfigMenu(),
            title='Config - Providers',
            header='Search Providers',
            topmenu='config',
            controller='config',
            action='providers'
        )

    @staticmethod
    def canAddNewznabProvider(name):
        if not name:
            return json_encode({'error': 'No Provider Name specified'})

        providerID = NewznabProvider(name, '').id
        if providerID not in sickrage.srCore.providersDict.newznab():
            return json_encode({'success': providerID})
        return json_encode({'error': 'Provider Name already exists as ' + name})

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, titleTAG):
        if not name:
            return json_encode({'error': 'No Provider Name specified'})

        providerObj = TorrentRssProvider(name, url, cookies, titleTAG)
        if providerObj.id not in sickrage.srCore.providersDict.torrentrss():
            (succ, errMsg) = providerObj.validateRSS()
            if succ:
                return json_encode({'success': providerObj.id})
            return json_encode({'error': errMsg})
        return json_encode({'error': 'Provider Name already exists as ' + name})

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
            error += "\nNo Provider Name specified"
        if not url:
            error += "\nNo Provider Url specified"
        if not key:
            error += "\nNo Provider Api key specified"

        if not error:
            tempProvider = NewznabProvider(name, url, key)
            success, tv_categories, error = tempProvider.get_newznab_categories()
        return json_encode({'success': success, 'tv_categories': tv_categories, 'error': error})

    def saveProviders(self, provider_strings='', provider_order='', **kwargs):
        results = []

        # enable/disable providers
        for curProviderStr in provider_order.split():
            curProvider, curEnabled = curProviderStr.split(':')
            if curProvider not in sickrage.srCore.providersDict.all():
                continue

            curProvObj = sickrage.srCore.providersDict.all()[curProvider]
            curProvObj.enabled = bool(sickrage.srCore.srConfig.to_int(curEnabled))

        # add all the newznab info we got into our list
        for curProviderStr in provider_strings.split():
            cur_type, curProviderStr = curProviderStr.split('|', 1)

            if cur_type == "newznab":
                cur_name, cur_url, cur_key, cur_cat = curProviderStr.split('|')
                cur_url = sickrage.srCore.srConfig.clean_url(cur_url)

                providerObj = NewznabProvider(cur_name, cur_url, key=cur_key)
                if providerObj.id not in sickrage.srCore.providersDict.newznab():
                    sickrage.srCore.providersDict.newznab().update(**{providerObj.id: providerObj})
                else:
                    providerObj = sickrage.srCore.providersDict.newznab()[providerObj.id]

                # newznab provider settings
                providerObj.name = cur_name
                providerObj.urls['base_url'] = cur_url
                providerObj.key = cur_key
                providerObj.catIDs = cur_cat
                providerObj.search_mode = str(getattr(kwargs, providerObj.id + '_search_mode', 'eponly')).strip()
                providerObj.search_fallback = sickrage.srCore.srConfig.checkbox_to_value(
                    getattr(kwargs, providerObj.id + '_search_fallback', 0))
                providerObj.enable_daily = sickrage.srCore.srConfig.checkbox_to_value(
                    getattr(kwargs, providerObj.id + '_enable_daily', 0))
                providerObj.enable_backlog = sickrage.srCore.srConfig.checkbox_to_value(
                    getattr(kwargs, providerObj.id + '_enable_backlog', 0))
            elif cur_type == "torrentrss":
                curName, curURL, curCookies, curTitleTAG = curProviderStr.split('|')
                curURL = sickrage.srCore.srConfig.clean_url(curURL)

                providerObj = TorrentRssProvider(curName, curURL, curCookies, curTitleTAG)
                if providerObj.id not in sickrage.srCore.providersDict.torrentrss():
                    sickrage.srCore.providersDict.torrentrss().update(**{providerObj.id: providerObj})
                else:
                    providerObj = sickrage.srCore.providersDict.torrentrss()[providerObj.id]

                # torrentrss provider settings
                providerObj.name = curName
                providerObj.urls['base_url'] = curURL
                providerObj.cookies = curCookies
                providerObj.curTitleTAG = curTitleTAG

        # dynamically load provider settings
        for providerID, providerObj in sickrage.srCore.providersDict.all().items():
            providerObj.minseed = int(str(getattr(kwargs, providerID + '_minseed', 0)).strip())
            providerObj.minleech = int(str(getattr(kwargs, providerID + '_minleech', 0)).strip())
            providerObj.ratio = str(getattr(kwargs, providerID + '_ratio', None)).strip()
            providerObj.digest = str(getattr(kwargs, providerID + '_digest', None)).strip()
            providerObj.hash = str(getattr(kwargs, providerID + '_hash', None)).strip()
            providerObj.api_key = str(getattr(kwargs, providerID + '_api_key', None)).strip()
            providerObj.username = str(getattr(kwargs, providerID + '_username', None)).strip()
            providerObj.password = str(getattr(kwargs, providerID + '_password', None)).strip()
            providerObj.passkey = str(getattr(kwargs, providerID + '_passkey', None)).strip()
            providerObj.pin = str(getattr(kwargs, providerID + '_pin', None)).strip()
            providerObj.confirmed = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_confirmed', 0))
            providerObj.ranked = sickrage.srCore.srConfig.checkbox_to_value(getattr(kwargs, providerID + '_ranked', 0))
            providerObj.engrelease = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_engrelease', 0))
            providerObj.onlyspasearch = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_onlyspasearch', 0))
            providerObj.sorting = str(getattr(kwargs, providerID + '_sorting', 'seeders')).strip()
            providerObj.freeleech = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_freeleech', 0))
            providerObj.search_mode = str(getattr(kwargs, providerID + '_search_mode', 'eponly')).strip()
            providerObj.search_fallback = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_search_fallback', 0))
            providerObj.enable_daily = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_enable_daily', 0))
            providerObj.enable_backlog = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_enable_backlog', 0))
            providerObj.cat = int(str(getattr(kwargs, providerID + '_cat', 0)).strip())
            providerObj.subtitle = sickrage.srCore.srConfig.checkbox_to_value(
                getattr(kwargs, providerID + '_subtitle', 0))

        # sort providers
        sickrage.srCore.providersDict.sort(re.findall(r'\w+[^\W\s]', provider_order))

        # save provider settings
        sickrage.srCore.srConfig.save()

        if len(results) > 0:
            for x in results:
                sickrage.srCore.srLogger.error(x)
            sickrage.srCore.srNotifications.error('Error(s) Saving Configuration',
                                                  '<br>\n'.join(results))
        else:
            sickrage.srCore.srNotifications.message('[PROVIDERS] Configuration Saved',
                                                    os.path.join(sickrage.CONFIG_FILE))

        return self.redirect("/config/providers/")


@Route('/config/notifications(/?.*)')
class ConfigNotifications(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigNotifications, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/notifications.mako",
            submenu=self.ConfigMenu(),
            title='Config - Notifications',
            header='Notifications',
            topmenu='config',
            controller='config',
            action='notifications'
        )

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

        sickrage.srCore.srConfig.USE_KODI = sickrage.srCore.srConfig.checkbox_to_value(use_kodi)
        sickrage.srCore.srConfig.KODI_ALWAYS_ON = sickrage.srCore.srConfig.checkbox_to_value(kodi_always_on)
        sickrage.srCore.srConfig.KODI_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(kodi_notify_onsnatch)
        sickrage.srCore.srConfig.KODI_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            kodi_notify_ondownload)
        sickrage.srCore.srConfig.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            kodi_notify_onsubtitledownload)
        sickrage.srCore.srConfig.KODI_UPDATE_LIBRARY = sickrage.srCore.srConfig.checkbox_to_value(kodi_update_library)
        sickrage.srCore.srConfig.KODI_UPDATE_FULL = sickrage.srCore.srConfig.checkbox_to_value(kodi_update_full)
        sickrage.srCore.srConfig.KODI_UPDATE_ONLYFIRST = sickrage.srCore.srConfig.checkbox_to_value(
            kodi_update_onlyfirst)
        sickrage.srCore.srConfig.KODI_HOST = sickrage.srCore.srConfig.clean_hosts(kodi_host)
        sickrage.srCore.srConfig.KODI_USERNAME = kodi_username
        sickrage.srCore.srConfig.KODI_PASSWORD = kodi_password

        sickrage.srCore.srConfig.USE_PLEX = sickrage.srCore.srConfig.checkbox_to_value(use_plex)
        sickrage.srCore.srConfig.PLEX_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(plex_notify_onsnatch)
        sickrage.srCore.srConfig.PLEX_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            plex_notify_ondownload)
        sickrage.srCore.srConfig.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            plex_notify_onsubtitledownload)
        sickrage.srCore.srConfig.PLEX_UPDATE_LIBRARY = sickrage.srCore.srConfig.checkbox_to_value(plex_update_library)
        sickrage.srCore.srConfig.PLEX_HOST = sickrage.srCore.srConfig.clean_hosts(plex_host)
        sickrage.srCore.srConfig.PLEX_SERVER_HOST = sickrage.srCore.srConfig.clean_hosts(plex_server_host)
        sickrage.srCore.srConfig.PLEX_SERVER_TOKEN = sickrage.srCore.srConfig.clean_host(plex_server_token)
        sickrage.srCore.srConfig.PLEX_USERNAME = plex_username
        sickrage.srCore.srConfig.PLEX_PASSWORD = plex_password
        sickrage.srCore.srConfig.USE_PLEX_CLIENT = sickrage.srCore.srConfig.checkbox_to_value(use_plex)
        sickrage.srCore.srConfig.PLEX_CLIENT_USERNAME = plex_username
        sickrage.srCore.srConfig.PLEX_CLIENT_PASSWORD = plex_password

        sickrage.srCore.srConfig.USE_EMBY = sickrage.srCore.srConfig.checkbox_to_value(use_emby)
        sickrage.srCore.srConfig.EMBY_HOST = sickrage.srCore.srConfig.clean_host(emby_host)
        sickrage.srCore.srConfig.EMBY_APIKEY = emby_apikey

        sickrage.srCore.srConfig.USE_GROWL = sickrage.srCore.srConfig.checkbox_to_value(use_growl)
        sickrage.srCore.srConfig.GROWL_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            growl_notify_onsnatch)
        sickrage.srCore.srConfig.GROWL_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            growl_notify_ondownload)
        sickrage.srCore.srConfig.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            growl_notify_onsubtitledownload)
        sickrage.srCore.srConfig.GROWL_HOST = sickrage.srCore.srConfig.clean_host(growl_host, default_port=23053)
        sickrage.srCore.srConfig.GROWL_PASSWORD = growl_password

        sickrage.srCore.srConfig.USE_FREEMOBILE = sickrage.srCore.srConfig.checkbox_to_value(use_freemobile)
        sickrage.srCore.srConfig.FREEMOBILE_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            freemobile_notify_onsnatch)
        sickrage.srCore.srConfig.FREEMOBILE_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            freemobile_notify_ondownload)
        sickrage.srCore.srConfig.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            freemobile_notify_onsubtitledownload)
        sickrage.srCore.srConfig.FREEMOBILE_ID = freemobile_id
        sickrage.srCore.srConfig.FREEMOBILE_APIKEY = freemobile_apikey

        sickrage.srCore.srConfig.USE_PROWL = sickrage.srCore.srConfig.checkbox_to_value(use_prowl)
        sickrage.srCore.srConfig.PROWL_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            prowl_notify_onsnatch)
        sickrage.srCore.srConfig.PROWL_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            prowl_notify_ondownload)
        sickrage.srCore.srConfig.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            prowl_notify_onsubtitledownload)
        sickrage.srCore.srConfig.PROWL_API = prowl_api
        sickrage.srCore.srConfig.PROWL_PRIORITY = prowl_priority

        sickrage.srCore.srConfig.USE_TWITTER = sickrage.srCore.srConfig.checkbox_to_value(use_twitter)
        sickrage.srCore.srConfig.TWITTER_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            twitter_notify_onsnatch)
        sickrage.srCore.srConfig.TWITTER_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            twitter_notify_ondownload)
        sickrage.srCore.srConfig.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            twitter_notify_onsubtitledownload)
        sickrage.srCore.srConfig.TWITTER_USEDM = sickrage.srCore.srConfig.checkbox_to_value(twitter_usedm)
        sickrage.srCore.srConfig.TWITTER_DMTO = twitter_dmto

        sickrage.srCore.srConfig.USE_BOXCAR = sickrage.srCore.srConfig.checkbox_to_value(use_boxcar)
        sickrage.srCore.srConfig.BOXCAR_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            boxcar_notify_onsnatch)
        sickrage.srCore.srConfig.BOXCAR_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            boxcar_notify_ondownload)
        sickrage.srCore.srConfig.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            boxcar_notify_onsubtitledownload)
        sickrage.srCore.srConfig.BOXCAR_USERNAME = boxcar_username

        sickrage.srCore.srConfig.USE_BOXCAR2 = sickrage.srCore.srConfig.checkbox_to_value(use_boxcar2)
        sickrage.srCore.srConfig.BOXCAR2_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            boxcar2_notify_onsnatch)
        sickrage.srCore.srConfig.BOXCAR2_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            boxcar2_notify_ondownload)
        sickrage.srCore.srConfig.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            boxcar2_notify_onsubtitledownload)
        sickrage.srCore.srConfig.BOXCAR2_ACCESSTOKEN = boxcar2_accesstoken

        sickrage.srCore.srConfig.USE_PUSHOVER = sickrage.srCore.srConfig.checkbox_to_value(use_pushover)
        sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            pushover_notify_onsnatch)
        sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pushover_notify_ondownload)
        sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pushover_notify_onsubtitledownload)
        sickrage.srCore.srConfig.PUSHOVER_USERKEY = pushover_userkey
        sickrage.srCore.srConfig.PUSHOVER_APIKEY = pushover_apikey
        sickrage.srCore.srConfig.PUSHOVER_DEVICE = pushover_device
        sickrage.srCore.srConfig.PUSHOVER_SOUND = pushover_sound

        sickrage.srCore.srConfig.USE_LIBNOTIFY = sickrage.srCore.srConfig.checkbox_to_value(use_libnotify)
        sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            libnotify_notify_onsnatch)
        sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            libnotify_notify_ondownload)
        sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            libnotify_notify_onsubtitledownload)

        sickrage.srCore.srConfig.USE_NMJ = sickrage.srCore.srConfig.checkbox_to_value(use_nmj)
        sickrage.srCore.srConfig.NMJ_HOST = sickrage.srCore.srConfig.clean_host(nmj_host)
        sickrage.srCore.srConfig.NMJ_DATABASE = nmj_database
        sickrage.srCore.srConfig.NMJ_MOUNT = nmj_mount

        sickrage.srCore.srConfig.USE_NMJv2 = sickrage.srCore.srConfig.checkbox_to_value(use_nmjv2)
        sickrage.srCore.srConfig.NMJv2_HOST = sickrage.srCore.srConfig.clean_host(nmjv2_host)
        sickrage.srCore.srConfig.NMJv2_DATABASE = nmjv2_database
        sickrage.srCore.srConfig.NMJv2_DBLOC = nmjv2_dbloc

        sickrage.srCore.srConfig.USE_SYNOINDEX = sickrage.srCore.srConfig.checkbox_to_value(use_synoindex)

        sickrage.srCore.srConfig.USE_SYNOLOGYNOTIFIER = sickrage.srCore.srConfig.checkbox_to_value(use_synologynotifier)
        sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            synologynotifier_notify_onsnatch)
        sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            synologynotifier_notify_ondownload)
        sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            synologynotifier_notify_onsubtitledownload)

        sickrage.srCore.srConfig.change_use_trakt(use_trakt)
        sickrage.srCore.srConfig.TRAKT_USERNAME = trakt_username
        sickrage.srCore.srConfig.TRAKT_REMOVE_WATCHLIST = sickrage.srCore.srConfig.checkbox_to_value(
            trakt_remove_watchlist)
        sickrage.srCore.srConfig.TRAKT_REMOVE_SERIESLIST = sickrage.srCore.srConfig.checkbox_to_value(
            trakt_remove_serieslist)
        sickrage.srCore.srConfig.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = sickrage.srCore.srConfig.checkbox_to_value(
            trakt_remove_show_from_sickrage)
        sickrage.srCore.srConfig.TRAKT_SYNC_WATCHLIST = sickrage.srCore.srConfig.checkbox_to_value(trakt_sync_watchlist)
        sickrage.srCore.srConfig.TRAKT_METHOD_ADD = int(trakt_method_add)
        sickrage.srCore.srConfig.TRAKT_START_PAUSED = sickrage.srCore.srConfig.checkbox_to_value(trakt_start_paused)
        sickrage.srCore.srConfig.TRAKT_USE_RECOMMENDED = sickrage.srCore.srConfig.checkbox_to_value(
            trakt_use_recommended)
        sickrage.srCore.srConfig.TRAKT_SYNC = sickrage.srCore.srConfig.checkbox_to_value(trakt_sync)
        sickrage.srCore.srConfig.TRAKT_SYNC_REMOVE = sickrage.srCore.srConfig.checkbox_to_value(trakt_sync_remove)
        sickrage.srCore.srConfig.TRAKT_DEFAULT_INDEXER = int(trakt_default_indexer)
        sickrage.srCore.srConfig.TRAKT_TIMEOUT = int(trakt_timeout)
        sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME = trakt_blacklist_name

        sickrage.srCore.srConfig.USE_EMAIL = sickrage.srCore.srConfig.checkbox_to_value(use_email)
        sickrage.srCore.srConfig.EMAIL_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            email_notify_onsnatch)
        sickrage.srCore.srConfig.EMAIL_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            email_notify_ondownload)
        sickrage.srCore.srConfig.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            email_notify_onsubtitledownload)
        sickrage.srCore.srConfig.EMAIL_HOST = sickrage.srCore.srConfig.clean_host(email_host)
        sickrage.srCore.srConfig.EMAIL_PORT = sickrage.srCore.srConfig.to_int(email_port, default=25)
        sickrage.srCore.srConfig.EMAIL_FROM = email_from
        sickrage.srCore.srConfig.EMAIL_TLS = sickrage.srCore.srConfig.checkbox_to_value(email_tls)
        sickrage.srCore.srConfig.EMAIL_USER = email_user
        sickrage.srCore.srConfig.EMAIL_PASSWORD = email_password
        sickrage.srCore.srConfig.EMAIL_LIST = email_list

        sickrage.srCore.srConfig.USE_PYTIVO = sickrage.srCore.srConfig.checkbox_to_value(use_pytivo)
        sickrage.srCore.srConfig.PYTIVO_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            pytivo_notify_onsnatch)
        sickrage.srCore.srConfig.PYTIVO_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pytivo_notify_ondownload)
        sickrage.srCore.srConfig.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pytivo_notify_onsubtitledownload)
        sickrage.srCore.srConfig.PYTIVO_UPDATE_LIBRARY = sickrage.srCore.srConfig.checkbox_to_value(
            pytivo_update_library)
        sickrage.srCore.srConfig.PYTIVO_HOST = sickrage.srCore.srConfig.clean_host(pytivo_host)
        sickrage.srCore.srConfig.PYTIVO_SHARE_NAME = pytivo_share_name
        sickrage.srCore.srConfig.PYTIVO_TIVO_NAME = pytivo_tivo_name

        sickrage.srCore.srConfig.USE_NMA = sickrage.srCore.srConfig.checkbox_to_value(use_nma)
        sickrage.srCore.srConfig.NMA_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(nma_notify_onsnatch)
        sickrage.srCore.srConfig.NMA_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            nma_notify_ondownload)
        sickrage.srCore.srConfig.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            nma_notify_onsubtitledownload)
        sickrage.srCore.srConfig.NMA_API = nma_api
        sickrage.srCore.srConfig.NMA_PRIORITY = nma_priority

        sickrage.srCore.srConfig.USE_PUSHALOT = sickrage.srCore.srConfig.checkbox_to_value(use_pushalot)
        sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            pushalot_notify_onsnatch)
        sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pushalot_notify_ondownload)
        sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pushalot_notify_onsubtitledownload)
        sickrage.srCore.srConfig.PUSHALOT_AUTHORIZATIONTOKEN = pushalot_authorizationtoken

        sickrage.srCore.srConfig.USE_PUSHBULLET = sickrage.srCore.srConfig.checkbox_to_value(use_pushbullet)
        sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONSNATCH = sickrage.srCore.srConfig.checkbox_to_value(
            pushbullet_notify_onsnatch)
        sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pushbullet_notify_ondownload)
        sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = sickrage.srCore.srConfig.checkbox_to_value(
            pushbullet_notify_onsubtitledownload)
        sickrage.srCore.srConfig.PUSHBULLET_API = pushbullet_api
        sickrage.srCore.srConfig.PUSHBULLET_DEVICE = pushbullet_device_list

        sickrage.srCore.srConfig.save()

        if len(results) > 0:
            for x in results:
                sickrage.srCore.srLogger.error(x)
            sickrage.srCore.srNotifications.error('Error(s) Saving Configuration',
                                                  '<br>\n'.join(results))
        else:
            sickrage.srCore.srNotifications.message('[NOTIFICATIONS] Configuration Saved',
                                                    os.path.join(sickrage.CONFIG_FILE))

        return self.redirect("/config/notifications/")


@Route('/config/subtitles(/?.*)')
class ConfigSubtitles(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSubtitles, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/subtitles.mako",
            submenu=self.ConfigMenu(),
            title='Config - Subtitles',
            header='Subtitles',
            topmenu='config',
            controller='config',
            action='subtitles'
        )

    def saveSubtitles(self, use_subtitles=None, subtitles_plugins=None, subtitles_languages=None, subtitles_dir=None,
                      service_order=None, subtitles_history=None, subtitles_finder_frequency=None,
                      subtitles_multi=None, embedded_subtitles_all=None, subtitles_extra_scripts=None,
                      subtitles_hearing_impaired=None,
                      addic7ed_user=None, addic7ed_pass=None, legendastv_user=None, legendastv_pass=None,
                      opensubtitles_user=None, opensubtitles_pass=None):

        results = []

        sickrage.srCore.srConfig.change_subtitle_searcher_freq(subtitles_finder_frequency)
        sickrage.srCore.srConfig.change_use_subtitles(use_subtitles)

        sickrage.srCore.srConfig.SUBTITLES_LANGUAGES = [lang.strip() for lang in subtitles_languages.split(',') if
                                                        subtitle_searcher.isValidLanguage(
                                                            lang.strip())] if subtitles_languages else []
        sickrage.srCore.srConfig.SUBTITLES_DIR = subtitles_dir
        sickrage.srCore.srConfig.SUBTITLES_HISTORY = sickrage.srCore.srConfig.checkbox_to_value(subtitles_history)
        sickrage.srCore.srConfig.EMBEDDED_SUBTITLES_ALL = sickrage.srCore.srConfig.checkbox_to_value(
            embedded_subtitles_all)
        sickrage.srCore.srConfig.SUBTITLES_HEARING_IMPAIRED = sickrage.srCore.srConfig.checkbox_to_value(
            subtitles_hearing_impaired)
        sickrage.srCore.srConfig.SUBTITLES_MULTI = sickrage.srCore.srConfig.checkbox_to_value(subtitles_multi)
        sickrage.srCore.srConfig.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in subtitles_extra_scripts.split('|') if
                                                            x.strip()]

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            curService, curEnabled = curServiceStr.split(':')
            subtitles_services_list.append(curService)
            subtitles_services_enabled.append(int(curEnabled))

        sickrage.srCore.srConfig.SUBTITLES_SERVICES_LIST = subtitles_services_list
        sickrage.srCore.srConfig.SUBTITLES_SERVICES_ENABLED = subtitles_services_enabled

        sickrage.srCore.srConfig.ADDIC7ED_USER = addic7ed_user or ''
        sickrage.srCore.srConfig.ADDIC7ED_PASS = addic7ed_pass or ''
        sickrage.srCore.srConfig.LEGENDASTV_USER = legendastv_user or ''
        sickrage.srCore.srConfig.LEGENDASTV_PASS = legendastv_pass or ''
        sickrage.srCore.srConfig.OPENSUBTITLES_USER = opensubtitles_user or ''
        sickrage.srCore.srConfig.OPENSUBTITLES_PASS = opensubtitles_pass or ''

        sickrage.srCore.srConfig.save()

        if len(results) > 0:
            for x in results:
                sickrage.srCore.srLogger.error(x)
            sickrage.srCore.srNotifications.error('Error(s) Saving Configuration',
                                                  '<br>\n'.join(results))
        else:
            sickrage.srCore.srNotifications.message('[SUBTITLES] Configuration Saved',
                                                    os.path.join(sickrage.CONFIG_FILE))

        return self.redirect("/config/subtitles/")


@Route('/config/anime(/?.*)')
class ConfigAnime(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigAnime, self).__init__(*args, **kwargs)

    def index(self):
        return self.render(
            "/config/anime.mako",
            submenu=self.ConfigMenu(),
            title='Config - Anime',
            header='Anime',
            topmenu='config',
            controller='config',
            action='anime'
        )

    def saveAnime(self, use_anidb=None, anidb_username=None, anidb_password=None, anidb_use_mylist=None,
                  split_home=None):

        results = []

        sickrage.srCore.srConfig.USE_ANIDB = sickrage.srCore.srConfig.checkbox_to_value(use_anidb)
        sickrage.srCore.srConfig.ANIDB_USERNAME = anidb_username
        sickrage.srCore.srConfig.ANIDB_PASSWORD = anidb_password
        sickrage.srCore.srConfig.ANIDB_USE_MYLIST = sickrage.srCore.srConfig.checkbox_to_value(anidb_use_mylist)
        sickrage.srCore.srConfig.ANIME_SPLIT_HOME = sickrage.srCore.srConfig.checkbox_to_value(split_home)

        sickrage.srCore.srConfig.save()

        if len(results) > 0:
            for x in results:
                sickrage.srCore.srLogger.error(x)
            sickrage.srCore.srNotifications.error('Error(s) Saving Configuration',
                                                  '<br>\n'.join(results))
        else:
            sickrage.srCore.srNotifications.message('[ANIME] Configuration Saved', os.path.join(sickrage.CONFIG_FILE))

        return self.redirect("/config/anime/")


@Route('/logs(/?.*)')
class Logs(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Logs, self).__init__(*args, **kwargs)

    def LogsMenu(self, level):
        menu = [
            {'title': 'Clear Errors', 'path': '/logs/clearerrors/',
             'requires': self.haveErrors() and level == sickrage.srCore.srLogger.ERROR,
             'icon': 'ui-icon ui-icon-trash'},
            {'title': 'Clear Warnings', 'path': '/logs/clearerrors/?level=' + str(sickrage.srCore.srLogger.WARNING),
             'requires': self.haveWarnings() and level == sickrage.srCore.srLogger.WARNING,
             'icon': 'ui-icon ui-icon-trash'},
        ]

        return menu

    def index(self, level=None):
        level = int(level or sickrage.srCore.srLogger.ERROR)
        return self.render(
            "/logs/errors.mako",
            header="Logs &amp; Errors",
            title="Logs &amp; Errors",
            topmenu="system",
            submenu=self.LogsMenu(level),
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

    def clearerrors(self, level=None):
        if int(level or sickrage.srCore.srLogger.ERROR) == sickrage.srCore.srLogger.WARNING:
            WarningViewer.clear()
        else:
            ErrorViewer.clear()

        return self.redirect("/logs/viewlog/")

    def viewlog(self, minLevel=None, logFilter='', logSearch='', maxLines=500):
        minLevel = minLevel or sickrage.srCore.srLogger.INFO

        logFiles = [sickrage.srCore.srConfig.LOG_FILE] + ["{}.{}".format(sickrage.srCore.srConfig.LOG_FILE, x) for x in
                                                          xrange(int(sickrage.srCore.srConfig.LOG_NR))]

        levelsFiltered = b'|'.join(
            [x for x in sickrage.srCore.srLogger.logLevels.keys() if
             sickrage.srCore.srLogger.logLevels[x] >= int(minLevel)])

        logRegex = re.compile(
            r"(?P<entry>^\d+\-\d+\-\d+\s+\d+\:\d+\:\d+\s+(?:{})[\s\S]+?(?:{})[\s\S]+?$)".format(levelsFiltered,
                                                                                                logFilter),
            re.S + re.M)

        data = []
        try:
            for logFile in [x for x in logFiles if os.path.isfile(x)]:
                data += list(reversed(re.findall("((?:^.+?{}.+?$))".format(logSearch),
                                                 "\n".join(next(readFileBuffered(logFile, reverse=True)).splitlines()),
                                                 re.S + re.M + re.I)))
                maxLines -= len(data)
                if len(data) == maxLines:
                    raise StopIteration

        except StopIteration:
            pass
        except Exception as e:
            pass

        return self.render(
            "/logs/view.mako",
            header="Log File",
            title="Logs",
            topmenu="system",
            logLines="\n".join(logRegex.findall("\n".join(data))),
            minLevel=int(minLevel),
            logNameFilters=sickrage.srCore.srLogger.logNameFilters,
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
