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


import os
import shutil
import socket
import ssl
import threading

import tornado.locale
from mako.lookup import TemplateLookup
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RedirectHandler, StaticFileHandler

import sickrage
from sickrage.core.helpers import create_https_certificates
from sickrage.core.webserver.handlers.account import AccountLinkHandler, AccountUnlinkHandler, AccountIsLinkedHandler
from sickrage.core.webserver.handlers.announcements import AnnouncementsHandler, MarkAnnouncementSeenHandler, AnnouncementCountHandler
from sickrage.core.webserver.handlers.api import ApiHandler
from sickrage.core.webserver.handlers.calendar import CalendarHandler
from sickrage.core.webserver.handlers.changelog import ChangelogHandler
from sickrage.core.webserver.handlers.config import ConfigHandler, ConfigResetHandler
from sickrage.core.webserver.handlers.config.anime import ConfigAnimeHandler, ConfigSaveAnimeHandler
from sickrage.core.webserver.handlers.config.backup_restore import ConfigBackupRestoreHandler, ConfigBackupHandler, \
    ConfigRestoreHandler, SaveBackupRestoreHandler
from sickrage.core.webserver.handlers.config.general import GenerateApiKeyHandler, SaveRootDirsHandler, \
    SaveAddShowDefaultsHandler, SaveGeneralHandler, ConfigGeneralHandler
from sickrage.core.webserver.handlers.config.notifications import ConfigNotificationsHandler, SaveNotificationsHandler
from sickrage.core.webserver.handlers.config.postprocessing import ConfigPostProcessingHandler, \
    SavePostProcessingHandler, TestNamingHandler, IsRarSupportedHandler, IsNamingPatternValidHandler
from sickrage.core.webserver.handlers.config.providers import ConfigProvidersHandler, CanAddNewznabProviderHandler, \
    CanAddTorrentRssProviderHandler, GetNewznabCategoriesHandler, SaveProvidersHandler
from sickrage.core.webserver.handlers.config.quality_settings import ConfigQualitySettingsHandler, SaveQualitiesHandler
from sickrage.core.webserver.handlers.config.search import ConfigSearchHandler, SaveSearchHandler
from sickrage.core.webserver.handlers.config.subtitles import ConfigSubtitlesHandler, ConfigSubtitleGetCodeHandler, \
    ConfigSubtitlesWantedLanguagesHandler, SaveSubtitlesHandler
from sickrage.core.webserver.handlers.history import HistoryHandler, HistoryTrimHandler, HistoryClearHandler
from sickrage.core.webserver.handlers.home import HomeHandler, IsAliveHandler, TestSABnzbdHandler, TestTorrentHandler, \
    TestFreeMobileHandler, TestTelegramHandler, TestJoinHandler, TestGrowlHandler, TestProwlHandler, TestBoxcar2Handler, \
    TestPushoverHandler, FetchReleasegroupsHandler, RetryEpisodeHandler, TwitterStep1Handler, TwitterStep2Handler, \
    TestTwitterHandler, TestTwilioHandler, TestSlackHandler, TestDiscordHandler, TestKODIHandler, TestPMCHandler, \
    TestPMSHandler, TestLibnotifyHandler, TestEMBYHandler, TestNMJHandler, SettingsNMJHandler, TestNMJv2Handler, \
    SettingsNMJv2Handler, GetTraktTokenHandler, TestTraktHandler, LoadShowNotifyListsHandler, SaveShowNotifyListHandler, \
    TestEmailHandler, TestNMAHandler, TestPushalotHandler, TestPushbulletHandler, GetPushbulletDevicesHandler, \
    ShutdownHandler, RestartHandler, UpdateCheckHandler, UpdateHandler, VerifyPathHandler, \
    InstallRequirementsHandler, BranchCheckoutHandler, DisplayShowHandler, TogglePauseHandler, \
    DeleteShowHandler, RefreshShowHandler, UpdateShowHandler, SubtitleShowHandler, UpdateKODIHandler, UpdatePLEXHandler, \
    UpdateEMBYHandler, SyncTraktHandler, DeleteEpisodeHandler, TestRenameHandler, DoRenameHandler, \
    SearchEpisodeHandler, GetManualSearchStatusHandler, SearchEpisodeSubtitlesHandler, \
    SetSceneNumberingHandler, ProviderStatusHandler, ServerStatusHandler, ShowProgressHandler, TestSynologyDSMHandler, TestAlexaHandler
