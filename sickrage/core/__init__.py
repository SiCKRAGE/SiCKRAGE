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
import locale
import logging
import os
import platform
import re
import shutil
import socket
import sys
import threading
import traceback
import uuid
from collections import deque
from urllib.parse import uses_netloc
from urllib.request import FancyURLopener

import rarfile
import sentry_sdk
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dateutil import tz
from fake_useragent import UserAgent
from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
from tornado.ioloop import IOLoop, PeriodicCallback

import sickrage
from sickrage.core.amqp.consumer import AMQPConsumer
from sickrage.core.announcements import Announcements
from sickrage.core.api import API
from sickrage.core.auth import AuthServer
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.config import Config
from sickrage.core.config.helpers import change_gui_lang
from sickrage.core.databases.cache import CacheDB
from sickrage.core.databases.config import ConfigDB, CustomStringEncryptedType
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import MultiEpNaming, DefaultHomePage, NzbMethod, TorrentMethod, CheckPropersInterval
from sickrage.core.helpers import generate_secret, make_dir, restore_app_data, get_disk_space_usage, get_free_space, launch_browser, torrent_webui_url, \
    encryption, md5_file_hash, flatten, get_internal_ip
from sickrage.core.logger import Logger
from sickrage.core.nameparser.validator import check_force_season_folders
from sickrage.core.processors import auto_postprocessor
from sickrage.core.processors.auto_postprocessor import AutoPostProcessor
from sickrage.core.queues.postprocessor import PostProcessorQueue
from sickrage.core.queues.search import SearchQueue
from sickrage.core.queues.show import ShowQueue
from sickrage.core.searchers.backlog_searcher import BacklogSearcher
from sickrage.core.searchers.daily_searcher import DailySearcher
from sickrage.core.searchers.failed_snatch_searcher import FailedSnatchSearcher
from sickrage.core.searchers.proper_searcher import ProperSearcher
from sickrage.core.searchers.subtitle_searcher import SubtitleSearcher
from sickrage.core.searchers.trakt_searcher import TraktSearcher
from sickrage.core.tv.show import TVShow
from sickrage.core.tv.show.helpers import get_show_list
from sickrage.core.ui import Notifications
from sickrage.core.updaters.rsscache_updater import RSSCacheUpdater
from sickrage.core.updaters.show_updater import ShowUpdater
from sickrage.core.updaters.tz_updater import TimeZoneUpdater
from sickrage.core.upnp import UPNPClient
from sickrage.core.version_updater import VersionUpdater, SourceUpdateManager
from sickrage.core.webserver import WebServer
from sickrage.core.websocket import check_web_socket_queue
from sickrage.metadata_providers import MetadataProviders
from sickrage.notification_providers import NotificationProviders
from sickrage.search_providers import SearchProviders
from sickrage.series_providers import SeriesProviders


