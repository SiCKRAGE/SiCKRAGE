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
from xml.etree.ElementTree import Element, ElementTree, SubElement

import sickrage
from sickrage.core.common import dateFormat
from sickrage.core.exceptions import ShowNotFoundException
from sickrage.core.helpers import indentXML
from sickrage.indexers import srIndexerApi
from sickrage.indexers.exceptions import indexer_episodenotfound, \
    indexer_error, indexer_seasonnotfound, indexer_shownotfound
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

        show_ID = show_obj.indexerid

        indexer_lang = show_obj.lang
        lINDEXER_API_PARMS = srIndexerApi(show_obj.indexer).api_params.copy()

        lINDEXER_API_PARMS['actors'] = True

        if indexer_lang and not indexer_lang == sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE:
            lINDEXER_API_PARMS['language'] = indexer_lang

        if show_obj.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = srIndexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)

        tv_node = Element("tvshow")

        try:
            myShow = t[int(show_ID)]
        except indexer_shownotfound:
            sickrage.srCore.srLogger.error("Unable to find show with id " + str(show_ID) + " on " + srIndexerApi(
                show_obj.indexer).name + ", skipping it")
            raise

        except indexer_error:
            sickrage.srCore.srLogger.error(
                "" + srIndexerApi(show_obj.indexer).name + " is down, can't use its data to add this show")
            raise

        # check for title and id
        if not (getattr(myShow, 'seriesname', None) and getattr(myShow, 'id', None)):
            sickrage.srCore.srLogger.info("Incomplete info for show with id " + str(show_ID) + " on " + srIndexerApi(
                show_obj.indexer).name + ", skipping it")
            return False

        title = SubElement(tv_node, "title")
        title.text = myShow["seriesname"]

        if getattr(myShow, 'rating', None):
            rating = SubElement(tv_node, "rating")
            rating.text = myShow["rating"]

        if getattr(myShow, 'firstaired', None):
            try:
                year_text = str(datetime.datetime.strptime(myShow["firstaired"], dateFormat).year)
                if year_text:
                    year = SubElement(tv_node, "year")
                    year.text = year_text
            except:
                pass

        if getattr(myShow, 'overview', None):
            plot = SubElement(tv_node, "plot")
            plot.text = myShow["overview"]

        if getattr(myShow, 'id', None):
            episodeguide = SubElement(tv_node, "episodeguide")
            episodeguideurl = SubElement(episodeguide, "url")
            episodeguideurl.text = srIndexerApi(show_obj.indexer).config['base_url'] + str(
                myShow["id"]) + '/all/en.zip'

        if getattr(myShow, 'contentrating', None):
            mpaa = SubElement(tv_node, "mpaa")
            mpaa.text = myShow["contentrating"]

        if getattr(myShow, 'id', None):
            indexerid = SubElement(tv_node, "id")
            indexerid.text = str(myShow["id"])

        if getattr(myShow, 'genre', None) and isinstance(myShow["genre"], basestring):
            genre = SubElement(tv_node, "genre")
            genre.text = " / ".join(x.strip() for x in myShow["genre"].split('|') if x.strip())

        if getattr(myShow, 'firstaired', None):
            premiered = SubElement(tv_node, "premiered")
            premiered.text = myShow["firstaired"]

        if getattr(myShow, 'network', None):
            studio = SubElement(tv_node, "studio")
            studio.text = myShow["network"].strip()

        if getattr(myShow, '_actors', None):
            for actor in myShow['_actors']:
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
        indentXML(tv_node)

        data = ElementTree(tv_node)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for an KODI-style episode.nfo and
        returns the resulting data object.
            show_obj: a TVEpisode instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        indexer_lang = ep_obj.show.lang

        lINDEXER_API_PARMS = srIndexerApi(ep_obj.show.indexer).api_params.copy()

        lINDEXER_API_PARMS['actors'] = True

        if indexer_lang and not indexer_lang == sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE:
            lINDEXER_API_PARMS['language'] = indexer_lang

        if ep_obj.show.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        try:
            t = srIndexerApi(ep_obj.show.indexer).indexer(**lINDEXER_API_PARMS)
            myShow = t[ep_obj.show.indexerid]
        except indexer_shownotfound as e:
            raise ShowNotFoundException(e.message)
        except indexer_error as e:
            sickrage.srCore.srLogger.error("Unable to connect to {} while creating meta files - skipping - {}".format(
                srIndexerApi(
                    ep_obj.show.indexer).name, e))
            return

        if len(eps_to_write) > 1:
            rootNode = Element("kodimultiepisode")
        else:
            rootNode = Element("episodedetails")

        # write an NFO containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (indexer_episodenotfound, indexer_seasonnotfound):
                sickrage.srCore.srLogger.info(
                    "Unable to find episode %dx%d on %s... has it been removed? Should I delete from db?" %
                    (curEpToWrite.season, curEpToWrite.episode, srIndexerApi(ep_obj.show.indexer).name))
                return None

            if not getattr(myEp, 'firstaired', None):
                myEp["firstaired"] = str(datetime.date.fromordinal(1))

            if not getattr(myEp, 'episodename', None):
                sickrage.srCore.srLogger.debug("Not generating nfo because the ep has no title")
                return None

            sickrage.srCore.srLogger.debug("Creating metadata for episode " + str(ep_obj.season) + "x" + str(ep_obj.episode))

            if len(eps_to_write) > 1:
                episode = SubElement(rootNode, "episodedetails")
            else:
                episode = rootNode

            if getattr(myEp, 'episodename', None):
                title = SubElement(episode, "title")
                title.text = myEp['episodename']

            if getattr(myShow, 'seriesname', None):
                showtitle = SubElement(episode, "showtitle")
                showtitle.text = myShow['seriesname']

            season = SubElement(episode, "season")
            season.text = str(curEpToWrite.season)

            episodenum = SubElement(episode, "episode")
            episodenum.text = str(curEpToWrite.episode)

            uniqueid = SubElement(episode, "uniqueid")
            uniqueid.text = str(curEpToWrite.indexerid)

            if curEpToWrite.airdate != datetime.date.fromordinal(1):
                aired = SubElement(episode, "aired")
                aired.text = str(curEpToWrite.airdate)

            if getattr(myEp, 'overview', None):
                plot = SubElement(episode, "plot")
                plot.text = myEp['overview']

            if curEpToWrite.season and getattr(myShow, 'runtime', None):
                runtime = SubElement(episode, "runtime")
                runtime.text = myShow["runtime"]

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

            if getattr(myEp, 'gueststars', None) and isinstance(myEp['gueststars'], basestring):
                for actor in (x.strip() for x in myEp['gueststars'].split('|') if x.strip()):
                    cur_actor = SubElement(episode, "actor")
                    cur_actor_name = SubElement(cur_actor, "name")
                    cur_actor_name.text = actor

            if getattr(myShow, '_actors', None):
                for actor in myShow['_actors']:
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
        indentXML(rootNode)
        data = ElementTree(rootNode)
        return data


# present a standard "interface" from the module
metadata_class = KODI_12PlusMetadata
