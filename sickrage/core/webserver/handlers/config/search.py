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

from tornado.web import authenticated

import sickrage
from sickrage.core.config.helpers import change_nzb_dir, change_torrent_dir, change_failed_snatch_age, change_daily_searcher_freq, \
    change_backlog_searcher_freq
from sickrage.core.enums import NzbMethod, TorrentMethod, CheckPropersInterval
from sickrage.core.helpers import checkbox_to_value, try_int, clean_url, clean_host, torrent_webui_url
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigSearchHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/search.mako',
                           submenu=ConfigWebHandler.menu,
                           title=_('Config - Search Clients'),
                           header=_('Search Clients'),
                           topmenu='config',
                           controller='config',
                           action='search')


class SaveSearchHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        use_nzbs = self.get_argument('use_nzbs', None)
        use_torrents = self.get_argument('use_torrents', None)
        nzb_dir = self.get_argument('nzb_dir', None)
        sab_username = self.get_argument('sab_username', None)
        sab_password = self.get_argument('sab_password', None)
        sab_apikey = self.get_argument('sab_apikey', None)
        sab_category = self.get_argument('sab_category', None)
        sab_category_anime = self.get_argument('sab_category_anime', None)
        sab_category_backlog = self.get_argument('sab_category_backlog', None)
        sab_category_anime_backlog = self.get_argument('sab_category_anime_backlog', None)
        sab_host = self.get_argument('sab_host', None)
        nzbget_username = self.get_argument('nzbget_username', None)
        nzbget_password = self.get_argument('nzbget_password', None)
        nzbget_category = self.get_argument('nzbget_category', None)
        nzbget_category_backlog = self.get_argument('nzbget_category_backlog', None)
        nzbget_category_anime = self.get_argument('nzbget_category_anime', None)
        nzbget_category_anime_backlog = self.get_argument('nzbget_category_anime_backlog', None)
        nzbget_priority = self.get_argument('nzbget_priority', None)
        nzbget_host = self.get_argument('nzbget_host', None)
        syno_dsm_host = self.get_argument('syno_dsm_host', None)
        syno_dsm_username = self.get_argument('syno_dsm_username', None)
        syno_dsm_password = self.get_argument('syno_dsm_password', None)
        syno_dsm_path = self.get_argument('syno_dsm_path', None)
        nzbget_use_https = self.get_argument('nzbget_use_https', None)
        backlog_frequency = self.get_argument('backlog_frequency', None)
        dailysearch_frequency = self.get_argument('dailysearch_frequency', None)
        nzb_method = self.get_argument('nzb_method', None)
        torrent_method = self.get_argument('torrent_method', None)
        usenet_retention = self.get_argument('usenet_retention', None)
        download_propers = self.get_argument('download_propers', None)
        check_propers_interval = self.get_argument('check_propers_interval', None)
        allow_high_priority = self.get_argument('allow_high_priority', None)
        sab_forced = self.get_argument('sab_forced', None)
        randomize_providers = self.get_argument('randomize_providers', None)
        use_failed_snatcher = self.get_argument('use_failed_snatcher', None)
        failed_snatch_age = self.get_argument('failed_snatch_age', None)
        torrent_dir = self.get_argument('torrent_dir', None)
        torrent_username = self.get_argument('torrent_username', None)
        torrent_password = self.get_argument('torrent_password', None)
        torrent_host = self.get_argument('torrent_host', None)
        torrent_label = self.get_argument('torrent_label', None)
        torrent_label_anime = self.get_argument('torrent_label_anime', None)
        torrent_path = self.get_argument('torrent_path', None)
        torrent_verify_cert = self.get_argument('torrent_verify_cert', None)
        torrent_seed_time = self.get_argument('torrent_seed_time', None)
        torrent_paused = self.get_argument('torrent_paused', None)
        torrent_high_bandwidth = self.get_argument('torrent_high_bandwidth', None)
        torrent_rpc_url = self.get_argument('torrent_rpc_url', None)
        torrent_auth_type = self.get_argument('torrent_auth_type', None)
        ignore_words = self.get_argument('ignore_words', None)
        require_words = self.get_argument('require_words', None)
        ignored_subs_list = self.get_argument('ignored_subs_list', None)
        enable_rss_cache = self.get_argument('enable_rss_cache', None)
        torrent_file_to_magnet = self.get_argument('torrent_file_to_magnet', None)
        torrent_magnet_to_file = self.get_argument('torrent_magnet_to_file', None)
        download_unverified_magnet_link = self.get_argument('download_unverified_magnet_link', None)

        results = []

        if not change_nzb_dir(nzb_dir):
            results += [_("Unable to create directory ") + os.path.normpath(nzb_dir) + _(", dir not changed.")]

        if not change_torrent_dir(torrent_dir):
            results += [_("Unable to create directory ") + os.path.normpath(torrent_dir) + _(", dir not changed.")]

        change_failed_snatch_age(failed_snatch_age)
        change_daily_searcher_freq(dailysearch_frequency)
        change_backlog_searcher_freq(backlog_frequency)

        sickrage.app.config.failed_snatches.enable = checkbox_to_value(use_failed_snatcher)
        sickrage.app.config.general.use_nzbs = checkbox_to_value(use_nzbs)
        sickrage.app.config.general.use_torrents = checkbox_to_value(use_torrents)
        sickrage.app.config.general.nzb_method = NzbMethod[nzb_method]
        sickrage.app.config.general.torrent_method = TorrentMethod[torrent_method]
        sickrage.app.config.general.usenet_retention = try_int(usenet_retention, 500)
        sickrage.app.config.general.ignore_words = ignore_words if ignore_words else ""
        sickrage.app.config.general.require_words = require_words if require_words else ""
        sickrage.app.config.general.ignored_subs_list = ignored_subs_list if ignored_subs_list else ""
        sickrage.app.config.general.randomize_providers = checkbox_to_value(randomize_providers)
        sickrage.app.config.general.enable_rss_cache = checkbox_to_value(enable_rss_cache)
        sickrage.app.config.general.torrent_file_to_magnet = checkbox_to_value(torrent_file_to_magnet)
        sickrage.app.config.general.torrent_magnet_to_file = checkbox_to_value(torrent_magnet_to_file)
        sickrage.app.config.general.download_unverified_magnet_link = checkbox_to_value(download_unverified_magnet_link)
        sickrage.app.config.general.download_propers = checkbox_to_value(download_propers)
        sickrage.app.config.general.proper_searcher_interval = CheckPropersInterval[check_propers_interval]
        sickrage.app.config.general.allow_high_priority = checkbox_to_value(allow_high_priority)
        sickrage.app.config.sabnzbd.username = sab_username
        sickrage.app.config.sabnzbd.password = sab_password
        sickrage.app.config.sabnzbd.apikey = sab_apikey.strip()
        sickrage.app.config.sabnzbd.category = sab_category
        sickrage.app.config.sabnzbd.category_backlog = sab_category_backlog
        sickrage.app.config.sabnzbd.category_anime = sab_category_anime
        sickrage.app.config.sabnzbd.category_anime_backlog = sab_category_anime_backlog
        sickrage.app.config.sabnzbd.host = clean_url(sab_host)
        sickrage.app.config.sabnzbd.forced = checkbox_to_value(sab_forced)
        sickrage.app.config.nzbget.username = nzbget_username
        sickrage.app.config.nzbget.password = nzbget_password
        sickrage.app.config.nzbget.category = nzbget_category
        sickrage.app.config.nzbget.category_backlog = nzbget_category_backlog
        sickrage.app.config.nzbget.category_anime = nzbget_category_anime
        sickrage.app.config.nzbget.category_anime_backlog = nzbget_category_anime_backlog
        sickrage.app.config.nzbget.host = clean_host(nzbget_host)
        sickrage.app.config.nzbget.use_https = checkbox_to_value(nzbget_use_https)
        sickrage.app.config.nzbget.priority = try_int(nzbget_priority, 100)
        sickrage.app.config.synology.host = clean_host(syno_dsm_host)
        sickrage.app.config.synology.username = syno_dsm_username
        sickrage.app.config.synology.password = syno_dsm_password
        sickrage.app.config.synology.path = syno_dsm_path.rstrip('/\\')
        sickrage.app.config.torrent.username = torrent_username
        sickrage.app.config.torrent.password = torrent_password
        sickrage.app.config.torrent.label = torrent_label
        sickrage.app.config.torrent.label_anime = torrent_label_anime
        sickrage.app.config.torrent.verify_cert = checkbox_to_value(torrent_verify_cert)
        sickrage.app.config.torrent.path = torrent_path.rstrip('/\\')
        sickrage.app.config.torrent.seed_time = torrent_seed_time
        sickrage.app.config.torrent.paused = checkbox_to_value(torrent_paused)
        sickrage.app.config.torrent.high_bandwidth = checkbox_to_value(torrent_high_bandwidth)
        sickrage.app.config.torrent.host = clean_url(torrent_host)
        sickrage.app.config.torrent.rpc_url = torrent_rpc_url
        sickrage.app.config.torrent.auth_type = torrent_auth_type

        torrent_webui_url(reset=True)

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[SEARCH] Configuration Saved to Database'))

        return self.redirect("/config/search/")
