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
import shutil
import socket
import ssl

import tornado.autoreload
import tornado.locale
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import ExtensionNotFound
from mako.lookup import TemplateLookup
from tornado.httpserver import HTTPServer
from tornado.ioloop import PeriodicCallback, IOLoop
from tornado.web import Application, RedirectHandler, StaticFileHandler

import sickrage
from sickrage.core.helpers import create_https_certificates
from sickrage.core.webserver.handlers.account import AccountLinkHandler, AccountUnlinkHandler, AccountIsLinkedHandler
from sickrage.core.webserver.handlers.announcements import AnnouncementsHandler, MarkAnnouncementSeenHandler, AnnouncementCountHandler
from sickrage.core.webserver.handlers.api import ApiSwaggerDotJsonHandler, ApiPingHandler, ApiProfileHandler
from sickrage.core.webserver.handlers.api.v1 import ApiV1Handler
from sickrage.core.webserver.handlers.api.v2 import ApiV2RetrieveSeriesMetadataHandler
from sickrage.core.webserver.handlers.api.v2.config import ApiV2ConfigHandler
from sickrage.core.webserver.handlers.api.v2.file_browser import ApiV2FileBrowserHandler
from sickrage.core.webserver.handlers.api.v2.history import ApiV2HistoryHandler
from sickrage.core.webserver.handlers.api.v2.postprocess import Apiv2PostProcessHandler
from sickrage.core.webserver.handlers.api.v2.schedule import ApiV2ScheduleHandler
from sickrage.core.webserver.handlers.api.v2.series import ApiV2SeriesHandler, ApiV2SeriesEpisodesHandler, ApiV2SeriesImagesHandler, ApiV2SeriesImdbInfoHandler, \
    ApiV2SeriesBlacklistHandler, ApiV2SeriesWhitelistHandler, ApiV2SeriesRefreshHandler, ApiV2SeriesUpdateHandler, ApiV2SeriesEpisodesRenameHandler, \
    ApiV2SeriesEpisodesManualSearchHandler
from sickrage.core.webserver.handlers.api.v2.series_provider import ApiV2SeriesProvidersHandler, ApiV2SeriesProvidersSearchHandler, \
    ApiV2SeriesProvidersLanguagesHandler
from sickrage.core.webserver.handlers.calendar import CalendarHandler
from sickrage.core.webserver.handlers.changelog import ChangelogHandler
from sickrage.core.webserver.handlers.config import ConfigWebHandler, ConfigResetHandler
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
from sickrage.core.webserver.handlers.home.add_shows import HomeAddShowsHandler, SearchSeriesProviderForShowNameHandler, \
    MassAddTableHandler, NewShowHandler, TraktShowsHandler, PopularShowsHandler, AddShowToBlacklistHandler, \
    ExistingShowsHandler, AddShowByIDHandler, AddNewShowHandler, AddExistingShowsHandler
from sickrage.core.webserver.handlers.home.postprocess import HomePostProcessHandler, HomeProcessEpisodeHandler
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