from sickrage.core.webserver.handlers.home.add_shows import HomeAddShowsHandler, SearchIndexersForShowNameHandler, \
    MassAddTableHandler, NewShowHandler, TraktShowsHandler, PopularShowsHandler, AddShowToBlacklistHandler, \
    ExistingShowsHandler, AddShowByIDHandler, AddNewShowHandler, AddExistingShowsHandler
from sickrage.core.webserver.handlers.home.postprocess import HomePostProcessHandler, HomeProcessEpisodeHandler
from sickrage.core.webserver.handlers.irc import IRCHandler
from sickrage.core.webserver.handlers.login import LoginHandler
from sickrage.core.webserver.handlers.logout import LogoutHandler
from sickrage.core.webserver.handlers.logs import LogsHandler, LogsClearAllHanlder, LogsViewHandler, \
    LogsClearErrorsHanlder, LogsClearWarningsHanlder, ErrorCountHandler, WarningCountHandler
from sickrage.core.webserver.handlers.manage import ManageHandler, ShowEpisodeStatusesHandler, EpisodeStatusesHandler, \
    ChangeEpisodeStatusesHandler, ShowSubtitleMissedHandler, SubtitleMissedHandler, DownloadSubtitleMissedHandler, \
    BacklogShowHandler, BacklogOverviewHandler, MassEditHandler, MassUpdateHandler, FailedDownloadsHandler, EditShowHandler, SetEpisodeStatusHandler
from sickrage.core.webserver.handlers.manage.queues import ManageQueuesHandler, ForceBacklogSearchHandler, \
    ForceFindPropersHandler, PauseDailySearcherHandler, PauseBacklogSearcherHandler, PausePostProcessorHandler, \
    ForceDailySearchHandler
from sickrage.core.webserver.handlers.not_found import NotFoundHandler
from sickrage.core.webserver.handlers.root import RobotsDotTxtHandler, MessagesDotPoHandler, \
    APIBulderHandler, SetHomeLayoutHandler, SetPosterSortByHandler, SetPosterSortDirHandler, \
    ToggleDisplayShowSpecialsHandler, SetScheduleLayoutHandler, ToggleScheduleDisplayPausedHandler, \
    SetScheduleSortHandler, ScheduleHandler, QuicksearchDotJsonHandler, SetHistoryLayoutHandler, ForceSchedulerJobHandler
from sickrage.core.webserver.handlers.web_file_browser import WebFileBrowserHandler, WebFileBrowserCompleteHandler
from sickrage.core.websocket import WebSocketUIHandler


class StaticImageHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super(StaticImageHandler, self).initialize(path, default_filename)

    def get(self, path, include_body=True):
        # image cache check
        self.root = (self.root, os.path.join(sickrage.app.cache_dir, 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickrage.app.cache_dir, 'images', path)))
        ]

        return super(StaticImageHandler, self).get(path, include_body)


