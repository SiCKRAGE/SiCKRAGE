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
import re
from xml.etree.ElementTree import Element, ElementTree, SubElement

import sickrage
from sickrage.core.common import dateFormat
from sickrage.core.helpers import replace_extension, indent_xml
from sickrage.metadata_providers import MetadataProvider
from sickrage.series_providers.exceptions import SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound


class MediaBrowserMetadata(MetadataProvider):
    """
    Metadata generation class for Media Browser 2.x/3.x - Standard Mode.

    The following file structure is used:

    show_root/series.xml                       (show metadata)
    show_root/folder.jpg                       (poster)
    show_root/backdrop.jpg                     (fanart)
    show_root/Season ##/folder.jpg             (season thumb)
    show_root/Season ##/filename.ext           (*)
    show_root/Season ##/metadata/filename.xml  (episode metadata)
    show_root/Season ##/metadata/filename.jpg  (episode thumb)
    """

    def __init__(self,
                 show_metadata=False,
                 episode_metadata=False,
                 fanart=False,
                 poster=False,
                 banner=False,
                 episode_thumbnails=False,
                 season_posters=False,
                 season_banners=False,
                 season_all_poster=False,
                 season_all_banner=False):

        MetadataProvider.__init__(self,
                                  show_metadata,
                                  episode_metadata,
                                  fanart,
                                  poster,
                                  banner,
                                  episode_thumbnails,
                                  season_posters,
                                  season_banners,
                                  season_all_poster,
                                  season_all_banner)

        self.name = 'MediaBrowser'

        self._ep_nfo_extension = 'xml'
        self._show_metadata_filename = 'series.xml'

        self.fanart_name = "backdrop.jpg"
        self.poster_name = "folder.jpg"

        # web-ui metadata template
        self.eg_show_metadata = "series.xml"
        self.eg_episode_metadata = "Season##\\metadata\\<i>filename</i>.xml"
        self.eg_fanart = "backdrop.jpg"
        self.eg_poster = "folder.jpg"
        self.eg_banner = "banner.jpg"
        self.eg_episode_thumbnails = "Season##\\metadata\\<i>filename</i>.jpg"
        self.eg_season_posters = "Season##\\folder.jpg"
        self.eg_season_banners = "Season##\\banner.jpg"
        self.eg_season_all_poster = "<i>not supported</i>"
        self.eg_season_all_banner = "<i>not supported</i>"

    # Override with empty methods for unsupported features
    def retrieve_show_metadata(self, folder):
        # while show metadata is generated, it is not supported for our lookup
        return None, None, None

    def create_season_all_poster(self, show_obj, force=False):
        pass

    def create_season_all_banner(self, show_obj, force=False):
        pass

    def get_episode_file_path(self, ep_obj):
        """
        Returns a full show dir/metadata/episode.xml path for MediaBrowser
        episode metadata files

        ep_obj: a TVEpisode object to get the path for
        """

        if os.path.isfile(ep_obj.location):
            xml_file_name = replace_extension(os.path.basename(ep_obj.location), self._ep_nfo_extension)
            metadata_dir_name = os.path.join(os.path.dirname(ep_obj.location), 'metadata')
            xml_file_path = os.path.join(metadata_dir_name, xml_file_name)
        else:
            sickrage.app.log.debug("Episode location doesn't exist: " + str(ep_obj.location))
            return ''

        return xml_file_path

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns a full show dir/metadata/episode.jpg path for MediaBrowser
        episode thumbs.

        ep_obj: a TVEpisode object to get the path from
        """

        if os.path.isfile(ep_obj.location):
            tbn_file_name = replace_extension(os.path.basename(ep_obj.location), 'jpg')
            metadata_dir_name = os.path.join(os.path.dirname(ep_obj.location), 'metadata')
            tbn_file_path = os.path.join(metadata_dir_name, tbn_file_name)
        else:
            return None

        return tbn_file_path

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/folder.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in os.listdir(show_obj.location) if
                    os.path.isdir(os.path.join(show_obj.location, x))]

        season_dir_regex = r'^Season\s+(\d+)$'

        season_dir = None

        for cur_dir in dir_list:
            # MediaBrowser 1.x only supports 'Specials'
            # MediaBrowser 2.x looks to only support 'Season 0'
            # MediaBrowser 3.x looks to mimic KODI/Plex support
            if season == 0 and cur_dir == "Specials":
                season_dir = cur_dir
                break

            match = re.match(season_dir_regex, cur_dir, re.I)
            if not match:
                continue

            cur_season = int(match.group(1))

            if cur_season == season:
                season_dir = cur_dir
                break

        if not season_dir:
            sickrage.app.log.debug("Unable to find a season dir for season " + str(season))
            return None

        sickrage.app.log.debug(
            "Using " + str(season_dir) + "/folder.jpg as season dir for season " + str(season))

        return os.path.join(show_obj.location, season_dir, 'folder.jpg')

    @staticmethod
    def get_season_banner_path(show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/banner.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in os.listdir(show_obj.location) if
                    os.path.isdir(os.path.join(show_obj.location, x))]

        season_dir_regex = r'^Season\s+(\d+)$'

        season_dir = None

        for cur_dir in dir_list:
            # MediaBrowser 1.x only supports 'Specials'
            # MediaBrowser 2.x looks to only support 'Season 0'
            # MediaBrowser 3.x looks to mimic KODI/Plex support
            if season == 0 and cur_dir == "Specials":
                season_dir = cur_dir
                break

            match = re.match(season_dir_regex, cur_dir, re.I)
            if not match:
                continue

            cur_season = int(match.group(1))

            if cur_season == season:
                season_dir = cur_dir
                break

        if not season_dir:
            sickrage.app.log.debug("Unable to find a season dir for season " + str(season))
            return None

        sickrage.app.log.debug(
            "Using " + str(season_dir) + "/banner.jpg as season dir for season " + str(season))

        return os.path.join(show_obj.location, season_dir, 'banner.jpg')

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        tv_node = Element("Series")

        series_provider_language = show_obj.lang or sickrage.app.config.general.series_provider_default_language

        myShow = show_obj.series_provider.search(show_obj.series_id, language=series_provider_language)
        if not myShow:
            return False

        # check for title and id
        if not (getattr(myShow, 'seriesname', None) and getattr(myShow, 'id', None)):
            sickrage.app.log.info(
                "Incomplete info for show with id " + str(show_obj.series_id) + " on " + show_obj.series_provider.name + ", skipping it")
            return False

        if getattr(myShow, 'id', None):
            series_id = SubElement(tv_node, "id")
            series_id.text = str(myShow['id'])

        if getattr(myShow, 'seriesname', None):
            SeriesName = SubElement(tv_node, "SeriesName")
            SeriesName.text = myShow['seriesname']

        if getattr(myShow, 'status', None):
            Status = SubElement(tv_node, "Status")
            Status.text = myShow['status']

        if getattr(myShow, 'network', None):
            Network = SubElement(tv_node, "Network")
            Network.text = myShow['network']

        if getattr(myShow, 'airstime', None):
            Airs_Time = SubElement(tv_node, "Airs_Time")
            Airs_Time.text = myShow['airstime']

        if getattr(myShow, 'airsdayofweek', None):
            Airs_DayOfWeek = SubElement(tv_node, "Airs_DayOfWeek")
            Airs_DayOfWeek.text = myShow['airsdayofweek']

        FirstAired = SubElement(tv_node, "FirstAired")
        if getattr(myShow, 'firstaired', None):
            FirstAired.text = myShow['firstaired']

        if getattr(myShow, 'contentrating', None):
            ContentRating = SubElement(tv_node, "ContentRating")
            ContentRating.text = myShow['contentrating']

            MPAARating = SubElement(tv_node, "MPAARating")
            MPAARating.text = myShow['contentrating']

            certification = SubElement(tv_node, "certification")
            certification.text = myShow['contentrating']

        MetadataType = SubElement(tv_node, "Type")
        MetadataType.text = "Series"

        if getattr(myShow, 'overview', None):
            Overview = SubElement(tv_node, "Overview")
            Overview.text = myShow['overview']

        if getattr(myShow, 'firstaired', None):
            PremiereDate = SubElement(tv_node, "PremiereDate")
            PremiereDate.text = myShow['firstaired']

        if getattr(myShow, 'rating', None):
            Rating = SubElement(tv_node, "Rating")
            Rating.text = myShow['rating']

        if getattr(myShow, 'firstaired', None):
            try:
                year_text = str(datetime.datetime.strptime(myShow['firstaired'], dateFormat).year)
                if year_text:
                    ProductionYear = SubElement(tv_node, "ProductionYear")
                    ProductionYear.text = year_text
            except Exception:
                pass

        if getattr(myShow, 'runtime', None):
            RunningTime = SubElement(tv_node, "RunningTime")
            RunningTime.text = myShow['runtime']

            Runtime = SubElement(tv_node, "Runtime")
            Runtime.text = myShow['runtime']

        if getattr(myShow, 'imdbid', None):
            imdb_id = SubElement(tv_node, "IMDB_ID")
            imdb_id.text = myShow['imdbid']

            imdb_id = SubElement(tv_node, "IMDB")
            imdb_id.text = myShow['imdbid']

            imdb_id = SubElement(tv_node, "IMDbId")
            imdb_id.text = myShow['imdbid']

        if getattr(myShow, 'zap2itid', None):
            Zap2ItId = SubElement(tv_node, "Zap2ItId")
            Zap2ItId.text = myShow['zap2itid']

        if getattr(myShow, 'genre', None) and isinstance(myShow["genre"], str):
            Genres = SubElement(tv_node, "Genres")
            for genre in myShow['genre'].split('|'):
                if genre.strip():
                    cur_genre = SubElement(Genres, "Genre")
                    cur_genre.text = genre.strip()

            Genre = SubElement(tv_node, "Genre")
            Genre.text = "|".join([x.strip() for x in myShow["genre"].split('|') if x.strip()])

        if getattr(myShow, 'network', None):
            Studios = SubElement(tv_node, "Studios")
            Studio = SubElement(Studios, "Studio")
            Studio.text = myShow['network']

            Persons = SubElement(tv_node, "Persons")
            for actor in show_obj.series_provider.actors(show_obj.series_id):
                if not ('name' in actor and actor['name'].strip()):
                    continue

                cur_actor = SubElement(Persons, "Person")

                cur_actor_name = SubElement(cur_actor, "Name")
                cur_actor_name.text = actor['name'].strip()

                cur_actor_type = SubElement(cur_actor, "Type")
                cur_actor_type.text = "Actor"

                if 'role' in actor and actor['role'].strip():
                    cur_actor_role = SubElement(cur_actor, "Role")
                    cur_actor_role.text = actor['role'].strip()

        indent_xml(tv_node)

        data = ElementTree(tv_node)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.related_episodes

        persons_dict = {
            'Director': [],
            'GuestStar': [],
            'Writer': []
        }

        series_provider_language = ep_obj.show.lang or sickrage.app.config.general.series_provider_default_language

        myShow = ep_obj.show.series_provider.search(ep_obj.show.series_id, language=series_provider_language)
        if not myShow:
            return False

        rootNode = Element("Item")

        # write an MediaBrowser XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound):
                sickrage.app.log.info(
                    f"Unable to find episode {curEpToWrite.season:d}x{curEpToWrite.episode:d} on {ep_obj.show.series_provider.name}... has it been removed? Should I delete from db?")
                return None

            if curEpToWrite == ep_obj:
                # root (or single) episode

                # default to today's date for specials if firstaired is not set
                if ep_obj.season == 0 and not getattr(myEp, 'firstaired', None):
                    myEp['firstaired'] = str(datetime.date.min)

                if not (getattr(myEp, 'episodename', None) and getattr(myEp, 'firstaired', None)):
                    return None

                episode = rootNode

                if curEpToWrite.name:
                    EpisodeName = SubElement(episode, "EpisodeName")
                    EpisodeName.text = curEpToWrite.name

                EpisodeNumber = SubElement(episode, "EpisodeNumber")
                EpisodeNumber.text = str(ep_obj.episode)

                if ep_obj.related_episodes:
                    EpisodeNumberEnd = SubElement(episode, "EpisodeNumberEnd")
                    EpisodeNumberEnd.text = str(curEpToWrite.episode)

                SeasonNumber = SubElement(episode, "SeasonNumber")
                SeasonNumber.text = str(curEpToWrite.season)

                if not ep_obj.related_episodes and getattr(myEp, 'absolute_number', None):
                    absolute_number = SubElement(episode, "absolute_number")
                    absolute_number.text = str(myEp['absolute_number'])

                if curEpToWrite.airdate > datetime.date.min:
                    FirstAired = SubElement(episode, "FirstAired")
                    FirstAired.text = str(curEpToWrite.airdate)

                MetadataType = SubElement(episode, "Type")
                MetadataType.text = "Episode"

                if curEpToWrite.description:
                    Overview = SubElement(episode, "Overview")
                    Overview.text = curEpToWrite.description

                if not ep_obj.related_episodes:
                    if getattr(myEp, 'rating', None):
                        Rating = SubElement(episode, "Rating")
                        Rating.text = myEp['rating']

                    if getattr(myShow, 'imdb_id', None):
                        IMDB_ID = SubElement(episode, "IMDB_ID")
                        IMDB_ID.text = myShow['imdb_id']

                        IMDB = SubElement(episode, "IMDB")
                        IMDB.text = myShow['imdb_id']

                        IMDbId = SubElement(episode, "IMDbId")
                        IMDbId.text = myShow['imdb_id']

                series_id = SubElement(episode, "id")
                series_id.text = str(curEpToWrite.series_id)

                # fill in Persons section with collected directors, guest starts and writers
                Persons = SubElement(episode, "Persons")
                for person_type, names in persons_dict.items():
                    # remove doubles
                    names = list(set(names))
                    for cur_name in names:
                        Person = SubElement(Persons, "Person")
                        cur_person_name = SubElement(Person, "Name")
                        cur_person_name.text = cur_name
                        cur_person_type = SubElement(Person, "Type")
                        cur_person_type.text = person_type

                for actor in ep_obj.show.series_provider.actors(int(ep_obj.show.series_id)):
                    if not ('name' in actor and actor['name'].strip()):
                        continue

                    cur_actor = SubElement(Persons, "Person")

                    cur_actor_name = SubElement(cur_actor, "Name")
                    cur_actor_name.text = actor['name'].strip()

                    cur_actor_type = SubElement(cur_actor, "Type")
                    cur_actor_type.text = "Actor"

                    if 'role' in actor and actor['role'].strip():
                        cur_actor_role = SubElement(cur_actor, "Role")
                        cur_actor_role.text = actor['role'].strip()

                Language = SubElement(episode, "Language")
                try:
                    Language.text = myEp['language']['overview']
                except Exception:
                    Language.text = sickrage.app.config.general.series_provider_default_language

                thumb = SubElement(episode, "filename")
                # TODO: See what this is needed for.. if its still needed
                # just write this to the NFO regardless of whether it actually exists or not
                # note: renaming files after nfo generation will break this, tough luck
                thumb_text = self.get_episode_thumb_path(ep_obj)
                if thumb_text:
                    thumb.text = thumb_text

            else:
                # append data from (if any) related episodes
                EpisodeNumberEnd.text = str(curEpToWrite.episode)

                if curEpToWrite.name:
                    if not EpisodeName.text:
                        EpisodeName.text = curEpToWrite.name
                    else:
                        EpisodeName.text = ', '.join([EpisodeName.text, curEpToWrite.name])

                if curEpToWrite.description:
                    if not Overview.text:
                        Overview.text = curEpToWrite.description
                    else:
                        Overview.text = '\r'.join([Overview.text, curEpToWrite.description])

            # collect all directors, guest stars and writers
            if getattr(myEp, 'director', None):
                persons_dict['Director'] += [x.strip() for x in myEp['director'].split('|') if x.strip()]
            if getattr(myEp, 'gueststars', None):
                persons_dict['GuestStar'] += [x.strip() for x in myEp['gueststars'].split('|') if x.strip()]
            if getattr(myEp, 'writer', None):
                persons_dict['Writer'] += [x.strip() for x in myEp['writer'].split('|') if x.strip()]

        indent_xml(rootNode)
        data = ElementTree(rootNode)

        return data