class WebServer(object):
    def __init__(self):
        super(WebServer, self).__init__()
        self.name = "TORNADO"
        self.daemon = True
        self.started = False
        self.handlers = {}
        self.video_root = None
        self.api_v1_root = None
        self.api_v2_root = None
        self.app = None
        self.server = None

    def start(self):
        self.started = True

        # load languages
        tornado.locale.load_gettext_translations(sickrage.LOCALE_DIR, 'messages')

        # Check configured web port is correct
        if sickrage.app.config.general.web_port < 21 or sickrage.app.config.general.web_port > 65535:
            sickrage.app.config.general.web_port = 8081

        # clear mako cache folder
        mako_cache = os.path.join(sickrage.app.cache_dir, 'mako')
        if os.path.isdir(mako_cache):
            shutil.rmtree(mako_cache, ignore_errors=True)

        # video root
        if sickrage.app.config.general.root_dirs:
            root_dirs = sickrage.app.config.general.root_dirs.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]

        # web root
        if sickrage.app.config.general.web_root:
            sickrage.app.config.general.web_root = sickrage.app.config.general.web_root = ('/' + sickrage.app.config.general.web_root.lstrip('/').strip('/'))

        # api root
        self.api_v1_root = fr'{sickrage.app.config.general.web_root}/api/(?:v1/)?({sickrage.app.config.general.api_v1_key})'
        self.api_v2_root = fr'{sickrage.app.config.general.web_root}/api/v2'

        # tornado SSL setup
        if sickrage.app.config.general.enable_https:
            if not self.load_ssl_certificate():
                sickrage.app.log.info("Unable to retrieve CERT/KEY files from SiCKRAGE API, disabling HTTPS")
                sickrage.app.config.general.enable_https = False

        # Load templates
        mako_lookup = TemplateLookup(
            directories=[sickrage.app.gui_views_dir],
            module_directory=os.path.join(sickrage.app.cache_dir, 'mako'),
            filesystem_checks=True,
            strict_undefined=True,
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace'
        )

        templates = {}
        for root, dirs, files in os.walk(sickrage.app.gui_views_dir):
            path = root.split(os.sep)

            for x in sickrage.app.gui_views_dir.split(os.sep):
                if x in path:
                    del path[path.index(x)]

            for file in files:
                filename = '{}/{}'.format('/'.join(path), file).lstrip('/')
                templates[filename] = mako_lookup.get_template(filename)

        # Websocket handler
        self.handlers['websocket_handlers'] = [
            (fr'{sickrage.app.config.general.web_root}/ws/ui', WebSocketUIHandler)
        ]

        # API v1 Handlers
        self.handlers['api_v1_handlers'] = [
            # api
            (fr'{self.api_v1_root}(/?.*)', ApiV1Handler),

            # api builder
            (fr'{sickrage.app.config.general.web_root}/api/builder', RedirectHandler,
             {"url": sickrage.app.config.general.web_root + '/apibuilder/'}),
        ]

        # API v2 Handlers
        self.handlers['api_v2_handlers'] = [
            (fr'{self.api_v2_root}/ping', ApiPingHandler),
            (fr'{self.api_v2_root}/profile', ApiProfileHandler),
            (fr'{self.api_v2_root}/swagger.json', ApiSwaggerDotJsonHandler, {'api_handlers': 'api_v2_handlers', 'api_version': '2.0.0'}),
            (fr'{self.api_v2_root}/config', ApiV2ConfigHandler),
            (fr'{self.api_v2_root}/file-browser', ApiV2FileBrowserHandler),
            (fr'{self.api_v2_root}/postprocess', Apiv2PostProcessHandler),
            (fr'{self.api_v2_root}/retrieve-series-metadata', ApiV2RetrieveSeriesMetadataHandler),
            (fr'{self.api_v2_root}/schedule', ApiV2ScheduleHandler),
            (fr'{self.api_v2_root}/history', ApiV2HistoryHandler),
            (fr'{self.api_v2_root}/series-providers', ApiV2SeriesProvidersHandler),
            (fr'{self.api_v2_root}/series-providers/([a-z]+)/search', ApiV2SeriesProvidersSearchHandler),
            (fr'{self.api_v2_root}/series-providers/([a-z]+)/languages', ApiV2SeriesProvidersLanguagesHandler),
            (fr'{self.api_v2_root}/series', ApiV2SeriesHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)', ApiV2SeriesHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/episodes', ApiV2SeriesEpisodesHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/episodes/rename', ApiV2SeriesEpisodesRenameHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/episodes/(s\d+e\d+)/search', ApiV2SeriesEpisodesManualSearchHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/images', ApiV2SeriesImagesHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/imdb-info', ApiV2SeriesImdbInfoHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/blacklist', ApiV2SeriesBlacklistHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/whitelist', ApiV2SeriesWhitelistHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/refresh', ApiV2SeriesRefreshHandler),
            (fr'{self.api_v2_root}/series/(\d+[-][a-z]+)/update', ApiV2SeriesUpdateHandler)
        ]

        # New UI Static File Handlers
        self.handlers['new_ui_static_file_handlers'] = [
            # media
            (fr'{sickrage.app.config.general.web_root}/app/static/media/(.*)', StaticImageHandler,
             {"path": os.path.join(sickrage.app.gui_app_dir, 'static', 'media')}),

            # css
            (fr'{sickrage.app.config.general.web_root}/app/static/css/(.*)', StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.gui_app_dir, 'static', 'css')}),

            # js
            (fr'{sickrage.app.config.general.web_root}/app/static/js/(.*)', StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.gui_app_dir, 'static', 'js')}),

            # base
            (fr"{sickrage.app.config.general.web_root}/app/(.*)", tornado.web.StaticFileHandler,
             {"path": sickrage.app.gui_app_dir, "default_filename": "index.html"})
        ]

        # Static File Handlers
        self.handlers['static_file_handlers'] = [
            # redirect to home
            (fr"({sickrage.app.config.general.web_root})(/?)", RedirectHandler,
             {"url": f"{sickrage.app.config.general.web_root}/home"}),

            # login
            (fr'{sickrage.app.config.general.web_root}/login(/?)', LoginHandler),

            # logout
            (fr'{sickrage.app.config.general.web_root}/logout(/?)', LogoutHandler),

            # favicon
            (fr'{sickrage.app.config.general.web_root}/(favicon\.ico)', StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.gui_static_dir, 'images/favicon.ico')}),

            # images
            (fr'{sickrage.app.config.general.web_root}/images/(.*)', StaticImageHandler,
             {"path": os.path.join(sickrage.app.gui_static_dir, 'images')}),

            # css
            (fr'{sickrage.app.config.general.web_root}/css/(.*)', StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.gui_static_dir, 'css')}),

            # scss
            (fr'{sickrage.app.config.general.web_root}/scss/(.*)', StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.gui_static_dir, 'scss')}),

            # fonts
            (fr'{sickrage.app.config.general.web_root}/fonts/(.*)', StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.gui_static_dir, 'fonts')}),

            # javascript
            (fr'{sickrage.app.config.general.web_root}/js/(.*)', StaticNoCacheFileHandler,
             {"path": os.path.join(sickrage.app.gui_static_dir, 'js')}),

            # videos
            (fr'{sickrage.app.config.general.web_root}/videos/(.*)', StaticNoCacheFileHandler,
             {"path": self.video_root}),
        ]

        # Handlers
        self.handlers['web_handlers'] = [
            (fr'{sickrage.app.config.general.web_root}/robots.txt', RobotsDotTxtHandler),
            (fr'{sickrage.app.config.general.web_root}/messages.po', MessagesDotPoHandler),
            (fr'{sickrage.app.config.general.web_root}/quicksearch.json', QuicksearchDotJsonHandler),
            (fr'{sickrage.app.config.general.web_root}/apibuilder(/?)', APIBulderHandler),
            (fr'{sickrage.app.config.general.web_root}/setHomeLayout(/?)', SetHomeLayoutHandler),
            (fr'{sickrage.app.config.general.web_root}/setPosterSortBy(/?)', SetPosterSortByHandler),
            (fr'{sickrage.app.config.general.web_root}/setPosterSortDir(/?)', SetPosterSortDirHandler),
            (fr'{sickrage.app.config.general.web_root}/setHistoryLayout(/?)', SetHistoryLayoutHandler),
            (fr'{sickrage.app.config.general.web_root}/toggleDisplayShowSpecials(/?)', ToggleDisplayShowSpecialsHandler),
            (fr'{sickrage.app.config.general.web_root}/toggleScheduleDisplayPaused(/?)', ToggleScheduleDisplayPausedHandler),
            (fr'{sickrage.app.config.general.web_root}/setScheduleSort(/?)', SetScheduleSortHandler),
            (fr'{sickrage.app.config.general.web_root}/forceSchedulerJob(/?)', ForceSchedulerJobHandler),
            (fr'{sickrage.app.config.general.web_root}/announcements(/?)', AnnouncementsHandler),
            (fr'{sickrage.app.config.general.web_root}/announcements/announcementCount(/?)', AnnouncementCountHandler),
            (fr'{sickrage.app.config.general.web_root}/announcements/mark-seen(/?)', MarkAnnouncementSeenHandler),
            (fr'{sickrage.app.config.general.web_root}/schedule(/?)', ScheduleHandler),
            (fr'{sickrage.app.config.general.web_root}/setScheduleLayout(/?)', SetScheduleLayoutHandler),
            (fr'{sickrage.app.config.general.web_root}/calendar(/?)', CalendarHandler),
            (fr'{sickrage.app.config.general.web_root}/changelog(/?)', ChangelogHandler),
            (fr'{sickrage.app.config.general.web_root}/account/link(/?)', AccountLinkHandler),
            (fr'{sickrage.app.config.general.web_root}/account/unlink(/?)', AccountUnlinkHandler),
            (fr'{sickrage.app.config.general.web_root}/account/is-linked(/?)', AccountIsLinkedHandler),
            (fr'{sickrage.app.config.general.web_root}/history(/?)', HistoryHandler),
            (fr'{sickrage.app.config.general.web_root}/history/clear(/?)', HistoryClearHandler),
            (fr'{sickrage.app.config.general.web_root}/history/trim(/?)', HistoryTrimHandler),
            (fr'{sickrage.app.config.general.web_root}/logs(/?)', LogsHandler),
            (fr'{sickrage.app.config.general.web_root}/logs/errorCount(/?)', ErrorCountHandler),
            (fr'{sickrage.app.config.general.web_root}/logs/warningCount(/?)', WarningCountHandler),
            (fr'{sickrage.app.config.general.web_root}/logs/view(/?)', LogsViewHandler),
            (fr'{sickrage.app.config.general.web_root}/logs/clearAll(/?)', LogsClearAllHanlder),
            (fr'{sickrage.app.config.general.web_root}/logs/clearWarnings(/?)', LogsClearWarningsHanlder),
            (fr'{sickrage.app.config.general.web_root}/logs/clearErrors(/?)', LogsClearErrorsHanlder),
            (fr'{sickrage.app.config.general.web_root}/browser(/?)', WebFileBrowserHandler),
            (fr'{sickrage.app.config.general.web_root}/browser/complete(/?)', WebFileBrowserCompleteHandler),
            (fr'{sickrage.app.config.general.web_root}/home(/?)', HomeHandler),
            (fr'{sickrage.app.config.general.web_root}/home/showProgress(/?)', ShowProgressHandler),
            (fr'{sickrage.app.config.general.web_root}/home/is-alive(/?)', IsAliveHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testSABnzbd(/?)', TestSABnzbdHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testSynologyDSM(/?)', TestSynologyDSMHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testTorrent(/?)', TestTorrentHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testFreeMobile(/?)', TestFreeMobileHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testTelegram(/?)', TestTelegramHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testJoin(/?)', TestJoinHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testGrowl(/?)', TestGrowlHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testProwl(/?)', TestProwlHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testBoxcar2(/?)', TestBoxcar2Handler),
            (fr'{sickrage.app.config.general.web_root}/home/testPushover(/?)', TestPushoverHandler),
            (fr'{sickrage.app.config.general.web_root}/home/twitterStep1(/?)', TwitterStep1Handler),
            (fr'{sickrage.app.config.general.web_root}/home/twitterStep2(/?)', TwitterStep2Handler),
            (fr'{sickrage.app.config.general.web_root}/home/testTwitter(/?)', TestTwitterHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testTwilio(/?)', TestTwilioHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testSlack(/?)', TestSlackHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testAlexa(/?)', TestAlexaHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testDiscord(/?)', TestDiscordHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testKODI(/?)', TestKODIHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testPMC(/?)', TestPMCHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testPMS(/?)', TestPMSHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testLibnotify(/?)', TestLibnotifyHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testEMBY(/?)', TestEMBYHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testNMJ(/?)', TestNMJHandler),
            (fr'{sickrage.app.config.general.web_root}/home/settingsNMJ(/?)', SettingsNMJHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testNMJv2(/?)', TestNMJv2Handler),
            (fr'{sickrage.app.config.general.web_root}/home/settingsNMJv2(/?)', SettingsNMJv2Handler),
            (fr'{sickrage.app.config.general.web_root}/home/getTraktToken(/?)', GetTraktTokenHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testTrakt(/?)', TestTraktHandler),
            (fr'{sickrage.app.config.general.web_root}/home/loadShowNotifyLists(/?)', LoadShowNotifyListsHandler),
            (fr'{sickrage.app.config.general.web_root}/home/saveShowNotifyList(/?)', SaveShowNotifyListHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testEmail(/?)', TestEmailHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testNMA(/?)', TestNMAHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testPushalot(/?)', TestPushalotHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testPushbullet(/?)', TestPushbulletHandler),
            (fr'{sickrage.app.config.general.web_root}/home/getPushbulletDevices(/?)', GetPushbulletDevicesHandler),
            (fr'{sickrage.app.config.general.web_root}/home/serverStatus(/?)', ServerStatusHandler),
            (fr'{sickrage.app.config.general.web_root}/home/providerStatus(/?)', ProviderStatusHandler),
            (fr'{sickrage.app.config.general.web_root}/home/shutdown(/?)', ShutdownHandler),
            (fr'{sickrage.app.config.general.web_root}/home/restart(/?)', RestartHandler),
            (fr'{sickrage.app.config.general.web_root}/home/updateCheck(/?)', UpdateCheckHandler),
            (fr'{sickrage.app.config.general.web_root}/home/update(/?)', UpdateHandler),
            (fr'{sickrage.app.config.general.web_root}/home/verifyPath(/?)', VerifyPathHandler),
            (fr'{sickrage.app.config.general.web_root}/home/installRequirements(/?)', InstallRequirementsHandler),
            (fr'{sickrage.app.config.general.web_root}/home/branchCheckout(/?)', BranchCheckoutHandler),
            (fr'{sickrage.app.config.general.web_root}/home/displayShow(/?)', DisplayShowHandler),
            (fr'{sickrage.app.config.general.web_root}/home/togglePause(/?)', TogglePauseHandler),
            (fr'{sickrage.app.config.general.web_root}/home/deleteShow', DeleteShowHandler),
            (fr'{sickrage.app.config.general.web_root}/home/refreshShow(/?)', RefreshShowHandler),
            (fr'{sickrage.app.config.general.web_root}/home/updateShow(/?)', UpdateShowHandler),
            (fr'{sickrage.app.config.general.web_root}/home/subtitleShow(/?)', SubtitleShowHandler),
            (fr'{sickrage.app.config.general.web_root}/home/updateKODI(/?)', UpdateKODIHandler),
            (fr'{sickrage.app.config.general.web_root}/home/updatePLEX(/?)', UpdatePLEXHandler),
            (fr'{sickrage.app.config.general.web_root}/home/updateEMBY(/?)', UpdateEMBYHandler),
            (fr'{sickrage.app.config.general.web_root}/home/syncTrakt(/?)', SyncTraktHandler),
            (fr'{sickrage.app.config.general.web_root}/home/deleteEpisode(/?)', DeleteEpisodeHandler),
            (fr'{sickrage.app.config.general.web_root}/home/testRename(/?)', TestRenameHandler),
            (fr'{sickrage.app.config.general.web_root}/home/doRename(/?)', DoRenameHandler),
            (fr'{sickrage.app.config.general.web_root}/home/searchEpisode(/?)', SearchEpisodeHandler),
            (fr'{sickrage.app.config.general.web_root}/home/getManualSearchStatus(/?)', GetManualSearchStatusHandler),
            (fr'{sickrage.app.config.general.web_root}/home/searchEpisodeSubtitles(/?)', SearchEpisodeSubtitlesHandler),
            (fr'{sickrage.app.config.general.web_root}/home/setSceneNumbering(/?)', SetSceneNumberingHandler),
            (fr'{sickrage.app.config.general.web_root}/home/retryEpisode(/?)', RetryEpisodeHandler),
            (fr'{sickrage.app.config.general.web_root}/home/fetch_releasegroups(/?)', FetchReleasegroupsHandler),
            (fr'{sickrage.app.config.general.web_root}/home/postprocess(/?)', HomePostProcessHandler),
            (fr'{sickrage.app.config.general.web_root}/home/postprocess/processEpisode(/?)', HomeProcessEpisodeHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows(/?)', HomeAddShowsHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/searchSeriesProviderForShowName(/?)', SearchSeriesProviderForShowNameHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/massAddTable(/?)', MassAddTableHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/newShow(/?)', NewShowHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/traktShows(/?)', TraktShowsHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/popularShows(/?)', PopularShowsHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/addShowToBlacklist(/?)', AddShowToBlacklistHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/existingShows(/?)', ExistingShowsHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/addShowByID(/?)', AddShowByIDHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/addNewShow(/?)', AddNewShowHandler),
            (fr'{sickrage.app.config.general.web_root}/home/addShows/addExistingShows(/?)', AddExistingShowsHandler),
            (fr'{sickrage.app.config.general.web_root}/manage(/?)', ManageHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/editShow(/?)', EditShowHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/showEpisodeStatuses(/?)', ShowEpisodeStatusesHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/episodeStatuses(/?)', EpisodeStatusesHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/changeEpisodeStatuses(/?)', ChangeEpisodeStatusesHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/setEpisodeStatus(/?)', SetEpisodeStatusHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/showSubtitleMissed(/?)', ShowSubtitleMissedHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/subtitleMissed(/?)', SubtitleMissedHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/downloadSubtitleMissed(/?)', DownloadSubtitleMissedHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/backlogShow(/?)', BacklogShowHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/backlogOverview(/?)', BacklogOverviewHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/massEdit(/?)', MassEditHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/massUpdate(/?)', MassUpdateHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/failedDownloads(/?)', FailedDownloadsHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/manageQueues(/?)', ManageQueuesHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/manageQueues/forceBacklogSearch(/?)', ForceBacklogSearchHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/manageQueues/forceDailySearch(/?)', ForceDailySearchHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/manageQueues/forceFindPropers(/?)', ForceFindPropersHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/manageQueues/pauseDailySearcher(/?)', PauseDailySearcherHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/manageQueues/pauseBacklogSearcher(/?)', PauseBacklogSearcherHandler),
            (fr'{sickrage.app.config.general.web_root}/manage/manageQueues/pausePostProcessor(/?)', PausePostProcessorHandler),
            (fr'{sickrage.app.config.general.web_root}/config(/?)', ConfigWebHandler),
            (fr'{sickrage.app.config.general.web_root}/config/reset(/?)', ConfigResetHandler),
            (fr'{sickrage.app.config.general.web_root}/config/anime(/?)', ConfigAnimeHandler),
            (fr'{sickrage.app.config.general.web_root}/config/anime/saveAnime(/?)', ConfigSaveAnimeHandler),
            (fr'{sickrage.app.config.general.web_root}/config/backuprestore(/?)', ConfigBackupRestoreHandler),
            (fr'{sickrage.app.config.general.web_root}/config/backuprestore/backup(/?)', ConfigBackupHandler),
            (fr'{sickrage.app.config.general.web_root}/config/backuprestore/restore(/?)', ConfigRestoreHandler),
            (fr'{sickrage.app.config.general.web_root}/config/backuprestore/saveBackupRestore(/?)', SaveBackupRestoreHandler),
            (fr'{sickrage.app.config.general.web_root}/config/general(/?)', ConfigGeneralHandler),
            (fr'{sickrage.app.config.general.web_root}/config/general/generateApiKey(/?)', GenerateApiKeyHandler),
            (fr'{sickrage.app.config.general.web_root}/config/general/saveRootDirs(/?)', SaveRootDirsHandler),
            (fr'{sickrage.app.config.general.web_root}/config/general/saveAddShowDefaults(/?)', SaveAddShowDefaultsHandler),
            (fr'{sickrage.app.config.general.web_root}/config/general/saveGeneral(/?)', SaveGeneralHandler),
            (fr'{sickrage.app.config.general.web_root}/config/notifications(/?)', ConfigNotificationsHandler),
            (fr'{sickrage.app.config.general.web_root}/config/notifications/saveNotifications(/?)', SaveNotificationsHandler),
            (fr'{sickrage.app.config.general.web_root}/config/postProcessing(/?)', ConfigPostProcessingHandler),
            (fr'{sickrage.app.config.general.web_root}/config/postProcessing/savePostProcessing(/?)', SavePostProcessingHandler),
            (fr'{sickrage.app.config.general.web_root}/config/postProcessing/testNaming(/?)', TestNamingHandler),
            (fr'{sickrage.app.config.general.web_root}/config/postProcessing/isNamingValid(/?)', IsNamingPatternValidHandler),
            (fr'{sickrage.app.config.general.web_root}/config/postProcessing/isRarSupported(/?)', IsRarSupportedHandler),
            (fr'{sickrage.app.config.general.web_root}/config/providers(/?)', ConfigProvidersHandler),
            (fr'{sickrage.app.config.general.web_root}/config/providers/canAddNewznabProvider(/?)', CanAddNewznabProviderHandler),
            (fr'{sickrage.app.config.general.web_root}/config/providers/canAddTorrentRssProvider(/?)', CanAddTorrentRssProviderHandler),
            (fr'{sickrage.app.config.general.web_root}/config/providers/getNewznabCategories(/?)', GetNewznabCategoriesHandler),
            (fr'{sickrage.app.config.general.web_root}/config/providers/saveProviders(/?)', SaveProvidersHandler),
            (fr'{sickrage.app.config.general.web_root}/config/qualitySettings(/?)', ConfigQualitySettingsHandler),
            (fr'{sickrage.app.config.general.web_root}/config/qualitySettings/saveQualities(/?)', SaveQualitiesHandler),
            (fr'{sickrage.app.config.general.web_root}/config/search(/?)', ConfigSearchHandler),
            (fr'{sickrage.app.config.general.web_root}/config/search/saveSearch(/?)', SaveSearchHandler),
            (fr'{sickrage.app.config.general.web_root}/config/subtitles(/?)', ConfigSubtitlesHandler),
            (fr'{sickrage.app.config.general.web_root}/config/subtitles/get_code(/?)', ConfigSubtitleGetCodeHandler),
            (fr'{sickrage.app.config.general.web_root}/config/subtitles/wanted_languages(/?)', ConfigSubtitlesWantedLanguagesHandler),
            (fr'{sickrage.app.config.general.web_root}/config/subtitles/saveSubtitles(/?)', SaveSubtitlesHandler),
        ]

        # Initialize Tornado application
        self.app = Application(
            handlers=sum(self.handlers.values(), []),
            debug=True,
            autoreload=False,
            gzip=sickrage.app.config.general.web_use_gzip,
            cookie_secret=sickrage.app.config.general.web_cookie_secret,
            login_url='%s/login/' % sickrage.app.config.general.web_root,
            templates=templates,
            default_handler_class=NotFoundHandler
        )

        # HTTPS Cert/Key object
        ssl_ctx = None
        if sickrage.app.config.general.enable_https:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(sickrage.app.https_cert_file, sickrage.app.https_key_file)

        # Web Server
        self.server = HTTPServer(self.app, ssl_options=ssl_ctx, xheaders=sickrage.app.config.general.handle_reverse_proxy)

        try:
            self.server.listen(sickrage.app.config.general.web_port, sickrage.app.web_host)
        except socket.error as e:
            sickrage.app.log.warning(e.strerror)
            raise SystemExit

    def load_ssl_certificate(self, certificate=None, private_key=None):
        if certificate and private_key:
            with open(sickrage.app.https_cert_file, 'w') as cert_out:
                cert_out.write(certificate)

            with open(sickrage.app.https_key_file, 'w') as key_out:
                key_out.write(private_key)
        else:
            if os.path.exists(sickrage.app.https_key_file) and os.path.exists(sickrage.app.https_cert_file):
                if self.is_certificate_valid() and not self.certificate_needs_renewal():
                    return True

            resp = sickrage.app.api.server.get_server_certificate(sickrage.app.config.general.server_id)
            if not resp or 'certificate' not in resp or 'private_key' not in resp:
                if not create_https_certificates(sickrage.app.https_cert_file, sickrage.app.https_key_file):
                    return False

                if not os.path.exists(sickrage.app.https_cert_file) or not os.path.exists(sickrage.app.https_key_file):
                    return False

                return True

            with open(sickrage.app.https_cert_file, 'w') as cert_out:
                cert_out.write(resp['certificate'])

            with open(sickrage.app.https_key_file, 'w') as key_out:
                key_out.write(resp['private_key'])

        sickrage.app.log.info("Loaded SSL certificate successfully, restarting server in 1 minute")

        if self.server:
            # restart after 1 minute
            IOLoop.current().add_timeout(datetime.timedelta(minutes=1), sickrage.app.restart)

        return True

    def certificate_needs_renewal(self):
        if not os.path.exists(sickrage.app.https_cert_file):
            return

        with open(sickrage.app.https_cert_file, 'rb') as f:
            cert_pem = f.read()

        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        not_valid_after = cert.not_valid_after

        return not_valid_after - datetime.datetime.utcnow() < (cert.not_valid_after - cert.not_valid_before) / 2

    def is_certificate_valid(self):
        if not os.path.exists(sickrage.app.https_cert_file):
            return

        with open(sickrage.app.https_cert_file, 'rb') as f:
            cert_pem = f.read()

        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        issuer = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0]
        subject = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0]

        if 'ZeroSSL' not in issuer.value:
            return False

        if subject.value != f'{sickrage.app.config.general.server_id}.external.sickrage.direct':
            return False

        try:
            ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            sans = ext.get_values_for_type(x509.DNSName)

            domains = [
                f'{sickrage.app.config.general.server_id}.external.sickrage.direct',
                f'{sickrage.app.config.general.server_id}.internal.sickrage.direct'
            ]

            for domain in sans:
                if domain not in domains:
                    return False
        except ExtensionNotFound:
            return False

        return True

    def shutdown(self):
        if self.started:
            self.started = False
            if self.server:
                self.server.close_all_connections()
                self.server.stop()