class StaticNoCacheFileHandler(StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')


class WebServer(threading.Thread):
    def __init__(self):
        super(WebServer, self).__init__()
        self.name = "TORNADO"
        self.daemon = True
        self.started = False
        self.video_root = None
        self.api_root = None
        self.app = None
        self.server = None
        self.io_loop = None

    def run(self):
        self.started = True
        self.io_loop = IOLoop()

        # load languages
        tornado.locale.load_gettext_translations(sickrage.LOCALE_DIR, 'messages')

        # Check configured web port is correct
        if sickrage.app.config.web_port < 21 or sickrage.app.config.web_port > 65535:
            sickrage.app.config.web_port = 8081

        # clear mako cache folder
        mako_cache = os.path.join(sickrage.app.cache_dir, 'mako')
        if os.path.isdir(mako_cache):
            shutil.rmtree(mako_cache, ignore_errors=True)

        # video root
        if sickrage.app.config.root_dirs:
            root_dirs = sickrage.app.config.root_dirs.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]

        # web root
        if sickrage.app.config.web_root:
            sickrage.app.config.web_root = sickrage.app.config.web_root = (
                    '/' + sickrage.app.config.web_root.lstrip('/').strip('/'))

        # api root
        self.api_root = r'%s/api/%s' % (sickrage.app.config.web_root, sickrage.app.config.api_key)

        # tornado setup
        if sickrage.app.config.enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not create_https_certificates(sickrage.app.config.https_cert, sickrage.app.config.https_key):
                sickrage.app.log.info("Unable to create CERT/KEY files, disabling HTTPS")
                sickrage.app.config.enable_https = False

            if not (os.path.exists(sickrage.app.config.https_cert) and os.path.exists(sickrage.app.config.https_key)):
                sickrage.app.log.warning("Disabled HTTPS because of missing CERT and KEY files")
                sickrage.app.config.enable_https = False

        # Load templates
        mako_lookup = TemplateLookup(
            directories=[sickrage.app.config.gui_views_dir],
            module_directory=os.path.join(sickrage.app.cache_dir, 'mako'),
            filesystem_checks=True,
            strict_undefined=True,
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace'
        )

        templates = {}
        for root, dirs, files in os.walk(sickrage.app.config.gui_views_dir):
            path = root.split(os.sep)

            for x in sickrage.app.config.gui_views_dir.split(os.sep):
                if x in path:
                    del path[path.index(x)]

            for file in files:
                filename = '{}/{}'.format('/'.join(path), file).lstrip('/')
                templates[filename] = mako_lookup.get_template(filename)

        # Load the app
        self.app = Application(
            debug=True,
            autoreload=False,
            gzip=sickrage.app.config.web_use_gzip,
            cookie_secret=sickrage.app.config.web_cookie_secret,
            login_url='%s/login/' % sickrage.app.config.web_root,
            templates=templates,
            default_handler_class=NotFoundHandler
        )

        # Websocket handler
        self.app.add_handlers('.*$', [
            (r'%s/ws/ui' % sickrage.app.config.web_root, WebSocketUIHandler)
        ])

        # Static File Handlers
        self.app.add_handlers('.*$', [
            # api
            (r'%s/api/(\w{32})(/?.*)' % sickrage.app.config.web_root, ApiHandler),

            # redirect to home
            (r"(%s)(/?)" % sickrage.app.config.web_root, RedirectHandler,
             {"url": "%s/home" % sickrage.app.config.web_root}),

            # api builder
            (r'%s/api/builder' % sickrage.app.config.web_root, RedirectHandler,
             {"url": sickrage.app.config.web_root + '/apibuilder/'}),

            # login
            (r'%s/login(/?)' % sickrage.app.config.web_root, LoginHandler),

            # logout
            (r'%s/logout(/?)' % sickrage.app.config.web_root, LogoutHandler),

            # favicon
            (r'%s/(favicon\.ico)' % sickrage.app.config.web_root, StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.config.gui_static_dir, 'images/favicon.ico')}),

            # images
            (r'%s/images/(.*)' % sickrage.app.config.web_root, StaticImageHandler,
             {"path": os.path.join(sickrage.app.config.gui_static_dir, 'images')}),

            # css
            (r'%s/css/(.*)' % sickrage.app.config.web_root, StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.config.gui_static_dir, 'css')}),

            # scss
            (r'%s/scss/(.*)' % sickrage.app.config.web_root, StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.config.gui_static_dir, 'scss')}),

            # fonts
            (r'%s/fonts/(.*)' % sickrage.app.config.web_root, StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.config.gui_static_dir, 'fonts')}),

            # javascript
            (r'%s/js/(.*)' % sickrage.app.config.web_root, StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.config.gui_static_dir, 'js')}),

            # videos
            (r'%s/videos/(.*)' % sickrage.app.config.web_root, StaticNoCacheFileHandler,
             {"path": self.video_root}),
        ])

        # Handlers
        self.app.add_handlers('.*$', [
            (r'%s/robots.txt' % sickrage.app.config.web_root, RobotsDotTxtHandler),
            (r'%s/messages.po' % sickrage.app.config.web_root, MessagesDotPoHandler),
            (r'%s/quicksearch.json' % sickrage.app.config.web_root, QuicksearchDotJsonHandler),
            (r'%s/apibuilder(/?)' % sickrage.app.config.web_root, APIBulderHandler),
            (r'%s/setHomeLayout(/?)' % sickrage.app.config.web_root, SetHomeLayoutHandler),
            (r'%s/setPosterSortBy(/?)' % sickrage.app.config.web_root, SetPosterSortByHandler),
            (r'%s/setPosterSortDir(/?)' % sickrage.app.config.web_root, SetPosterSortDirHandler),
            (r'%s/setHistoryLayout(/?)' % sickrage.app.config.web_root, SetHistoryLayoutHandler),
            (r'%s/toggleDisplayShowSpecials(/?)' % sickrage.app.config.web_root, ToggleDisplayShowSpecialsHandler),
            (r'%s/toggleScheduleDisplayPaused(/?)' % sickrage.app.config.web_root, ToggleScheduleDisplayPausedHandler),
            (r'%s/setScheduleSort(/?)' % sickrage.app.config.web_root, SetScheduleSortHandler),
            (r'%s/forceSchedulerJob(/?)' % sickrage.app.config.web_root, ForceSchedulerJobHandler),
            (r'%s/announcements(/?)' % sickrage.app.config.web_root, AnnouncementsHandler),
            (r'%s/announcements/announcementCount(/?)' % sickrage.app.config.web_root, AnnouncementCountHandler),
            (r'%s/announcements/mark-seen(/?)' % sickrage.app.config.web_root, MarkAnnouncementSeenHandler),
            (r'%s/schedule(/?)' % sickrage.app.config.web_root, ScheduleHandler),
            (r'%s/setScheduleLayout(/?)' % sickrage.app.config.web_root, SetScheduleLayoutHandler),
            (r'%s/calendar(/?)' % sickrage.app.config.web_root, CalendarHandler),
            (r'%s/changelog(/?)' % sickrage.app.config.web_root, ChangelogHandler),
            (r'%s/account/link(/?)' % sickrage.app.config.web_root, AccountLinkHandler),
            (r'%s/account/unlink(/?)' % sickrage.app.config.web_root, AccountUnlinkHandler),
            (r'%s/account/is-linked(/?)' % sickrage.app.config.web_root, AccountIsLinkedHandler),
            (r'%s/history(/?)' % sickrage.app.config.web_root, HistoryHandler),
            (r'%s/history/clear(/?)' % sickrage.app.config.web_root, HistoryClearHandler),
            (r'%s/history/trim(/?)' % sickrage.app.config.web_root, HistoryTrimHandler),
            (r'%s/irc(/?)' % sickrage.app.config.web_root, IRCHandler),
            (r'%s/logs(/?)' % sickrage.app.config.web_root, LogsHandler),
            (r'%s/logs/errorCount(/?)' % sickrage.app.config.web_root, ErrorCountHandler),
            (r'%s/logs/warningCount(/?)' % sickrage.app.config.web_root, WarningCountHandler),
            (r'%s/logs/view(/?)' % sickrage.app.config.web_root, LogsViewHandler),
            (r'%s/logs/clearAll(/?)' % sickrage.app.config.web_root, LogsClearAllHanlder),
            (r'%s/logs/clearWarnings(/?)' % sickrage.app.config.web_root, LogsClearWarningsHanlder),
            (r'%s/logs/clearErrors(/?)' % sickrage.app.config.web_root, LogsClearErrorsHanlder),
            (r'%s/browser(/?)' % sickrage.app.config.web_root, WebFileBrowserHandler),
            (r'%s/browser/complete(/?)' % sickrage.app.config.web_root, WebFileBrowserCompleteHandler),
            (r'%s/home(/?)' % sickrage.app.config.web_root, HomeHandler),
            (r'%s/home/showProgress(/?)' % sickrage.app.config.web_root, ShowProgressHandler),
            (r'%s/home/is-alive(/?)' % sickrage.app.config.web_root, IsAliveHandler),
            (r'%s/home/testSABnzbd(/?)' % sickrage.app.config.web_root, TestSABnzbdHandler),
            (r'%s/home/testSynologyDSM(/?)' % sickrage.app.config.web_root, TestSynologyDSMHandler),
            (r'%s/home/testTorrent(/?)' % sickrage.app.config.web_root, TestTorrentHandler),
            (r'%s/home/testFreeMobile(/?)' % sickrage.app.config.web_root, TestFreeMobileHandler),
            (r'%s/home/testTelegram(/?)' % sickrage.app.config.web_root, TestTelegramHandler),
            (r'%s/home/testJoin(/?)' % sickrage.app.config.web_root, TestJoinHandler),
            (r'%s/home/testGrowl(/?)' % sickrage.app.config.web_root, TestGrowlHandler),
            (r'%s/home/testProwl(/?)' % sickrage.app.config.web_root, TestProwlHandler),
            (r'%s/home/testBoxcar2(/?)' % sickrage.app.config.web_root, TestBoxcar2Handler),
            (r'%s/home/testPushover(/?)' % sickrage.app.config.web_root, TestPushoverHandler),
            (r'%s/home/twitterStep1(/?)' % sickrage.app.config.web_root, TwitterStep1Handler),
            (r'%s/home/twitterStep2(/?)' % sickrage.app.config.web_root, TwitterStep2Handler),
            (r'%s/home/testTwitter(/?)' % sickrage.app.config.web_root, TestTwitterHandler),
            (r'%s/home/testTwilio(/?)' % sickrage.app.config.web_root, TestTwilioHandler),
            (r'%s/home/testSlack(/?)' % sickrage.app.config.web_root, TestSlackHandler),
            (r'%s/home/testAlexa(/?)' % sickrage.app.config.web_root, TestAlexaHandler),
            (r'%s/home/testDiscord(/?)' % sickrage.app.config.web_root, TestDiscordHandler),
            (r'%s/home/testKODI(/?)' % sickrage.app.config.web_root, TestKODIHandler),
            (r'%s/home/testPMC(/?)' % sickrage.app.config.web_root, TestPMCHandler),
            (r'%s/home/testPMS(/?)' % sickrage.app.config.web_root, TestPMSHandler),
            (r'%s/home/testLibnotify(/?)' % sickrage.app.config.web_root, TestLibnotifyHandler),
            (r'%s/home/testEMBY(/?)' % sickrage.app.config.web_root, TestEMBYHandler),
            (r'%s/home/testNMJ(/?)' % sickrage.app.config.web_root, TestNMJHandler),
            (r'%s/home/settingsNMJ(/?)' % sickrage.app.config.web_root, SettingsNMJHandler),
            (r'%s/home/testNMJv2(/?)' % sickrage.app.config.web_root, TestNMJv2Handler),
            (r'%s/home/settingsNMJv2(/?)' % sickrage.app.config.web_root, SettingsNMJv2Handler),
            (r'%s/home/getTraktToken(/?)' % sickrage.app.config.web_root, GetTraktTokenHandler),
            (r'%s/home/testTrakt(/?)' % sickrage.app.config.web_root, TestTraktHandler),
            (r'%s/home/loadShowNotifyLists(/?)' % sickrage.app.config.web_root, LoadShowNotifyListsHandler),
            (r'%s/home/saveShowNotifyList(/?)' % sickrage.app.config.web_root, SaveShowNotifyListHandler),
            (r'%s/home/testEmail(/?)' % sickrage.app.config.web_root, TestEmailHandler),
            (r'%s/home/testNMA(/?)' % sickrage.app.config.web_root, TestNMAHandler),
            (r'%s/home/testPushalot(/?)' % sickrage.app.config.web_root, TestPushalotHandler),
            (r'%s/home/testPushbullet(/?)' % sickrage.app.config.web_root, TestPushbulletHandler),
            (r'%s/home/getPushbulletDevices(/?)' % sickrage.app.config.web_root, GetPushbulletDevicesHandler),
            (r'%s/home/serverStatus(/?)' % sickrage.app.config.web_root, ServerStatusHandler),
            (r'%s/home/providerStatus(/?)' % sickrage.app.config.web_root, ProviderStatusHandler),
            (r'%s/home/shutdown(/?)' % sickrage.app.config.web_root, ShutdownHandler),
            (r'%s/home/restart(/?)' % sickrage.app.config.web_root, RestartHandler),
            (r'%s/home/updateCheck(/?)' % sickrage.app.config.web_root, UpdateCheckHandler),
            (r'%s/home/update(/?)' % sickrage.app.config.web_root, UpdateHandler),
            (r'%s/home/verifyPath(/?)' % sickrage.app.config.web_root, VerifyPathHandler),
            (r'%s/home/installRequirements(/?)' % sickrage.app.config.web_root, InstallRequirementsHandler),
            (r'%s/home/branchCheckout(/?)' % sickrage.app.config.web_root, BranchCheckoutHandler),
            (r'%s/home/displayShow(/?)' % sickrage.app.config.web_root, DisplayShowHandler),
            (r'%s/home/togglePause(/?)' % sickrage.app.config.web_root, TogglePauseHandler),
            (r'%s/home/deleteShow' % sickrage.app.config.web_root, DeleteShowHandler),
            (r'%s/home/refreshShow(/?)' % sickrage.app.config.web_root, RefreshShowHandler),
            (r'%s/home/updateShow(/?)' % sickrage.app.config.web_root, UpdateShowHandler),
            (r'%s/home/subtitleShow(/?)' % sickrage.app.config.web_root, SubtitleShowHandler),
            (r'%s/home/updateKODI(/?)' % sickrage.app.config.web_root, UpdateKODIHandler),
            (r'%s/home/updatePLEX(/?)' % sickrage.app.config.web_root, UpdatePLEXHandler),
            (r'%s/home/updateEMBY(/?)' % sickrage.app.config.web_root, UpdateEMBYHandler),
            (r'%s/home/syncTrakt(/?)' % sickrage.app.config.web_root, SyncTraktHandler),
            (r'%s/home/deleteEpisode(/?)' % sickrage.app.config.web_root, DeleteEpisodeHandler),
            (r'%s/home/testRename(/?)' % sickrage.app.config.web_root, TestRenameHandler),
            (r'%s/home/doRename(/?)' % sickrage.app.config.web_root, DoRenameHandler),
            (r'%s/home/searchEpisode(/?)' % sickrage.app.config.web_root, SearchEpisodeHandler),
            (r'%s/home/getManualSearchStatus(/?)' % sickrage.app.config.web_root, GetManualSearchStatusHandler),
            (r'%s/home/searchEpisodeSubtitles(/?)' % sickrage.app.config.web_root, SearchEpisodeSubtitlesHandler),
            (r'%s/home/setSceneNumbering(/?)' % sickrage.app.config.web_root, SetSceneNumberingHandler),
            (r'%s/home/retryEpisode(/?)' % sickrage.app.config.web_root, RetryEpisodeHandler),
            (r'%s/home/fetch_releasegroups(/?)' % sickrage.app.config.web_root, FetchReleasegroupsHandler),
            (r'%s/home/postprocess(/?)' % sickrage.app.config.web_root, HomePostProcessHandler),
            (r'%s/home/postprocess/processEpisode(/?)' % sickrage.app.config.web_root, HomeProcessEpisodeHandler),
            (r'%s/home/addShows(/?)' % sickrage.app.config.web_root, HomeAddShowsHandler),
            (r'%s/home/addShows/searchIndexersForShowName(/?)' % sickrage.app.config.web_root, SearchIndexersForShowNameHandler),
            (r'%s/home/addShows/massAddTable(/?)' % sickrage.app.config.web_root, MassAddTableHandler),
            (r'%s/home/addShows/newShow(/?)' % sickrage.app.config.web_root, NewShowHandler),
            (r'%s/home/addShows/traktShows(/?)' % sickrage.app.config.web_root, TraktShowsHandler),
            (r'%s/home/addShows/popularShows(/?)' % sickrage.app.config.web_root, PopularShowsHandler),
            (r'%s/home/addShows/addShowToBlacklist(/?)' % sickrage.app.config.web_root, AddShowToBlacklistHandler),
            (r'%s/home/addShows/existingShows(/?)' % sickrage.app.config.web_root, ExistingShowsHandler),
            (r'%s/home/addShows/addShowByID(/?)' % sickrage.app.config.web_root, AddShowByIDHandler),
            (r'%s/home/addShows/addNewShow(/?)' % sickrage.app.config.web_root, AddNewShowHandler),
            (r'%s/home/addShows/addExistingShows(/?)' % sickrage.app.config.web_root, AddExistingShowsHandler),
            (r'%s/manage(/?)' % sickrage.app.config.web_root, ManageHandler),
            (r'%s/manage/editShow(/?)' % sickrage.app.config.web_root, EditShowHandler),
            (r'%s/manage/showEpisodeStatuses(/?)' % sickrage.app.config.web_root, ShowEpisodeStatusesHandler),
            (r'%s/manage/episodeStatuses(/?)' % sickrage.app.config.web_root, EpisodeStatusesHandler),
            (r'%s/manage/changeEpisodeStatuses(/?)' % sickrage.app.config.web_root, ChangeEpisodeStatusesHandler),
            (r'%s/manage/setEpisodeStatus(/?)' % sickrage.app.config.web_root, SetEpisodeStatusHandler),
            (r'%s/manage/showSubtitleMissed(/?)' % sickrage.app.config.web_root, ShowSubtitleMissedHandler),
            (r'%s/manage/subtitleMissed(/?)' % sickrage.app.config.web_root, SubtitleMissedHandler),
            (r'%s/manage/downloadSubtitleMissed(/?)' % sickrage.app.config.web_root, DownloadSubtitleMissedHandler),
            (r'%s/manage/backlogShow(/?)' % sickrage.app.config.web_root, BacklogShowHandler),
            (r'%s/manage/backlogOverview(/?)' % sickrage.app.config.web_root, BacklogOverviewHandler),
            (r'%s/manage/massEdit(/?)' % sickrage.app.config.web_root, MassEditHandler),
            (r'%s/manage/massUpdate(/?)' % sickrage.app.config.web_root, MassUpdateHandler),
            (r'%s/manage/failedDownloads(/?)' % sickrage.app.config.web_root, FailedDownloadsHandler),
            (r'%s/manage/manageQueues(/?)' % sickrage.app.config.web_root, ManageQueuesHandler),
            (r'%s/manage/manageQueues/forceBacklogSearch(/?)' % sickrage.app.config.web_root, ForceBacklogSearchHandler),
            (r'%s/manage/manageQueues/forceDailySearch(/?)' % sickrage.app.config.web_root, ForceDailySearchHandler),
            (r'%s/manage/manageQueues/forceFindPropers(/?)' % sickrage.app.config.web_root, ForceFindPropersHandler),
            (r'%s/manage/manageQueues/pauseDailySearcher(/?)' % sickrage.app.config.web_root, PauseDailySearcherHandler),
            (r'%s/manage/manageQueues/pauseBacklogSearcher(/?)' % sickrage.app.config.web_root, PauseBacklogSearcherHandler),
            (r'%s/manage/manageQueues/pausePostProcessor(/?)' % sickrage.app.config.web_root, PausePostProcessorHandler),
            (r'%s/config(/?)' % sickrage.app.config.web_root, ConfigHandler),
            (r'%s/config/reset(/?)' % sickrage.app.config.web_root, ConfigResetHandler),
            (r'%s/config/anime(/?)' % sickrage.app.config.web_root, ConfigAnimeHandler),
            (r'%s/config/anime/saveAnime(/?)' % sickrage.app.config.web_root, ConfigSaveAnimeHandler),
            (r'%s/config/backuprestore(/?)' % sickrage.app.config.web_root, ConfigBackupRestoreHandler),
            (r'%s/config/backuprestore/backup(/?)' % sickrage.app.config.web_root, ConfigBackupHandler),
            (r'%s/config/backuprestore/restore(/?)' % sickrage.app.config.web_root, ConfigRestoreHandler),
            (r'%s/config/backuprestore/saveBackupRestore(/?)' % sickrage.app.config.web_root, SaveBackupRestoreHandler),
            (r'%s/config/general(/?)' % sickrage.app.config.web_root, ConfigGeneralHandler),
            (r'%s/config/general/generateApiKey(/?)' % sickrage.app.config.web_root, GenerateApiKeyHandler),
            (r'%s/config/general/saveRootDirs(/?)' % sickrage.app.config.web_root, SaveRootDirsHandler),
            (r'%s/config/general/saveAddShowDefaults(/?)' % sickrage.app.config.web_root, SaveAddShowDefaultsHandler),
            (r'%s/config/general/saveGeneral(/?)' % sickrage.app.config.web_root, SaveGeneralHandler),
            (r'%s/config/notifications(/?)' % sickrage.app.config.web_root, ConfigNotificationsHandler),
            (r'%s/config/notifications/saveNotifications(/?)' % sickrage.app.config.web_root, SaveNotificationsHandler),
            (r'%s/config/postProcessing(/?)' % sickrage.app.config.web_root, ConfigPostProcessingHandler),
            (r'%s/config/postProcessing/savePostProcessing(/?)' % sickrage.app.config.web_root, SavePostProcessingHandler),
            (r'%s/config/postProcessing/testNaming(/?)' % sickrage.app.config.web_root, TestNamingHandler),
            (r'%s/config/postProcessing/isNamingValid(/?)' % sickrage.app.config.web_root, IsNamingPatternValidHandler),
            (r'%s/config/postProcessing/isRarSupported(/?)' % sickrage.app.config.web_root, IsRarSupportedHandler),
            (r'%s/config/providers(/?)' % sickrage.app.config.web_root, ConfigProvidersHandler),
            (r'%s/config/providers/canAddNewznabProvider(/?)' % sickrage.app.config.web_root, CanAddNewznabProviderHandler),
            (r'%s/config/providers/canAddTorrentRssProvider(/?)' % sickrage.app.config.web_root, CanAddTorrentRssProviderHandler),
            (r'%s/config/providers/getNewznabCategories(/?)' % sickrage.app.config.web_root, GetNewznabCategoriesHandler),
            (r'%s/config/providers/saveProviders(/?)' % sickrage.app.config.web_root, SaveProvidersHandler),
            (r'%s/config/qualitySettings(/?)' % sickrage.app.config.web_root, ConfigQualitySettingsHandler),
            (r'%s/config/qualitySettings/saveQualities(/?)' % sickrage.app.config.web_root, SaveQualitiesHandler),
            (r'%s/config/search(/?)' % sickrage.app.config.web_root, ConfigSearchHandler),
            (r'%s/config/search/saveSearch(/?)' % sickrage.app.config.web_root, SaveSearchHandler),
            (r'%s/config/subtitles(/?)' % sickrage.app.config.web_root, ConfigSubtitlesHandler),
            (r'%s/config/subtitles/get_code(/?)' % sickrage.app.config.web_root, ConfigSubtitleGetCodeHandler),
            (r'%s/config/subtitles/wanted_languages(/?)' % sickrage.app.config.web_root, ConfigSubtitlesWantedLanguagesHandler),
            (r'%s/config/subtitles/saveSubtitles(/?)' % sickrage.app.config.web_root, SaveSubtitlesHandler),
        ])

        # HTTPS Cert/Key object
        ssl_ctx = None
        if sickrage.app.config.enable_https:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(sickrage.app.config.https_cert, sickrage.app.config.https_key)

        # Web Server
        self.server = HTTPServer(self.app, ssl_options=ssl_ctx, xheaders=sickrage.app.config.handle_reverse_proxy)

        try:
            self.server.listen(sickrage.app.config.web_port)
        except socket.error as e:
            sickrage.app.log.warning(e.strerror)
            raise SystemExit

        self.io_loop.start()

    def shutdown(self):
        if self.started:
            self.started = False
            if self.server:
                self.server.close_all_connections()
                self.server.stop()

            if self.io_loop:
                self.io_loop.stop()
