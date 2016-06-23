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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import os.path

import babelfish

import sickrage
from sickrage.core.common import ARCHIVED, DOWNLOADED, Quality, SKIPPED, \
    UNAIRED, UNKNOWN, WANTED, dateTimeFormat, statusStrings
from sickrage.core.databases import Connection, SchemaUpgrade

MIN_DB_VERSION = 9  # oldest db version we support migrating from
MAX_DB_VERSION = 43


class MainDB(Connection):
    def __init__(self, filename='sickrage.db', suffix=None, row_type=None):
        super(MainDB, self).__init__(filename, suffix, row_type)

    class SanityCheck(Connection):
        def __init__(self):
            super(MainDB.SanityCheck, self).__init__()
            self.fix_missing_tables()
            self.fix_missing_table_indexes()
            self.fix_duplicate_shows()
            self.fix_duplicate_episodes()
            self.fix_orphan_episodes()
            self.fix_unaired_episodes()
            self.fix_tvrage_show_statues()
            self.fix_episode_statuses()
            self.fix_invalid_airdates()
            self.fix_subtitles_codes()
            self.fix_show_nfo_lang()
            self.convert_tvrage_to_tvdb()
            self.convert_archived_to_compund()

        # todo: fix spelling to compound
        def convert_archived_to_compund(self):
            sickrage.srCore.srLogger.debug('Checking for archived episodes not qualified')

            query = "SELECT episode_id, showid, status, location, season, episode " + \
                    "FROM tv_episodes WHERE status = {}".format(ARCHIVED)

            sqlResults = self.select(query)
            if sqlResults:
                sickrage.srCore.srLogger.warning(
                    "Found %i shows with bare archived status, attempting automatic conversion..." % len(
                        sqlResults))

            for archivedEp in sqlResults:
                fixedStatus = Quality.compositeStatus(ARCHIVED, Quality.UNKNOWN)
                existing = archivedEp['location'] and os.path.exists(archivedEp['location'])
                if existing:
                    quality = Quality.assumeQuality(archivedEp['location'])
                    fixedStatus = Quality.compositeStatus(ARCHIVED, quality)

                sickrage.srCore.srLogger.info('Changing status from {} to {} for {}: S{}E{} at {} (File {})'
                                              .format(statusStrings[ARCHIVED], statusStrings[fixedStatus],
                                                      archivedEp['showid'], archivedEp['season'], archivedEp['episode'],
                                                      archivedEp['location'] if archivedEp[
                                                          'location'] else 'unknown location',
                                                      ('NOT FOUND', 'EXISTS')[bool(existing)]))

                self.action(
                    "UPDATE tv_episodes SET status = {0} WHERE episode_id = {}".format(fixedStatus,
                                                                                       archivedEp['episode_id']))

        def convert_tvrage_to_tvdb(self):
            sickrage.srCore.srLogger.debug("Checking for shows with tvrage id's, since tvrage is gone")
            from sickrage.indexers.config import INDEXER_TVRAGE, INDEXER_TVDB

            sqlResults = self.select(
                "SELECT indexer_id, show_name, location FROM tv_shows WHERE indexer = {}".format(INDEXER_TVRAGE))

            if sqlResults:
                sickrage.srCore.srLogger.warning(
                    "Found {} shows with TVRage ID's, attempting automatic conversion...".format(len(sqlResults)))

            for tvrage_show in sqlResults:
                sickrage.srCore.srLogger.info(
                    "Processing {} at {}".format(tvrage_show['show_name'], tvrage_show['location']))
                mapping = self.select(
                    "SELECT mindexer_id FROM indexer_mapping WHERE indexer_id=%i AND indexer=%i AND mindexer=%i" %
                    (tvrage_show['indexer_id'], INDEXER_TVRAGE, INDEXER_TVDB))

                if len(mapping) != 1:
                    sickrage.srCore.srLogger.warning(
                        "Error mapping show from tvrage to tvdb for %s (%s), found %i mapping results. Cannot convert automatically!" %
                        (tvrage_show['show_name'], tvrage_show['location'], len(mapping)))
                    sickrage.srCore.srLogger.warning(
                        "Removing the TVRage show and it's episodes from the DB, use 'addExistingShow'")
                    self.action("DELETE FROM tv_shows WHERE indexer_id = %i AND indexer = %i" % (
                        tvrage_show['indexer_id'], INDEXER_TVRAGE))
                    self.action("DELETE FROM tv_episodes WHERE showid = %i" % tvrage_show['indexer_id'])
                    continue

                sickrage.srCore.srLogger.info('Checking if there is already a show with id:%i in the show list')
                duplicate = self.select("SELECT * FROM tv_shows WHERE indexer_id = %i AND indexer = %i" % (
                    mapping[0]['mindexer_id'], INDEXER_TVDB))
                if duplicate:
                    sickrage.srCore.srLogger.warning(
                        'Found %s which has the same id as %s, cannot convert automatically so I am pausing %s' %
                        (duplicate[0]['show_name'], tvrage_show['show_name'], duplicate[0]['show_name']))
                    self.action("UPDATE tv_shows SET paused=1 WHERE indexer=%i AND indexer_id=%i" %
                                (INDEXER_TVDB, duplicate[0]['indexer_id']))

                    sickrage.srCore.srLogger.warning(
                        "Removing %s and it's episodes from the DB" % tvrage_show['show_name'])
                    self.action("DELETE FROM tv_shows WHERE indexer_id = %i AND indexer = %i" % (
                        tvrage_show['indexer_id'], INDEXER_TVRAGE))
                    self.action("DELETE FROM tv_episodes WHERE showid = %i" % tvrage_show['indexer_id'])
                    sickrage.srCore.srLogger.warning(
                        'Manually move the season folders from %s into %s, and delete %s before rescanning %s and unpausing it' %
                        (tvrage_show['location'], duplicate[0]['location'], tvrage_show['location'],
                         duplicate[0]['show_name']))
                    continue

                sickrage.srCore.srLogger.info(
                    'Mapping %s to tvdb id %i' % (tvrage_show['show_name'], mapping[0]['mindexer_id']))

                self.action(
                    "UPDATE tv_shows SET indexer=%i, indexer_id=%i WHERE indexer_id=%i" %
                    (INDEXER_TVDB, mapping[0]['mindexer_id'], tvrage_show['indexer_id'])
                )

                sickrage.srCore.srLogger.info('Relinking episodes to show')
                self.action(
                    "UPDATE tv_episodes SET indexer=%i, showid=%i, indexerid=0 WHERE showid=%i" %
                    (INDEXER_TVDB, mapping[0]['mindexer_id'], tvrage_show['indexer_id'])
                )

                sickrage.srCore.srLogger.warning('Please perform a full update on %s' % tvrage_show['show_name'])

        def fix_duplicate_shows(self, column='indexer_id'):

            sqlResults = self.select(
                "SELECT show_id, " + column + ", COUNT(" + column + ") as count FROM tv_shows GROUP BY " + column + " HAVING count > 1")

            for cur_duplicate in sqlResults:

                sickrage.srCore.srLogger.debug(
                    "Duplicate show detected! " + column + ": " + str(cur_duplicate[column]) + " count: " + str(
                        cur_duplicate["count"]))

                cur_dupe_results = self.select(
                    "SELECT show_id, " + column + " FROM tv_shows WHERE " + column + " = ? LIMIT ?",
                    [cur_duplicate[column], int(cur_duplicate["count"]) - 1]
                )

                for cur_dupe_id in cur_dupe_results:
                    sickrage.srCore.srLogger.info(
                        "Deleting duplicate show with " + column + ": " + str(
                            cur_dupe_id[column]) + " show_id: " + str(
                            cur_dupe_id["show_id"]))
                    self.action("DELETE FROM tv_shows WHERE show_id = ?", [cur_dupe_id["show_id"]])

        def fix_duplicate_episodes(self):

            sqlResults = self.select(
                "SELECT showid, season, episode, COUNT(showid) AS count FROM tv_episodes GROUP BY showid, season, episode HAVING count > 1")

            for cur_duplicate in sqlResults:

                sickrage.srCore.srLogger.debug(
                    "Duplicate episode detected! showid: " + str(cur_duplicate["showid"]) + " season: " + str(
                        cur_duplicate["season"]) + " episode: " + str(
                        cur_duplicate["episode"]) + " count: " + str(
                        cur_duplicate["count"]))

                cur_dupe_results = self.select(
                    "SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? ORDER BY episode_id DESC LIMIT ?",
                    [cur_duplicate["showid"], cur_duplicate["season"], cur_duplicate["episode"],
                     int(cur_duplicate["count"]) - 1]
                )

                for cur_dupe_id in cur_dupe_results:
                    sickrage.srCore.srLogger.info(
                        "Deleting duplicate episode with episode_id: " + str(cur_dupe_id["episode_id"]))
                    self.action("DELETE FROM tv_episodes WHERE episode_id = ?", [cur_dupe_id["episode_id"]])

        def fix_orphan_episodes(self):

            sqlResults = self.select(
                "SELECT episode_id, showid, tv_shows.indexer_id FROM tv_episodes LEFT JOIN tv_shows ON tv_episodes.showid=tv_shows.indexer_id WHERE tv_shows.indexer_id IS NULL")

            for cur_orphan in sqlResults:
                sickrage.srCore.srLogger.debug(
                    "Orphan episode detected! episode_id: " + str(cur_orphan["episode_id"]) + " showid: " + str(
                        cur_orphan["showid"]))
                sickrage.srCore.srLogger.info(
                    "Deleting orphan episode with episode_id: " + str(cur_orphan["episode_id"]))
                self.action("DELETE FROM tv_episodes WHERE episode_id = ?", [cur_orphan["episode_id"]])

        def fix_missing_table_indexes(self):
            if not self.hasIndex('idx_indexer_id'):
                sickrage.srCore.srLogger.info("Missing idx_indexer_id for TV Shows table detected!, fixing...")
                self.action("CREATE UNIQUE INDEX idx_indexer_id ON tv_shows(indexer_id);")

            if not self.hasIndex('idx_tv_episodes_showid_airdate'):
                sickrage.srCore.srLogger.info(
                    "Missing idx_tv_episodes_showid_airdate for TV Episodes table detected!, fixing...")
                self.action("CREATE INDEX idx_tv_episodes_showid_airdate ON tv_episodes(showid, airdate);")

            if not self.hasIndex('idx_showid'):
                sickrage.srCore.srLogger.info("Missing idx_showid for TV Episodes table detected!, fixing...")
                self.action("CREATE INDEX idx_showid ON tv_episodes (showid);")

            if not self.hasIndex('idx_status'):
                sickrage.srCore.srLogger.info("Missing idx_status for TV Episodes table detected!, fixing...")
                self.action("CREATE INDEX idx_status ON tv_episodes (status, season, episode, airdate)")

            if not self.hasIndex('idx_sta_epi_air'):
                sickrage.srCore.srLogger.info("Missing idx_sta_epi_air for TV Episodes table detected!, fixing...")
                self.action("CREATE INDEX idx_sta_epi_air ON tv_episodes (status, episode, airdate)")

            if not self.hasIndex('idx_sta_epi_sta_air'):
                sickrage.srCore.srLogger.info("Missing idx_sta_epi_sta_air for TV Episodes table detected!, fixing...")
                self.action("CREATE INDEX idx_sta_epi_sta_air ON tv_episodes (season, episode, status, airdate)")

        def fix_unaired_episodes(self):

            curDate = datetime.date.today()

            sqlResults = self.select(
                "SELECT episode_id FROM tv_episodes WHERE (airdate > ? OR airdate = 1) AND status IN (?,?) AND season > 0",
                [curDate.toordinal(), SKIPPED, WANTED])

            for cur_unaired in sqlResults:
                sickrage.srCore.srLogger.info(
                    "Fixing unaired episode status for episode_id: %s" % cur_unaired["episode_id"])
                self.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?",
                            [UNAIRED, cur_unaired["episode_id"]])

        def fix_tvrage_show_statues(self):
            status_map = {
                'returning series': 'Continuing',
                'canceled/ended': 'Ended',
                'tbd/on the bubble': 'Continuing',
                'in development': 'Continuing',
                'new series': 'Continuing',
                'never aired': 'Ended',
                'final season': 'Continuing',
                'on hiatus': 'Continuing',
                'pilot ordered': 'Continuing',
                'pilot rejected': 'Ended',
                'canceled': 'Ended',
                'ended': 'Ended',
                '': 'Unknown',
            }

            for old_status, new_status in status_map.items():
                self.action("UPDATE tv_shows SET status = ? WHERE LOWER(status) = ?", [new_status, old_status])

        def fix_episode_statuses(self):
            sqlResults = self.select("SELECT episode_id, showid FROM tv_episodes WHERE status IS NULL")

            for cur_ep in sqlResults:
                sickrage.srCore.srLogger.debug(
                    "MALFORMED episode status detected! episode_id: " + str(
                        cur_ep["episode_id"]) + " showid: " + str(
                        cur_ep["showid"]))
                sickrage.srCore.srLogger.info(
                    "Fixing malformed episode status with episode_id: " + str(cur_ep["episode_id"]))
                self.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?",
                            [UNKNOWN, cur_ep["episode_id"]])

        def fix_invalid_airdates(self):

            sqlResults = self.select(
                "SELECT episode_id, showid FROM tv_episodes WHERE airdate >= ? OR airdate < 1",
                [datetime.date.max.toordinal()])

            for bad_airdate in sqlResults:
                sickrage.srCore.srLogger.debug(
                    "Bad episode airdate detected! episode_id: " + str(
                        bad_airdate["episode_id"]) + " showid: " + str(
                        bad_airdate["showid"]))
                sickrage.srCore.srLogger.info(
                    "Fixing bad episode airdate for episode_id: " + str(bad_airdate["episode_id"]))
                self.action("UPDATE tv_episodes SET airdate = '1' WHERE episode_id = ?",
                            [bad_airdate["episode_id"]])

        def fix_subtitles_codes(self):

            sqlResults = self.select(
                "SELECT subtitles, episode_id FROM tv_episodes WHERE subtitles != '' AND subtitles_lastsearch < ?;",
                [datetime.datetime(2015, 7, 15, 17, 20, 44, 326380).strftime(dateTimeFormat)]
            )

            validLanguages = [babelfish.Language.fromopensubtitles(language).opensubtitles for language in
                              babelfish.language_converters['opensubtitles'].codes if len(language) == 3]

            if not sqlResults:
                return

            for sqlResult in sqlResults:
                langs = []

                sickrage.srCore.srLogger.debug("Checking subtitle codes for episode_id: %s, codes: %s" %
                                               (sqlResult['episode_id'], sqlResult['subtitles']))

                for subcode in sqlResult['subtitles'].split(','):
                    if not len(subcode) is 3 or subcode not in validLanguages:
                        sickrage.srCore.srLogger.debug("Fixing subtitle codes for episode_id: %s, invalid code: %s" %
                                                       (sqlResult['episode_id'], subcode))
                        continue

                    langs.append(subcode)

                self.action(
                    "UPDATE tv_episodes SET subtitles = ?, subtitles_lastsearch = ? WHERE episode_id = ?;",
                    [','.join(langs), datetime.datetime.now().strftime(dateTimeFormat),
                     sqlResult['episode_id']])

        def fix_show_nfo_lang(self):
            self.action("UPDATE tv_shows SET lang = '' WHERE lang = 0 OR lang = '0'")

        def fix_missing_tables(self):
            if self.checkDBVersion() == MAX_DB_VERSION:
                if not self.hasTable('tmdb_info'):
                    sickrage.srCore.srLogger.info("Missing tmdb_info table detected!, fixing...")
                    MainDB.AddTmdbInfo().execute()

    class InitialSchema(SchemaUpgrade):

        def __init__(self, filename='sickrage.db', suffix=None, row_type=None):
            super(MainDB.InitialSchema, self).__init__(filename, suffix, row_type)

        def test(self):
            return self.hasTable("db_version")

        def execute(self, **kwargs):
            if not self.hasTable("tv_shows") and not self.hasTable("db_version"):
                queries = [
                    "CREATE TABLE db_version(db_version INTEGER);",
                    "CREATE TABLE history(action NUMERIC, date NUMERIC, showid NUMERIC, season NUMERIC, episode NUMERIC, quality NUMERIC, resource TEXT, provider TEXT, version NUMERIC DEFAULT -1);",
                    "CREATE TABLE imdb_info(indexer_id INTEGER PRIMARY KEY, imdb_id TEXT, title TEXT, year NUMERIC, akas TEXT, runtimes NUMERIC, genres TEXT, countries TEXT, country_codes TEXT, certificates TEXT, rating TEXT, votes INTEGER, last_update NUMERIC);",
                    "CREATE TABLE tmdb_info(indexer_id INTEGER PRIMARY KEY, tmdb_id TEXT, name TEXT, first_air_date NUMERIC, akas TEXT, episode_run_time NUMERIC, genres TEXT, origin_country TEXT, languages TEXT, production_companies TEXT, popularity TEXT, vote_count INTEGER, last_air_date NUMERIC);",
                    "CREATE TABLE info(last_backlog NUMERIC, last_indexer NUMERIC, last_proper_search NUMERIC);",
                    "CREATE TABLE scene_numbering(indexer TEXT, indexer_id INTEGER, season INTEGER, episode INTEGER, scene_season INTEGER, scene_episode INTEGER, absolute_number NUMERIC, scene_absolute_number NUMERIC, PRIMARY KEY(indexer_id, season, episode));",
                    "CREATE TABLE tv_shows(show_id INTEGER PRIMARY KEY, indexer_id NUMERIC, indexer NUMERIC, show_name TEXT, location TEXT, network TEXT, genre TEXT, classification TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, air_by_date NUMERIC, lang TEXT, subtitles NUMERIC, notify_list TEXT, imdb_id TEXT, tmdb_id TEXT, last_update_indexer NUMERIC, dvdorder NUMERIC, archive_firstmatch NUMERIC, rls_require_words TEXT, rls_ignore_words TEXT, sports NUMERIC, anime NUMERIC, scene NUMERIC, default_ep_status NUMERIC DEFAULT -1);",
                    "CREATE TABLE tv_episodes(episode_id INTEGER PRIMARY KEY, showid NUMERIC, indexerid NUMERIC, indexer TEXT, name TEXT, season NUMERIC, episode NUMERIC, description TEXT, airdate NUMERIC, hasnfo NUMERIC, hastbn NUMERIC, status NUMERIC, location TEXT, file_size NUMERIC, release_name TEXT, subtitles TEXT, subtitles_searchcount NUMERIC, subtitles_lastsearch TIMESTAMP, is_proper NUMERIC, scene_season NUMERIC, scene_episode NUMERIC, absolute_number NUMERIC, scene_absolute_number NUMERIC, version NUMERIC DEFAULT -1, release_group TEXT);",
                    "CREATE TABLE blacklist(show_id INTEGER, range TEXT, keyword TEXT);",
                    "CREATE TABLE whitelist(show_id INTEGER, range TEXT, keyword TEXT);",
                    "CREATE TABLE xem_refresh(indexer TEXT, indexer_id INTEGER PRIMARY KEY, last_refreshed INTEGER);",
                    "CREATE TABLE indexer_mapping(indexer_id INTEGER, indexer NUMERIC, mindexer_id INTEGER, mindexer NUMERIC, PRIMARY KEY (indexer_id, indexer));",
                    "CREATE UNIQUE INDEX idx_indexer_id ON tv_shows(indexer_id);",
                    "CREATE INDEX idx_showid ON tv_episodes(showid);",
                    "CREATE INDEX idx_sta_epi_air ON tv_episodes(status, episode, airdate);",
                    "CREATE INDEX idx_sta_epi_sta_air ON tv_episodes(season, episode, status, airdate);",
                    "CREATE INDEX idx_status ON tv_episodes(status,season,episode,airdate);",
                    "CREATE INDEX idx_tv_episodes_showid_airdate ON tv_episodes(showid, airdate);",
                    "INSERT INTO db_version(db_version) VALUES (43);"
                ]
                for query in queries:
                    self.action(query)

            else:
                cur_db_version = self.checkDBVersion()

                if cur_db_version < MIN_DB_VERSION:
                    sickrage.srCore.srLogger.log_error_and_exit("Your database version (" +
                                                                str(
                                                                    cur_db_version) + ") is too old to migrate from what this version of SiCKRAGE supports (" +
                                                                str(
                                                                    MIN_DB_VERSION) + ").\n" + "Remove database file to begin fresh."
                                                                )

                if cur_db_version > MAX_DB_VERSION:
                    sickrage.srCore.srLogger.log_error_and_exit("Your database version (" +
                                                                str(
                                                                    cur_db_version) + ") has been incremented past what this version of SiCKRAGE supports (" +
                                                                str(MAX_DB_VERSION) + ").\n" +
                                                                "If you have used other forks of SiCKRAGE, your database may be unusable due to their modifications."
                                                                )

    class AddSizeAndSceneNameFields(InitialSchema):
        def test(self):
            return self.checkDBVersion() >= 10

        def execute(self, **kwargs):
            from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException

            self.backup(10)

            if not self.hasColumn("tv_episodes", "file_size"):
                self.addColumn("tv_episodes", "file_size")

            if not self.hasColumn("tv_episodes", "release_name"):
                self.addColumn("tv_episodes", "release_name", "TEXT", "")

            ep_results = self.select("SELECT episode_id, location, file_size FROM tv_episodes")

            sickrage.srCore.srLogger.info("Adding file size to all episodes in DB, please be patient")
            for cur_ep in ep_results:
                if not cur_ep["location"]:
                    continue

                # if there is no size yet then populate it for us
                if (not cur_ep["file_size"] or not int(cur_ep["file_size"])) and os.path.isfile(cur_ep["location"]):
                    cur_size = os.path.getsize(cur_ep["location"])
                    self.action("UPDATE tv_episodes SET file_size = ? WHERE episode_id = ?",
                                [cur_size, int(cur_ep["episode_id"])])

            # check each snatch to see if we can use it to get a release name from
            history_results = self.select("SELECT * FROM history WHERE provider != -1 ORDER BY date ASC")

            sickrage.srCore.srLogger.info("Adding release name to all episodes still in history")
            for cur_result in history_results:
                # find the associated download, if there isn't one then ignore it
                download_results = self.select(
                    "SELECT resource FROM history WHERE provider = -1 AND showid = ? AND season = ? AND episode = ? AND date > ?",
                    [cur_result["showid"], cur_result["season"], cur_result["episode"], cur_result["date"]])
                if not download_results:
                    sickrage.srCore.srLogger.debug("Found a snatch in the history for " + cur_result[
                        "resource"] + " but couldn't find the associated download, skipping it")
                    continue

                nzb_name = cur_result["resource"]
                file_name = os.path.basename(download_results[0]["resource"])

                # take the extension off the filename, it's not needed
                if '.' in file_name:
                    file_name = file_name.rpartition('.')[0]

                # find the associated episode on disk
                ep_results = self.select(
                    "SELECT episode_id, status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? AND location != ''",
                    [cur_result["showid"], cur_result["season"], cur_result["episode"]])
                if not ep_results:
                    sickrage.srCore.srLogger.debug(
                        "The episode " + nzb_name + " was found in history but doesn't exist on disk anymore, skipping")
                    continue

                # get the status/quality of the existing ep and make sure it's what we expect
                ep_status, ep_quality = Quality.splitCompositeStatus(int(ep_results[0]["status"]))
                if ep_status != DOWNLOADED:
                    continue

                if ep_quality != int(cur_result["quality"]):
                    continue

                # make sure this is actually a real release name and not a season pack or something
                for cur_name in (nzb_name, file_name):
                    sickrage.srCore.srLogger.debug("Checking if " + cur_name + " is actually a good release name")
                    try:
                        np = NameParser(False)
                        parse_result = np.parse(cur_name)
                    except (InvalidNameException, InvalidShowException):
                        continue

                    if parse_result.series_name and parse_result.season_number is not None and parse_result.episode_numbers and parse_result.release_group:
                        # if all is well by this point we'll just put the release name into the database
                        self.action("UPDATE tv_episodes SET release_name = ? WHERE episode_id = ?",
                                    [cur_name, ep_results[0]["episode_id"]])
                        break

            # check each snatch to see if we can use it to get a release name from
            empty_results = self.select("SELECT episode_id, location FROM tv_episodes WHERE release_name = ''")

            sickrage.srCore.srLogger.info("Adding release name to all episodes with obvious scene filenames")
            for cur_result in empty_results:

                ep_file_name = os.path.basename(cur_result["location"])
                ep_file_name = os.path.splitext(ep_file_name)[0]

                # only want to find real scene names here so anything with a space in it is out
                if ' ' in ep_file_name:
                    continue

                try:
                    np = NameParser(False)
                    parse_result = np.parse(ep_file_name)
                except (InvalidNameException, InvalidShowException):
                    continue

                if not parse_result.release_group:
                    continue

                sickrage.srCore.srLogger.debug(
                    "Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid")
                self.action("UPDATE tv_episodes SET release_name = ? WHERE episode_id = ?",
                            [ep_file_name, cur_result["episode_id"]])

            self.incDBVersion(10)

    class RenameSeasonFolders(AddSizeAndSceneNameFields):
        def test(self):
            return self.checkDBVersion() >= 11

        def execute(self, **kwargs):
            # rename the column
            self.action("ALTER TABLE tv_shows RENAME TO tmp_tv_shows")
            self.action(
                "CREATE TABLE tv_shows (show_id INTEGER PRIMARY KEY, location TEXT, show_name TEXT, tvdb_id NUMERIC, network TEXT, genre TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, tvr_id NUMERIC, tvr_name TEXT, air_by_date NUMERIC, lang TEXT)")
            sql = "INSERT INTO tv_shows SELECT * FROM tmp_tv_shows"
            self.action(sql)

            # flip the values to be opposite of what they were before
            self.action("UPDATE tv_shows SET flatten_folders = 2 WHERE flatten_folders = 1")
            self.action("UPDATE tv_shows SET flatten_folders = 1 WHERE flatten_folders = 0")
            self.action("UPDATE tv_shows SET flatten_folders = 0 WHERE flatten_folders = 2")
            self.action("DROP TABLE tmp_tv_shows")

            self.incDBVersion(11)

    class Add1080pAndRawHdQualities(RenameSeasonFolders):
        """Add support for 1080p related qualities along with RawHD

        Quick overview of what the upgrade needs to do:

               quality   | old  | new
            --------------------------
            hdwebdl      | 1<<3 | 1<<5
            hdbluray     | 1<<4 | 1<<7
            fullhdbluray | 1<<5 | 1<<8
            --------------------------
            rawhdtv      |      | 1<<3
            fullhdtv     |      | 1<<4
            fullhdwebdl  |      | 1<<6
        """

        def test(self):
            return self.checkDBVersion() >= 12

        def _update_status(self, old_status):
            (status, quality) = Quality.splitCompositeStatus(old_status)
            return Quality.compositeStatus(status, self._update_quality(quality))

        def _update_quality(self, old_quality):
            """Update bitwise flags to reflect new quality values

            Check flag bits (clear old then set their new locations) starting
            with the highest bits so we dont overwrite data we need later on
            """

            result = old_quality
            # move fullhdbluray from 1<<5 to 1<<8 if set
            if result & (1 << 5):
                result &= ~(1 << 5)
                result |= 1 << 8
            # move hdbluray from 1<<4 to 1<<7 if set
            if result & (1 << 4):
                result &= ~(1 << 4)
                result |= 1 << 7
            # move hdwebdl from 1<<3 to 1<<5 if set
            if result & (1 << 3):
                result &= ~(1 << 3)
                result |= 1 << 5

            return result

        def _update_composite_qualities(self, status):
            """Unpack, Update, Return new quality values

            Unpack the composite archive/initial values.
            Update either qualities if needed.
            Then return the new compsite quality value.
            """

            best = (status & (0xffff << 16)) >> 16
            initial = status & 0xffff

            best = self._update_quality(best)
            initial = self._update_quality(initial)

            result = ((best << 16) | initial)
            return result

        def execute(self, **kwargs):
            self.backup(self.checkDBVersion())

            # update the default quality so we dont grab the wrong qualities after migration
            sickrage.srCore.srConfig.QUALITY_DEFAULT = self._update_composite_qualities(
                sickrage.srCore.srConfig.QUALITY_DEFAULT)

            sickrage.srCore.srConfig.save()

            # upgrade previous HD to HD720p -- shift previous qualities to new placevalues
            old_hd = Quality.combineQualities(
                [Quality.HDTV, Quality.HDWEBDL >> 2, Quality.HDBLURAY >> 3], [])
            new_hd = Quality.combineQualities([Quality.HDTV, Quality.HDWEBDL, Quality.HDBLURAY],
                                              [])

            # update ANY -- shift existing qualities and add new 1080p qualities, note that rawHD was not added to the ANY template
            old_any = Quality.combineQualities(
                [Quality.SDTV, Quality.SDDVD, Quality.HDTV, Quality.HDWEBDL >> 2,
                 Quality.HDBLURAY >> 3, Quality.UNKNOWN], [])
            new_any = Quality.combineQualities(
                [Quality.SDTV, Quality.SDDVD, Quality.HDTV, Quality.FULLHDTV,
                 Quality.HDWEBDL, Quality.FULLHDWEBDL, Quality.HDBLURAY,
                 Quality.FULLHDBLURAY,
                 Quality.UNKNOWN], [])

            # update qualities (including templates)
            cl = []
            sickrage.srCore.srLogger.info("[1/4] Updating pre-defined templates and the quality for each show...")
            shows = self.select("SELECT * FROM tv_shows")
            for cur_show in shows:
                if cur_show["quality"] == old_hd:
                    new_quality = new_hd
                elif cur_show["quality"] == old_any:
                    new_quality = new_any
                else:
                    new_quality = self._update_composite_qualities(cur_show["quality"])
                cl.append(["UPDATE tv_shows SET quality = ? WHERE show_id = ?", [new_quality, cur_show["show_id"]]])

            if len(cl) > 0:
                self.mass_action(cl)
                del cl  # cleanup

            # update status that are are within the old hdwebdl (1<<3 which is 8) and better -- exclude unknown (1<<15 which is 32768)
            cl = []
            sickrage.srCore.srLogger.info("[2/4] Updating the status for the episodes within each show...")
            episodes = self.select("SELECT * FROM tv_episodes WHERE status < 3276800 AND status >= 800")
            for cur_episode in episodes:
                cl.append(["UPDATE tv_episodes SET status = ? WHERE episode_id = ?",
                           [self._update_status(cur_episode["status"]), cur_episode["episode_id"]]])
            if len(cl) > 0:
                self.mass_action(cl)
                del cl  # cleanup

            # update previous history so it shows the correct action
            cl = []
            sickrage.srCore.srLogger.info("[3/4] Updating history to reflect the correct action...")
            historyAction = self.select("SELECT * FROM history WHERE action < 3276800 AND action >= 800")
            for cur_entry in historyAction:
                cl.append(["UPDATE history SET action = ? WHERE showid = ? AND date = ?",
                           [self._update_status(cur_entry["action"]), cur_entry["showid"], cur_entry["date"]]])
            if len(cl) > 0:
                self.mass_action(cl)
                del cl  # cleanup

            # update previous history so it shows the correct quality
            cl = []
            sickrage.srCore.srLogger.info("[4/4] Updating history to reflect the correct quality...")
            historyQuality = self.select("SELECT * FROM history WHERE quality < 32768 AND quality >= 8")
            for cur_entry in historyQuality:
                cl.append(["UPDATE history SET quality = ? WHERE showid = ? AND date = ?",
                           [self._update_quality(cur_entry["quality"]), cur_entry["showid"], cur_entry["date"]]])
            if len(cl) > 0:
                self.mass_action(cl)
                del cl  # cleanup

            self.incDBVersion(12)

            # cleanup and reduce db if any previous data was removed
            sickrage.srCore.srLogger.debug("Performing a vacuum on the database.")
            self.action("VACUUM")

    class AddShowidTvdbidIndex(Add1080pAndRawHdQualities):
        """ Adding index on tvdb_id (tv_shows) and showid (tv_episodes) to speed up searches/queries """

        def test(self):
            return self.checkDBVersion() >= 13

        def execute(self, **kwargs):
            self.backup(13)

            sickrage.srCore.srLogger.info("Check for duplicate shows before adding unique index.")
            MainDB().SanityCheck().fix_duplicate_shows('tvdb_id')

            sickrage.srCore.srLogger.info(
                "Adding index on tvdb_id (tv_shows) and showid (tv_episodes) to speed up searches/queries.")
            if not self.hasTable("idx_showid"):
                self.action("CREATE INDEX idx_showid ON tv_episodes (showid);")
            if not self.hasTable("idx_tvdb_id"):
                self.action("CREATE UNIQUE INDEX idx_tvdb_id ON tv_shows (tvdb_id);")

            self.incDBVersion(13)

    class AddLastUpdateTvdb(AddShowidTvdbidIndex):
        """ Adding column last_update_tvdb to tv_shows for controlling nightly updates """

        def test(self):
            return self.checkDBVersion() >= 14

        def execute(self, **kwargs):
            self.backup(14)

            sickrage.srCore.srLogger.info("Adding column last_update_tvdb to tvshows")
            if not self.hasColumn("tv_shows", "last_update_tvdb"):
                self.addColumn("tv_shows", "last_update_tvdb", default=1)

            self.incDBVersion(14)

    class AddDbIncreaseTo15(AddLastUpdateTvdb):
        def test(self):
            return self.checkDBVersion() >= 15

        def execute(self, **kwargs):
            self.incDBVersion(15)

    class AddImdbInfo(AddDbIncreaseTo15):
        def test(self):
            return self.checkDBVersion() >= 16

        def execute(self, **kwargs):
            self.action(
                "CREATE TABLE imdb_info (tvdb_id INTEGER PRIMARY KEY, imdb_id TEXT, title TEXT, year NUMERIC, akas TEXT, runtimes NUMERIC, genres TEXT, countries TEXT, country_codes TEXT, certificates TEXT, rating TEXT, votes INTEGER, last_update NUMERIC)")

            if not self.hasColumn("tv_shows", "imdb_id"):
                self.addColumn("tv_shows", "imdb_id")

            self.incDBVersion(16)

    class AddProperNamingSupport(AddImdbInfo):
        def test(self):
            return self.checkDBVersion() >= 17

        def execute(self, **kwargs):
            self.addColumn("tv_episodes", "is_proper")
            self.incDBVersion(17)

    class AddEmailSubscriptionTable(AddProperNamingSupport):
        def test(self):
            return self.checkDBVersion() >= 18

        def execute(self, **kwargs):
            self.addColumn('tv_shows', 'notify_list', 'TEXT', None)
            self.incDBVersion(18)

    class AddProperSearch(AddEmailSubscriptionTable):
        def test(self):
            return self.checkDBVersion() >= 19

        def execute(self, **kwargs):
            self.backup(19)

            sickrage.srCore.srLogger.info("Adding column last_proper_search to info")
            if not self.hasColumn("info", "last_proper_search"):
                self.addColumn("info", "last_proper_search", default=1)

            self.incDBVersion(19)

    class AddDvdOrderOption(AddProperSearch):
        def test(self):
            return self.checkDBVersion() >= 20

        def execute(self, **kwargs):
            sickrage.srCore.srLogger.info("Adding column dvdorder to tvshows")
            if not self.hasColumn("tv_shows", "dvdorder"):
                self.addColumn("tv_shows", "dvdorder", "NUMERIC", "0")

            self.incDBVersion(20)

    class AddSubtitlesSupport(AddDvdOrderOption):
        def test(self):
            return self.checkDBVersion() >= 21

        def execute(self, **kwargs):
            if not self.hasColumn("tv_shows", "subtitles"):
                self.addColumn("tv_shows", "subtitles")
                self.addColumn("tv_episodes", "subtitles", "TEXT", "")
                self.addColumn("tv_episodes", "subtitles_searchcount")
                self.addColumn("tv_episodes", "subtitles_lastsearch", "TIMESTAMP", str(datetime.datetime.min))
            self.incDBVersion(21)

    class ConvertTvShowsToIndexerScheme(AddSubtitlesSupport):
        def test(self):
            return self.checkDBVersion() >= 22

        def execute(self, **kwargs):
            self.backup(22)

            sickrage.srCore.srLogger.info("Converting TV Shows table to Indexer Scheme...")

            if self.hasTable("tmp_tv_shows"):
                sickrage.srCore.srLogger.info("Removing temp tv show tables left behind from previous updates...")
                self.action("DROP TABLE tmp_tv_shows")

            self.action("ALTER TABLE tv_shows RENAME TO tmp_tv_shows")
            self.action(
                "CREATE TABLE tv_shows (show_id INTEGER PRIMARY KEY, indexer_id NUMERIC, indexer NUMERIC, show_name TEXT, location TEXT, network TEXT, genre TEXT, classification TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, air_by_date NUMERIC, lang TEXT, subtitles NUMERIC, notify_list TEXT, imdb_id TEXT, tmdb_id TEXT, last_update_indexer NUMERIC, dvdorder NUMERIC)")
            self.action("INSERT INTO tv_shows SELECT * FROM tmp_tv_shows")
            self.action("DROP TABLE tmp_tv_shows")

            self.action("CREATE UNIQUE INDEX idx_indexer_id ON tv_shows (indexer_id);")

            self.action("UPDATE tv_shows SET classification = 'Scripted'")
            self.action("UPDATE tv_shows SET indexer = 1")

            self.incDBVersion(22)

    class ConvertTvEpisodesToIndexerScheme(ConvertTvShowsToIndexerScheme):
        def test(self):
            return self.checkDBVersion() >= 23

        def execute(self, **kwargs):
            self.backup(23)

            sickrage.srCore.srLogger.info("Converting TV Episodes table to Indexer Scheme...")

            if self.hasTable("tmp_tv_episodes"):
                sickrage.srCore.srLogger.info("Removing temp tv episode tables left behind from previous updates...")
                self.action("DROP TABLE tmp_tv_episodes")

            self.action("ALTER TABLE tv_episodes RENAME TO tmp_tv_episodes")
            self.action(
                "CREATE TABLE tv_episodes (episode_id INTEGER PRIMARY KEY, showid NUMERIC, indexerid NUMERIC, indexer NUMERIC, name TEXT, season NUMERIC, episode NUMERIC, description TEXT, airdate NUMERIC, hasnfo NUMERIC, hastbn NUMERIC, status NUMERIC, location TEXT, file_size NUMERIC, release_name TEXT, subtitles TEXT, subtitles_searchcount NUMERIC, subtitles_lastsearch TIMESTAMP, is_proper NUMERIC)")
            self.action(
                "INSERT INTO tv_episodes SELECT * FROM tmp_tv_episodes")
            self.action("DROP TABLE tmp_tv_episodes")

            self.action("CREATE INDEX idx_tv_episodes_showid_airdate ON tv_episodes(showid,airdate);")
            self.action("CREATE INDEX idx_showid ON tv_episodes (showid);")
            self.action("CREATE INDEX idx_status ON tv_episodes (status,season,episode,airdate)")
            self.action("CREATE INDEX idx_sta_epi_air ON tv_episodes (status,episode, airdate)")
            self.action("CREATE INDEX idx_sta_epi_sta_air ON tv_episodes (season,episode, status, airdate)")

            self.action("UPDATE tv_episodes SET indexer = 1")

            self.incDBVersion(23)

    class ConvertImdbInfoToIndexerScheme(ConvertTvEpisodesToIndexerScheme):
        def test(self):
            return self.checkDBVersion() >= 24

        def execute(self, **kwargs):
            self.backup(24)

            sickrage.srCore.srLogger.info("Converting IMDB Info table to Indexer Scheme...")

            if self.hasTable("tmp_imdb_info"):
                sickrage.srCore.srLogger.info("Removing temp imdb info tables left behind from previous updates...")
                self.action("DROP TABLE tmp_imdb_info")

            self.action("ALTER TABLE imdb_info RENAME TO tmp_imdb_info")
            self.action(
                "CREATE TABLE imdb_info (indexer_id INTEGER PRIMARY KEY, imdb_id TEXT, title TEXT, year NUMERIC, akas TEXT, runtimes NUMERIC, genres TEXT, countries TEXT, country_codes TEXT, certificates TEXT, rating TEXT, votes INTEGER, last_update NUMERIC)")
            self.action(
                "INSERT INTO imdb_info SELECT * FROM tmp_imdb_info")
            self.action("DROP TABLE tmp_imdb_info")

            self.incDBVersion(24)

    class ConvertInfoToIndexerScheme(ConvertImdbInfoToIndexerScheme):
        def test(self):
            return self.checkDBVersion() >= 25

        def execute(self, **kwargs):
            self.backup(25)

            sickrage.srCore.srLogger.info("Converting Info table to Indexer Scheme...")

            if self.hasTable("tmp_info"):
                sickrage.srCore.srLogger.info("Removing temp info tables left behind from previous updates...")
                self.action("DROP TABLE tmp_info")

            self.action("ALTER TABLE info RENAME TO tmp_info")
            self.action(
                "CREATE TABLE info (last_backlog NUMERIC, last_indexer NUMERIC, last_proper_search NUMERIC)")
            self.action(
                "INSERT INTO info SELECT * FROM tmp_info")
            self.action("DROP TABLE tmp_info")

            self.incDBVersion(25)

    class AddArchiveFirstMatchOption(ConvertInfoToIndexerScheme):
        def test(self):
            return self.checkDBVersion() >= 26

        def execute(self, **kwargs):
            self.backup(26)

            sickrage.srCore.srLogger.info("Adding column archive_firstmatch to tvshows")
            if not self.hasColumn("tv_shows", "archive_firstmatch"):
                self.addColumn("tv_shows", "archive_firstmatch", "NUMERIC", "0")

            self.incDBVersion(26)

    class AddSceneNumbering(AddArchiveFirstMatchOption):
        def test(self):
            return self.checkDBVersion() >= 27

        def execute(self, **kwargs):
            self.backup(27)

            if self.hasTable("scene_numbering"):
                self.action("DROP TABLE scene_numbering")

            self.action(
                "CREATE TABLE scene_numbering (indexer TEXT, indexer_id INTEGER, season INTEGER, episode INTEGER, scene_season INTEGER, scene_episode INTEGER, PRIMARY KEY (indexer_id, season, episode, scene_season, scene_episode))")

            self.incDBVersion(27)

    class ConvertIndexerToInteger(AddSceneNumbering):
        def test(self):
            return self.checkDBVersion() >= 28

        def execute(self, **kwargs):
            self.backup(28)

            sickrage.srCore.srLogger.info("Converting Indexer to Integer ...")

            self.mass_action([
                ["UPDATE tv_shows SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]],
                ["UPDATE tv_shows SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]],
                ["UPDATE tv_episodes SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]],
                ["UPDATE tv_episodes SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]],
                ["UPDATE scene_numbering SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]],
                ["UPDATE scene_numbering SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]]
            ])

            self.incDBVersion(28)

    class AddRequireAndIgnoreWords(ConvertIndexerToInteger):
        """ Adding column rls_require_words and rls_ignore_words to tv_shows """

        def test(self):
            return self.checkDBVersion() >= 29

        def execute(self, **kwargs):
            self.backup(29)

            sickrage.srCore.srLogger.info("Adding column rls_require_words to tvshows")
            if not self.hasColumn("tv_shows", "rls_require_words"):
                self.addColumn("tv_shows", "rls_require_words", "TEXT", "")

            sickrage.srCore.srLogger.info("Adding column rls_ignore_words to tvshows")
            if not self.hasColumn("tv_shows", "rls_ignore_words"):
                self.addColumn("tv_shows", "rls_ignore_words", "TEXT", "")

            self.incDBVersion(29)

    class AddSportsOption(AddRequireAndIgnoreWords):
        def test(self):
            return self.checkDBVersion() >= 30

        def execute(self, **kwargs):
            self.backup(30)

            sickrage.srCore.srLogger.info("Adding column sports to tvshows")
            if not self.hasColumn("tv_shows", "sports"):
                self.addColumn("tv_shows", "sports", "NUMERIC", "0")

            if self.hasColumn("tv_shows", "air_by_date") and self.hasColumn("tv_shows", "sports"):
                # update sports column
                cl = []
                sickrage.srCore.srLogger.info("[4/4] Updating tv_shows to reflect the correct sports value...")
                historyQuality = self.select(
                    "SELECT * FROM tv_shows WHERE LOWER(classification) = 'sports' AND air_by_date = 1 AND sports = 0")
                for cur_entry in historyQuality:
                    cl.append(["UPDATE tv_shows SET sports = ? WHERE show_id = ?",
                               [cur_entry["air_by_date"], cur_entry["show_id"]]])
                    cl.append(["UPDATE tv_shows SET air_by_date = 0 WHERE show_id = ?", [cur_entry["show_id"]]])

                if len(cl) > 0:
                    self.mass_action(cl)
                    del cl  # cleanup

            self.incDBVersion(30)

    class AddSceneNumberingToTvEpisodes(AddSportsOption):
        def test(self):
            return self.checkDBVersion() >= 31

        def execute(self, **kwargs):
            self.backup(31)

            sickrage.srCore.srLogger.info("Adding column scene_season and scene_episode to tvepisodes")
            self.addColumn("tv_episodes", "scene_season", "NUMERIC", "NULL")
            self.addColumn("tv_episodes", "scene_episode", "NUMERIC", "NULL")

            self.incDBVersion(31)

    class AddAnimeTvShow(AddSceneNumberingToTvEpisodes):
        def test(self):
            return self.checkDBVersion() >= 32

        def execute(self, **kwargs):
            self.backup(32)

            sickrage.srCore.srLogger.info("Adding column anime to tv_episodes")
            self.addColumn("tv_shows", "anime", "NUMERIC", "0")

            self.incDBVersion(32)

    class AddAbsoluteNumbering(AddAnimeTvShow):
        def test(self):
            return self.checkDBVersion() >= 33

        def execute(self, **kwargs):
            self.backup(33)

            sickrage.srCore.srLogger.info("Adding column absolute_number to tv_episodes")
            self.addColumn("tv_episodes", "absolute_number", "NUMERIC", "0")

            self.incDBVersion(33)

    class AddSceneAbsoluteNumbering(AddAbsoluteNumbering):
        def test(self):
            return self.checkDBVersion() >= 34

        def execute(self, **kwargs):
            self.backup(34)

            sickrage.srCore.srLogger.info("Adding column absolute_number and scene_absolute_number to scene_numbering")
            self.addColumn("scene_numbering", "absolute_number", "NUMERIC", "0")
            self.addColumn("scene_numbering", "scene_absolute_number", "NUMERIC", "0")

            self.incDBVersion(34)

    class AddAnimeBlacklistWhitelist(AddSceneAbsoluteNumbering):
        def test(self):
            return self.checkDBVersion() >= 35

        def execute(self, **kwargs):
            self.backup(35)

            self.mass_action([
                ["CREATE TABLE blacklist (show_id INTEGER, range TEXT, keyword TEXT)"],
                ["CREATE TABLE whitelist (show_id INTEGER, range TEXT, keyword TEXT)"]
            ])

            self.incDBVersion(35)

    class AddSceneAbsoluteNumbering2(AddAnimeBlacklistWhitelist):
        def test(self):
            return self.checkDBVersion() >= 36

        def execute(self, **kwargs):
            self.backup(36)

            sickrage.srCore.srLogger.info("Adding column scene_absolute_number to tv_episodes")
            self.addColumn("tv_episodes", "scene_absolute_number", "NUMERIC", "0")

            self.incDBVersion(36)

    class AddXemRefresh(AddSceneAbsoluteNumbering2):
        def test(self):
            return self.checkDBVersion() >= 37

        def execute(self, **kwargs):
            self.backup(37)

            sickrage.srCore.srLogger.info("Creating table xem_refresh")
            self.action(
                "CREATE TABLE xem_refresh (indexer TEXT, indexer_id INTEGER PRIMARY KEY, last_refreshed INTEGER)")

            self.incDBVersion(37)

    class AddSceneToTvShows(AddXemRefresh):
        def test(self):
            return self.checkDBVersion() >= 38

        def execute(self, **kwargs):
            self.backup(38)

            sickrage.srCore.srLogger.info("Adding column scene to tv_shows")
            self.addColumn("tv_shows", "scene", "NUMERIC", "0")

            self.incDBVersion(38)

    class AddIndexerMapping(AddSceneToTvShows):
        def test(self):
            return self.checkDBVersion() >= 39

        def execute(self, **kwargs):
            self.backup(39)

            if self.hasTable("indexer_mapping"):
                self.action("DROP TABLE indexer_mapping")

            sickrage.srCore.srLogger.info("Adding table indexer_mapping")
            self.action(
                "CREATE TABLE indexer_mapping (indexer_id INTEGER, indexer NUMERIC, mindexer_id INTEGER, mindexer NUMERIC, PRIMARY KEY (indexer_id, indexer))")

            self.incDBVersion(39)

    class AddVersionToTvEpisodes(AddIndexerMapping):
        def test(self):
            return self.checkDBVersion() >= 40

        def execute(self, **kwargs):
            self.backup(40)

            sickrage.srCore.srLogger.info("Adding column version to tv_episodes and history")
            self.addColumn("tv_episodes", "version", "NUMERIC", "-1")
            self.addColumn("tv_episodes", "release_group", "TEXT", "")
            self.addColumn("history", "version", "NUMERIC", "-1")

            self.incDBVersion(40)

    class AddDefaultEpStatusToTvShows(AddVersionToTvEpisodes):
        def test(self):
            return self.checkDBVersion() >= 41

        def execute(self, **kwargs):
            self.backup(41)

            sickrage.srCore.srLogger.info("Adding column default_ep_status to tv_shows")
            self.addColumn("tv_shows", "default_ep_status", "NUMERIC", "-1")

            self.incDBVersion(41)

    class AlterTvShowsFieldTypes(AddDefaultEpStatusToTvShows):
        def test(self):
            return self.checkDBVersion() >= 42

        def execute(self, **kwargs):
            self.backup(42)

            sickrage.srCore.srLogger.info("Converting column indexer and default_ep_status field types to numeric")
            self.action("ALTER TABLE tv_shows RENAME TO tmp_tv_shows")
            self.action(
                "CREATE TABLE tv_shows (show_id INTEGER PRIMARY KEY, indexer_id NUMERIC, indexer NUMERIC, show_name TEXT, location TEXT, network TEXT, genre TEXT, classification TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, air_by_date NUMERIC, lang TEXT, subtitles NUMERIC, notify_list TEXT, imdb_id TEXT, tmdb_id TEXT, last_update_indexer NUMERIC, dvdorder NUMERIC, archive_firstmatch NUMERIC, rls_require_words TEXT, rls_ignore_words TEXT, sports NUMERIC, anime NUMERIC, scene NUMERIC, default_ep_status NUMERIC)")
            self.action("INSERT INTO tv_shows SELECT * FROM tmp_tv_shows")
            self.action("DROP TABLE tmp_tv_shows")

            self.incDBVersion(42)

    class AddTmdbInfo(AlterTvShowsFieldTypes):
        def test(self):
            return self.checkDBVersion() >= 43

        def execute(self, **kwargs):
            self.backup(43)
            self.action(
                "CREATE TABLE tmdb_info (indexer_id INTEGER PRIMARY KEY, tmdb_id TEXT, name TEXT, first_air_date NUMERIC, akas TEXT, episode_run_time NUMERIC, genres TEXT, origin_country TEXT, languages TEXT, production_companies TEXT, popularity TEXT, vote_count INTEGER, last_air_date NUMERIC)")

            if not self.hasColumn("tv_shows", "tmdb_id"):
                self.addColumn("tv_shows", "tmdb_id")

            self.incDBVersion(43)
