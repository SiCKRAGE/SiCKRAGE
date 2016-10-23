# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
from xml.etree.ElementTree import Element, ElementTree, SubElement

import sickrage
from sickrage.core.common import dateFormat
from sickrage.core.exceptions import ShowNotFoundException
from sickrage.core.helpers import replaceExtension, indentXML
from sickrage.indexers import srIndexerApi
from sickrage.indexers.exceptions import indexer_episodenotfound, \
    indexer_error, indexer_seasonnotfound, indexer_shownotfound
from sickrage.metadata import GenericMetadata


class WDTVMetadata(GenericMetadata):
    """
    Metadata generation class for WDTV

    The following file structure is used:

    show_root/folder.jpg                    (poster)
    show_root/Season ##/folder.jpg          (season thumb)
    show_root/Season ##/filename.ext        (*)
    show_root/Season ##/filename.metathumb  (episode thumb)
    show_root/Season ##/filename.xml        (episode metadata)
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

        GenericMetadata.__init__(self,
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

        self.name = 'WDTV'

        self._ep_nfo_extension = 'xml'

        self.poster_name = "folder.jpg"

        # web-ui metadata template
        self.eg_show_metadata = "<i>not supported</i>"
        self.eg_episode_metadata = "Season##\\<i>filename</i>.xml"
        self.eg_fanart = "<i>not supported</i>"
        self.eg_poster = "folder.jpg"
        self.eg_banner = "<i>not supported</i>"
        self.eg_episode_thumbnails = "Season##\\<i>filename</i>.metathumb"
        self.eg_season_posters = "Season##\\folder.jpg"
        self.eg_season_banners = "<i>not supported</i>"
        self.eg_season_all_poster = "<i>not supported</i>"
        self.eg_season_all_banner = "<i>not supported</i>"

    # Override with empty methods for unsupported features
    def retrieveShowMetadata(self, folder):
        # no show metadata generated, we abort this lookup function
        return None, None, None

    def create_show_metadata(self, show_obj):
        pass

    def update_show_indexer_metadata(self, show_obj):
        pass

    def get_show_file_path(self, show_obj):
        pass

    def create_fanart(self, show_obj):
        pass

    def create_banner(self, show_obj):
        pass

    def create_season_banners(self, show_obj):
        pass

    def create_season_all_poster(self, show_obj):
        pass

    def create_season_all_banner(self, show_obj):
        pass

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns the path where the episode thumbnail should be stored. Defaults to
        the same path as the episode file but with a .metathumb extension.

        ep_obj: a TVEpisode instance for which to create the thumbnail
        """
        if os.path.isfile(ep_obj.location):
            tbn_filename = replaceExtension(ep_obj.location, 'metathumb')
        else:
            return None

        return tbn_filename

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Season thumbs for WDTV go in Show Dir/Season X/folder.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in os.listdir(show_obj.location) if
                    os.path.isdir(os.path.join(show_obj.location, x))]

        season_dir_regex = r'^Season\s+(\d+)$'

        season_dir = None

        for cur_dir in dir_list:
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
            sickrage.srCore.srLogger.debug("Unable to find a season dir for season " + str(season))
            return None

        sickrage.srCore.srLogger.debug("Using " + str(season_dir) + "/folder.jpg as season dir for season " + str(season))

        return os.path.join(show_obj.location, season_dir, 'folder.jpg')

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a WDTV style episode.xml
        and returns the resulting data object.

        ep_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        indexer_lang = ep_obj.show.lang

        try:
            lINDEXER_API_PARMS = srIndexerApi(ep_obj.show.indexer).api_params.copy()

            lINDEXER_API_PARMS['actors'] = True

            if indexer_lang and not indexer_lang == sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE:
                lINDEXER_API_PARMS['language'] = indexer_lang

            if ep_obj.show.dvdorder != 0:
                lINDEXER_API_PARMS['dvdorder'] = True

            t = srIndexerApi(ep_obj.show.indexer).indexer(**lINDEXER_API_PARMS)
            myShow = t[ep_obj.show.indexerid]
        except indexer_shownotfound as e:
            raise ShowNotFoundException(e.message)
        except indexer_error as e:
            sickrage.srCore.srLogger.error("Unable to connect to " + srIndexerApi(
                ep_obj.show.indexer).name + " while creating meta files - skipping - {}".format(e.message))
            return False

        rootNode = Element("details")

        # write an WDTV XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (indexer_episodenotfound, indexer_seasonnotfound):
                sickrage.srCore.srLogger.info(
                    "Unable to find episode %dx%d on %s... has it been removed? Should I delete from db?" %
                    (curEpToWrite.season, curEpToWrite.episode, srIndexerApi(ep_obj.show.indexer).name))
                return None

            if ep_obj.season == 0 and not getattr(myEp, 'firstaired', None):
                myEp["firstaired"] = str(datetime.date.fromordinal(1))

            if not (getattr(myEp, 'episodename', None) and getattr(myEp, 'firstaired', None)):
                return None

            if len(eps_to_write) > 1:
                episode = SubElement(rootNode, "details")
            else:
                episode = rootNode

            # TODO: get right EpisodeID
            episodeID = SubElement(episode, "id")
            episodeID.text = str(curEpToWrite.indexerid)

            title = SubElement(episode, "title")
            title.text = ep_obj.prettyName()

            if getattr(myShow, 'seriesname', None):
                seriesName = SubElement(episode, "series_name")
                seriesName.text = myShow["seriesname"]

            if curEpToWrite.name:
                episodeName = SubElement(episode, "episode_name")
                episodeName.text = curEpToWrite.name

            seasonNumber = SubElement(episode, "season_number")
            seasonNumber.text = str(curEpToWrite.season)

            episodeNum = SubElement(episode, "episode_number")
            episodeNum.text = str(curEpToWrite.episode)

            firstAired = SubElement(episode, "firstaired")

            if curEpToWrite.airdate != datetime.date.fromordinal(1):
                firstAired.text = str(curEpToWrite.airdate)

            if getattr(myShow, 'firstaired', None):
                try:
                    year_text = str(datetime.datetime.strptime(myShow["firstaired"], dateFormat).year)
                    if year_text:
                        year = SubElement(episode, "year")
                        year.text = year_text
                except Exception:
                    pass

            if curEpToWrite.season != 0 and getattr(myShow, 'runtime', None):
                runtime = SubElement(episode, "runtime")
                runtime.text = myShow["runtime"]

            if getattr(myShow, 'genre', None):
                genre = SubElement(episode, "genre")
                genre.text = " / ".join([x.strip() for x in myShow["genre"].split('|') if x.strip()])

            if getattr(myEp, 'director', None):
                director = SubElement(episode, "director")
                director.text = myEp['director']

            if getattr(myShow, '_actors', None):
                for actor in myShow['_actors']:
                    if not ('name' in actor and actor['name'].strip()):
                        continue

                    cur_actor = SubElement(episode, "actor")

                    cur_actor_name = SubElement(cur_actor, "name")
                    cur_actor_name.text = actor['name']

                    if 'role' in actor and actor['role'].strip():
                        cur_actor_role = SubElement(cur_actor, "role")
                        cur_actor_role.text = actor['role'].strip()

            if curEpToWrite.description:
                overview = SubElement(episode, "overview")
                overview.text = curEpToWrite.description

        # Make it purdy
        indentXML(rootNode)
        data = ElementTree(rootNode)
        return data


# present a standard "interface" from the module
metadata_class = WDTVMetadata
