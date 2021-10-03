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
from sickrage.metadata_providers import MetadataProvider
from sickrage.series_providers.exceptions import SeriesProviderEpisodeNotFound, \
    SeriesProviderSeasonNotFound


class KODI_12PlusMetadata(MetadataProvider):
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

        series_provider_language = show_obj.lang or sickrage.app.config.general.series_provider_default_language
        series_info = show_obj.series_provider.get_series_info(show_obj.series_id, language=series_provider_language)
        if not series_info:
            return False

        # check for title and id
        if not (getattr(series_info, 'name', None) and getattr(series_info, 'id', None)):
            sickrage.app.log.info("Incomplete info for show with id " + str(show_obj.series_id) + " on " + show_obj.series_provider.name + ", skipping it")
            return False

        title = SubElement(tv_node, "title")
        title.text = series_info["name"]

        if getattr(series_info, 'rating', None):
            rating = SubElement(tv_node, "rating")
            rating.text = str(series_info["rating"])

        if getattr(series_info, 'firstAired', None):
            try:
                year_text = str(datetime.datetime.strptime(series_info["firstAired"], dateFormat).year)
                if year_text:
                    year = SubElement(tv_node, "year")
                    year.text = year_text
            except Exception:
                pass

        if getattr(series_info, 'overview', None):
            plot = SubElement(tv_node, "plot")
            plot.text = series_info["overview"]

        # if getattr(series_info, 'id', None):
        #    episodeguide = SubElement(tv_node, "episodeguide")
        #    episodeguideurl = SubElement(episodeguide, "url")
        #    episodeguideurl.text = IndexerApi(show_obj.series_provider_id).config['base_url'] + str(
        #        series_info["id"]) + '/all/en.zip'

        # if getattr(series_info, 'contentrating', None):
        #     mpaa = SubElement(tv_node, "mpaa")
        #     mpaa.text = series_info["contentrating"]

        if getattr(series_info, 'id', None):
            series_id = SubElement(tv_node, "id")
            series_id.text = str(series_info["id"])

        if getattr(series_info, 'genres', None):
            genre = SubElement(tv_node, "genre")
            genre.text = " / ".join(x['name'] for x in series_info["genres"])

        if getattr(series_info, 'firstAired', None):
            premiered = SubElement(tv_node, "premiered")
            premiered.text = series_info["firstAired"]

        if getattr(series_info, 'network', None):
            studio = SubElement(tv_node, "studio")
            studio.text = series_info["network"].strip()

        for person in series_info['people']:
            if 'name' not in person or not person['name'].strip():
                continue

            if person['role'].strip() == 'Actor':
                cur_actor = SubElement(tv_node, "actor")

                cur_actor_role = SubElement(cur_actor, "role")
                cur_actor_role.text = person['role'].strip()

                cur_actor_name = SubElement(cur_actor, "name")
                cur_actor_name.text = person['name'].strip()

                if person['imageUrl'].strip():
                    cur_actor_thumb = SubElement(cur_actor, "thumb")
                    cur_actor_thumb.text = person['imageUrl'].strip()

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

        series_provider_language = ep_obj.show.lang or sickrage.app.config.general.series_provider_default_language
        series_info = ep_obj.show.series_provider.get_series_info(ep_obj.show.series_id, language=series_provider_language)
        if not series_info:
            return False

        if len(eps_to_write) > 1:
            root_node = Element("kodimultiepisode")
        else:
            root_node = Element("episodedetails")

        # write an NFO containing info for all matching episodes
        for curEpToWrite in eps_to_write:
            try:
                series_episode_info = series_info[curEpToWrite.season][curEpToWrite.episode]
            except (SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound):
                sickrage.app.log.info(
                    f"Unable to find episode {curEpToWrite.season:d}x{curEpToWrite.episode:d} on {ep_obj.show.series_provider.name}"
                    f"... has it been removed? Should I delete from db?")
                return None

            if not getattr(series_episode_info, 'firstAired', None):
                series_episode_info["firstAired"] = str(datetime.date.min)

            if not getattr(series_episode_info, 'name', None):
                sickrage.app.log.debug("Not generating nfo because the ep has no title")
                return None

            sickrage.app.log.debug(f"Creating metadata for episode {ep_obj.season}x{ep_obj.episode}")

            if len(eps_to_write) > 1:
                episode = SubElement(root_node, "episodedetails")
            else:
                episode = root_node

            if getattr(series_episode_info, 'name', None):
                title = SubElement(episode, "title")
                title.text = series_episode_info['name']

            if getattr(series_info, 'name', None):
                showtitle = SubElement(episode, "showtitle")
                showtitle.text = series_info['name']

            season = SubElement(episode, "season")
            season.text = str(curEpToWrite.season)

            episodenum = SubElement(episode, "episode")
            episodenum.text = str(curEpToWrite.episode)

            uniqueid = SubElement(episode, "uniqueid")
            uniqueid.text = str(curEpToWrite.series_id)

            if curEpToWrite.airdate > datetime.date.min:
                aired = SubElement(episode, "aired")
                aired.text = str(curEpToWrite.airdate)

            if getattr(series_episode_info, 'overview', None):
                plot = SubElement(episode, "plot")
                plot.text = series_episode_info['overview']

            if curEpToWrite.season and getattr(series_info, 'runtime', None):
                runtime = SubElement(episode, "runtime")
                runtime.text = series_info["runtime"]

            if getattr(series_episode_info, 'airsbefore_season', None):
                displayseason = SubElement(episode, "displayseason")
                displayseason.text = series_episode_info['airsbefore_season']

            if getattr(series_episode_info, 'airsbefore_episode', None):
                displayepisode = SubElement(episode, "displayepisode")
                displayepisode.text = series_episode_info['airsbefore_episode']

            if getattr(series_episode_info, 'filename', None):
                thumb = SubElement(episode, "thumb")
                thumb.text = series_episode_info['filename'].strip()

            # watched = SubElement(episode, "watched")
            # watched.text = 'false'

            if getattr(series_episode_info, 'rating', None):
                rating = SubElement(episode, "rating")
                rating.text = str(series_episode_info['rating'])

            for person in series_info['people']:
                if 'name' not in person or not person['name'].strip():
                    continue

                if person['role'].strip() == 'Actor':
                    cur_actor = SubElement(episode, "actor")

                    cur_actor_role = SubElement(cur_actor, "role")
                    cur_actor_role.text = person['role'].strip()

                    cur_actor_name = SubElement(cur_actor, "name")
                    cur_actor_name.text = person['name'].strip()

                    if person['imageUrl'].strip():
                        cur_actor_thumb = SubElement(cur_actor, "thumb")
                        cur_actor_thumb.text = person['imageUrl'].strip()
                elif person['role'].strip() == 'Writer':
                    ep_credits = SubElement(episode, "credits")
                    ep_credits.text = series_episode_info['writer'].strip()
                elif person['role'].strip() == 'Director':
                    director = SubElement(episode, "director")
                    director.text = series_episode_info['director'].strip()
                elif person['role'].strip() == 'Guest Star':
                    cur_actor = SubElement(episode, "actor")
                    cur_actor_name = SubElement(cur_actor, "name")
                    cur_actor_name.text = person['name'].strip()

        # Make it purdy
        indent_xml(root_node)
        data = ElementTree(root_node)
        return data
