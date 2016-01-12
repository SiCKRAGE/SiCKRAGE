# Author: echel0n <sickrage.tv@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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
import logging
import os
import os.path
import re
import urlparse

from configobj import ConfigObjError, ConfigObj

import sickrage
from sickrage.core.common import SD, WANTED, SKIPPED
from sickrage.core.databases import main_db
from sickrage.core.helpers import backupVersionedFile, decrypt, encrypt, makeDir, generateCookieSecret
from sickrage.core.logger import SRLogger
from sickrage.core.nameparser import validator
from sickrage.core.searchers import backlog_searcher
from sickrage.providers import NewznabProvider, TorrentRssProvider, GenericProvider, NZBProvider, TorrentProvider


class Config(object):
    @staticmethod
    def change_HTTPS_CERT(https_cert):
        """
        Replace HTTPS Certificate file path
    
        :param https_cert: path to the new certificate file
        :return: True on success, False on failure
        """
        if https_cert == '':
            sickrage.HTTPS_CERT = ''
            return True

        if os.path.normpath(sickrage.HTTPS_CERT) != os.path.normpath(https_cert):
            if makeDir(os.path.dirname(os.path.abspath(https_cert))):
                sickrage.HTTPS_CERT = os.path.normpath(https_cert)
                logging.info("Changed https cert path to " + https_cert)
            else:
                return False
    
        return True

    @staticmethod
    def change_HTTPS_KEY(https_key):
        """
        Replace HTTPS Key file path
    
        :param https_key: path to the new key file
        :return: True on success, False on failure
        """
        if https_key == '':
            sickrage.HTTPS_KEY = ''
            return True

        if os.path.normpath(sickrage.HTTPS_KEY) != os.path.normpath(https_key):
            if makeDir(os.path.dirname(os.path.abspath(https_key))):
                sickrage.HTTPS_KEY = os.path.normpath(https_key)
                logging.info("Changed https key path to " + https_key)
            else:
                return False
    
        return True

    @staticmethod
    def change_LOG_DIR(new_log_dir, new_web_log):
        """
        Change logger directory for application and webserver
    
        :param new_log_dir: Path to new logger directory
        :param new_web_log: Enable/disable web logger
        :return: True on success, False on failure
        """
        log_dir_changed = False
        log_dir = os.path.normpath(os.path.join(sickrage.DATA_DIR, new_log_dir))
        web_log = Config.checkbox_to_value(new_web_log)

        if os.path.normpath(sickrage.LOG_DIR) != log_dir:
            if makeDir(log_dir):
                sickrage.LOG_DIR = log_dir
                SRLogger.logFile = sickrage.LOG_FILE = os.path.join(sickrage.LOG_DIR, 'sickrage.log')
                SRLogger.initialize()

                logging.info("Initialized new log file in " + sickrage.LOG_DIR)
                log_dir_changed = True

            else:
                return False

        if sickrage.WEB_LOG != web_log or log_dir_changed == True:
            sickrage.WEB_LOG = web_log
    
        return True

    @staticmethod
    def change_NZB_DIR(nzb_dir):
        """
        Change NZB Folder
    
        :param nzb_dir: New NZB Folder location
        :return: True on success, False on failure
        """
        if nzb_dir == '':
            sickrage.NZB_DIR = ''
            return True

        if os.path.normpath(sickrage.NZB_DIR) != os.path.normpath(nzb_dir):
            if makeDir(nzb_dir):
                sickrage.NZB_DIR = os.path.normpath(nzb_dir)
                logging.info("Changed NZB folder to " + nzb_dir)
            else:
                return False
    
        return True

    @staticmethod
    def change_TORRENT_DIR(torrent_dir):
        """
        Change torrent directory
    
        :param torrent_dir: New torrent directory
        :return: True on success, False on failure
        """
        if torrent_dir == '':
            sickrage.TORRENT_DIR = ''
            return True

        if os.path.normpath(sickrage.TORRENT_DIR) != os.path.normpath(torrent_dir):
            if makeDir(torrent_dir):
                sickrage.TORRENT_DIR = os.path.normpath(torrent_dir)
                logging.info("Changed torrent folder to " + torrent_dir)
            else:
                return False
    
        return True

    @staticmethod
    def change_TV_DOWNLOAD_DIR(tv_download_dir):
        """
        Change TV_DOWNLOAD directory (used by postprocessor)
    
        :param tv_download_dir: New tv download directory
        :return: True on success, False on failure
        """
        if tv_download_dir == '':
            sickrage.TV_DOWNLOAD_DIR = ''
            return True

        if os.path.normpath(sickrage.TV_DOWNLOAD_DIR) != os.path.normpath(tv_download_dir):
            if makeDir(tv_download_dir):
                sickrage.TV_DOWNLOAD_DIR = os.path.normpath(tv_download_dir)
                logging.info("Changed TV download folder to " + tv_download_dir)
            else:
                return False

        return True

    @staticmethod
    def change_AUTOPOSTPROCESSOR_FREQ(freq):
        """
        Change frequency of automatic postprocessing thread
        TODO: Make all thread frequency changers in config.py return True/False status
    
        :param freq: New frequency
        """
        sickrage.AUTOPOSTPROCESSOR_FREQ = Config.to_int(freq, default=sickrage.DEFAULT_AUTOPOSTPROCESSOR_FREQ)

        if sickrage.AUTOPOSTPROCESSOR_FREQ < sickrage.MIN_AUTOPOSTPROCESSOR_FREQ:
            sickrage.AUTOPOSTPROCESSOR_FREQ = sickrage.MIN_AUTOPOSTPROCESSOR_FREQ

        sickrage.Scheduler.modify_job('POSTPROCESSOR',
                                      trigger=sickrage.Scheduler.SRIntervalTrigger(
                                              **{'minutes': sickrage.AUTOPOSTPROCESSOR_FREQ,
                                                 'min': sickrage.MIN_AUTOPOSTPROCESSOR_FREQ}))

    @staticmethod
    def change_DAILY_SEARCHER_FREQ(freq):
        """
        Change frequency of daily search thread
    
        :param freq: New frequency
        """
        sickrage.DAILY_SEARCHER_FREQ = Config.to_int(freq, default=sickrage.DEFAULT_DAILY_SEARCHER_FREQ)
        sickrage.Scheduler.modify_job('DAILYSEARCHER',
                                      trigger=sickrage.Scheduler.SRIntervalTrigger(
                                              **{'minutes': sickrage.DAILY_SEARCHER_FREQ,
                                                 'min': sickrage.MIN_DAILY_SEARCHER_FREQ}))

    @staticmethod
    def change_BACKLOG_SEARCHER_FREQ(freq):
        """
        Change frequency of backlog thread
    
        :param freq: New frequency
        """
        sickrage.BACKLOG_SEARCHER_FREQ = Config.to_int(freq, default=sickrage.DEFAULT_BACKLOG_SEARCHER_FREQ)
        sickrage.MIN_BACKLOG_SEARCHER_FREQ = backlog_searcher.get_backlog_cycle_time()
        sickrage.Scheduler.modify_job('BACKLOG',
                                      trigger=sickrage.Scheduler.SRIntervalTrigger(
                                              **{'minutes': sickrage.BACKLOG_SEARCHER_FREQ,
                                                 'min': sickrage.MIN_BACKLOG_SEARCHER_FREQ}))

    @staticmethod
    def change_UPDATER_FREQ(freq):
        """
        Change frequency of daily updater thread
    
        :param freq: New frequency
        """
        sickrage.VERSION_UPDATER_FREQ = Config.to_int(freq, default=sickrage.DEFAULT_VERSION_UPDATE_FREQ)
        sickrage.Scheduler.modify_job('VERSIONUPDATER',
                                      trigger=sickrage.Scheduler.SRIntervalTrigger(
                                              **{'hours': sickrage.VERSION_UPDATER_FREQ,
                                                 'min': sickrage.MIN_VERSION_UPDATER_FREQ}))

    @staticmethod
    def change_SHOWUPDATE_HOUR(freq):
        """
        Change frequency of show updater thread
    
        :param freq: New frequency
        """
        sickrage.SHOWUPDATE_HOUR = Config.to_int(freq, default=sickrage.DEFAULT_SHOWUPDATE_HOUR)
        if sickrage.SHOWUPDATE_HOUR < 0 or sickrage.SHOWUPDATE_HOUR > 23:
            sickrage.SHOWUPDATE_HOUR = 0

        sickrage.Scheduler.modify_job('SHOWUPDATER',
                                      trigger=sickrage.Scheduler.SRIntervalTrigger(
                                              **{'hours': 1,
                                                 'start_date': datetime.datetime.now().replace(
                                                         hour=sickrage.SHOWUPDATE_HOUR)}))

    @staticmethod
    def change_SUBTITLE_SEARCHER_FREQ(freq):
        """
        Change frequency of subtitle thread
    
        :param freq: New frequency
        """
        sickrage.SUBTITLE_SEARCHER_FREQ = Config.to_int(freq, default=sickrage.DEFAULT_SUBTITLE_SEARCHER_FREQ)
        sickrage.Scheduler.modify_job('SUBTITLESEARCHER',
                                      trigger=sickrage.Scheduler.SRIntervalTrigger(
                                              **{'hours': sickrage.SUBTITLE_SEARCHER_FREQ,
                                                 'min': sickrage.MIN_SUBTITLE_SEARCHER_FREQ}))

    @staticmethod
    def change_VERSION_NOTIFY(version_notify):
        """
        Change frequency of versioncheck thread
    
        :param version_notify: New frequency
        """
        sickrage.VERSION_NOTIFY = Config.checkbox_to_value(version_notify)
        if not sickrage.VERSION_NOTIFY:
            sickrage.NEWEST_VERSION_STRING = None

    @staticmethod
    def change_DOWNLOAD_PROPERS(download_propers):
        """
        Enable/Disable proper download thread
        TODO: Make this return True/False on success/failure
    
        :param download_propers: New desired state
        """
        sickrage.DOWNLOAD_PROPERS = Config.checkbox_to_value(download_propers)
        job = sickrage.Scheduler.get_job('PROPERSEARCHER')
        (job.pause, job.resume)[sickrage.DOWNLOAD_PROPERS]()

    @staticmethod
    def change_USE_TRAKT(use_trakt):
        """
        Enable/disable trakt thread
        TODO: Make this return true/false on success/failure
    
        :param use_trakt: New desired state
        """
        sickrage.USE_TRAKT = Config.checkbox_to_value(use_trakt)
        job = sickrage.Scheduler.get_job('TRAKTSEARCHER')
        (job.pause, job.resume)[sickrage.USE_TRAKT]()

    @staticmethod
    def change_USE_SUBTITLES(use_subtitles):
        """
        Enable/Disable subtitle searcher
        TODO: Make this return true/false on success/failure
    
        :param use_subtitles: New desired state
        """
        sickrage.USE_SUBTITLES = Config.checkbox_to_value(use_subtitles)
        job = sickrage.Scheduler.get_job('SUBTITLESEARCHER')
        (job.pause, job.resume)[sickrage.USE_SUBTITLES]()

    @staticmethod
    def change_PROCESS_AUTOMATICALLY(process_automatically):
        """
        Enable/Disable postprocessor thread
        TODO: Make this return True/False on success/failure
    
        :param process_automatically: New desired state
        """
        sickrage.PROCESS_AUTOMATICALLY = Config.checkbox_to_value(process_automatically)
        job = sickrage.Scheduler.get_job('POSTPROCESSOR')
        (job.pause, job.resume)[sickrage.PROCESS_AUTOMATICALLY]()

    @staticmethod
    def CheckSection(CFG, sec):
        """ Check if INI section exists, if not create it """

        if sec in CFG:
            return True

        CFG[sec] = {}
        return False

    @staticmethod
    def checkbox_to_value(option, value_on=1, value_off=0):
        """
        Turns checkbox option 'on' or 'true' to value_on (1)
        any other value returns value_off (0)
        """

        if isinstance(option, list):
            option = option[-1]

        if option == 'on' or option == 'true':
            return value_on

        return value_off

    @staticmethod
    def clean_host(host, default_port=None):
        """
        Returns host or host:port or empty string from a given url or host
        If no port is found and default_port is given use host:default_port
        """

        host = host.strip()

        if host:

            match_host_port = re.search(r'(?:http.*://)?(?P<host>[^:/]+).?(?P<port>[0-9]*).*', host)

            cleaned_host = match_host_port.group('host')
            cleaned_port = match_host_port.group('port')

            if cleaned_host:

                if cleaned_port:
                    host = cleaned_host + ':' + cleaned_port

                elif default_port:
                    host = cleaned_host + ':' + str(default_port)

                else:
                    host = cleaned_host
    
            else:
                host = ''

        return host

    @staticmethod
    def clean_hosts(hosts, default_port=None):
        """
        Returns list of cleaned hosts by Config.clean_host
    
        :param hosts: list of hosts
        :param default_port: default port to use
        :return: list of cleaned hosts
        """
        cleaned_hosts = []

        for cur_host in [x.strip() for x in hosts.split(",")]:
            if cur_host:
                cleaned_host = Config.clean_host(cur_host, default_port)
                if cleaned_host:
                    cleaned_hosts.append(cleaned_host)

        if cleaned_hosts:
            cleaned_hosts = ",".join(cleaned_hosts)
    
        else:
            cleaned_hosts = ''

        return cleaned_hosts

    @staticmethod
    def clean_url(url):
        """
        Returns an cleaned url starting with a scheme and folder with trailing /
        or an empty string
        """

        if url and url.strip():

            url = url.strip()

            if '://' not in url:
                url = '//' + url

            scheme, netloc, path, query, fragment = urlparse.urlsplit(url, 'http')

            if not path:
                path = path + '/'

            cleaned_url = urlparse.urlunsplit((scheme, netloc, path, query, fragment))

        else:
            cleaned_url = ''

        return cleaned_url

    @staticmethod
    def to_int(val, default=0):
        """ Return int value of val or default on error """

        try:
            val = int(val)
        except Exception:
            val = default

        return val

    ################################################################################
    # Check_setting_int                                                            #
    ################################################################################
    @staticmethod
    def minimax(val, default, low, high):
        """ Return value forced within range """

        val = Config.to_int(val, default=default)

        if val < low:
            return low
        if val > high:
            return high

        return val

    ################################################################################
    # Check_setting_int                                                            #
    ################################################################################
    @staticmethod
    def check_setting_int(config, cfg_name, item_name, def_val, silent=True):
        try:
            my_val = config[cfg_name][item_name]
            if str(my_val).lower() == "true":
                my_val = 1
            elif str(my_val).lower() == "false":
                my_val = 0

            my_val = int(my_val)

            if str(my_val) == str(None):
                raise
        except Exception:
            my_val = def_val
            try:
                config[cfg_name][item_name] = my_val
            except Exception:
                config[cfg_name] = {}
                config[cfg_name][item_name] = my_val

        if not silent:
            logging.debug(item_name + " -> " + str(my_val))

        return my_val

    ################################################################################
    # Check_setting_float                                                          #
    ################################################################################
    @staticmethod
    def check_setting_float(config, cfg_name, item_name, def_val, silent=True):
        try:
            my_val = float(config[cfg_name][item_name])
            if str(my_val) == str(None):
                raise
        except Exception:
            my_val = def_val
            try:
                config[cfg_name][item_name] = my_val
            except Exception:
                config[cfg_name] = {}
                config[cfg_name][item_name] = my_val

        if not silent:
            logging.debug(item_name + " -> " + str(my_val))

        return my_val

    ################################################################################
    # Check_setting_str                                                            #
    ################################################################################
    @staticmethod
    def check_setting_str(config, cfg_name, item_name, def_val, silent=True, censor_log=False):
        # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
        if bool(item_name.find('password') + 1):
            encryption_version = sickrage.ENCRYPTION_VERSION
        else:
            encryption_version = 0

        try:
            my_val = decrypt(config[cfg_name][item_name], encryption_version)
            if str(my_val) == str(None):
                raise
        except Exception:
            my_val = def_val
            try:
                config[cfg_name][item_name] = encrypt(my_val, encryption_version)
            except Exception:
                config[cfg_name] = {}
                config[cfg_name][item_name] = encrypt(my_val, encryption_version)

        if censor_log or (cfg_name, item_name) in SRLogger.censoredItems:
            SRLogger.censoredItems[cfg_name, item_name] = my_val

        if not silent:
            logging.debug(item_name + " -> " + my_val)

        return my_val

    class ConfigMigrator():
        def __init__(self, config_obj):
            """
            Initializes a config migrator that can take the config from the version indicated in the config
            file up to the version required by SB
            """

            self.config_obj = config_obj

            # check the version of the config
            self.config_version = Config.check_setting_int(config_obj, 'General', 'config_version',
                                                           sickrage.CONFIG_VERSION)
            self.expected_config_version = sickrage.CONFIG_VERSION
            self.migration_names = {
                1: 'Custom naming',
                2: 'Sync backup number with version number',
                3: 'Rename omgwtfnzb variables',
                4: 'Add newznab catIDs',
                5: 'Metadata update',
                6: 'Convert from XBMC to new KODI variables',
                7: 'Use version 2 for password encryption'
            }

        def migrate_config(self):
            """
            Calls each successive migration until the config is the same version as SB expects
            """

            if self.config_version > self.expected_config_version:
                logging.log_error_and_exit(
                        """Your config version (%i) has been incremented past what this version of SiCKRAGE supports (%i).
                        If you have used other forks or a newer version of SiCKRAGE, your config file may be unusable due to their modifications.""" %
                        (self.config_version, self.expected_config_version)
                )

            sickrage.CONFIG_VERSION = self.config_version

            while self.config_version < self.expected_config_version:
                next_version = self.config_version + 1

                if next_version in self.migration_names:
                    migration_name = ': ' + self.migration_names[next_version]
                else:
                    migration_name = ''

                logging.info("Backing up config before upgrade")
                if not backupVersionedFile(sickrage.CONFIG_FILE, self.config_version):
                    logging.log_error_and_exit("Config backup failed, abort upgrading config")
                else:
                    logging.info("Proceeding with upgrade")

                # do the migration, expect a method named _migrate_v<num>
                logging.info("Migrating config up to version " + str(next_version) + migration_name)
                getattr(self, '_migrate_v' + str(next_version))()
                self.config_version = next_version

                # save new config after migration
                sickrage.CONFIG_VERSION = self.config_version

            return self.config_obj

        # Migration v1: Custom naming
        def _migrate_v1(self):
            """
            Reads in the old naming settings from your config and generates a new config template from them.
            """

            sickrage.NAMING_PATTERN = self._name_to_pattern()
            logging.info(
                "Based on your old settings I'm setting your new naming pattern to: " + sickrage.NAMING_PATTERN)

            sickrage.NAMING_CUSTOM_ABD = bool(Config.check_setting_int(self.config_obj, 'General', 'naming_dates', 0))

            if sickrage.NAMING_CUSTOM_ABD:
                sickrage.NAMING_ABD_PATTERN = self._name_to_pattern(True)
                logging.info(
                    "Adding a custom air-by-date naming pattern to your config: " + sickrage.NAMING_ABD_PATTERN)
            else:
                sickrage.NAMING_ABD_PATTERN = validator.name_abd_presets[0]

            sickrage.NAMING_MULTI_EP = int(
                Config.check_setting_int(self.config_obj, 'General', 'NAMING_MULTI_EP_TYPE', 1))

            # see if any of their shows used season folders
            season_folder_shows = main_db.MainDB().select("SELECT * FROM tv_shows WHERE flatten_folders = 0")

            # if any shows had season folders on then prepend season folder to the pattern
            if season_folder_shows:

                old_season_format = Config.check_setting_str(self.config_obj, 'General', 'season_folders_format',
                                                             'Season %02d')

                if old_season_format:
                    try:
                        new_season_format = old_season_format % 9
                        new_season_format = str(new_season_format).replace('09', '%0S')
                        new_season_format = new_season_format.replace('9', '%S')

                        logging.info(
                                "Changed season folder format from " + old_season_format + " to " + new_season_format + ", prepending it to your naming config")
                        sickrage.NAMING_PATTERN = new_season_format + os.sep + sickrage.NAMING_PATTERN

                    except (TypeError, ValueError):
                        logging.error("Can't change " + old_season_format + " to new season format")

            # if no shows had it on then don't flatten any shows and don't put season folders in the config
            else:

                logging.info("No shows were using season folders before so I'm disabling flattening on all shows")

                # don't flatten any shows at all
                main_db.MainDB().action("UPDATE tv_shows SET flatten_folders = 0")

            sickrage.NAMING_FORCE_FOLDERS = validator.check_force_season_folders()

        def _name_to_pattern(self, abd=False):

            # get the old settings from the file
            use_periods = bool(Config.check_setting_int(self.config_obj, 'General', 'naming_use_periods', 0))
            ep_type = Config.check_setting_int(self.config_obj, 'General', 'NAMING_EP_TYPE', 0)
            sep_type = Config.check_setting_int(self.config_obj, 'General', 'NAMING_SEP_TYPE', 0)
            use_quality = bool(Config.check_setting_int(self.config_obj, 'General', 'naming_quality', 0))

            use_show_name = bool(Config.check_setting_int(self.config_obj, 'General', 'naming_show_name', 1))
            use_ep_name = bool(Config.check_setting_int(self.config_obj, 'General', 'naming_ep_name', 1))

            # make the presets into templates
            naming_ep_type = ("%Sx%0E",
                              "s%0Se%0E",
                              "S%0SE%0E",
                              "%0Sx%0E")
            naming_sep_type = (" - ", " ")

            # set up our data to use
            if use_periods:
                show_name = '%S.N'
                ep_name = '%E.N'
                ep_quality = '%Q.N'
                abd_string = '%A.D'
            else:
                show_name = '%SN'
                ep_name = '%EN'
                ep_quality = '%QN'
                abd_string = '%A-D'

            if abd:
                ep_string = abd_string
            else:
                ep_string = naming_ep_type[ep_type]

            finalName = ""

            # start with the show name
            if use_show_name:
                finalName += show_name + naming_sep_type[sep_type]

            # add the season/ep stuff
            finalName += ep_string

            # add the episode name
            if use_ep_name:
                finalName += naming_sep_type[sep_type] + ep_name

            # add the quality
            if use_quality:
                finalName += naming_sep_type[sep_type] + ep_quality

            if use_periods:
                finalName = re.sub(r"\s+", ".", finalName)

            return finalName

        # Migration v2: Dummy migration to sync backup number with config version number
        def _migrate_v2(self):
            return

        # Migration v2: Rename omgwtfnzb variables
        def _migrate_v3(self):
            """
            Reads in the old naming settings from your config and generates a new config template from them.
            """
            # get the old settings from the file and store them in the new variable names
            sickrage.OMGWTFNZBS_USERNAME = Config.check_setting_str(self.config_obj, 'omgwtfnzbs', 'omgwtfnzbs_uid', '')
            sickrage.OMGWTFNZBS_APIKEY = Config.check_setting_str(self.config_obj, 'omgwtfnzbs', 'omgwtfnzbs_key', '')

        # Migration v4: Add default newznab catIDs
        def _migrate_v4(self):
            """ Update newznab providers so that the category IDs can be set independently via the config """

            new_newznab_data = []
            old_newznab_data = Config.check_setting_str(self.config_obj, 'Newznab', 'newznab_data', '')

            if old_newznab_data:
                old_newznab_data_list = old_newznab_data.split("!!!")

                for cur_provider_data in old_newznab_data_list:
                    try:
                        name, url, key, enabled = cur_provider_data.split("|")
                    except ValueError:
                        logging.error("Skipping Newznab provider string: '" + cur_provider_data + "', incorrect format")
                        continue

                    if name == 'Sick Beard Index':
                        key = '0'

                    if name == 'NZBs.org':
                        catIDs = '5030,5040,5060,5070,5090'
                    else:
                        catIDs = '5030,5040,5060'

                    cur_provider_data_list = [name, url, key, catIDs, enabled]
                    new_newznab_data.append("|".join(cur_provider_data_list))

                sickrage.NEWZNAB_DATA = "!!!".join(new_newznab_data)

        # Migration v5: Metadata upgrade
        def _migrate_v5(self):
            """ Updates metadata values to the new format """

            """ Quick overview of what the upgrade does:
    
            new | old | description (new)
            ----+-----+--------------------
              1 |  1  | show metadata
              2 |  2  | episode metadata
              3 |  4  | show fanart
              4 |  3  | show poster
              5 |  -  | show banner
              6 |  5  | episode thumb
              7 |  6  | season poster
              8 |  -  | season banner
              9 |  -  | season all poster
             10 |  -  | season all banner
    
            Note that the ini places start at 1 while the list index starts at 0.
            old format: 0|0|0|0|0|0 -- 6 places
            new format: 0|0|0|0|0|0|0|0|0|0 -- 10 places
    
            Drop the use of use_banner option.
            Migrate the poster override to just using the banner option (applies to xbmc only).
            """

            metadata_xbmc = Config.check_setting_str(self.config_obj, 'General', 'metadata_xbmc', '0|0|0|0|0|0')
            metadata_xbmc_12plus = Config.check_setting_str(self.config_obj, 'General', 'metadata_xbmc_12plus',
                                                            '0|0|0|0|0|0')
            metadata_mediabrowser = Config.check_setting_str(self.config_obj, 'General', 'metadata_mediabrowser',
                                                             '0|0|0|0|0|0')
            metadata_ps3 = Config.check_setting_str(self.config_obj, 'General', 'metadata_ps3', '0|0|0|0|0|0')
            metadata_wdtv = Config.check_setting_str(self.config_obj, 'General', 'metadata_wdtv', '0|0|0|0|0|0')
            metadata_tivo = Config.check_setting_str(self.config_obj, 'General', 'metadata_tivo', '0|0|0|0|0|0')
            metadata_mede8er = Config.check_setting_str(self.config_obj, 'General', 'metadata_mede8er', '0|0|0|0|0|0')

            use_banner = bool(Config.check_setting_int(self.config_obj, 'General', 'use_banner', 0))

            def _migrate_metadata(metadata, metadata_name, use_banner):
                cur_metadata = metadata.split('|')
                # if target has the old number of values, do upgrade
                if len(cur_metadata) == 6:
                    logging.info("Upgrading " + metadata_name + " metadata, old value: " + metadata)
                    cur_metadata.insert(4, '0')
                    cur_metadata.append('0')
                    cur_metadata.append('0')
                    cur_metadata.append('0')
                    # swap show fanart, show poster
                    cur_metadata[3], cur_metadata[2] = cur_metadata[2], cur_metadata[3]
                    # if user was using use_banner to override the poster, instead enable the banner option and deactivate poster
                    if metadata_name == 'XBMC' and use_banner:
                        cur_metadata[4], cur_metadata[3] = cur_metadata[3], '0'
                    # write new format
                    metadata = '|'.join(cur_metadata)
                    logging.info("Upgrading " + metadata_name + " metadata, new value: " + metadata)

                elif len(cur_metadata) == 10:

                    metadata = '|'.join(cur_metadata)
                    logging.info("Keeping " + metadata_name + " metadata, value: " + metadata)

                else:
                    logging.error("Skipping " + metadata_name + " metadata: '" + metadata + "', incorrect format")
                    metadata = '0|0|0|0|0|0|0|0|0|0'
                    logging.info("Setting " + metadata_name + " metadata, new value: " + metadata)

                return metadata

            sickrage.METADATA_XBMC = _migrate_metadata(metadata_xbmc, 'XBMC', use_banner)
            sickrage.METADATA_XBMC_12PLUS = _migrate_metadata(metadata_xbmc_12plus, 'XBMC 12+', use_banner)
            sickrage.METADATA_MEDIABROWSER = _migrate_metadata(metadata_mediabrowser, 'MediaBrowser', use_banner)
            sickrage.METADATA_PS3 = _migrate_metadata(metadata_ps3, 'PS3', use_banner)
            sickrage.METADATA_WDTV = _migrate_metadata(metadata_wdtv, 'WDTV', use_banner)
            sickrage.METADATA_TIVO = _migrate_metadata(metadata_tivo, 'TIVO', use_banner)
            sickrage.METADATA_MEDE8ER = _migrate_metadata(metadata_mede8er, 'Mede8er', use_banner)

        # Migration v6: Convert from XBMC to KODI variables
        def _migrate_v6(self):
            sickrage.USE_KODI = bool(Config.check_setting_int(self.config_obj, 'XBMC', 'use_xbmc', 0))
            sickrage.KODI_ALWAYS_ON = bool(Config.check_setting_int(self.config_obj, 'XBMC', 'xbmc_always_on', 1))
            sickrage.KODI_NOTIFY_ONSNATCH = bool(
                Config.check_setting_int(self.config_obj, 'XBMC', 'xbmc_notify_onsnatch', 0))
            sickrage.KODI_NOTIFY_ONDOWNLOAD = bool(
                Config.check_setting_int(self.config_obj, 'XBMC', 'xbmc_notify_ondownload', 0))
            sickrage.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                    Config.check_setting_int(self.config_obj, 'XBMC', 'xbmc_notify_onsubtitledownload', 0))
            sickrage.KODI_UPDATE_LIBRARY = bool(
                Config.check_setting_int(self.config_obj, 'XBMC', 'xbmc_update_library', 0))
            sickrage.KODI_UPDATE_FULL = bool(Config.check_setting_int(self.config_obj, 'XBMC', 'xbmc_update_full', 0))
            sickrage.KODI_UPDATE_ONLYFIRST = bool(
                Config.check_setting_int(self.config_obj, 'XBMC', 'xbmc_update_onlyfirst', 0))
            sickrage.KODI_HOST = Config.check_setting_str(self.config_obj, 'XBMC', 'xbmc_host', '')
            sickrage.KODI_USERNAME = Config.check_setting_str(self.config_obj, 'XBMC', 'xbmc_username', '',
                                                              censor_log=True)
            sickrage.KODI_PASSWORD = Config.check_setting_str(self.config_obj, 'XBMC', 'xbmc_password', '',
                                                              censor_log=True)
            sickrage.METADATA_KODI = Config.check_setting_str(self.config_obj, 'General', 'metadata_xbmc',
                                                              '0|0|0|0|0|0|0|0|0|0')
            sickrage.METADATA_KODI_12PLUS = Config.check_setting_str(self.config_obj, 'General', 'metadata_xbmc_12plus',
                                                                     '0|0|0|0|0|0|0|0|0|0')

        # Migration v6: Use version 2 for password encryption
        def _migrate_v7(self):
            sickrage.ENCRYPTION_VERSION = 2

    @staticmethod
    def load_config(cfgfile, defaults=False):
        # load config and use defaults if requested
        if not os.path.isfile(cfgfile):
            if not defaults:
                raise ConfigObjError
            cfgobj = ConfigObj(cfgfile)
        else:
            cfgobj = Config.ConfigMigrator(ConfigObj(cfgfile)).migrate_config()

        # config sanity check
        Config.CheckSection(cfgobj, 'General')
        Config.CheckSection(cfgobj, 'Blackhole')
        Config.CheckSection(cfgobj, 'Newzbin')
        Config.CheckSection(cfgobj, 'SABnzbd')
        Config.CheckSection(cfgobj, 'NZBget')
        Config.CheckSection(cfgobj, 'KODI')
        Config.CheckSection(cfgobj, 'PLEX')
        Config.CheckSection(cfgobj, 'Emby')
        Config.CheckSection(cfgobj, 'Growl')
        Config.CheckSection(cfgobj, 'Prowl')
        Config.CheckSection(cfgobj, 'Twitter')
        Config.CheckSection(cfgobj, 'Boxcar')
        Config.CheckSection(cfgobj, 'Boxcar2')
        Config.CheckSection(cfgobj, 'NMJ')
        Config.CheckSection(cfgobj, 'NMJv2')
        Config.CheckSection(cfgobj, 'Synology')
        Config.CheckSection(cfgobj, 'SynologyNotifier')
        Config.CheckSection(cfgobj, 'pyTivo')
        Config.CheckSection(cfgobj, 'NMA')
        Config.CheckSection(cfgobj, 'Pushalot')
        Config.CheckSection(cfgobj, 'Pushbullet')
        Config.CheckSection(cfgobj, 'Subtitles')
        Config.CheckSection(cfgobj, 'pyTivo')
        Config.CheckSection(cfgobj, 'theTVDB')
        Config.CheckSection(cfgobj, 'Trakt')

        # Need to be before any passwords
        sickrage.ENCRYPTION_VERSION = Config.check_setting_int(
                cfgobj, 'General', 'encryption_version', 0
        )

        sickrage.ENCRYPTION_SECRET = Config.check_setting_str(
                cfgobj, 'General', 'encryption_secret', generateCookieSecret(), censor_log=True
        )

        sickrage.DEBUG = bool(Config.check_setting_int(cfgobj, 'General', 'debug', 0))
        sickrage.DEVELOPER = bool(Config.check_setting_int(cfgobj, 'General', 'developer', 0))

        # logging settings
        sickrage.LOG_DIR = os.path.normpath(
                os.path.join(sickrage.DATA_DIR, Config.check_setting_str(cfgobj, 'General', 'log_dir', 'Logs'))
        )

        sickrage.LOG_NR = Config.check_setting_int(cfgobj, 'General', 'log_nr', 5)
        sickrage.LOG_SIZE = Config.check_setting_int(cfgobj, 'General', 'log_size', 1048576)

        sickrage.LOG_FILE = Config.check_setting_str(
                cfgobj, 'General', 'log_file', os.path.join(sickrage.LOG_DIR, 'sickrage.log')
        )

        # misc settings
        sickrage.GUI_NAME = Config.check_setting_str(cfgobj, 'GUI', 'gui_name', 'slick')
        sickrage.GUI_DIR = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'gui', sickrage.GUI_NAME)
        sickrage.THEME_NAME = Config.check_setting_str(cfgobj, 'GUI', 'theme_name', 'dark')
        sickrage.SOCKET_TIMEOUT = Config.check_setting_int(cfgobj, 'General', 'socket_timeout', 30)

        sickrage.DEFAULT_PAGE = Config.check_setting_str(cfgobj, 'General', 'default_page', 'home')

        # git settings
        sickrage.GIT_REMOTE_URL = Config.check_setting_str(
                cfgobj, 'General', 'git_remote_url',
                'https://github.com/{}/{}.git'.format(sickrage.GIT_ORG, sickrage.GIT_REPO)
        )
        sickrage.GIT_PATH = Config.check_setting_str(cfgobj, 'General', 'git_path', '')
        sickrage.GIT_AUTOISSUES = bool(Config.check_setting_int(cfgobj, 'General', 'git_autoissues', 0))
        sickrage.GIT_USERNAME = Config.check_setting_str(cfgobj, 'General', 'git_username', '')
        sickrage.GIT_PASSWORD = Config.check_setting_str(cfgobj, 'General', 'git_password', '', censor_log=True)
        sickrage.GIT_NEWVER = bool(Config.check_setting_int(cfgobj, 'General', 'git_newver', 0))
        sickrage.GIT_RESET = bool(Config.check_setting_int(cfgobj, 'General', 'git_reset', 1))
        sickrage.GIT_BRANCH = Config.check_setting_str(cfgobj, 'General', 'branch', '')
        sickrage.GIT_REMOTE = Config.check_setting_str(cfgobj, 'General', 'git_remote', 'origin')
        sickrage.CUR_COMMIT_HASH = Config.check_setting_str(cfgobj, 'General', 'cur_commit_hash', '')
        sickrage.CUR_COMMIT_BRANCH = Config.check_setting_str(cfgobj, 'General', 'cur_commit_branch', '')

        # cache settings
        sickrage.CACHE_DIR = Config.check_setting_str(cfgobj, 'General', 'cache_dir', 'cache')
        if not os.path.isabs(sickrage.CACHE_DIR):
            sickrage.CACHE_DIR = os.path.join(sickrage.DATA_DIR, sickrage.CACHE_DIR)

        # web settings
        sickrage.WEB_PORT = Config.check_setting_int(cfgobj, 'General', 'web_port', 8081)
        sickrage.WEB_HOST = Config.check_setting_str(cfgobj, 'General', 'web_host', '0.0.0.0')
        sickrage.WEB_IPV6 = bool(Config.check_setting_int(cfgobj, 'General', 'web_ipv6', 0))
        sickrage.WEB_ROOT = Config.check_setting_str(cfgobj, 'General', 'web_root', '').rstrip("/")
        sickrage.WEB_LOG = bool(Config.check_setting_int(cfgobj, 'General', 'web_log', 0))
        sickrage.WEB_USERNAME = Config.check_setting_str(cfgobj, 'General', 'web_username', '', censor_log=True)
        sickrage.WEB_PASSWORD = Config.check_setting_str(cfgobj, 'General', 'web_password', '', censor_log=True)
        sickrage.WEB_COOKIE_SECRET = Config.check_setting_str(
                cfgobj, 'General', 'web_cookie_secret', generateCookieSecret(), censor_log=True
        )
        sickrage.WEB_USE_GZIP = bool(Config.check_setting_int(cfgobj, 'General', 'web_use_gzip', 1))

        sickrage.SSL_VERIFY = bool(Config.check_setting_int(cfgobj, 'General', 'ssl_verify', 1))
        sickrage.LAUNCH_BROWSER = bool(Config.check_setting_int(cfgobj, 'General', 'launch_browser', 1))
        sickrage.INDEXER_DEFAULT_LANGUAGE = Config.check_setting_str(cfgobj, 'General', 'indexerDefaultLang', 'en')
        sickrage.EP_DEFAULT_DELETED_STATUS = Config.check_setting_int(cfgobj, 'General', 'ep_default_deleted_status', 6)
        sickrage.DOWNLOAD_URL = Config.check_setting_str(cfgobj, 'General', 'download_url', "")
        sickrage.LOCALHOST_IP = Config.check_setting_str(cfgobj, 'General', 'localhost_ip', '')
        sickrage.CPU_PRESET = Config.check_setting_str(cfgobj, 'General', 'cpu_preset', 'NORMAL')
        sickrage.ANON_REDIRECT = Config.check_setting_str(cfgobj, 'General', 'anon_redirect', 'http://dereferer.org/?')
        sickrage.PROXY_SETTING = Config.check_setting_str(cfgobj, 'General', 'proxy_setting', '')
        sickrage.PROXY_INDEXERS = bool(Config.check_setting_int(cfgobj, 'General', 'proxy_indexers', 1))
        sickrage.TRASH_REMOVE_SHOW = bool(Config.check_setting_int(cfgobj, 'General', 'trash_remove_show', 0))
        sickrage.TRASH_ROTATE_LOGS = bool(Config.check_setting_int(cfgobj, 'General', 'trash_rotate_logs', 0))
        sickrage.SORT_ARTICLE = bool(Config.check_setting_int(cfgobj, 'General', 'sort_article', 0))
        sickrage.API_KEY = Config.check_setting_str(cfgobj, 'General', 'api_key', '', censor_log=True)
        sickrage.ENABLE_HTTPS = bool(Config.check_setting_int(cfgobj, 'General', 'enable_https', 0))
        sickrage.HTTPS_CERT = Config.check_setting_str(cfgobj, 'General', 'https_cert', 'server.crt')
        sickrage.HTTPS_KEY = Config.check_setting_str(cfgobj, 'General', 'https_key', 'server.key')
        sickrage.HANDLE_REVERSE_PROXY = bool(Config.check_setting_int(cfgobj, 'General', 'handle_reverse_proxy', 0))
        sickrage.NEWS_LAST_READ = Config.check_setting_str(cfgobj, 'General', 'news_last_read', '1970-01-01')

        # show settings
        sickrage.ROOT_DIRS = Config.check_setting_str(cfgobj, 'General', 'root_dirs', '')
        sickrage.QUALITY_DEFAULT = Config.check_setting_int(cfgobj, 'General', 'quality_default', SD)
        sickrage.STATUS_DEFAULT = Config.check_setting_int(cfgobj, 'General', 'status_default', SKIPPED)
        sickrage.STATUS_DEFAULT_AFTER = Config.check_setting_int(cfgobj, 'General', 'status_default_after', WANTED)
        sickrage.VERSION_NOTIFY = bool(Config.check_setting_int(cfgobj, 'General', 'version_notify', 1))
        sickrage.AUTO_UPDATE = bool(Config.check_setting_int(cfgobj, 'General', 'auto_update', 0))
        sickrage.NOTIFY_ON_UPDATE = bool(Config.check_setting_int(cfgobj, 'General', 'notify_on_update', 1))
        sickrage.FLATTEN_FOLDERS_DEFAULT = bool(
            Config.check_setting_int(cfgobj, 'General', 'flatten_folders_default', 0))
        sickrage.INDEXER_DEFAULT = Config.check_setting_int(cfgobj, 'General', 'indexer_default', 0)
        sickrage.INDEXER_TIMEOUT = Config.check_setting_int(cfgobj, 'General', 'indexer_timeout', 20)
        sickrage.ANIME_DEFAULT = bool(Config.check_setting_int(cfgobj, 'General', 'anime_default', 0))
        sickrage.SCENE_DEFAULT = bool(Config.check_setting_int(cfgobj, 'General', 'scene_default', 0))
        sickrage.ARCHIVE_DEFAULT = bool(Config.check_setting_int(cfgobj, 'General', 'archive_default', 0))

        # naming settings
        sickrage.NAMING_PATTERN = Config.check_setting_str(cfgobj, 'General', 'naming_pattern',
                                                           'Season %0S/%SN - S%0SE%0E - %EN')
        sickrage.NAMING_ABD_PATTERN = Config.check_setting_str(cfgobj, 'General', 'naming_abd_pattern',
                                                               '%SN - %A.D - %EN')
        sickrage.NAMING_CUSTOM_ABD = bool(Config.check_setting_int(cfgobj, 'General', 'naming_custom_abd', 0))
        sickrage.NAMING_SPORTS_PATTERN = Config.check_setting_str(cfgobj, 'General', 'naming_sports_pattern',
                                                                  '%SN - %A-D - %EN')
        sickrage.NAMING_ANIME_PATTERN = Config.check_setting_str(cfgobj, 'General', 'naming_anime_pattern',
                                                                 'Season %0S/%SN - S%0SE%0E - %EN')
        sickrage.NAMING_ANIME = Config.check_setting_int(cfgobj, 'General', 'naming_anime', 3)
        sickrage.NAMING_CUSTOM_SPORTS = bool(Config.check_setting_int(cfgobj, 'General', 'naming_custom_sports', 0))
        sickrage.NAMING_CUSTOM_ANIME = bool(Config.check_setting_int(cfgobj, 'General', 'naming_custom_anime', 0))
        sickrage.NAMING_MULTI_EP = Config.check_setting_int(cfgobj, 'General', 'naming_multi_ep', 1)
        sickrage.NAMING_ANIME_MULTI_EP = Config.check_setting_int(cfgobj, 'General', 'naming_anime_multi_ep', 1)
        sickrage.NAMING_STRIP_YEAR = bool(Config.check_setting_int(cfgobj, 'General', 'naming_strip_year', 0))

        # provider settings
        sickrage.USE_NZBS = bool(Config.check_setting_int(cfgobj, 'General', 'use_nzbs', 0))
        sickrage.USE_TORRENTS = bool(Config.check_setting_int(cfgobj, 'General', 'use_torrents', 1))
        sickrage.NZB_METHOD = Config.check_setting_str(cfgobj, 'General', 'nzb_method', 'blackhole')
        sickrage.TORRENT_METHOD = Config.check_setting_str(cfgobj, 'General', 'torrent_method', 'blackhole')
        sickrage.DOWNLOAD_PROPERS = bool(Config.check_setting_int(cfgobj, 'General', 'download_propers', 1))
        sickrage.PROPER_SEARCHER_INTERVAL = Config.check_setting_str(cfgobj, 'General', 'check_propers_interval',
                                                                     'daily')
        sickrage.RANDOMIZE_PROVIDERS = bool(Config.check_setting_int(cfgobj, 'General', 'randomize_providers', 0))
        sickrage.ALLOW_HIGH_PRIORITY = bool(Config.check_setting_int(cfgobj, 'General', 'allow_high_priority', 1))
        sickrage.SKIP_REMOVED_FILES = bool(Config.check_setting_int(cfgobj, 'General', 'skip_removed_files', 0))
        sickrage.USENET_RETENTION = Config.check_setting_int(cfgobj, 'General', 'usenet_retention', 500)

        # scheduler settings
        sickrage.AUTOPOSTPROCESSOR_FREQ = Config.check_setting_int(
                cfgobj, 'General', 'autopostprocessor_frequency', sickrage.DEFAULT_AUTOPOSTPROCESSOR_FREQ
        )

        sickrage.SUBTITLE_SEARCHER_FREQ = Config.check_setting_int(
                cfgobj, 'Subtitles', 'subtitles_finder_frequency', sickrage.DEFAULT_SUBTITLE_SEARCHER_FREQ
        )

        sickrage.NAMECACHE_FREQ = Config.check_setting_int(cfgobj, 'General', 'namecache_frequency',
                                                           sickrage.DEFAULT_NAMECACHE_FREQ)
        sickrage.DAILY_SEARCHER_FREQ = Config.check_setting_int(cfgobj, 'General', 'dailysearch_frequency',
                                                                sickrage.DEFAULT_DAILY_SEARCHER_FREQ)
        sickrage.BACKLOG_SEARCHER_FREQ = Config.check_setting_int(cfgobj, 'General', 'backlog_frequency',
                                                                  sickrage.DEFAULT_BACKLOG_SEARCHER_FREQ)
        sickrage.VERSION_UPDATER_FREQ = Config.check_setting_int(cfgobj, 'General', 'update_frequency',
                                                                 sickrage.DEFAULT_VERSION_UPDATE_FREQ)
        sickrage.SHOWUPDATE_HOUR = Config.check_setting_int(cfgobj, 'General', 'showupdate_hour',
                                                            sickrage.DEFAULT_SHOWUPDATE_HOUR)
        sickrage.BACKLOG_DAYS = Config.check_setting_int(cfgobj, 'General', 'backlog_days', 7)

        sickrage.NZB_DIR = Config.check_setting_str(cfgobj, 'Blackhole', 'nzb_dir', '')
        sickrage.TORRENT_DIR = Config.check_setting_str(cfgobj, 'Blackhole', 'torrent_dir', '')

        sickrage.TV_DOWNLOAD_DIR = Config.check_setting_str(cfgobj, 'General', 'tv_download_dir', '')
        sickrage.PROCESS_AUTOMATICALLY = bool(Config.check_setting_int(cfgobj, 'General', 'process_automatically', 0))
        sickrage.NO_DELETE = bool(Config.check_setting_int(cfgobj, 'General', 'no_delete', 0))
        sickrage.UNPACK = bool(Config.check_setting_int(cfgobj, 'General', 'unpack', 0))
        sickrage.RENAME_EPISODES = bool(Config.check_setting_int(cfgobj, 'General', 'rename_episodes', 1))
        sickrage.AIRDATE_EPISODES = bool(Config.check_setting_int(cfgobj, 'General', 'airdate_episodes', 0))
        sickrage.FILE_TIMESTAMP_TIMEZONE = Config.check_setting_str(cfgobj, 'General', 'file_timestamp_timezone',
                                                                    'network')
        sickrage.KEEP_PROCESSED_DIR = bool(Config.check_setting_int(cfgobj, 'General', 'keep_processed_dir', 1))
        sickrage.PROCESS_METHOD = Config.check_setting_str(cfgobj, 'General', 'process_method',
                                                           'copy' if sickrage.KEEP_PROCESSED_DIR else 'move')
        sickrage.DELRARCONTENTS = bool(Config.check_setting_int(cfgobj, 'General', 'del_rar_contents', 0))
        sickrage.MOVE_ASSOCIATED_FILES = bool(Config.check_setting_int(cfgobj, 'General', 'move_associated_files', 0))
        sickrage.POSTPONE_IF_SYNC_FILES = bool(Config.check_setting_int(cfgobj, 'General', 'postpone_if_sync_files', 1))
        sickrage.SYNC_FILES = Config.check_setting_str(cfgobj, 'General', 'sync_files',
                                                       '!sync,lftp-pget-status,part,bts,!qb')
        sickrage.NFO_RENAME = bool(Config.check_setting_int(cfgobj, 'General', 'nfo_rename', 1))
        sickrage.CREATE_MISSING_SHOW_DIRS = bool(
            Config.check_setting_int(cfgobj, 'General', 'create_missing_show_dirs', 0))
        sickrage.ADD_SHOWS_WO_DIR = bool(Config.check_setting_int(cfgobj, 'General', 'add_shows_wo_dir', 0))

        sickrage.NZBS = bool(Config.check_setting_int(cfgobj, 'NZBs', 'nzbs', 0))
        sickrage.NZBS_UID = Config.check_setting_str(cfgobj, 'NZBs', 'nzbs_uid', '', censor_log=True)
        sickrage.NZBS_HASH = Config.check_setting_str(cfgobj, 'NZBs', 'nzbs_hash', '', censor_log=True)

        sickrage.NEWZBIN = bool(Config.check_setting_int(cfgobj, 'Newzbin', 'newzbin', 0))
        sickrage.NEWZBIN_USERNAME = Config.check_setting_str(cfgobj, 'Newzbin', 'newzbin_username', '', censor_log=True)
        sickrage.NEWZBIN_PASSWORD = Config.check_setting_str(cfgobj, 'Newzbin', 'newzbin_password', '', censor_log=True)

        sickrage.SAB_USERNAME = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_username', '', censor_log=True)
        sickrage.SAB_PASSWORD = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_password', '', censor_log=True)
        sickrage.SAB_APIKEY = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_apikey', '', censor_log=True)
        sickrage.SAB_CATEGORY = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_category', 'tv')
        sickrage.SAB_CATEGORY_BACKLOG = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_category_backlog',
                                                                 sickrage.SAB_CATEGORY)
        sickrage.SAB_CATEGORY_ANIME = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_category_anime', 'anime')
        sickrage.SAB_CATEGORY_ANIME_BACKLOG = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_category_anime_backlog',
                                                                       sickrage.SAB_CATEGORY_ANIME)
        sickrage.SAB_HOST = Config.check_setting_str(cfgobj, 'SABnzbd', 'sab_host', '')
        sickrage.SAB_FORCED = bool(Config.check_setting_int(cfgobj, 'SABnzbd', 'sab_forced', 0))

        sickrage.NZBGET_USERNAME = Config.check_setting_str(cfgobj, 'NZBget', 'nzbget_username', 'nzbget',
                                                            censor_log=True)
        sickrage.NZBGET_PASSWORD = Config.check_setting_str(cfgobj, 'NZBget', 'nzbget_password', 'tegbzn6789',
                                                            censor_log=True)
        sickrage.NZBGET_CATEGORY = Config.check_setting_str(cfgobj, 'NZBget', 'nzbget_category', 'tv')
        sickrage.NZBGET_CATEGORY_BACKLOG = Config.check_setting_str(cfgobj, 'NZBget', 'nzbget_category_backlog',
                                                                    sickrage.NZBGET_CATEGORY)
        sickrage.NZBGET_CATEGORY_ANIME = Config.check_setting_str(cfgobj, 'NZBget', 'nzbget_category_anime', 'anime')
        sickrage.NZBGET_CATEGORY_ANIME_BACKLOG = Config.check_setting_str(
                cfgobj, 'NZBget', 'nzbget_category_anime_backlog', sickrage.NZBGET_CATEGORY_ANIME
        )
        sickrage.NZBGET_HOST = Config.check_setting_str(cfgobj, 'NZBget', 'nzbget_host', '')
        sickrage.NZBGET_USE_HTTPS = bool(Config.check_setting_int(cfgobj, 'NZBget', 'nzbget_use_https', 0))
        sickrage.NZBGET_PRIORITY = Config.check_setting_int(cfgobj, 'NZBget', 'nzbget_priority', 100)

        sickrage.TORRENT_USERNAME = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_username', '', censor_log=True)
        sickrage.TORRENT_PASSWORD = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_password', '', censor_log=True)
        sickrage.TORRENT_HOST = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_host', '')
        sickrage.TORRENT_PATH = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_path', '')
        sickrage.TORRENT_SEED_TIME = Config.check_setting_int(cfgobj, 'TORRENT', 'torrent_seed_time', 0)
        sickrage.TORRENT_PAUSED = bool(Config.check_setting_int(cfgobj, 'TORRENT', 'torrent_paused', 0))
        sickrage.TORRENT_HIGH_BANDWIDTH = bool(Config.check_setting_int(cfgobj, 'TORRENT', 'torrent_high_bandwidth', 0))
        sickrage.TORRENT_LABEL = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_label', '')
        sickrage.TORRENT_LABEL_ANIME = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_label_anime', '')
        sickrage.TORRENT_VERIFY_CERT = bool(Config.check_setting_int(cfgobj, 'TORRENT', 'torrent_verify_cert', 0))
        sickrage.TORRENT_RPCURL = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_rpcurl', 'transmission')
        sickrage.TORRENT_AUTH_TYPE = Config.check_setting_str(cfgobj, 'TORRENT', 'torrent_auth_type', '')

        sickrage.USE_KODI = bool(Config.check_setting_int(cfgobj, 'KODI', 'use_kodi', 0))
        sickrage.KODI_ALWAYS_ON = bool(Config.check_setting_int(cfgobj, 'KODI', 'kodi_always_on', 1))
        sickrage.KODI_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'KODI', 'kodi_notify_onsnatch', 0))
        sickrage.KODI_NOTIFY_ONDOWNLOAD = bool(Config.check_setting_int(cfgobj, 'KODI', 'kodi_notify_ondownload', 0))
        sickrage.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'KODI', 'kodi_notify_onsubtitledownload', 0))
        sickrage.KODI_UPDATE_LIBRARY = bool(Config.check_setting_int(cfgobj, 'KODI', 'kodi_update_library', 0))
        sickrage.KODI_UPDATE_FULL = bool(Config.check_setting_int(cfgobj, 'KODI', 'kodi_update_full', 0))
        sickrage.KODI_UPDATE_ONLYFIRST = bool(Config.check_setting_int(cfgobj, 'KODI', 'kodi_update_onlyfirst', 0))
        sickrage.KODI_HOST = Config.check_setting_str(cfgobj, 'KODI', 'kodi_host', '')
        sickrage.KODI_USERNAME = Config.check_setting_str(cfgobj, 'KODI', 'kodi_username', '', censor_log=True)
        sickrage.KODI_PASSWORD = Config.check_setting_str(cfgobj, 'KODI', 'kodi_password', '', censor_log=True)

        sickrage.USE_PLEX = bool(Config.check_setting_int(cfgobj, 'Plex', 'use_plex', 0))
        sickrage.PLEX_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'Plex', 'plex_notify_onsnatch', 0))
        sickrage.PLEX_NOTIFY_ONDOWNLOAD = bool(Config.check_setting_int(cfgobj, 'Plex', 'plex_notify_ondownload', 0))
        sickrage.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Plex', 'plex_notify_onsubtitledownload', 0))
        sickrage.PLEX_UPDATE_LIBRARY = bool(Config.check_setting_int(cfgobj, 'Plex', 'plex_update_library', 0))
        sickrage.PLEX_SERVER_HOST = Config.check_setting_str(cfgobj, 'Plex', 'plex_server_host', '')
        sickrage.PLEX_SERVER_TOKEN = Config.check_setting_str(cfgobj, 'Plex', 'plex_server_token', '')
        sickrage.PLEX_HOST = Config.check_setting_str(cfgobj, 'Plex', 'plex_host', '')
        sickrage.PLEX_USERNAME = Config.check_setting_str(cfgobj, 'Plex', 'plex_username', '', censor_log=True)
        sickrage.PLEX_PASSWORD = Config.check_setting_str(cfgobj, 'Plex', 'plex_password', '', censor_log=True)
        sickrage.USE_PLEX_CLIENT = bool(Config.check_setting_int(cfgobj, 'Plex', 'use_plex_client', 0))
        sickrage.PLEX_CLIENT_USERNAME = Config.check_setting_str(cfgobj, 'Plex', 'plex_client_username', '',
                                                                 censor_log=True)
        sickrage.PLEX_CLIENT_PASSWORD = Config.check_setting_str(cfgobj, 'Plex', 'plex_client_password', '',
                                                                 censor_log=True)

        sickrage.USE_EMBY = bool(Config.check_setting_int(cfgobj, 'Emby', 'use_emby', 0))
        sickrage.EMBY_HOST = Config.check_setting_str(cfgobj, 'Emby', 'emby_host', '')
        sickrage.EMBY_APIKEY = Config.check_setting_str(cfgobj, 'Emby', 'emby_apikey', '')

        sickrage.USE_GROWL = bool(Config.check_setting_int(cfgobj, 'Growl', 'use_growl', 0))
        sickrage.GROWL_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'Growl', 'growl_notify_onsnatch', 0))
        sickrage.GROWL_NOTIFY_ONDOWNLOAD = bool(Config.check_setting_int(cfgobj, 'Growl', 'growl_notify_ondownload', 0))
        sickrage.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Growl', 'growl_notify_onsubtitledownload', 0))
        sickrage.GROWL_HOST = Config.check_setting_str(cfgobj, 'Growl', 'growl_host', '')
        sickrage.GROWL_PASSWORD = Config.check_setting_str(cfgobj, 'Growl', 'growl_password', '', censor_log=True)

        sickrage.USE_FREEMOBILE = bool(Config.check_setting_int(cfgobj, 'FreeMobile', 'use_freemobile', 0))
        sickrage.FREEMOBILE_NOTIFY_ONSNATCH = bool(
                Config.check_setting_int(cfgobj, 'FreeMobile', 'freemobile_notify_onsnatch', 0))
        sickrage.FREEMOBILE_NOTIFY_ONDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'FreeMobile', 'freemobile_notify_ondownload', 0))
        sickrage.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'FreeMobile', 'freemobile_notify_onsubtitledownload', 0))
        sickrage.FREEMOBILE_ID = Config.check_setting_str(cfgobj, 'FreeMobile', 'freemobile_id', '')
        sickrage.FREEMOBILE_APIKEY = Config.check_setting_str(cfgobj, 'FreeMobile', 'freemobile_apikey', '')

        sickrage.USE_PROWL = bool(Config.check_setting_int(cfgobj, 'Prowl', 'use_prowl', 0))
        sickrage.PROWL_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'Prowl', 'prowl_notify_onsnatch', 0))
        sickrage.PROWL_NOTIFY_ONDOWNLOAD = bool(Config.check_setting_int(cfgobj, 'Prowl', 'prowl_notify_ondownload', 0))
        sickrage.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Prowl', 'prowl_notify_onsubtitledownload', 0))
        sickrage.PROWL_API = Config.check_setting_str(cfgobj, 'Prowl', 'prowl_api', '', censor_log=True)
        sickrage.PROWL_PRIORITY = Config.check_setting_str(cfgobj, 'Prowl', 'prowl_priority', "0")

        sickrage.USE_TWITTER = bool(Config.check_setting_int(cfgobj, 'Twitter', 'use_twitter', 0))
        sickrage.TWITTER_NOTIFY_ONSNATCH = bool(
            Config.check_setting_int(cfgobj, 'Twitter', 'twitter_notify_onsnatch', 0))
        sickrage.TWITTER_NOTIFY_ONDOWNLOAD = bool(
            Config.check_setting_int(cfgobj, 'Twitter', 'twitter_notify_ondownload', 0))
        sickrage.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Twitter', 'twitter_notify_onsubtitledownload', 0))
        sickrage.TWITTER_USERNAME = Config.check_setting_str(cfgobj, 'Twitter', 'twitter_username', '', censor_log=True)
        sickrage.TWITTER_PASSWORD = Config.check_setting_str(cfgobj, 'Twitter', 'twitter_password', '', censor_log=True)
        sickrage.TWITTER_PREFIX = Config.check_setting_str(cfgobj, 'Twitter', 'twitter_prefix', sickrage.GIT_REPO)
        sickrage.TWITTER_DMTO = Config.check_setting_str(cfgobj, 'Twitter', 'twitter_dmto', '')
        sickrage.TWITTER_USEDM = bool(Config.check_setting_int(cfgobj, 'Twitter', 'twitter_usedm', 0))

        sickrage.USE_BOXCAR = bool(Config.check_setting_int(cfgobj, 'Boxcar', 'use_boxcar', 0))
        sickrage.BOXCAR_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'Boxcar', 'boxcar_notify_onsnatch', 0))
        sickrage.BOXCAR_NOTIFY_ONDOWNLOAD = bool(
            Config.check_setting_int(cfgobj, 'Boxcar', 'boxcar_notify_ondownload', 0))
        sickrage.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Boxcar', 'boxcar_notify_onsubtitledownload', 0))
        sickrage.BOXCAR_USERNAME = Config.check_setting_str(cfgobj, 'Boxcar', 'boxcar_username', '', censor_log=True)

        sickrage.USE_BOXCAR2 = bool(Config.check_setting_int(cfgobj, 'Boxcar2', 'use_boxcar2', 0))
        sickrage.BOXCAR2_NOTIFY_ONSNATCH = bool(
            Config.check_setting_int(cfgobj, 'Boxcar2', 'boxcar2_notify_onsnatch', 0))
        sickrage.BOXCAR2_NOTIFY_ONDOWNLOAD = bool(
            Config.check_setting_int(cfgobj, 'Boxcar2', 'boxcar2_notify_ondownload', 0))
        sickrage.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Boxcar2', 'boxcar2_notify_onsubtitledownload', 0))
        sickrage.BOXCAR2_ACCESSTOKEN = Config.check_setting_str(cfgobj, 'Boxcar2', 'boxcar2_accesstoken', '',
                                                                censor_log=True)

        sickrage.USE_PUSHOVER = bool(Config.check_setting_int(cfgobj, 'Pushover', 'use_pushover', 0))
        sickrage.PUSHOVER_NOTIFY_ONSNATCH = bool(
            Config.check_setting_int(cfgobj, 'Pushover', 'pushover_notify_onsnatch', 0))
        sickrage.PUSHOVER_NOTIFY_ONDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Pushover', 'pushover_notify_ondownload', 0))
        sickrage.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Pushover', 'pushover_notify_onsubtitledownload', 0))
        sickrage.PUSHOVER_USERKEY = Config.check_setting_str(cfgobj, 'Pushover', 'pushover_userkey', '',
                                                             censor_log=True)
        sickrage.PUSHOVER_APIKEY = Config.check_setting_str(cfgobj, 'Pushover', 'pushover_apikey', '', censor_log=True)
        sickrage.PUSHOVER_DEVICE = Config.check_setting_str(cfgobj, 'Pushover', 'pushover_device', '')
        sickrage.PUSHOVER_SOUND = Config.check_setting_str(cfgobj, 'Pushover', 'pushover_sound', 'pushover')

        sickrage.USE_LIBNOTIFY = bool(Config.check_setting_int(cfgobj, 'Libnotify', 'use_libnotify', 0))
        sickrage.LIBNOTIFY_NOTIFY_ONSNATCH = bool(
                Config.check_setting_int(cfgobj, 'Libnotify', 'libnotify_notify_onsnatch', 0))
        sickrage.LIBNOTIFY_NOTIFY_ONDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Libnotify', 'libnotify_notify_ondownload', 0))
        sickrage.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Libnotify', 'libnotify_notify_onsubtitledownload', 0))

        sickrage.USE_NMJ = bool(Config.check_setting_int(cfgobj, 'NMJ', 'use_nmj', 0))
        sickrage.NMJ_HOST = Config.check_setting_str(cfgobj, 'NMJ', 'nmj_host', '')
        sickrage.NMJ_DATABASE = Config.check_setting_str(cfgobj, 'NMJ', 'nmj_database', '')
        sickrage.NMJ_MOUNT = Config.check_setting_str(cfgobj, 'NMJ', 'nmj_mount', '')

        sickrage.USE_NMJv2 = bool(Config.check_setting_int(cfgobj, 'NMJv2', 'use_nmjv2', 0))
        sickrage.NMJv2_HOST = Config.check_setting_str(cfgobj, 'NMJv2', 'nmjv2_host', '')
        sickrage.NMJv2_DATABASE = Config.check_setting_str(cfgobj, 'NMJv2', 'nmjv2_database', '')
        sickrage.NMJv2_DBLOC = Config.check_setting_str(cfgobj, 'NMJv2', 'nmjv2_dbloc', '')

        sickrage.USE_SYNOINDEX = bool(Config.check_setting_int(cfgobj, 'Synology', 'use_synoindex', 0))

        sickrage.USE_SYNOLOGYNOTIFIER = bool(
            Config.check_setting_int(cfgobj, 'SynologyNotifier', 'use_synologynotifier', 0))
        sickrage.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = bool(
                Config.check_setting_int(cfgobj, 'SynologyNotifier', 'synologynotifier_notify_onsnatch', 0))
        sickrage.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'SynologyNotifier', 'synologynotifier_notify_ondownload', 0))
        sickrage.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'SynologyNotifier', 'synologynotifier_notify_onsubtitledownload', 0))

        sickrage.THETVDB_APITOKEN = Config.check_setting_str(cfgobj, 'theTVDB', 'thetvdb_apitoken', '', censor_log=True)

        sickrage.USE_TRAKT = bool(Config.check_setting_int(cfgobj, 'Trakt', 'use_trakt', 0))
        sickrage.TRAKT_USERNAME = Config.check_setting_str(cfgobj, 'Trakt', 'trakt_username', '', censor_log=True)
        sickrage.TRAKT_ACCESS_TOKEN = Config.check_setting_str(cfgobj, 'Trakt', 'trakt_access_token', '',
                                                               censor_log=True)
        sickrage.TRAKT_REFRESH_TOKEN = Config.check_setting_str(cfgobj, 'Trakt', 'trakt_refresh_token', '',
                                                                censor_log=True)
        sickrage.TRAKT_REMOVE_WATCHLIST = bool(Config.check_setting_int(cfgobj, 'Trakt', 'trakt_remove_watchlist', 0))
        sickrage.TRAKT_REMOVE_SERIESLIST = bool(Config.check_setting_int(cfgobj, 'Trakt', 'trakt_remove_serieslist', 0))
        sickrage.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = bool(
                Config.check_setting_int(cfgobj, 'Trakt', 'trakt_remove_show_from_sickrage', 0))
        sickrage.TRAKT_SYNC_WATCHLIST = bool(Config.check_setting_int(cfgobj, 'Trakt', 'trakt_sync_watchlist', 0))
        sickrage.TRAKT_METHOD_ADD = Config.check_setting_int(cfgobj, 'Trakt', 'trakt_method_add', 0)
        sickrage.TRAKT_START_PAUSED = bool(Config.check_setting_int(cfgobj, 'Trakt', 'trakt_start_paused', 0))
        sickrage.TRAKT_USE_RECOMMENDED = bool(Config.check_setting_int(cfgobj, 'Trakt', 'trakt_use_recommended', 0))
        sickrage.TRAKT_SYNC = bool(Config.check_setting_int(cfgobj, 'Trakt', 'trakt_sync', 0))
        sickrage.TRAKT_SYNC_REMOVE = bool(Config.check_setting_int(cfgobj, 'Trakt', 'trakt_sync_remove', 0))
        sickrage.TRAKT_DEFAULT_INDEXER = Config.check_setting_int(cfgobj, 'Trakt', 'trakt_default_indexer', 1)
        sickrage.TRAKT_TIMEOUT = Config.check_setting_int(cfgobj, 'Trakt', 'trakt_timeout', 30)
        sickrage.TRAKT_BLACKLIST_NAME = Config.check_setting_str(cfgobj, 'Trakt', 'trakt_blacklist_name', '')

        sickrage.USE_PYTIVO = bool(Config.check_setting_int(cfgobj, 'pyTivo', 'use_pytivo', 0))
        sickrage.PYTIVO_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'pyTivo', 'pytivo_notify_onsnatch', 0))
        sickrage.PYTIVO_NOTIFY_ONDOWNLOAD = bool(
            Config.check_setting_int(cfgobj, 'pyTivo', 'pytivo_notify_ondownload', 0))
        sickrage.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'pyTivo', 'pytivo_notify_onsubtitledownload', 0))
        sickrage.PYTIVO_UPDATE_LIBRARY = bool(Config.check_setting_int(cfgobj, 'pyTivo', 'pyTivo_update_library', 0))
        sickrage.PYTIVO_HOST = Config.check_setting_str(cfgobj, 'pyTivo', 'pytivo_host', '')
        sickrage.PYTIVO_SHARE_NAME = Config.check_setting_str(cfgobj, 'pyTivo', 'pytivo_share_name', '')
        sickrage.PYTIVO_TIVO_NAME = Config.check_setting_str(cfgobj, 'pyTivo', 'pytivo_tivo_name', '')

        sickrage.USE_NMA = bool(Config.check_setting_int(cfgobj, 'NMA', 'use_nma', 0))
        sickrage.NMA_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'NMA', 'nma_notify_onsnatch', 0))
        sickrage.NMA_NOTIFY_ONDOWNLOAD = bool(Config.check_setting_int(cfgobj, 'NMA', 'nma_notify_ondownload', 0))
        sickrage.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'NMA', 'nma_notify_onsubtitledownload', 0))
        sickrage.NMA_API = Config.check_setting_str(cfgobj, 'NMA', 'nma_api', '', censor_log=True)
        sickrage.NMA_PRIORITY = Config.check_setting_str(cfgobj, 'NMA', 'nma_priority', "0")

        sickrage.USE_PUSHALOT = bool(Config.check_setting_int(cfgobj, 'Pushalot', 'use_pushalot', 0))
        sickrage.PUSHALOT_NOTIFY_ONSNATCH = bool(
            Config.check_setting_int(cfgobj, 'Pushalot', 'pushalot_notify_onsnatch', 0))
        sickrage.PUSHALOT_NOTIFY_ONDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Pushalot', 'pushalot_notify_ondownload', 0))
        sickrage.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Pushalot', 'pushalot_notify_onsubtitledownload', 0))
        sickrage.PUSHALOT_AUTHORIZATIONTOKEN = Config.check_setting_str(cfgobj, 'Pushalot',
                                                                        'pushalot_authorizationtoken', '',
                                                                        censor_log=True)

        sickrage.USE_PUSHBULLET = bool(Config.check_setting_int(cfgobj, 'Pushbullet', 'use_pushbullet', 0))
        sickrage.PUSHBULLET_NOTIFY_ONSNATCH = bool(
                Config.check_setting_int(cfgobj, 'Pushbullet', 'pushbullet_notify_onsnatch', 0))
        sickrage.PUSHBULLET_NOTIFY_ONDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Pushbullet', 'pushbullet_notify_ondownload', 0))
        sickrage.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Pushbullet', 'pushbullet_notify_onsubtitledownload', 0))
        sickrage.PUSHBULLET_API = Config.check_setting_str(cfgobj, 'Pushbullet', 'pushbullet_api', '', censor_log=True)
        sickrage.PUSHBULLET_DEVICE = Config.check_setting_str(cfgobj, 'Pushbullet', 'pushbullet_device', '')

        # email notify settings
        sickrage.USE_EMAIL = bool(Config.check_setting_int(cfgobj, 'Email', 'use_email', 0))
        sickrage.EMAIL_NOTIFY_ONSNATCH = bool(Config.check_setting_int(cfgobj, 'Email', 'email_notify_onsnatch', 0))
        sickrage.EMAIL_NOTIFY_ONDOWNLOAD = bool(Config.check_setting_int(cfgobj, 'Email', 'email_notify_ondownload', 0))
        sickrage.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
                Config.check_setting_int(cfgobj, 'Email', 'email_notify_onsubtitledownload', 0))
        sickrage.EMAIL_HOST = Config.check_setting_str(cfgobj, 'Email', 'email_host', '')
        sickrage.EMAIL_PORT = Config.check_setting_int(cfgobj, 'Email', 'email_port', 25)
        sickrage.EMAIL_TLS = bool(Config.check_setting_int(cfgobj, 'Email', 'email_tls', 0))
        sickrage.EMAIL_USER = Config.check_setting_str(cfgobj, 'Email', 'email_user', '', censor_log=True)
        sickrage.EMAIL_PASSWORD = Config.check_setting_str(cfgobj, 'Email', 'email_password', '', censor_log=True)
        sickrage.EMAIL_FROM = Config.check_setting_str(cfgobj, 'Email', 'email_from', '')
        sickrage.EMAIL_LIST = Config.check_setting_str(cfgobj, 'Email', 'email_list', '')

        # subtitle settings
        sickrage.USE_SUBTITLES = bool(Config.check_setting_int(cfgobj, 'Subtitles', 'use_subtitles', 0))
        sickrage.SUBTITLES_LANGUAGES = Config.check_setting_str(cfgobj, 'Subtitles', 'subtitles_languages', '').split(
            ',')
        sickrage.SUBTITLES_DIR = Config.check_setting_str(cfgobj, 'Subtitles', 'subtitles_dir', '')
        sickrage.SUBTITLES_SERVICES_LIST = Config.check_setting_str(cfgobj, 'Subtitles', 'SUBTITLES_SERVICES_LIST',
                                                                    '').split(
                ',')
        sickrage.SUBTITLES_DEFAULT = bool(Config.check_setting_int(cfgobj, 'Subtitles', 'subtitles_default', 0))
        sickrage.SUBTITLES_HISTORY = bool(Config.check_setting_int(cfgobj, 'Subtitles', 'subtitles_history', 0))
        sickrage.SUBTITLES_HEARING_IMPAIRED = bool(
                Config.check_setting_int(cfgobj, 'Subtitles', 'subtitles_hearing_impaired', 0))
        sickrage.EMBEDDED_SUBTITLES_ALL = bool(
            Config.check_setting_int(cfgobj, 'Subtitles', 'embedded_subtitles_all', 0))
        sickrage.SUBTITLES_MULTI = bool(Config.check_setting_int(cfgobj, 'Subtitles', 'subtitles_multi', 1))
        sickrage.SUBTITLES_SERVICES_ENABLED = [int(x) for x in
                                               Config.check_setting_str(cfgobj, 'Subtitles',
                                                                        'SUBTITLES_SERVICES_ENABLED',
                                                                        '').split(
                                                       '|')
                                               if x]
        sickrage.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in
                                            Config.check_setting_str(cfgobj, 'Subtitles', 'subtitles_extra_scripts',
                                                                     '').split('|') if
                                            x.strip()]

        sickrage.ADDIC7ED_USER = Config.check_setting_str(cfgobj, 'Subtitles', 'addic7ed_username', '', censor_log=True)
        sickrage.ADDIC7ED_PASS = Config.check_setting_str(cfgobj, 'Subtitles', 'addic7ed_password', '', censor_log=True)

        sickrage.LEGENDASTV_USER = Config.check_setting_str(cfgobj, 'Subtitles', 'legendastv_username', '',
                                                            censor_log=True)
        sickrage.LEGENDASTV_PASS = Config.check_setting_str(cfgobj, 'Subtitles', 'legendastv_password', '',
                                                            censor_log=True)

        sickrage.OPENSUBTITLES_USER = Config.check_setting_str(cfgobj, 'Subtitles', 'opensubtitles_username', '',
                                                               censor_log=True)
        sickrage.OPENSUBTITLES_PASS = Config.check_setting_str(cfgobj, 'Subtitles', 'opensubtitles_password', '',
                                                               censor_log=True)

        sickrage.USE_FAILED_DOWNLOADS = bool(
            Config.check_setting_int(cfgobj, 'FailedDownloads', 'use_failed_downloads', 0))
        sickrage.DELETE_FAILED = bool(Config.check_setting_int(cfgobj, 'FailedDownloads', 'delete_failed', 0))

        sickrage.REQUIRE_WORDS = Config.check_setting_str(cfgobj, 'General', 'require_words', '')
        sickrage.IGNORE_WORDS = Config.check_setting_str(cfgobj, 'General', 'ignore_words',
                                                         'german,french,core2hd,dutch,swedish,reenc,MrLss')
        sickrage.IGNORED_SUBS_LIST = Config.check_setting_str(cfgobj, 'General', 'ignored_subs_list',
                                                              'dk,fin,heb,kor,nor,nordic,pl,swe')

        sickrage.CALENDAR_UNPROTECTED = bool(Config.check_setting_int(cfgobj, 'General', 'calendar_unprotected', 0))
        sickrage.CALENDAR_ICONS = bool(Config.check_setting_int(cfgobj, 'General', 'calendar_icons', 0))

        sickrage.NO_RESTART = bool(Config.check_setting_int(cfgobj, 'General', 'no_restart', 0))
        sickrage.EXTRA_SCRIPTS = [x.strip() for x in
                                  Config.check_setting_str(cfgobj, 'General', 'extra_scripts', '').split('|') if
                                  x.strip()]
        sickrage.USE_LISTVIEW = bool(Config.check_setting_int(cfgobj, 'General', 'use_listview', 0))

        sickrage.USE_ANIDB = bool(Config.check_setting_int(cfgobj, 'ANIDB', 'use_anidb', 0))
        sickrage.ANIDB_USERNAME = Config.check_setting_str(cfgobj, 'ANIDB', 'anidb_username', '', censor_log=True)
        sickrage.ANIDB_PASSWORD = Config.check_setting_str(cfgobj, 'ANIDB', 'anidb_password', '', censor_log=True)
        sickrage.ANIDB_USE_MYLIST = bool(Config.check_setting_int(cfgobj, 'ANIDB', 'anidb_use_mylist', 0))

        sickrage.ANIME_SPLIT_HOME = bool(Config.check_setting_int(cfgobj, 'ANIME', 'anime_split_home', 0))

        sickrage.METADATA_KODI = Config.check_setting_str(cfgobj, 'General', 'metadata_kodi', '0|0|0|0|0|0|0|0|0|0')
        sickrage.METADATA_KODI_12PLUS = Config.check_setting_str(cfgobj, 'General', 'metadata_kodi_12plus',
                                                                 '0|0|0|0|0|0|0|0|0|0')
        sickrage.METADATA_MEDIABROWSER = Config.check_setting_str(cfgobj, 'General', 'metadata_mediabrowser',
                                                           '0|0|0|0|0|0|0|0|0|0')
        sickrage.METADATA_PS3 = Config.check_setting_str(cfgobj, 'General', 'metadata_ps3', '0|0|0|0|0|0|0|0|0|0')
        sickrage.METADATA_WDTV = Config.check_setting_str(cfgobj, 'General', 'metadata_wdtv', '0|0|0|0|0|0|0|0|0|0')
        sickrage.METADATA_TIVO = Config.check_setting_str(cfgobj, 'General', 'metadata_tivo', '0|0|0|0|0|0|0|0|0|0')
        sickrage.METADATA_MEDE8ER = Config.check_setting_str(cfgobj, 'General', 'metadata_mede8er',
                                                             '0|0|0|0|0|0|0|0|0|0')

        sickrage.HOME_LAYOUT = Config.check_setting_str(cfgobj, 'GUI', 'home_layout', 'poster')
        sickrage.HISTORY_LAYOUT = Config.check_setting_str(cfgobj, 'GUI', 'history_layout', 'detailed')
        sickrage.HISTORY_LIMIT = Config.check_setting_str(cfgobj, 'GUI', 'history_limit', '100')
        sickrage.DISPLAY_SHOW_SPECIALS = bool(Config.check_setting_int(cfgobj, 'GUI', 'display_show_specials', 1))
        sickrage.COMING_EPS_LAYOUT = Config.check_setting_str(cfgobj, 'GUI', 'coming_eps_layout', 'banner')
        sickrage.COMING_EPS_DISPLAY_PAUSED = bool(
            Config.check_setting_int(cfgobj, 'GUI', 'coming_eps_display_paused', 0))
        sickrage.COMING_EPS_SORT = Config.check_setting_str(cfgobj, 'GUI', 'coming_eps_sort', 'date')
        sickrage.COMING_EPS_MISSED_RANGE = Config.check_setting_int(cfgobj, 'GUI', 'coming_eps_missed_range', 7)
        sickrage.FUZZY_DATING = bool(Config.check_setting_int(cfgobj, 'GUI', 'fuzzy_dating', 0))
        sickrage.TRIM_ZERO = bool(Config.check_setting_int(cfgobj, 'GUI', 'trim_zero', 0))
        sickrage.DATE_PRESET = Config.check_setting_str(cfgobj, 'GUI', 'date_preset', '%x')
        sickrage.TIME_PRESET_W_SECONDS = Config.check_setting_str(cfgobj, 'GUI', 'time_preset', '%I:%M:%S %p')
        sickrage.TIMEZONE_DISPLAY = Config.check_setting_str(cfgobj, 'GUI', 'timezone_display', 'local')
        sickrage.POSTER_SORTBY = Config.check_setting_str(cfgobj, 'GUI', 'poster_sortby', 'name')
        sickrage.POSTER_SORTDIR = Config.check_setting_int(cfgobj, 'GUI', 'poster_sortdir', 1)
        sickrage.FILTER_ROW = bool(Config.check_setting_int(cfgobj, 'GUI', 'filter_row', 1))
        sickrage.DISPLAY_ALL_SEASONS = bool(Config.check_setting_int(cfgobj, 'General', 'display_all_seasons', 1))

        sickrage.NEWZNAB_DATA = Config.check_setting_str(cfgobj, 'Newznab', 'newznab_data',
                                                         NewznabProvider.getDefaultProviders())
        sickrage.TORRENTRSS_DATA = Config.check_setting_str(cfgobj, 'TorrentRss', 'torrentrss_data',
                                                            TorrentRssProvider.getDefaultProviders())

        # NEWZNAB PROVIDER LIST
        sickrage.newznabProviderList = NewznabProvider.getProviderList(sickrage.NEWZNAB_DATA)

        # TORRENT RSS PROVIDER LIST
        sickrage.torrentRssProviderList = TorrentRssProvider.getProviderList(sickrage.TORRENTRSS_DATA)

        # NZB AND TORRENT PROVIDER DICT
        sickrage.providersDict = {
            GenericProvider.NZB: {p.id: p for p in NZBProvider.getProviderList()},
            GenericProvider.TORRENT: {p.id: p for p in TorrentProvider.getProviderList()},
        }

        sickrage.PROVIDER_ORDER = Config.check_setting_str(cfgobj, 'General', 'provider_order', '').split()

        # TORRENT PROVIDER SETTINGS
        for providerID, providerObj in sickrage.providersDict[GenericProvider.TORRENT].items():
            providerObj.enabled = bool(Config.check_setting_int(cfgobj, providerID.upper(), providerID, 0))

            if hasattr(providerObj, 'api_key'):
                providerObj.api_key = Config.check_setting_str(
                        cfgobj, providerID.upper(), providerID + '_api_key', '', censor_log=True
                )

            if hasattr(providerObj, 'hash'):
                providerObj.hash = Config.check_setting_str(
                        cfgobj, providerID.upper(), providerID + '_hash', '', censor_log=True
                )

            if hasattr(providerObj, 'digest'):
                providerObj.digest = Config.check_setting_str(
                        cfgobj, providerID.upper(), providerID + '_digest', '', censor_log=True
                )

            if hasattr(providerObj, 'username'):
                providerObj.username = Config.check_setting_str(
                        cfgobj, providerID.upper(), providerID + '_username', '', censor_log=True
                )

            if hasattr(providerObj, 'password'):
                providerObj.password = Config.check_setting_str(
                        cfgobj, providerID.upper(), providerID + '_password', '', censor_log=True
                )

            if hasattr(providerObj, 'passkey'):
                providerObj.passkey = Config.check_setting_str(cfgobj, providerID.upper(),
                                                               providerID + '_passkey', '',
                                                               censor_log=True)
            if hasattr(providerObj, 'pin'):
                providerObj.pin = Config.check_setting_str(cfgobj, providerID.upper(),
                                                           providerID + '_pin', '', censor_log=True)
            if hasattr(providerObj, 'confirmed'):
                providerObj.confirmed = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                      providerID + '_confirmed', 1))
            if hasattr(providerObj, 'ranked'):
                providerObj.ranked = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                   providerID + '_ranked', 1))

            if hasattr(providerObj, 'engrelease'):
                providerObj.engrelease = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                       providerID + '_engrelease', 0))

            if hasattr(providerObj, 'onlyspasearch'):
                providerObj.onlyspasearch = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                          providerID + '_onlyspasearch',
                                                                          0))

            if hasattr(providerObj, 'sorting'):
                providerObj.sorting = Config.check_setting_str(cfgobj, providerID.upper(),
                                                               providerID + '_sorting', 'seeders')
            if hasattr(providerObj, 'options'):
                providerObj.options = Config.check_setting_str(cfgobj, providerID.upper(),
                                                               providerID + '_options', '')
            if hasattr(providerObj, 'ratio'):
                providerObj.ratio = Config.check_setting_str(cfgobj, providerID.upper(),
                                                             providerID + '_ratio', '')
            if hasattr(providerObj, 'minseed'):
                providerObj.minseed = Config.check_setting_int(cfgobj, providerID.upper(),
                                                               providerID + '_minseed', 1)
            if hasattr(providerObj, 'minleech'):
                providerObj.minleech = Config.check_setting_int(cfgobj, providerID.upper(),
                                                                providerID + '_minleech', 0)
            if hasattr(providerObj, 'freeleech'):
                providerObj.freeleech = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                      providerID + '_freeleech', 0))
            if hasattr(providerObj, 'search_mode'):
                providerObj.search_mode = Config.check_setting_str(cfgobj, providerID.upper(),
                                                                   providerID + '_search_mode',
                                                                   'eponly')
            if hasattr(providerObj, 'search_fallback'):
                providerObj.search_fallback = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                            providerID + '_search_fallback',
                                                                            0))

            if hasattr(providerObj, 'enable_daily'):
                providerObj.enable_daily = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                         providerID + '_enable_daily',
                                                                         1))

            if hasattr(providerObj, 'enable_backlog') and hasattr(providerObj, 'supportsBacklog'):
                providerObj.enable_backlog = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                           providerID + '_enable_backlog',
                                                                           providerObj.supportsBacklog))

            if hasattr(providerObj, 'cat'):
                providerObj.cat = Config.check_setting_int(cfgobj, providerID.upper(),
                                                           providerID + '_cat', 0)
            if hasattr(providerObj, 'subtitle'):
                providerObj.subtitle = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                     providerID + '_subtitle', 0))

        # NZB PROVIDER SETTINGS
        for providerID, providerObj in sickrage.providersDict[GenericProvider.NZB].items():
            providerObj.enabled = bool(
                    Config.check_setting_int(cfgobj, providerID.upper(), providerID, 0))
            if hasattr(providerObj, 'api_key'):
                providerObj.api_key = Config.check_setting_str(cfgobj, providerID.upper(),
                                                               providerID + '_api_key', '', censor_log=True)
            if hasattr(providerObj, 'username'):
                providerObj.username = Config.check_setting_str(cfgobj, providerID.upper(),
                                                                providerID + '_username', '', censor_log=True)
            if hasattr(providerObj, 'search_mode'):
                providerObj.search_mode = Config.check_setting_str(cfgobj, providerID.upper(),
                                                                   providerID + '_search_mode',
                                                                   'eponly')
            if hasattr(providerObj, 'search_fallback'):
                providerObj.search_fallback = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                            providerID + '_search_fallback',
                                                                            0))
            if hasattr(providerObj, 'enable_daily'):
                providerObj.enable_daily = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                         providerID + '_enable_daily',
                                                                         1))

            if hasattr(providerObj, 'enable_backlog') and hasattr(providerObj, 'supportsBacklog'):
                providerObj.enable_backlog = bool(Config.check_setting_int(cfgobj, providerID.upper(),
                                                                           providerID + '_enable_backlog',
                                                                           providerObj.supportsBacklog))

        return Config.save_config(cfgfile)

    @staticmethod
    def save_config(cfgfile):
        new_config = ConfigObj(cfgfile)

        # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
        new_config[b'General'] = {}
        new_config[b'General'][b'git_autoissues'] = int(sickrage.GIT_AUTOISSUES)
        new_config[b'General'][b'git_username'] = sickrage.GIT_USERNAME
        new_config[b'General'][b'git_password'] = encrypt(sickrage.GIT_PASSWORD, sickrage.ENCRYPTION_VERSION)
        new_config[b'General'][b'git_reset'] = int(sickrage.GIT_RESET)
        new_config[b'General'][b'branch'] = sickrage.GIT_BRANCH
        new_config[b'General'][b'git_remote'] = sickrage.GIT_REMOTE
        new_config[b'General'][b'git_remote_url'] = sickrage.GIT_REMOTE_URL
        new_config[b'General'][b'cur_commit_hash'] = sickrage.CUR_COMMIT_HASH
        new_config[b'General'][b'cur_commit_branch'] = sickrage.CUR_COMMIT_BRANCH
        new_config[b'General'][b'git_newver'] = int(sickrage.GIT_NEWVER)
        new_config[b'General'][b'config_version'] = sickrage.CONFIG_VERSION
        new_config[b'General'][b'encryption_version'] = int(sickrage.ENCRYPTION_VERSION)
        new_config[b'General'][b'encryption_secret'] = sickrage.ENCRYPTION_SECRET
        new_config[b'General'][b'log_dir'] = sickrage.LOG_DIR or 'Logs'
        new_config[b'General'][b'log_nr'] = int(sickrage.LOG_NR)
        new_config[b'General'][b'log_size'] = int(sickrage.LOG_SIZE)
        new_config[b'General'][b'socket_timeout'] = sickrage.SOCKET_TIMEOUT
        new_config[b'General'][b'web_port'] = sickrage.WEB_PORT
        new_config[b'General'][b'web_host'] = sickrage.WEB_HOST
        new_config[b'General'][b'web_ipv6'] = int(sickrage.WEB_IPV6)
        new_config[b'General'][b'web_log'] = int(sickrage.WEB_LOG)
        new_config[b'General'][b'web_root'] = sickrage.WEB_ROOT
        new_config[b'General'][b'web_username'] = sickrage.WEB_USERNAME
        new_config[b'General'][b'web_password'] = encrypt(sickrage.WEB_PASSWORD, sickrage.ENCRYPTION_VERSION)
        new_config[b'General'][b'web_cookie_secret'] = sickrage.WEB_COOKIE_SECRET
        new_config[b'General'][b'web_use_gzip'] = int(sickrage.WEB_USE_GZIP)
        new_config[b'General'][b'ssl_verify'] = int(sickrage.SSL_VERIFY)
        new_config[b'General'][b'download_url'] = sickrage.DOWNLOAD_URL
        new_config[b'General'][b'localhost_ip'] = sickrage.LOCALHOST_IP
        new_config[b'General'][b'cpu_preset'] = sickrage.CPU_PRESET
        new_config[b'General'][b'anon_redirect'] = sickrage.ANON_REDIRECT
        new_config[b'General'][b'api_key'] = sickrage.API_KEY
        new_config[b'General'][b'debug'] = int(sickrage.DEBUG)
        new_config[b'General'][b'default_page'] = sickrage.DEFAULT_PAGE
        new_config[b'General'][b'enable_https'] = int(sickrage.ENABLE_HTTPS)
        new_config[b'General'][b'https_cert'] = sickrage.HTTPS_CERT
        new_config[b'General'][b'https_key'] = sickrage.HTTPS_KEY
        new_config[b'General'][b'handle_reverse_proxy'] = int(sickrage.HANDLE_REVERSE_PROXY)
        new_config[b'General'][b'use_nzbs'] = int(sickrage.USE_NZBS)
        new_config[b'General'][b'use_torrents'] = int(sickrage.USE_TORRENTS)
        new_config[b'General'][b'nzb_method'] = sickrage.NZB_METHOD
        new_config[b'General'][b'torrent_method'] = sickrage.TORRENT_METHOD
        new_config[b'General'][b'usenet_retention'] = int(sickrage.USENET_RETENTION)
        new_config[b'General'][b'autopostprocessor_frequency'] = int(sickrage.AUTOPOSTPROCESSOR_FREQ)
        new_config[b'General'][b'dailysearch_frequency'] = int(sickrage.DAILY_SEARCHER_FREQ)
        new_config[b'General'][b'backlog_frequency'] = int(sickrage.BACKLOG_SEARCHER_FREQ)
        new_config[b'General'][b'update_frequency'] = int(sickrage.VERSION_UPDATER_FREQ)
        new_config[b'General'][b'showupdate_hour'] = int(sickrage.SHOWUPDATE_HOUR)
        new_config[b'General'][b'download_propers'] = int(sickrage.DOWNLOAD_PROPERS)
        new_config[b'General'][b'randomize_providers'] = int(sickrage.RANDOMIZE_PROVIDERS)
        new_config[b'General'][b'check_propers_interval'] = sickrage.PROPER_SEARCHER_INTERVAL
        new_config[b'General'][b'allow_high_priority'] = int(sickrage.ALLOW_HIGH_PRIORITY)
        new_config[b'General'][b'skip_removed_files'] = int(sickrage.SKIP_REMOVED_FILES)
        new_config[b'General'][b'quality_default'] = int(sickrage.QUALITY_DEFAULT)
        new_config[b'General'][b'status_default'] = int(sickrage.STATUS_DEFAULT)
        new_config[b'General'][b'status_default_after'] = int(sickrage.STATUS_DEFAULT_AFTER)
        new_config[b'General'][b'flatten_folders_default'] = int(sickrage.FLATTEN_FOLDERS_DEFAULT)
        new_config[b'General'][b'indexer_default'] = int(sickrage.INDEXER_DEFAULT)
        new_config[b'General'][b'indexer_timeout'] = int(sickrage.INDEXER_TIMEOUT)
        new_config[b'General'][b'anime_default'] = int(sickrage.ANIME_DEFAULT)
        new_config[b'General'][b'scene_default'] = int(sickrage.SCENE_DEFAULT)
        new_config[b'General'][b'archive_default'] = int(sickrage.ARCHIVE_DEFAULT)
        new_config[b'General'][b'provider_order'] = ' '.join(sickrage.PROVIDER_ORDER)
        new_config[b'General'][b'version_notify'] = int(sickrage.VERSION_NOTIFY)
        new_config[b'General'][b'auto_update'] = int(sickrage.AUTO_UPDATE)
        new_config[b'General'][b'notify_on_update'] = int(sickrage.NOTIFY_ON_UPDATE)
        new_config[b'General'][b'naming_strip_year'] = int(sickrage.NAMING_STRIP_YEAR)
        new_config[b'General'][b'naming_pattern'] = sickrage.NAMING_PATTERN
        new_config[b'General'][b'naming_custom_abd'] = int(sickrage.NAMING_CUSTOM_ABD)
        new_config[b'General'][b'naming_abd_pattern'] = sickrage.NAMING_ABD_PATTERN
        new_config[b'General'][b'naming_custom_sports'] = int(sickrage.NAMING_CUSTOM_SPORTS)
        new_config[b'General'][b'naming_sports_pattern'] = sickrage.NAMING_SPORTS_PATTERN
        new_config[b'General'][b'naming_custom_anime'] = int(sickrage.NAMING_CUSTOM_ANIME)
        new_config[b'General'][b'naming_anime_pattern'] = sickrage.NAMING_ANIME_PATTERN
        new_config[b'General'][b'naming_multi_ep'] = int(sickrage.NAMING_MULTI_EP)
        new_config[b'General'][b'naming_anime_multi_ep'] = int(sickrage.NAMING_ANIME_MULTI_EP)
        new_config[b'General'][b'naming_anime'] = int(sickrage.NAMING_ANIME)
        new_config[b'General'][b'indexerDefaultLang'] = sickrage.INDEXER_DEFAULT_LANGUAGE
        new_config[b'General'][b'ep_default_deleted_status'] = int(sickrage.EP_DEFAULT_DELETED_STATUS)
        new_config[b'General'][b'launch_browser'] = int(sickrage.LAUNCH_BROWSER)
        new_config[b'General'][b'trash_remove_show'] = int(sickrage.TRASH_REMOVE_SHOW)
        new_config[b'General'][b'trash_rotate_logs'] = int(sickrage.TRASH_ROTATE_LOGS)
        new_config[b'General'][b'sort_article'] = int(sickrage.SORT_ARTICLE)
        new_config[b'General'][b'proxy_setting'] = sickrage.PROXY_SETTING
        new_config[b'General'][b'proxy_indexers'] = int(sickrage.PROXY_INDEXERS)

        new_config[b'General'][b'use_listview'] = int(sickrage.USE_LISTVIEW)
        new_config[b'General'][b'metadata_kodi'] = sickrage.METADATA_KODI
        new_config[b'General'][b'metadata_kodi_12plus'] = sickrage.METADATA_KODI_12PLUS
        new_config[b'General'][b'metadata_mediabrowser'] = sickrage.METADATA_MEDIABROWSER
        new_config[b'General'][b'metadata_ps3'] = sickrage.METADATA_PS3
        new_config[b'General'][b'metadata_wdtv'] = sickrage.METADATA_WDTV
        new_config[b'General'][b'metadata_tivo'] = sickrage.METADATA_TIVO
        new_config[b'General'][b'metadata_mede8er'] = sickrage.METADATA_MEDE8ER

        new_config[b'General'][b'backlog_days'] = int(sickrage.BACKLOG_DAYS)

        new_config[b'General'][b'cache_dir'] = sickrage.ACTUAL_CACHE_DIR if sickrage.ACTUAL_CACHE_DIR else 'cache'
        new_config[b'General'][b'root_dirs'] = sickrage.ROOT_DIRS if sickrage.ROOT_DIRS else ''
        new_config[b'General'][b'tv_download_dir'] = sickrage.TV_DOWNLOAD_DIR
        new_config[b'General'][b'keep_processed_dir'] = int(sickrage.KEEP_PROCESSED_DIR)
        new_config[b'General'][b'process_method'] = sickrage.PROCESS_METHOD
        new_config[b'General'][b'del_rar_contents'] = int(sickrage.DELRARCONTENTS)
        new_config[b'General'][b'move_associated_files'] = int(sickrage.MOVE_ASSOCIATED_FILES)
        new_config[b'General'][b'sync_files'] = sickrage.SYNC_FILES
        new_config[b'General'][b'postpone_if_sync_files'] = int(sickrage.POSTPONE_IF_SYNC_FILES)
        new_config[b'General'][b'nfo_rename'] = int(sickrage.NFO_RENAME)
        new_config[b'General'][b'process_automatically'] = int(sickrage.PROCESS_AUTOMATICALLY)
        new_config[b'General'][b'no_delete'] = int(sickrage.NO_DELETE)
        new_config[b'General'][b'unpack'] = int(sickrage.UNPACK)
        new_config[b'General'][b'rename_episodes'] = int(sickrage.RENAME_EPISODES)
        new_config[b'General'][b'airdate_episodes'] = int(sickrage.AIRDATE_EPISODES)
        new_config[b'General'][b'file_timestamp_timezone'] = sickrage.FILE_TIMESTAMP_TIMEZONE
        new_config[b'General'][b'create_missing_show_dirs'] = int(sickrage.CREATE_MISSING_SHOW_DIRS)
        new_config[b'General'][b'add_shows_wo_dir'] = int(sickrage.ADD_SHOWS_WO_DIR)

        new_config[b'General'][b'extra_scripts'] = '|'.join(sickrage.EXTRA_SCRIPTS)
        new_config[b'General'][b'git_path'] = sickrage.GIT_PATH
        new_config[b'General'][b'ignore_words'] = sickrage.IGNORE_WORDS
        new_config[b'General'][b'require_words'] = sickrage.REQUIRE_WORDS
        new_config[b'General'][b'ignored_subs_list'] = sickrage.IGNORED_SUBS_LIST
        new_config[b'General'][b'calendar_unprotected'] = int(sickrage.CALENDAR_UNPROTECTED)
        new_config[b'General'][b'calendar_icons'] = int(sickrage.CALENDAR_ICONS)
        new_config[b'General'][b'no_restart'] = int(sickrage.NO_RESTART)
        new_config[b'General'][b'developer'] = int(sickrage.DEVELOPER)
        new_config[b'General'][b'display_all_seasons'] = int(sickrage.DISPLAY_ALL_SEASONS)
        new_config[b'General'][b'news_last_read'] = sickrage.NEWS_LAST_READ

        new_config[b'Blackhole'] = {}
        new_config[b'Blackhole'][b'nzb_dir'] = sickrage.NZB_DIR
        new_config[b'Blackhole'][b'torrent_dir'] = sickrage.TORRENT_DIR

        new_config[b'NZBs'] = {}
        new_config[b'NZBs'][b'nzbs'] = int(sickrage.NZBS)
        new_config[b'NZBs'][b'nzbs_uid'] = sickrage.NZBS_UID
        new_config[b'NZBs'][b'nzbs_hash'] = sickrage.NZBS_HASH

        new_config[b'Newzbin'] = {}
        new_config[b'Newzbin'][b'newzbin'] = int(sickrage.NEWZBIN)
        new_config[b'Newzbin'][b'newzbin_username'] = sickrage.NEWZBIN_USERNAME
        new_config[b'Newzbin'][b'newzbin_password'] = encrypt(sickrage.NEWZBIN_PASSWORD,
                                                              sickrage.ENCRYPTION_VERSION)

        new_config[b'SABnzbd'] = {}
        new_config[b'SABnzbd'][b'sab_username'] = sickrage.SAB_USERNAME
        new_config[b'SABnzbd'][b'sab_password'] = encrypt(sickrage.SAB_PASSWORD, sickrage.ENCRYPTION_VERSION)
        new_config[b'SABnzbd'][b'sab_apikey'] = sickrage.SAB_APIKEY
        new_config[b'SABnzbd'][b'sab_category'] = sickrage.SAB_CATEGORY
        new_config[b'SABnzbd'][b'sab_category_backlog'] = sickrage.SAB_CATEGORY_BACKLOG
        new_config[b'SABnzbd'][b'sab_category_anime'] = sickrage.SAB_CATEGORY_ANIME
        new_config[b'SABnzbd'][b'sab_category_anime_backlog'] = sickrage.SAB_CATEGORY_ANIME_BACKLOG
        new_config[b'SABnzbd'][b'sab_host'] = sickrage.SAB_HOST
        new_config[b'SABnzbd'][b'sab_forced'] = int(sickrage.SAB_FORCED)

        new_config[b'NZBget'] = {}

        new_config[b'NZBget'][b'nzbget_username'] = sickrage.NZBGET_USERNAME
        new_config[b'NZBget'][b'nzbget_password'] = encrypt(sickrage.NZBGET_PASSWORD,
                                                            sickrage.ENCRYPTION_VERSION)
        new_config[b'NZBget'][b'nzbget_category'] = sickrage.NZBGET_CATEGORY
        new_config[b'NZBget'][b'nzbget_category_backlog'] = sickrage.NZBGET_CATEGORY_BACKLOG
        new_config[b'NZBget'][b'nzbget_category_anime'] = sickrage.NZBGET_CATEGORY_ANIME
        new_config[b'NZBget'][b'nzbget_category_anime_backlog'] = sickrage.NZBGET_CATEGORY_ANIME_BACKLOG
        new_config[b'NZBget'][b'nzbget_host'] = sickrage.NZBGET_HOST
        new_config[b'NZBget'][b'nzbget_use_https'] = int(sickrage.NZBGET_USE_HTTPS)
        new_config[b'NZBget'][b'nzbget_priority'] = sickrage.NZBGET_PRIORITY

        new_config[b'TORRENT'] = {}
        new_config[b'TORRENT'][b'torrent_username'] = sickrage.TORRENT_USERNAME
        new_config[b'TORRENT'][b'torrent_password'] = encrypt(sickrage.TORRENT_PASSWORD,
                                                              sickrage.ENCRYPTION_VERSION)
        new_config[b'TORRENT'][b'torrent_host'] = sickrage.TORRENT_HOST
        new_config[b'TORRENT'][b'torrent_path'] = sickrage.TORRENT_PATH
        new_config[b'TORRENT'][b'torrent_seed_time'] = int(sickrage.TORRENT_SEED_TIME)
        new_config[b'TORRENT'][b'torrent_paused'] = int(sickrage.TORRENT_PAUSED)
        new_config[b'TORRENT'][b'torrent_high_bandwidth'] = int(sickrage.TORRENT_HIGH_BANDWIDTH)
        new_config[b'TORRENT'][b'torrent_label'] = sickrage.TORRENT_LABEL
        new_config[b'TORRENT'][b'torrent_label_anime'] = sickrage.TORRENT_LABEL_ANIME
        new_config[b'TORRENT'][b'torrent_verify_cert'] = int(sickrage.TORRENT_VERIFY_CERT)
        new_config[b'TORRENT'][b'torrent_rpcurl'] = sickrage.TORRENT_RPCURL
        new_config[b'TORRENT'][b'torrent_auth_type'] = sickrage.TORRENT_AUTH_TYPE

        new_config[b'KODI'] = {}
        new_config[b'KODI'][b'use_kodi'] = int(sickrage.USE_KODI)
        new_config[b'KODI'][b'kodi_always_on'] = int(sickrage.KODI_ALWAYS_ON)
        new_config[b'KODI'][b'kodi_notify_onsnatch'] = int(sickrage.KODI_NOTIFY_ONSNATCH)
        new_config[b'KODI'][b'kodi_notify_ondownload'] = int(sickrage.KODI_NOTIFY_ONDOWNLOAD)
        new_config[b'KODI'][b'kodi_notify_onsubtitledownload'] = int(sickrage.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'KODI'][b'kodi_update_library'] = int(sickrage.KODI_UPDATE_LIBRARY)
        new_config[b'KODI'][b'kodi_update_full'] = int(sickrage.KODI_UPDATE_FULL)
        new_config[b'KODI'][b'kodi_update_onlyfirst'] = int(sickrage.KODI_UPDATE_ONLYFIRST)
        new_config[b'KODI'][b'kodi_host'] = sickrage.KODI_HOST
        new_config[b'KODI'][b'kodi_username'] = sickrage.KODI_USERNAME
        new_config[b'KODI'][b'kodi_password'] = encrypt(sickrage.KODI_PASSWORD, sickrage.ENCRYPTION_VERSION)

        new_config[b'Plex'] = {}
        new_config[b'Plex'][b'use_plex'] = int(sickrage.USE_PLEX)
        new_config[b'Plex'][b'plex_notify_onsnatch'] = int(sickrage.PLEX_NOTIFY_ONSNATCH)
        new_config[b'Plex'][b'plex_notify_ondownload'] = int(sickrage.PLEX_NOTIFY_ONDOWNLOAD)
        new_config[b'Plex'][b'plex_notify_onsubtitledownload'] = int(sickrage.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Plex'][b'plex_update_library'] = int(sickrage.PLEX_UPDATE_LIBRARY)
        new_config[b'Plex'][b'plex_server_host'] = sickrage.PLEX_SERVER_HOST
        new_config[b'Plex'][b'plex_server_token'] = sickrage.PLEX_SERVER_TOKEN
        new_config[b'Plex'][b'plex_host'] = sickrage.PLEX_HOST
        new_config[b'Plex'][b'plex_username'] = sickrage.PLEX_USERNAME
        new_config[b'Plex'][b'plex_password'] = encrypt(sickrage.PLEX_PASSWORD, sickrage.ENCRYPTION_VERSION)

        new_config[b'Emby'] = {}
        new_config[b'Emby'][b'use_emby'] = int(sickrage.USE_EMBY)
        new_config[b'Emby'][b'emby_host'] = sickrage.EMBY_HOST
        new_config[b'Emby'][b'emby_apikey'] = sickrage.EMBY_APIKEY

        new_config[b'Growl'] = {}
        new_config[b'Growl'][b'use_growl'] = int(sickrage.USE_GROWL)
        new_config[b'Growl'][b'growl_notify_onsnatch'] = int(sickrage.GROWL_NOTIFY_ONSNATCH)
        new_config[b'Growl'][b'growl_notify_ondownload'] = int(sickrage.GROWL_NOTIFY_ONDOWNLOAD)
        new_config[b'Growl'][b'growl_notify_onsubtitledownload'] = int(sickrage.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Growl'][b'growl_host'] = sickrage.GROWL_HOST
        new_config[b'Growl'][b'growl_password'] = encrypt(sickrage.GROWL_PASSWORD,
                                                          sickrage.ENCRYPTION_VERSION)

        new_config[b'FreeMobile'] = {}
        new_config[b'FreeMobile'][b'use_freemobile'] = int(sickrage.USE_FREEMOBILE)
        new_config[b'FreeMobile'][b'freemobile_notify_onsnatch'] = int(sickrage.FREEMOBILE_NOTIFY_ONSNATCH)
        new_config[b'FreeMobile'][b'freemobile_notify_ondownload'] = int(sickrage.FREEMOBILE_NOTIFY_ONDOWNLOAD)
        new_config[b'FreeMobile'][b'freemobile_notify_onsubtitledownload'] = int(
                sickrage.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'FreeMobile'][b'freemobile_id'] = sickrage.FREEMOBILE_ID
        new_config[b'FreeMobile'][b'freemobile_apikey'] = sickrage.FREEMOBILE_APIKEY

        new_config[b'Prowl'] = {}
        new_config[b'Prowl'][b'use_prowl'] = int(sickrage.USE_PROWL)
        new_config[b'Prowl'][b'prowl_notify_onsnatch'] = int(sickrage.PROWL_NOTIFY_ONSNATCH)
        new_config[b'Prowl'][b'prowl_notify_ondownload'] = int(sickrage.PROWL_NOTIFY_ONDOWNLOAD)
        new_config[b'Prowl'][b'prowl_notify_onsubtitledownload'] = int(sickrage.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Prowl'][b'prowl_api'] = sickrage.PROWL_API
        new_config[b'Prowl'][b'prowl_priority'] = sickrage.PROWL_PRIORITY

        new_config[b'Twitter'] = {}
        new_config[b'Twitter'][b'use_twitter'] = int(sickrage.USE_TWITTER)
        new_config[b'Twitter'][b'twitter_notify_onsnatch'] = int(sickrage.TWITTER_NOTIFY_ONSNATCH)
        new_config[b'Twitter'][b'twitter_notify_ondownload'] = int(sickrage.TWITTER_NOTIFY_ONDOWNLOAD)
        new_config[b'Twitter'][b'twitter_notify_onsubtitledownload'] = int(sickrage.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Twitter'][b'twitter_username'] = sickrage.TWITTER_USERNAME
        new_config[b'Twitter'][b'twitter_password'] = encrypt(sickrage.TWITTER_PASSWORD,
                                                              sickrage.ENCRYPTION_VERSION)
        new_config[b'Twitter'][b'twitter_prefix'] = sickrage.TWITTER_PREFIX
        new_config[b'Twitter'][b'twitter_dmto'] = sickrage.TWITTER_DMTO
        new_config[b'Twitter'][b'twitter_usedm'] = int(sickrage.TWITTER_USEDM)

        new_config[b'Boxcar'] = {}
        new_config[b'Boxcar'][b'use_boxcar'] = int(sickrage.USE_BOXCAR)
        new_config[b'Boxcar'][b'boxcar_notify_onsnatch'] = int(sickrage.BOXCAR_NOTIFY_ONSNATCH)
        new_config[b'Boxcar'][b'boxcar_notify_ondownload'] = int(sickrage.BOXCAR_NOTIFY_ONDOWNLOAD)
        new_config[b'Boxcar'][b'boxcar_notify_onsubtitledownload'] = int(sickrage.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Boxcar'][b'boxcar_username'] = sickrage.BOXCAR_USERNAME

        new_config[b'Boxcar2'] = {}
        new_config[b'Boxcar2'][b'use_boxcar2'] = int(sickrage.USE_BOXCAR2)
        new_config[b'Boxcar2'][b'boxcar2_notify_onsnatch'] = int(sickrage.BOXCAR2_NOTIFY_ONSNATCH)
        new_config[b'Boxcar2'][b'boxcar2_notify_ondownload'] = int(sickrage.BOXCAR2_NOTIFY_ONDOWNLOAD)
        new_config[b'Boxcar2'][b'boxcar2_notify_onsubtitledownload'] = int(sickrage.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Boxcar2'][b'boxcar2_accesstoken'] = sickrage.BOXCAR2_ACCESSTOKEN

        new_config[b'Pushover'] = {}
        new_config[b'Pushover'][b'use_pushover'] = int(sickrage.USE_PUSHOVER)
        new_config[b'Pushover'][b'pushover_notify_onsnatch'] = int(sickrage.PUSHOVER_NOTIFY_ONSNATCH)
        new_config[b'Pushover'][b'pushover_notify_ondownload'] = int(sickrage.PUSHOVER_NOTIFY_ONDOWNLOAD)
        new_config[b'Pushover'][b'pushover_notify_onsubtitledownload'] = int(
                sickrage.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Pushover'][b'pushover_userkey'] = sickrage.PUSHOVER_USERKEY
        new_config[b'Pushover'][b'pushover_apikey'] = sickrage.PUSHOVER_APIKEY
        new_config[b'Pushover'][b'pushover_device'] = sickrage.PUSHOVER_DEVICE
        new_config[b'Pushover'][b'pushover_sound'] = sickrage.PUSHOVER_SOUND

        new_config[b'Libnotify'] = {}
        new_config[b'Libnotify'][b'use_libnotify'] = int(sickrage.USE_LIBNOTIFY)
        new_config[b'Libnotify'][b'libnotify_notify_onsnatch'] = int(sickrage.LIBNOTIFY_NOTIFY_ONSNATCH)
        new_config[b'Libnotify'][b'libnotify_notify_ondownload'] = int(sickrage.LIBNOTIFY_NOTIFY_ONDOWNLOAD)
        new_config[b'Libnotify'][b'libnotify_notify_onsubtitledownload'] = int(
                sickrage.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)

        new_config[b'NMJ'] = {}
        new_config[b'NMJ'][b'use_nmj'] = int(sickrage.USE_NMJ)
        new_config[b'NMJ'][b'nmj_host'] = sickrage.NMJ_HOST
        new_config[b'NMJ'][b'nmj_database'] = sickrage.NMJ_DATABASE
        new_config[b'NMJ'][b'nmj_mount'] = sickrage.NMJ_MOUNT

        new_config[b'NMJv2'] = {}
        new_config[b'NMJv2'][b'use_nmjv2'] = int(sickrage.USE_NMJv2)
        new_config[b'NMJv2'][b'nmjv2_host'] = sickrage.NMJv2_HOST
        new_config[b'NMJv2'][b'nmjv2_database'] = sickrage.NMJv2_DATABASE
        new_config[b'NMJv2'][b'nmjv2_dbloc'] = sickrage.NMJv2_DBLOC

        new_config[b'Synology'] = {}
        new_config[b'Synology'][b'use_synoindex'] = int(sickrage.USE_SYNOINDEX)

        new_config[b'SynologyNotifier'] = {}
        new_config[b'SynologyNotifier'][b'use_synologynotifier'] = int(sickrage.USE_SYNOLOGYNOTIFIER)
        new_config[b'SynologyNotifier'][b'synologynotifier_notify_onsnatch'] = int(
                sickrage.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)
        new_config[b'SynologyNotifier'][b'synologynotifier_notify_ondownload'] = int(
                sickrage.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)
        new_config[b'SynologyNotifier'][b'synologynotifier_notify_onsubtitledownload'] = int(
                sickrage.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)

        new_config[b'theTVDB'] = {}
        new_config[b'theTVDB'][b'thetvdb_apitoken'] = sickrage.THETVDB_APITOKEN

        new_config[b'Trakt'] = {}
        new_config[b'Trakt'][b'use_trakt'] = int(sickrage.USE_TRAKT)
        new_config[b'Trakt'][b'trakt_username'] = sickrage.TRAKT_USERNAME
        new_config[b'Trakt'][b'trakt_access_token'] = sickrage.TRAKT_ACCESS_TOKEN
        new_config[b'Trakt'][b'trakt_refresh_token'] = sickrage.TRAKT_REFRESH_TOKEN
        new_config[b'Trakt'][b'trakt_remove_watchlist'] = int(sickrage.TRAKT_REMOVE_WATCHLIST)
        new_config[b'Trakt'][b'trakt_remove_serieslist'] = int(sickrage.TRAKT_REMOVE_SERIESLIST)
        new_config[b'Trakt'][b'trakt_remove_show_from_sickrage'] = int(sickrage.TRAKT_REMOVE_SHOW_FROM_SICKRAGE)
        new_config[b'Trakt'][b'trakt_sync_watchlist'] = int(sickrage.TRAKT_SYNC_WATCHLIST)
        new_config[b'Trakt'][b'trakt_method_add'] = int(sickrage.TRAKT_METHOD_ADD)
        new_config[b'Trakt'][b'trakt_start_paused'] = int(sickrage.TRAKT_START_PAUSED)
        new_config[b'Trakt'][b'trakt_use_recommended'] = int(sickrage.TRAKT_USE_RECOMMENDED)
        new_config[b'Trakt'][b'trakt_sync'] = int(sickrage.TRAKT_SYNC)
        new_config[b'Trakt'][b'trakt_sync_remove'] = int(sickrage.TRAKT_SYNC_REMOVE)
        new_config[b'Trakt'][b'trakt_default_indexer'] = int(sickrage.TRAKT_DEFAULT_INDEXER)
        new_config[b'Trakt'][b'trakt_timeout'] = int(sickrage.TRAKT_TIMEOUT)
        new_config[b'Trakt'][b'trakt_blacklist_name'] = sickrage.TRAKT_BLACKLIST_NAME

        new_config[b'pyTivo'] = {}
        new_config[b'pyTivo'][b'use_pytivo'] = int(sickrage.USE_PYTIVO)
        new_config[b'pyTivo'][b'pytivo_notify_onsnatch'] = int(sickrage.PYTIVO_NOTIFY_ONSNATCH)
        new_config[b'pyTivo'][b'pytivo_notify_ondownload'] = int(sickrage.PYTIVO_NOTIFY_ONDOWNLOAD)
        new_config[b'pyTivo'][b'pytivo_notify_onsubtitledownload'] = int(sickrage.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'pyTivo'][b'pyTivo_update_library'] = int(sickrage.PYTIVO_UPDATE_LIBRARY)
        new_config[b'pyTivo'][b'pytivo_host'] = sickrage.PYTIVO_HOST
        new_config[b'pyTivo'][b'pytivo_share_name'] = sickrage.PYTIVO_SHARE_NAME
        new_config[b'pyTivo'][b'pytivo_tivo_name'] = sickrage.PYTIVO_TIVO_NAME

        new_config[b'NMA'] = {}
        new_config[b'NMA'][b'use_nma'] = int(sickrage.USE_NMA)
        new_config[b'NMA'][b'nma_notify_onsnatch'] = int(sickrage.NMA_NOTIFY_ONSNATCH)
        new_config[b'NMA'][b'nma_notify_ondownload'] = int(sickrage.NMA_NOTIFY_ONDOWNLOAD)
        new_config[b'NMA'][b'nma_notify_onsubtitledownload'] = int(sickrage.NMA_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'NMA'][b'nma_api'] = sickrage.NMA_API
        new_config[b'NMA'][b'nma_priority'] = sickrage.NMA_PRIORITY

        new_config[b'Pushalot'] = {}
        new_config[b'Pushalot'][b'use_pushalot'] = int(sickrage.USE_PUSHALOT)
        new_config[b'Pushalot'][b'pushalot_notify_onsnatch'] = int(sickrage.PUSHALOT_NOTIFY_ONSNATCH)
        new_config[b'Pushalot'][b'pushalot_notify_ondownload'] = int(sickrage.PUSHALOT_NOTIFY_ONDOWNLOAD)
        new_config[b'Pushalot'][b'pushalot_notify_onsubtitledownload'] = int(
                sickrage.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Pushalot'][b'pushalot_authorizationtoken'] = sickrage.PUSHALOT_AUTHORIZATIONTOKEN

        new_config[b'Pushbullet'] = {}
        new_config[b'Pushbullet'][b'use_pushbullet'] = int(sickrage.USE_PUSHBULLET)
        new_config[b'Pushbullet'][b'pushbullet_notify_onsnatch'] = int(sickrage.PUSHBULLET_NOTIFY_ONSNATCH)
        new_config[b'Pushbullet'][b'pushbullet_notify_ondownload'] = int(sickrage.PUSHBULLET_NOTIFY_ONDOWNLOAD)
        new_config[b'Pushbullet'][b'pushbullet_notify_onsubtitledownload'] = int(
                sickrage.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Pushbullet'][b'pushbullet_api'] = sickrage.PUSHBULLET_API
        new_config[b'Pushbullet'][b'pushbullet_device'] = sickrage.PUSHBULLET_DEVICE

        new_config[b'Email'] = {}
        new_config[b'Email'][b'use_email'] = int(sickrage.USE_EMAIL)
        new_config[b'Email'][b'email_notify_onsnatch'] = int(sickrage.EMAIL_NOTIFY_ONSNATCH)
        new_config[b'Email'][b'email_notify_ondownload'] = int(sickrage.EMAIL_NOTIFY_ONDOWNLOAD)
        new_config[b'Email'][b'email_notify_onsubtitledownload'] = int(sickrage.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Email'][b'email_host'] = sickrage.EMAIL_HOST
        new_config[b'Email'][b'email_port'] = int(sickrage.EMAIL_PORT)
        new_config[b'Email'][b'email_tls'] = int(sickrage.EMAIL_TLS)
        new_config[b'Email'][b'email_user'] = sickrage.EMAIL_USER
        new_config[b'Email'][b'email_password'] = encrypt(sickrage.EMAIL_PASSWORD,
                                                          sickrage.ENCRYPTION_VERSION)
        new_config[b'Email'][b'email_from'] = sickrage.EMAIL_FROM
        new_config[b'Email'][b'email_list'] = sickrage.EMAIL_LIST

        new_config[b'Newznab'] = {}
        new_config[b'Newznab'][b'newznab_data'] = sickrage.NEWZNAB_DATA

        new_config[b'TorrentRss'] = {}
        new_config[b'TorrentRss'][b'torrentrss_data'] = '!!!'.join(
                [x.configStr() for x in sickrage.torrentRssProviderList])

        new_config[b'GUI'] = {}
        new_config[b'GUI'][b'gui_name'] = sickrage.GUI_NAME
        new_config[b'GUI'][b'theme_name'] = sickrage.THEME_NAME
        new_config[b'GUI'][b'home_layout'] = sickrage.HOME_LAYOUT
        new_config[b'GUI'][b'history_layout'] = sickrage.HISTORY_LAYOUT
        new_config[b'GUI'][b'history_limit'] = sickrage.HISTORY_LIMIT
        new_config[b'GUI'][b'display_show_specials'] = int(sickrage.DISPLAY_SHOW_SPECIALS)
        new_config[b'GUI'][b'coming_eps_layout'] = sickrage.COMING_EPS_LAYOUT
        new_config[b'GUI'][b'coming_eps_display_paused'] = int(sickrage.COMING_EPS_DISPLAY_PAUSED)
        new_config[b'GUI'][b'coming_eps_sort'] = sickrage.COMING_EPS_SORT
        new_config[b'GUI'][b'coming_eps_missed_range'] = int(sickrage.COMING_EPS_MISSED_RANGE)
        new_config[b'GUI'][b'fuzzy_dating'] = int(sickrage.FUZZY_DATING)
        new_config[b'GUI'][b'trim_zero'] = int(sickrage.TRIM_ZERO)
        new_config[b'GUI'][b'date_preset'] = sickrage.DATE_PRESET
        new_config[b'GUI'][b'time_preset'] = sickrage.TIME_PRESET_W_SECONDS
        new_config[b'GUI'][b'timezone_display'] = sickrage.TIMEZONE_DISPLAY
        new_config[b'GUI'][b'poster_sortby'] = sickrage.POSTER_SORTBY
        new_config[b'GUI'][b'poster_sortdir'] = sickrage.POSTER_SORTDIR
        new_config[b'GUI'][b'filter_row'] = int(sickrage.FILTER_ROW)

        new_config[b'Subtitles'] = {}
        new_config[b'Subtitles'][b'use_subtitles'] = int(sickrage.USE_SUBTITLES)
        new_config[b'Subtitles'][b'subtitles_languages'] = ','.join(sickrage.SUBTITLES_LANGUAGES)
        new_config[b'Subtitles'][b'SUBTITLES_SERVICES_LIST'] = ','.join(sickrage.SUBTITLES_SERVICES_LIST)
        new_config[b'Subtitles'][b'SUBTITLES_SERVICES_ENABLED'] = '|'.join(
                [str(x) for x in sickrage.SUBTITLES_SERVICES_ENABLED])
        new_config[b'Subtitles'][b'subtitles_dir'] = sickrage.SUBTITLES_DIR
        new_config[b'Subtitles'][b'subtitles_default'] = int(sickrage.SUBTITLES_DEFAULT)
        new_config[b'Subtitles'][b'subtitles_history'] = int(sickrage.SUBTITLES_HISTORY)
        new_config[b'Subtitles'][b'embedded_subtitles_all'] = int(sickrage.EMBEDDED_SUBTITLES_ALL)
        new_config[b'Subtitles'][b'subtitles_hearing_impaired'] = int(sickrage.SUBTITLES_HEARING_IMPAIRED)
        new_config[b'Subtitles'][b'subtitles_finder_frequency'] = int(sickrage.SUBTITLE_SEARCHER_FREQ)
        new_config[b'Subtitles'][b'subtitles_multi'] = int(sickrage.SUBTITLES_MULTI)
        new_config[b'Subtitles'][b'subtitles_extra_scripts'] = '|'.join(sickrage.SUBTITLES_EXTRA_SCRIPTS)

        new_config[b'Subtitles'][b'addic7ed_username'] = sickrage.ADDIC7ED_USER
        new_config[b'Subtitles'][b'addic7ed_password'] = encrypt(sickrage.ADDIC7ED_PASS,
                                                                 sickrage.ENCRYPTION_VERSION)

        new_config[b'Subtitles'][b'legendastv_username'] = sickrage.LEGENDASTV_USER
        new_config[b'Subtitles'][b'legendastv_password'] = encrypt(sickrage.LEGENDASTV_PASS,
                                                                   sickrage.ENCRYPTION_VERSION)

        new_config[b'Subtitles'][b'opensubtitles_username'] = sickrage.OPENSUBTITLES_USER
        new_config[b'Subtitles'][b'opensubtitles_password'] = encrypt(sickrage.OPENSUBTITLES_PASS,
                                                                      sickrage.ENCRYPTION_VERSION)

        new_config[b'FailedDownloads'] = {}
        new_config[b'FailedDownloads'][b'use_failed_downloads'] = int(sickrage.USE_FAILED_DOWNLOADS)
        new_config[b'FailedDownloads'][b'delete_failed'] = int(sickrage.DELETE_FAILED)

        new_config[b'ANIDB'] = {}
        new_config[b'ANIDB'][b'use_anidb'] = int(sickrage.USE_ANIDB)
        new_config[b'ANIDB'][b'anidb_username'] = sickrage.ANIDB_USERNAME
        new_config[b'ANIDB'][b'anidb_password'] = encrypt(sickrage.ANIDB_PASSWORD,
                                                          sickrage.ENCRYPTION_VERSION)
        new_config[b'ANIDB'][b'anidb_use_mylist'] = int(sickrage.ANIDB_USE_MYLIST)

        new_config[b'ANIME'] = {}
        new_config[b'ANIME'][b'anime_split_home'] = int(sickrage.ANIME_SPLIT_HOME)

        # dynamically save provider settings
        for providerID, providerObj in sickrage.providersDict[GenericProvider.TORRENT].items():
            new_config[providerID.upper()] = {}
            new_config[providerID.upper()][providerID] = int(providerObj.enabled)
            if hasattr(providerObj, 'digest'):
                new_config[providerID.upper()][
                    providerID + '_digest'] = providerObj.digest
            if hasattr(providerObj, 'hash'):
                new_config[providerID.upper()][
                    providerID + '_hash'] = providerObj.hash
            if hasattr(providerObj, 'api_key'):
                new_config[providerID.upper()][
                    providerID + '_api_key'] = providerObj.api_key
            if hasattr(providerObj, 'username'):
                new_config[providerID.upper()][
                    providerID + '_username'] = providerObj.username
            if hasattr(providerObj, 'password'):
                new_config[providerID.upper()][providerID + '_password'] = encrypt(
                        providerObj.password, sickrage.ENCRYPTION_VERSION)
            if hasattr(providerObj, 'passkey'):
                new_config[providerID.upper()][
                    providerID + '_passkey'] = providerObj.passkey
            if hasattr(providerObj, 'pin'):
                new_config[providerID.upper()][
                    providerID + '_pin'] = providerObj.pin
            if hasattr(providerObj, 'confirmed'):
                new_config[providerID.upper()][providerID + '_confirmed'] = int(
                        providerObj.confirmed)
            if hasattr(providerObj, 'ranked'):
                new_config[providerID.upper()][providerID + '_ranked'] = int(
                        providerObj.ranked)
            if hasattr(providerObj, 'engrelease'):
                new_config[providerID.upper()][providerID + '_engrelease'] = int(
                        providerObj.engrelease)
            if hasattr(providerObj, 'onlyspasearch'):
                new_config[providerID.upper()][providerID + '_onlyspasearch'] = int(
                        providerObj.onlyspasearch)
            if hasattr(providerObj, 'sorting'):
                new_config[providerID.upper()][
                    providerID + '_sorting'] = providerObj.sorting
            if hasattr(providerObj, 'ratio'):
                new_config[providerID.upper()][
                    providerID + '_ratio'] = providerObj.ratio
            if hasattr(providerObj, 'minseed'):
                new_config[providerID.upper()][providerID + '_minseed'] = int(
                        providerObj.minseed)
            if hasattr(providerObj, 'minleech'):
                new_config[providerID.upper()][providerID + '_minleech'] = int(
                        providerObj.minleech)
            if hasattr(providerObj, 'options'):
                new_config[providerID.upper()][
                    providerID + '_options'] = providerObj.options
            if hasattr(providerObj, 'freeleech'):
                new_config[providerID.upper()][providerID + '_freeleech'] = int(
                        providerObj.freeleech)
            if hasattr(providerObj, 'search_mode'):
                new_config[providerID.upper()][
                    providerID + '_search_mode'] = providerObj.search_mode
            if hasattr(providerObj, 'search_fallback'):
                new_config[providerID.upper()][providerID + '_search_fallback'] = int(
                        providerObj.search_fallback)
            if hasattr(providerObj, 'enable_daily'):
                new_config[providerID.upper()][providerID + '_enable_daily'] = int(
                        providerObj.enable_daily)
            if hasattr(providerObj, 'enable_backlog'):
                new_config[providerID.upper()][providerID + '_enable_backlog'] = int(
                        providerObj.enable_backlog)
            if hasattr(providerObj, 'cat'):
                new_config[providerID.upper()][providerID + '_cat'] = int(
                        providerObj.cat)
            if hasattr(providerObj, 'subtitle'):
                new_config[providerID.upper()][providerID + '_subtitle'] = int(
                        providerObj.subtitle)

        for providerID, providerObj in sickrage.providersDict[GenericProvider.NZB].items():
            new_config[providerID.upper()] = {}
            new_config[providerID.upper()][providerID] = int(providerObj.enabled)

            if hasattr(providerObj, 'api_key'):
                new_config[providerID.upper()][
                    providerID + '_api_key'] = providerObj.api_key
            if hasattr(providerObj, 'username'):
                new_config[providerID.upper()][
                    providerID + '_username'] = providerObj.username
            if hasattr(providerObj, 'search_mode'):
                new_config[providerID.upper()][
                    providerID + '_search_mode'] = providerObj.search_mode
            if hasattr(providerObj, 'search_fallback'):
                new_config[providerID.upper()][providerID + '_search_fallback'] = int(
                        providerObj.search_fallback)
            if hasattr(providerObj, 'enable_daily'):
                new_config[providerID.upper()][providerID + '_enable_daily'] = int(
                        providerObj.enable_daily)
            if hasattr(providerObj, 'enable_backlog'):
                new_config[providerID.upper()][providerID + '_enable_backlog'] = int(
                        providerObj.enable_backlog)

        new_config.write()
        return new_config
