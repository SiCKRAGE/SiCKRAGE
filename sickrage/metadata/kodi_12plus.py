# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.



import datetime
from xml.etree.ElementTree import Element, ElementTree, SubElement

import sickrage
from sickrage.core.common import dateFormat
from sickrage.core.helpers import indent_xml
from sickrage.indexers import IndexerApi
from sickrage.indexers.exceptions import indexer_episodenotfound, \
    indexer_seasonnotfound
from sickrage.metadata import GenericMetadata


class KODI_12PlusMetadata(GenericMetadata):
    """
    Metadata generation class for KODI 12+.

    The following file structure is used:

    show_root/tvshow.nfo                    (show metadata)
    show_root/fanart.jpg                    (fanart)
    show_root/poster.jpg                    (poster)
    show_root/banner.jpg                    (banner)
    show_root/Season ##/filename.ext        (*)
    show_root/Season ##/filename.nfo        (episode metadata)
    show_root/Season ##/filename-thumb.jpg  (episode thumb)
    show_root/season##-poster.jpg           (season posters)
    show_root/season##-banner.jpg           (season banners)
    show_root/season-all-poster.jpg         (season all poster)
    show_root/season-all-banner.jpg         (season all banner)
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

        self.name = 'KODI 12+'

        self.poster_name = "poster.jpg"
        self.season_all_poster_name = "season-all-poster.jpg"

        # web-ui metadata template
        self.eg_show_metadata = "tvshow.nfo"
        self.eg_episode_metadata = "Season##\\<i>filename</i>.nfo"
        self.eg_fanart = "fanart.jpg"
        self.eg_poster = "poster.jpg"
        self.eg_banner = "banner.jpg"
        self.eg_episode_thumbnails = "Season##\\<i>filename</i>-thumb.jpg"
        self.eg_season_posters = "season##-poster.jpg"
        self.eg_season_banners = "season##-banner.jpg"
        self.eg_season_all_poster = "season-all-poster.jpg"
        self.eg_season_all_banner = "season-all-banner.jpg"

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for an KODI-style tvshow.nfo and
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        tv_node = Element("tvshow")

        show_ID = show_obj.indexer_id

        indexer_lang = show_obj.lang or sickrage.app.config.indexer_default_language

        lINDEXER_API_PARMS = IndexerApi(show_obj.indexer).api_params.copy()
        lINDEXER_API_PARMS['language'] = indexer_lang

        if show_obj.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = IndexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)
        indexer_data = t[int(show_ID)]
        if not indexer_data:
            return False

        # check for title and id
        if not (getattr(indexer_data, 'seriesname', None) and getattr(indexer_data, 'id', None)):
            sickrage.app.log.info("Incomplete info for show with id " + str(show_ID) + " on " + IndexerApi(show_obj.indexer).name + ", skipping it")
            return False

        title = SubElement(tv_node, "title")
        title.text = indexer_data["seriesname"]

        if getattr(indexer_data, 'rating', None):
            rating = SubElement(tv_node, "rating")
            rating.text = indexer_data["rating"]

        if getattr(indexer_data, 'firstaired', None):
            try:
                year_text = str(datetime.datetime.strptime(indexer_data["firstaired"], dateFormat).year)
                if year_text:
                    year = SubElement(tv_node, "year")
                    year.text = year_text
            except Exception:
                pass

        if getattr(indexer_data, 'overview', None):
            plot = SubElement(tv_node, "plot")
            plot.text = indexer_data["overview"]

        # if getattr(indexer_data, 'id', None):
        #    episodeguide = SubElement(tv_node, "episodeguide")
        #    episodeguideurl = SubElement(episodeguide, "url")
        #    episodeguideurl.text = IndexerApi(show_obj.indexer).config['base_url'] + str(
        #        indexer_data["id"]) + '/all/en.zip'

        if getattr(indexer_data, 'contentrating', None):
            mpaa = SubElement(tv_node, "mpaa")
            mpaa.text = indexer_data["contentrating"]

        if getattr(indexer_data, 'id', None):
            indexer_id = SubElement(tv_node, "id")
            indexer_id.text = str(indexer_data["id"])

        if getattr(indexer_data, 'genre', None) and isinstance(indexer_data["genre"], str):
            genre = SubElement(tv_node, "genre")
            genre.text = " / ".join(x.strip() for x in indexer_data["genre"].split('|') if x.strip())

        if getattr(indexer_data, 'firstaired', None):
            premiered = SubElement(tv_node, "premiered")
            premiered.text = indexer_data["firstaired"]

        if getattr(indexer_data, 'network', None):
            studio = SubElement(tv_node, "studio")
            studio.text = indexer_data["network"].strip()

        for actor in t.actors(int(show_ID)):
            cur_actor = SubElement(tv_node, "actor")

            if 'name' in actor and actor['name'].strip():
                cur_actor_name = SubElement(cur_actor, "name")
                cur_actor_name.text = actor['name'].strip()
            else:
                continue

            if 'role' in actor and actor['role'].strip():
                cur_actor_role = SubElement(cur_actor, "role")
                cur_actor_role.text = actor['role'].strip()

            if 'image' in actor and actor['image'].strip():
                cur_actor_thumb = SubElement(cur_actor, "thumb")
                cur_actor_thumb.text = actor['image'].strip()

        # Make it purdy
        indent_xml(tv_node)

        data = ElementTree(tv_node)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for an KODI-style episode.nfo and
        returns the resulting data object.
            show_obj: a TVEpisode instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.related_episodes

        indexer_lang = ep_obj.show.lang or sickrage.app.config.indexer_default_language

        lINDEXER_API_PARMS = IndexerApi(ep_obj.show.indexer).api_params.copy()
        lINDEXER_API_PARMS['language'] = indexer_lang

        if ep_obj.show.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = IndexerApi(ep_obj.show.indexer).indexer(**lINDEXER_API_PARMS)
        indexer_data = t[ep_obj.show.indexer_id]
        if not indexer_data:
            return False

        if len(eps_to_write) > 1:
            rootNode = Element("kodimultiepisode")
        else:
            rootNode = Element("episodedetails")

        # write an NFO containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = indexer_data[curEpToWrite.season][curEpToWrite.episode]
            except (indexer_episodenotfound, indexer_seasonnotfound):
                sickrage.app.log.info(
                    "Unable to find episode %dx%d on %s... has it been removed? Should I delete from db?" %
                    (curEpToWrite.season, curEpToWrite.episode, IndexerApi(ep_obj.show.indexer).name))
                return None

            if not getattr(myEp, 'firstaired', None):
                myEp["firstaired"] = str(datetime.date.min)

            if not getattr(myEp, 'episodename', None):
                sickrage.app.log.debug("Not generating nfo because the ep has no title")
                return None

            sickrage.app.log.debug(
                "Creating metadata for episode " + str(ep_obj.season) + "x" + str(ep_obj.episode))

            if len(eps_to_write) > 1:
                episode = SubElement(rootNode, "episodedetails")
            else:
                episode = rootNode

            if getattr(myEp, 'episodename', None):
                title = SubElement(episode, "title")
                title.text = myEp['episodename']

            if getattr(indexer_data, 'seriesname', None):
                showtitle = SubElement(episode, "showtitle")
                showtitle.text = indexer_data['seriesname']

            season = SubElement(episode, "season")
            season.text = str(curEpToWrite.season)

            episodenum = SubElement(episode, "episode")
            episodenum.text = str(curEpToWrite.episode)

            uniqueid = SubElement(episode, "uniqueid")
            uniqueid.text = str(curEpToWrite.indexer_id)

            if curEpToWrite.airdate > datetime.date.min:
                aired = SubElement(episode, "aired")
                aired.text = str(curEpToWrite.airdate)

            if getattr(myEp, 'overview', None):
                plot = SubElement(episode, "plot")
                plot.text = myEp['overview']

            if curEpToWrite.season and getattr(indexer_data, 'runtime', None):
                runtime = SubElement(episode, "runtime")
                runtime.text = indexer_data["runtime"]

            if getattr(myEp, 'airsbefore_season', None):
                displayseason = SubElement(episode, "displayseason")
                displayseason.text = myEp['airsbefore_season']

            if getattr(myEp, 'airsbefore_episode', None):
                displayepisode = SubElement(episode, "displayepisode")
                displayepisode.text = myEp['airsbefore_episode']

            if getattr(myEp, 'filename', None):
                thumb = SubElement(episode, "thumb")
                thumb.text = myEp['filename'].strip()

            # watched = SubElement(episode, "watched")
            # watched.text = 'false'

            if getattr(myEp, 'writer', None):
                ep_credits = SubElement(episode, "credits")
                ep_credits.text = myEp['writer'].strip()

            if getattr(myEp, 'director', None):
                director = SubElement(episode, "director")
                director.text = myEp['director'].strip()

            if getattr(myEp, 'rating', None):
                rating = SubElement(episode, "rating")
                rating.text = myEp['rating']

            if getattr(myEp, 'gueststars', None) and isinstance(myEp['gueststars'], str):
                for actor in (x.strip() for x in myEp['gueststars'].split('|') if x.strip()):
                    cur_actor = SubElement(episode, "actor")
                    cur_actor_name = SubElement(cur_actor, "name")
                    cur_actor_name.text = actor

            for actor in t.actors(int(ep_obj.show.indexer_id)):
                cur_actor = SubElement(episode, "actor")

                if 'name' in actor and actor['name'].strip():
                    cur_actor_name = SubElement(cur_actor, "name")
                    cur_actor_name.text = actor['name'].strip()
                else:
                    continue

                if 'role' in actor and actor['role'].strip():
                    cur_actor_role = SubElement(cur_actor, "role")
                    cur_actor_role.text = actor['role'].strip()

                if 'image' in actor and actor['image'].strip():
                    cur_actor_thumb = SubElement(cur_actor, "thumb")
                    cur_actor_thumb.text = actor['image'].strip()

        # Make it purdy
        indent_xml(rootNode)
        data = ElementTree(rootNode)
        return data