class Core(object):
    def __init__(self):
        self.started = False
        self.loading_shows = False
        self.daemon = None
        self.pid = os.getpid()

        self.gui_static_dir = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'static')
        self.gui_views_dir = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'views')
        self.gui_app_dir = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'app')

        self.https_cert_file = None
        self.https_key_file = None

        self.trakt_api_key = '5c65f55e11d48c35385d9e8670615763a605fad28374c8ae553a7b7a50651ddd'
        self.trakt_api_secret = 'b53e32045ac122a445ef163e6d859403301ffe9b17fb8321d428531b69022a82'
        self.trakt_app_id = '4562'

        self.fanart_api_key = '9b3afaf26f6241bdb57d6cc6bd798da7'

        self.git_remote = "origin"
        self.git_remote_url = "https://git.sickrage.ca/SiCKRAGE/sickrage"

        self.unrar_tool = rarfile.UNRAR_TOOL

        self.naming_force_folders = False

        self.min_auto_postprocessor_freq = 1
        self.min_daily_searcher_freq = 10
        self.min_backlog_searcher_freq = 10
        self.min_version_updater_freq = 1
        self.min_subtitle_searcher_freq = 1
        self.min_failed_snatch_age = 1

        try:
            self.tz = tz.tzwinlocal() if tz.tzwinlocal else tz.tzlocal()
        except Exception:
            self.tz = tz.tzlocal()

        self.shows = {}
        self.shows_recent = deque(maxlen=5)

        self.main_db = None
        self.cache_db = None

        self.config_file = None
        self.data_dir = None
        self.cache_dir = None
        self.quiet = None
        self.no_launch = None
        self.disable_updates = None
        self.web_port = None
        self.web_host = None
        self.web_root = None
        self.developer = None
        self.db_type = None
        self.db_prefix = None
        self.db_host = None
        self.db_port = None
        self.db_username = None
        self.db_password = None
        self.debug = None
        self.latest_version_string = None

        self.naming_ep_type = (
            "%(seasonnumber)dx%(episodenumber)02d",
            "s%(seasonnumber)02de%(episodenumber)02d",
            "S%(seasonnumber)02dE%(episodenumber)02d",
            "%(seasonnumber)02dx%(episodenumber)02d",
            "S%(seasonnumber)02d E%(episodenumber)02d"
        )

        self.sports_ep_type = (
            "%(seasonnumber)dx%(episodenumber)02d",
            "s%(seasonnumber)02de%(episodenumber)02d",
            "S%(seasonnumber)02dE%(episodenumber)02d",
            "%(seasonnumber)02dx%(episodenumber)02d",
            "S%(seasonnumber)02 dE%(episodenumber)02d"
        )

        self.naming_ep_type_text = (
            "1x02",
            "s01e02",
            "S01E02",
            "01x02",
            "S01 E02"
        )

        self.naming_multi_ep_type = {
            0: ["-%(episodenumber)02d"] * len(self.naming_ep_type),
            1: [" - " + x for x in self.naming_ep_type],
            2: [x + "%(episodenumber)02d" for x in ("x", "e", "E", "x")]
        }

        self.naming_multi_ep_type_text = (
            "extend",
            "duplicate",
            "repeat"
        )

        self.naming_sep_type = (
            " - ",
            " "
        )

        self.naming_sep_type_text = (
            " - ",
            "space"
        )

        self.user_agent = 'SiCKRAGE.CE.1/({};{};{})'.format(platform.system(), platform.release(), str(uuid.uuid1()))
        self.languages = [language for language in os.listdir(sickrage.LOCALE_DIR) if '_' in language]
        self.client_web_urls = {'torrent': '', 'newznab': ''}

        self.notification_providers = {}
        self.metadata_providers = {}
        self.search_providers = {}
        self.series_providers = {}

        self.adba_connection = None
        self.log = None
        self.config = None
        self.alerts = None
        self.scheduler = None
        self.wserver = None
        self.google_auth = None
        self.show_queue = None
        self.search_queue = None
        self.postprocessor_queue = None
        self.version_updater = None
        self.show_updater = None
        self.tz_updater = None
        self.rsscache_updater = None
        self.daily_searcher = None
        self.failed_snatch_searcher = None
        self.backlog_searcher = None
        self.proper_searcher = None
        self.trakt_searcher = None
        self.subtitle_searcher = None
        self.auto_postprocessor = None
        self.upnp_client = None
        self.auth_server = None
        self.announcements = None
        self.api = None
        self.amqp_consumer = None

    def start(self):
        self.started = True

        # thread name
        threading.currentThread().setName('CORE')

        # init sentry
        self.init_sentry()

        # scheduler
        self.scheduler = TornadoScheduler({'apscheduler.timezone': 'UTC'})

        # init core classes
        self.api = API()
        self.config = Config(self.db_type, self.db_prefix, self.db_host, self.db_port, self.db_username, self.db_password)
        self.main_db = MainDB(self.db_type, self.db_prefix, self.db_host, self.db_port, self.db_username, self.db_password)
        self.cache_db = CacheDB(self.db_type, self.db_prefix, self.db_host, self.db_port, self.db_username, self.db_password)
        self.notification_providers = NotificationProviders()
        self.metadata_providers = MetadataProviders()
        self.search_providers = SearchProviders()
        self.series_providers = SeriesProviders()
        self.log = Logger()
        self.alerts = Notifications()
        self.wserver = WebServer()
        self.show_queue = ShowQueue()
        self.search_queue = SearchQueue()
        self.postprocessor_queue = PostProcessorQueue()
        self.version_updater = VersionUpdater()
        self.show_updater = ShowUpdater()
        self.tz_updater = TimeZoneUpdater()
        self.rsscache_updater = RSSCacheUpdater()
        self.daily_searcher = DailySearcher()
        self.failed_snatch_searcher = FailedSnatchSearcher()
        self.backlog_searcher = BacklogSearcher()
        self.proper_searcher = ProperSearcher()
        self.trakt_searcher = TraktSearcher()
        self.subtitle_searcher = SubtitleSearcher()
        self.auto_postprocessor = AutoPostProcessor()
        self.upnp_client = UPNPClient()
        self.announcements = Announcements()
        self.amqp_consumer = AMQPConsumer()

        # authorization sso client
        self.auth_server = AuthServer()

        # check available space
        try:
            self.log.info("Performing disk space checks")
            total_space, available_space = get_free_space(self.data_dir)
            if available_space < 100:
                self.log.warning('Shutting down as SiCKRAGE needs some space to work. You\'ll get corrupted data otherwise. Only %sMB left', available_space)
                return
        except Exception:
            self.log.error('Failed getting disk space: %s', traceback.format_exc())

        # check if we need to perform a restore first
        if os.path.exists(os.path.abspath(os.path.join(self.data_dir, 'restore'))):
            self.log.info('Performing restore of backup files')
            success = restore_app_data(os.path.abspath(os.path.join(self.data_dir, 'restore')), self.data_dir)
            self.log.info("Restoring SiCKRAGE backup: %s!" % ("FAILED", "SUCCESSFUL")[success])
            if success:
                # remove restore files
                shutil.rmtree(os.path.abspath(os.path.join(self.data_dir, 'restore')), ignore_errors=True)

        # migrate old database file names to new ones
        if os.path.isfile(os.path.abspath(os.path.join(self.data_dir, 'sickbeard.db'))):
            if os.path.isfile(os.path.join(self.data_dir, 'sickrage.db')):
                helpers.move_file(os.path.join(self.data_dir, 'sickrage.db'),
                                  os.path.join(self.data_dir, '{}.bak-{}'
                                               .format('sickrage.db',
                                                       datetime.datetime.now().strftime(
                                                           '%Y%m%d_%H%M%S'))))

            helpers.move_file(os.path.abspath(os.path.join(self.data_dir, 'sickbeard.db')),
                              os.path.abspath(os.path.join(self.data_dir, 'sickrage.db')))

        # setup databases
        self.main_db.setup()
        self.config.db.setup()
        self.cache_db.setup()

        # load config
        self.config.load()

        # migrate config
        self.config.migrate_config_file(self.config_file)

        # add server id tag to sentry
        sentry_sdk.set_tag('server_id', self.config.general.server_id)

        # add user to sentry
        sentry_sdk.set_user({
            'id': self.config.user.sub_id,
            'username': self.config.user.username,
            'email': self.config.user.email
        })

        # config overrides
        if self.web_port:
            self.config.general.web_port = self.web_port
        if self.web_root:
            self.config.general.web_root = self.web_root

        # set language
        change_gui_lang(self.config.gui.gui_lang)

        # set socket timeout
        socket.setdefaulttimeout(self.config.general.socket_timeout)

        # set ssl cert/key filenames
        self.https_cert_file = os.path.abspath(os.path.join(self.data_dir, 'server.crt'))
        self.https_key_file = os.path.abspath(os.path.join(self.data_dir, 'server.key'))

        # setup logger settings
        self.log.logSize = self.config.general.log_size
        self.log.logNr = self.config.general.log_nr
        self.log.logFile = os.path.join(self.data_dir, 'logs', 'sickrage.log')
        self.log.debugLogging = self.debug or self.config.general.debug
        self.log.consoleLogging = not self.quiet

        # start logger
        self.log.start()

        # user agent
        if self.config.general.random_user_agent:
            self.user_agent = UserAgent().random

        uses_netloc.append('scgi')
        FancyURLopener.version = self.user_agent

        # set torrent client web url
        torrent_webui_url(True)

        if self.config.general.default_page not in DefaultHomePage:
            self.config.general.default_page = DefaultHomePage.HOME

        # attempt to help prevent users from breaking links by using a bad url
        if not self.config.general.anon_redirect.endswith('?'):
            self.config.general.anon_redirect = ''

        if not re.match(r'\d+\|[^|]+(?:\|[^|]+)*', self.config.general.root_dirs):
            self.config.general.root_dirs = ''

        self.naming_force_folders = check_force_season_folders()

        if self.config.general.nzb_method not in NzbMethod:
            self.config.general.nzb_method = NzbMethod.BLACKHOLE

        if self.config.general.torrent_method not in TorrentMethod:
            self.config.general.torrent_method = TorrentMethod.BLACKHOLE

        if self.config.general.auto_postprocessor_freq < self.min_auto_postprocessor_freq:
            self.config.general.auto_postprocessor_freq = self.min_auto_postprocessor_freq

        if self.config.general.daily_searcher_freq < self.min_daily_searcher_freq:
            self.config.general.daily_searcher_freq = self.min_daily_searcher_freq

        if self.config.general.backlog_searcher_freq < self.min_backlog_searcher_freq:
            self.config.general.backlog_searcher_freq = self.min_backlog_searcher_freq

        if self.config.general.version_updater_freq < self.min_version_updater_freq:
            self.config.general.version_updater_freq = self.min_version_updater_freq

        if self.config.general.subtitle_searcher_freq < self.min_subtitle_searcher_freq:
            self.config.general.subtitle_searcher_freq = self.min_subtitle_searcher_freq

        if self.config.failed_snatches.age < self.min_failed_snatch_age:
            self.config.failed_snatches.age = self.min_failed_snatch_age

        if self.config.general.proper_searcher_interval not in CheckPropersInterval:
            self.config.general.proper_searcher_interval = CheckPropersInterval.DAILY

        if self.config.general.show_update_hour < 0 or self.config.general.show_update_hour > 23:
            self.config.general.show_update_hour = 0

        # add app updater job
        self.scheduler.add_job(
            self.version_updater.task,
            IntervalTrigger(
                hours=1,
                start_date=datetime.datetime.now() + datetime.timedelta(minutes=4),
                timezone='utc'
            ),
            name=self.version_updater.name,
            id=self.version_updater.name
        )

        # add show updater job
        self.scheduler.add_job(
            self.show_updater.task,
            IntervalTrigger(
                days=1,
                start_date=datetime.datetime.now().replace(hour=self.config.general.show_update_hour),
                timezone='utc'
            ),
            name=self.show_updater.name,
            id=self.show_updater.name
        )

        # add rss cache updater job
        self.scheduler.add_job(
            self.rsscache_updater.task,
            IntervalTrigger(
                minutes=15,
                timezone='utc'
            ),
            name=self.rsscache_updater.name,
            id=self.rsscache_updater.name
        )

        # add daily search job
        self.scheduler.add_job(
            self.daily_searcher.task,
            IntervalTrigger(
                minutes=self.config.general.daily_searcher_freq,
                start_date=datetime.datetime.now() + datetime.timedelta(minutes=4),
                timezone='utc'
            ),
            name=self.daily_searcher.name,
            id=self.daily_searcher.name
        )

        # add failed snatch search job
        self.scheduler.add_job(
            self.failed_snatch_searcher.task,
            IntervalTrigger(
                hours=1,
                start_date=datetime.datetime.now() + datetime.timedelta(minutes=4),
                timezone='utc'
            ),
            name=self.failed_snatch_searcher.name,
            id=self.failed_snatch_searcher.name
        )

        # add backlog search job
        self.scheduler.add_job(
            self.backlog_searcher.task,
            IntervalTrigger(
                minutes=self.config.general.backlog_searcher_freq,
                start_date=datetime.datetime.now() + datetime.timedelta(minutes=30),
                timezone='utc'
            ),
            name=self.backlog_searcher.name,
            id=self.backlog_searcher.name
        )

        # add auto-postprocessing job
        self.scheduler.add_job(
            self.auto_postprocessor.task,
            IntervalTrigger(
                minutes=self.config.general.auto_postprocessor_freq,
                timezone='utc'
            ),
            name=self.auto_postprocessor.name,
            id=self.auto_postprocessor.name
        )

        # add find proper job
        self.scheduler.add_job(
            self.proper_searcher.task,
            IntervalTrigger(minutes=self.config.general.proper_searcher_interval.value, timezone='utc'),
            name=self.proper_searcher.name,
            id=self.proper_searcher.name
        )

        # add trakt.tv checker job
        self.scheduler.add_job(
            self.trakt_searcher.task,
            IntervalTrigger(
                hours=1,
                timezone='utc'
            ),
            name=self.trakt_searcher.name,
            id=self.trakt_searcher.name
        )

        # add subtitles finder job
        self.scheduler.add_job(
            self.subtitle_searcher.task,
            IntervalTrigger(
                hours=self.config.general.subtitle_searcher_freq,
                timezone='utc'
            ),
            name=self.subtitle_searcher.name,
            id=self.subtitle_searcher.name
        )

        # add upnp client job
        self.scheduler.add_job(
            self.upnp_client.task,
            IntervalTrigger(
                seconds=self.upnp_client._nat_portmap_lifetime,
                timezone='utc'
            ),
            name=self.upnp_client.name,
            id=self.upnp_client.name
        )

        # start queues
        self.search_queue.start_worker(self.config.general.max_queue_workers)
        self.show_queue.start_worker(self.config.general.max_queue_workers)
        self.postprocessor_queue.start_worker(self.config.general.max_queue_workers)

        # start web server
        self.wserver.start()

        # start scheduler service
        self.scheduler.start()

        # perform server checkup
        IOLoop.current().add_callback(self.server_checkup)

        # load shows
        IOLoop.current().add_callback(self.load_shows)

        # load network timezones
        IOLoop.current().spawn_callback(self.tz_updater.update_network_timezones)

        # load search provider urls
        IOLoop.current().spawn_callback(self.search_providers.update_urls)

        # startup message
        IOLoop.current().add_callback(self.startup_message)

        # launch browser
        IOLoop.current().add_callback(self.launch_browser)

        # watch websocket message queue
        PeriodicCallback(check_web_socket_queue, 100).start()

        # perform server checkups every hour
        PeriodicCallback(self.server_checkup, 1 * 60 * 60 * 1000).start()

        # perform shutdown trigger check every 5 seconds
        PeriodicCallback(self.shutdown_trigger, 5 * 1000).start()

        # start ioloop
        IOLoop.current().start()

    def init_sentry(self):
        # sentry log handler
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )

        # init sentry logging
        sentry_sdk.init(
            dsn="https://d4bf4ed225c946c8972c7238ad07d124@sentry.sickrage.ca/2?verify_ssl=0",
            integrations=[sentry_logging],
            release=sickrage.version(),
            environment=('master', 'develop')['dev' in sickrage.version()],
            ignore_errors=[
                'KeyboardInterrupt',
                'PermissionError',
                'FileNotFoundError',
                'EpisodeNotFoundException'
            ]
        )

        # sentry tags
        sentry_tags = {
            'platform': platform.platform(),
            'locale': repr(locale.getdefaultlocale()),
            'python': platform.python_version(),
            'install_type': sickrage.install_type()
        }

        # set sentry tags
        for tag_key, tag_value in sentry_tags.items():
            sentry_sdk.set_tag(tag_key, tag_value)

        # set loggers to ignore
        ignored_loggers = [
            'enzyme.parsers.ebml.core',
            'subliminal.core',
            'subliminal.utils',
            'subliminal.refiners.tvdb',
            'subliminal.refiners.metadata',
            'subliminal.providers.tvsubtitles',
            'pika.connection',
            'pika.adapters.base_connection',
            'pika.adapters.utils.io_services_utils',
            'pika.adapters.utils.connection_workflow',
            'pika.adapters.utils.selector_ioloop_adapter'
        ]

        for item in ignored_loggers:
            ignore_logger(item)

    def server_checkup(self):
        if self.config.general.server_id:
            server_status = self.api.server.get_status(self.config.general.server_id)
            if server_status and not server_status['registered']:
                # re-register server
                server_id = self.api.server.register_server(
                    ip_addresses=','.join([get_internal_ip()]),
                    web_protocol=('http', 'https')[self.config.general.enable_https],
                    web_port=self.config.general.web_port,
                    web_root=self.config.general.web_root,
                    server_version=sickrage.version(),
                )

                if server_id:
                    self.log.info('Re-registered SiCKRAGE server with SiCKRAGE API')
                    sentry_sdk.set_tag('server_id', self.config.general.server_id)
                    self.config.general.server_id = server_id
                    self.config.save(mark_dirty=True)
            else:
                self.log.debug('Updating SiCKRAGE server data on SiCKRAGE API')

                # update server information
                self.api.server.update_server(
                    server_id=self.config.general.server_id,
                    ip_addresses=','.join([get_internal_ip()]),
                    web_protocol=('http', 'https')[self.config.general.enable_https],
                    web_port=self.config.general.web_port,
                    web_root=self.config.general.web_root,
                    server_version=sickrage.version(),
                )

    def load_shows(self):
        threading.currentThread().setName('CORE')

        session = self.main_db.session()

        self.log.info('Loading initial shows list')

        self.loading_shows = True

        self.shows = {}
        for query in session.query(MainDB.TVShow).with_entities(MainDB.TVShow.series_id, MainDB.TVShow.series_provider_id, MainDB.TVShow.name,
                                                                MainDB.TVShow.location):
            try:
                # if not os.path.isdir(query.location) and self.config.general.create_missing_show_dirs:
                #     make_dir(query.location)

                self.log.info('Loading show {}'.format(query.name))
                self.shows.update({(query.series_id, query.series_provider_id): TVShow(query.series_id, query.series_provider_id)})
            except Exception as e:
                self.log.debug('There was an error loading show: {}'.format(query.name))

        self.loading_shows = False

        self.log.info('Loading initial shows list finished')

    def startup_message(self):
        self.log.info("SiCKRAGE :: STARTED")
        self.log.info(f"SiCKRAGE :: APP VERSION:[{sickrage.version()}]")
        self.log.info(f"SiCKRAGE :: CONFIG VERSION:[v{self.config.db.version}]")
        self.log.info(f"SiCKRAGE :: DATABASE VERSION:[v{self.main_db.version}]")
        self.log.info(f"SiCKRAGE :: DATABASE TYPE:[{self.db_type}]")
        self.log.info(f"SiCKRAGE :: INSTALL TYPE:[{self.version_updater.updater.type}]")
        self.log.info(
            f"SiCKRAGE :: URL:[{('http', 'https')[self.config.general.enable_https]}://{(get_internal_ip(), self.web_host)[self.web_host not in ['', '0.0.0.0']]}:{self.config.general.web_port}/{self.config.general.web_root.lstrip('/')}]")

    def launch_browser(self):
        if not self.no_launch and self.config.general.launch_browser:
            launch_browser(protocol=('http', 'https')[self.config.general.enable_https],
                           host=(get_internal_ip(), self.web_host)[self.web_host != ''],
                           startport=self.config.general.web_port)

    def shutdown(self, restart=False):
        if self.started:
            self.log.info('SiCKRAGE IS {}!!!'.format(('SHUTTING DOWN', 'RESTARTING')[restart]))

            # shutdown scheduler
            if self.scheduler:
                try:
                    self.scheduler.shutdown()
                except (SchedulerNotRunningError, RuntimeError):
                    pass

            # shutdown webserver
            if self.wserver:
                self.wserver.shutdown()

            # stop queues
            self.search_queue.shutdown()
            self.show_queue.shutdown()
            self.postprocessor_queue.shutdown()

            # stop amqp consumer
            self.amqp_consumer.stop()

            # log out of ADBA
            if self.adba_connection:
                self.log.debug("Shutting down ANIDB connection")
                self.adba_connection.stop()

            # save shows
            self.log.info('Saving all shows to the database')
            for show in self.shows.values():
                show.save()

            # save settings
            self.config.save()

            # shutdown logging
            if self.log:
                self.log.close()

        if restart:
            os.execl(sys.executable, sys.executable, *sys.argv)

        if self.daemon:
            self.daemon.stop()

        self.started = False

    def restart(self):
        self.shutdown(restart=True)

    def shutdown_trigger(self):
        if not self.started:
            IOLoop.current().stop()
