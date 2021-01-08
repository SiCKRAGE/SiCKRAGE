# Author: echel0n <echel0n@sickrage.ca>
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import importlib
import inspect
import os
import pkgutil
import re
from xml.etree.ElementTree import ElementTree

import fanart

import sickrage
from sickrage.core.enums import SeriesProviderID
from sickrage.core.helpers import chmod_as_parent, replace_extension, try_int
from sickrage.core.websession import WebSession
from sickrage.series_providers.exceptions import SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound
from sickrage.series_providers.helpers import map_series_providers


class MetadataProvider(object):
    """
    Base class for all metadata providers. Default behavior is meant to mostly
    follow KODI 12+ metadata standards. Has support for:
    - show metadata file
    - episode metadata file
    - episode thumbnail
    - show fanart
    - show poster
    - show banner
    - season thumbnails (poster)
    - season thumbnails (banner)
    - season all poster
    - season all banner
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
                 season_all_banner=False,
                 enabled=False):

        self.name = "Generic"
        self.enabled = enabled

        self._ep_nfo_extension = "nfo"
        self._show_metadata_filename = "tvshow.nfo"

        self.fanart_name = "fanart.jpg"
        self.poster_name = "poster.jpg"
        self.banner_name = "banner.jpg"

        self.season_all_poster_name = "season-all-poster.jpg"
        self.season_all_banner_name = "season-all-banner.jpg"

        self.show_metadata = show_metadata
        self.episode_metadata = episode_metadata
        self.fanart = fanart
        self.poster = poster
        self.banner = banner
        self.episode_thumbnails = episode_thumbnails
        self.season_posters = season_posters
        self.season_banners = season_banners
        self.season_all_poster = season_all_poster
        self.season_all_banner = season_all_banner

    @property
    def id(self):
        return str(re.sub(r"[^\w\d_]", "_", str(re.sub(r"[+]", "plus", self.name))).lower())

    @property
    def config(self):
        return "|".join(map(str, map(int, [self.show_metadata, self.episode_metadata, self.fanart, self.poster, self.banner, self.episode_thumbnails,
                                           self.season_posters, self.season_banners, self.season_all_poster, self.season_all_banner, self.enabled])))

    @config.setter
    def config(self, values):
        if not values:
            values = '0|0|0|0|0|0|0|0|0|0|0'

        self.show_metadata, self.episode_metadata, self.fanart, self.poster, self.banner, self.episode_thumbnails, self.season_posters, \
        self.season_banners, self.season_all_poster, self.season_all_banner, self.enabled = tuple(map(bool, map(int, values.split('|'))))

    @staticmethod
    def _check_exists(location):
        if location:
            result = os.path.isfile(location)
            return result
        return False

    def _has_show_metadata(self, show_obj):
        return self._check_exists(self.get_show_file_path(show_obj))

    def _has_episode_metadata(self, ep_obj):
        return self._check_exists(self.get_episode_file_path(ep_obj))

    def _has_fanart(self, show_obj):
        return self._check_exists(self.get_fanart_path(show_obj))

    def _has_poster(self, show_obj):
        return self._check_exists(self.get_poster_path(show_obj))

    def _has_banner(self, show_obj):
        return self._check_exists(self.get_banner_path(show_obj))

    def _has_episode_thumb(self, ep_obj):
        return self._check_exists(self.get_episode_thumb_path(ep_obj))

    def _has_season_poster(self, show_obj, season):
        return self._check_exists(self.get_season_poster_path(show_obj, season))

    def _has_season_banner(self, show_obj, season):
        return self._check_exists(self.get_season_banner_path(show_obj, season))

    def _has_season_all_poster(self, show_obj):
        return self._check_exists(self.get_season_all_poster_path(show_obj))

    def _has_season_all_banner(self, show_obj):
        return self._check_exists(self.get_season_all_banner_path(show_obj))

    def get_show_file_path(self, show_obj):
        return os.path.join(show_obj.location, self._show_metadata_filename)

    def get_episode_file_path(self, ep_obj):
        return replace_extension(ep_obj.location, self._ep_nfo_extension)

    def get_fanart_path(self, show_obj):
        return os.path.join(show_obj.location, self.fanart_name)

    def get_poster_path(self, show_obj):
        return os.path.join(show_obj.location, self.poster_name)

    def get_banner_path(self, show_obj):
        return os.path.join(show_obj.location, self.banner_name)

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns the path where the episode thumbnail should be stored.
        ep_obj: a TVEpisode instance for which to create the thumbnail
        """
        if os.path.isfile(ep_obj.location):

            tbn_filename = ep_obj.location.rpartition(".")

            if tbn_filename[0] == "":
                tbn_filename = ep_obj.location + "-thumb.jpg"
            else:
                tbn_filename = tbn_filename[0] + "-thumb.jpg"
        else:
            return None

        return tbn_filename

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Returns the full path to the file for a given season poster.

        show_obj: a TVShow instance for which to generate the path
        season: a season number to be used for the path. Note that season 0
                means specials.
        """

        # Our specials thumbnail is, well, special
        if season == 0:
            season_poster_filename = 'season-specials'
        else:
            season_poster_filename = 'season' + str(season).zfill(2)

        return os.path.join(show_obj.location, season_poster_filename + '-poster.jpg')

    @staticmethod
    def get_season_banner_path(show_obj, season):
        """
        Returns the full path to the file for a given season banner.

        show_obj: a TVShow instance for which to generate the path
        season: a season number to be used for the path. Note that season 0
                means specials.
        """

        # Our specials thumbnail is, well, special
        if season == 0:
            season_banner_filename = 'season-specials'
        else:
            season_banner_filename = 'season' + str(season).zfill(2)

        return os.path.join(show_obj.location, season_banner_filename + '-banner.jpg')

    def get_season_all_poster_path(self, show_obj):
        return os.path.join(show_obj.location, self.season_all_poster_name)

    def get_season_all_banner_path(self, show_obj):
        return os.path.join(show_obj.location, self.season_all_banner_name)

    def _show_data(self, show_obj):
        """
        This should be overridden by the implementing class. It should
        provide the content of the show metadata file.
        """
        return None

    def _ep_data(self, ep_obj):
        """
        This should be overridden by the implementing class. It should
        provide the content of the episode metadata file.
        """
        return None

    def create_show_metadata(self, show_obj, force=False):
        if self.show_metadata and show_obj and (not self._has_show_metadata(show_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating show metadata for " + show_obj.name)
            return self.write_show_file(show_obj)
        return False

    def create_episode_metadata(self, ep_obj, force=False):
        if self.episode_metadata and ep_obj and (not self._has_episode_metadata(ep_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating episode metadata for " + ep_obj.pretty_name())
            return self.write_ep_file(ep_obj)
        return False

    def create_fanart(self, show_obj, which=0, force=False):
        if self.fanart and show_obj and (not self._has_fanart(show_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating fanart for " + show_obj.name)
            return self.save_fanart(show_obj, which)
        return False

    def create_poster(self, show_obj, which=0, force=False):
        if self.poster and show_obj and (not self._has_poster(show_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating poster for " + show_obj.name)
            return self.save_poster(show_obj, which)
        return False

    def create_banner(self, show_obj, which=0, force=False):
        if self.banner and show_obj and (not self._has_banner(show_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating banner for " + show_obj.name)
            return self.save_banner(show_obj, which)
        return False

    def create_episode_thumb(self, ep_obj, force=False):
        if self.episode_thumbnails and ep_obj and (not self._has_episode_thumb(ep_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating episode thumbnail for " + ep_obj.pretty_name())
            return self.save_thumbnail(ep_obj)
        return False

    def create_season_posters(self, show_obj, force=False):
        if self.season_posters and show_obj:
            result = []
            for ep_obj in show_obj.episodes:
                if not self._has_season_poster(show_obj, ep_obj.season) or force:
                    sickrage.app.log.debug("Metadata provider " + self.name + " creating season posters for " + show_obj.name)
                    result = result + [self.save_season_poster(show_obj, ep_obj.season)]
            return all(result)
        return False

    def create_season_banners(self, show_obj, force=False):
        if self.season_banners and show_obj:
            result = []
            sickrage.app.log.debug("Metadata provider " + self.name + " creating season banners for " + show_obj.name)
            for ep_obj in show_obj.episodes:
                if not self._has_season_banner(show_obj, ep_obj.season) or force:
                    result = result + [self.save_season_banner(show_obj, ep_obj.season)]
            return all(result)
        return False

    def create_season_all_poster(self, show_obj, force=False):
        if self.season_all_poster and show_obj and (not self._has_season_all_poster(show_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating season all poster for " + show_obj.name)
            return self.save_season_all_poster(show_obj)
        return False

    def create_season_all_banner(self, show_obj, force=False):
        if self.season_all_banner and show_obj and (not self._has_season_all_banner(show_obj) or force):
            sickrage.app.log.debug("Metadata provider " + self.name + " creating season all banner for " + show_obj.name)
            return self.save_season_all_banner(show_obj)
        return False

    def _get_episode_thumb_url(self, ep_obj):
        """
        Returns the URL to use for downloading an episode's thumbnail. Uses
        theTVDB.com data.

        ep_obj: a TVEpisode object for which to grab the thumb URL
        """
        all_eps = [ep_obj] + ep_obj.related_episodes

        # validate show
        if not self.validate_show(ep_obj.show):
            return None

        # try all included episodes in case some have thumbs and others don't
        for cur_ep in all_eps:
            myEp = self.validate_show(cur_ep.show, cur_ep.season, cur_ep.episode)
            if not myEp:
                continue

            thumb_url = getattr(myEp, 'filename', None)
            if thumb_url:
                return thumb_url

        return None

    def write_show_file(self, show_obj):
        """
        Generates and writes show_obj's metadata under the given path to the
        filename given by get_show_file_path()

        show_obj: TVShow object for which to create the metadata

        path: An absolute or relative path where we should put the file. Note that
                the file name will be the default show_file_name.

        Note that this method expects that _show_data will return an ElementTree
        object. If your _show_data returns data in another format yo'll need to
        override this method.
        """

        data = self._show_data(show_obj)
        if not data:
            return False

        nfo_file_path = self.get_show_file_path(show_obj)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                sickrage.app.log.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                chmod_as_parent(nfo_file_dir)

            sickrage.app.log.debug("Writing show nfo file to " + nfo_file_path)

            with open(nfo_file_path, 'wb') as nfo_file:
                data.write(nfo_file, encoding='utf-8')

            chmod_as_parent(nfo_file_path)
        except IOError as e:
            sickrage.app.log.warning("Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? {}".format(e))
            return False

        return True

    def write_ep_file(self, ep_obj):
        """
        Generates and writes ep_obj's metadata under the given path with the
        given filename root. Uses the episode's name with the extension in
        _ep_nfo_extension.

        ep_obj: TVEpisode object for which to create the metadata

        file_name_path: The file name to use for this metadata. Note that the extension
                will be automatically added based on _ep_nfo_extension. This should
                include an absolute path.

        Note that this method expects that _ep_data will return an ElementTree
        object. If your _ep_data returns data in another format yo'll need to
        override this method.
        """

        data = self._ep_data(ep_obj)
        if not data:
            return False

        nfo_file_path = self.get_episode_file_path(ep_obj)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                sickrage.app.log.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                chmod_as_parent(nfo_file_dir)

            sickrage.app.log.debug("Writing episode nfo file to " + nfo_file_path)

            with open(nfo_file_path, 'wb') as nfo_file:
                data.write(nfo_file, encoding='utf-8')

            chmod_as_parent(nfo_file_path)
        except IOError as e:
            sickrage.app.log.warning("Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? {}".format(e))
            return False

        return True

    def save_thumbnail(self, ep_obj):
        """
        Retrieves a thumbnail and saves it to the correct spot. This method should not need to
        be overridden by implementing classes, changing get_episode_thumb_path and
        _get_episode_thumb_url should suffice.

        ep_obj: a TVEpisode object for which to generate a thumbnail
        """

        file_path = self.get_episode_thumb_path(ep_obj)

        if not file_path:
            sickrage.app.log.debug("Unable to find a file path to use for this thumbnail, not generating it")
            return False

        thumb_url = self._get_episode_thumb_url(ep_obj)

        # if we can't find one then give up
        if not thumb_url:
            sickrage.app.log.debug("No thumb is available for this episode, not creating a thumb")
            return False

        thumb_data = self.get_show_image(thumb_url)

        result = self._write_image(thumb_data, file_path)

        if not result:
            return False

        for cur_ep in [ep_obj] + ep_obj.related_episodes:
            cur_ep.hastbn = True
            cur_ep.save()

        return True

    def save_fanart(self, show_obj, which=0):
        """
        Downloads a fanart image and saves it to the filename specified by fanart_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download fanart
        """

        # use the default fanart name
        fanart_path = self.get_fanart_path(show_obj)

        fanart_data = self._retrieve_show_image('fanart', show_obj, which)

        if not fanart_data:
            sickrage.app.log.debug("No fanart image was retrieved, unable to write fanart")
            return False

        return self._write_image(fanart_data, fanart_path)

    def save_poster(self, show_obj, which=0):
        """
        Downloads a poster image and saves it to the filename specified by poster_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download a poster
        """

        # use the default poster name
        poster_path = self.get_poster_path(show_obj)

        poster_data = self._retrieve_show_image('poster', show_obj, which)

        if not poster_data:
            sickrage.app.log.debug("No show poster image was retrieved, unable to write poster")
            return False

        return self._write_image(poster_data, poster_path)

    def save_banner(self, show_obj, which=0):
        """
        Downloads a banner image and saves it to the filename specified by banner_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download a banner
        """

        # use the default banner name
        banner_path = self.get_banner_path(show_obj)

        banner_data = self._retrieve_show_image('series', show_obj, which)

        if not banner_data:
            sickrage.app.log.debug("No show banner image was retrieved, unable to write banner")
            return False

        return self._write_image(banner_data, banner_path)

    def save_season_poster(self, show_obj, season, which=0):
        season_url = self._retrieve_season_poster_image(show_obj, season, which)

        season_poster_file_path = self.get_season_poster_path(show_obj, season)
        if not season_poster_file_path:
            sickrage.app.log.debug("Path for season " + str(season) + " came back blank, skipping this season")
            return False

        seasonData = self.get_show_image(season_url)
        if not seasonData:
            sickrage.app.log.debug("No season poster data available, skipping this season")
            return False

        return self._write_image(seasonData, season_poster_file_path)

    def save_season_banner(self, show_obj, season, which=0):
        season_url = self._retrieve_season_banner_image(show_obj, season, which)

        season_banner_file_path = self.get_season_banner_path(show_obj, season)
        if not season_banner_file_path:
            sickrage.app.log.debug("Path for season " + str(season) + " came back blank, skipping this season")
            return False

        seasonData = self.get_show_image(season_url)
        if not seasonData:
            sickrage.app.log.debug("No season banner data available, skipping this season")
            return False

        return self._write_image(seasonData, season_banner_file_path)

    def save_season_all_poster(self, show_obj, which=0):
        # use the default season all poster name
        poster_path = self.get_season_all_poster_path(show_obj)

        poster_data = self._retrieve_show_image('poster', show_obj, which)

        if not poster_data:
            sickrage.app.log.debug("No show poster image was retrieved, unable to write season all poster")
            return False

        return self._write_image(poster_data, poster_path)

    def save_season_all_banner(self, show_obj, which=0):
        # use the default season all banner name
        banner_path = self.get_season_all_banner_path(show_obj)

        banner_data = self._retrieve_show_image('series', show_obj, which)

        if not banner_data:
            sickrage.app.log.debug("No show banner image was retrieved, unable to write season all banner")
            return False

        return self._write_image(banner_data, banner_path)

    def _write_image(self, image_data, image_path, force=False):
        """
        Saves the data in image_data to the location image_path. Returns True/False
        to represent success or failure.

        image_data: binary image data to write to file
        image_path: file location to save the image to
        """

        # don't bother overwriting it
        if os.path.isfile(image_path) and not force:
            sickrage.app.log.debug("Image already exists, not downloading")
            return False

        image_dir = os.path.dirname(image_path)

        if not image_data:
            sickrage.app.log.debug("Unable to retrieve image to save in %s, skipping" % image_path)
            return False

        try:
            if not os.path.isdir(image_dir):
                sickrage.app.log.debug("Metadata dir didn't exist, creating it at " + image_dir)
                os.makedirs(image_dir)
                chmod_as_parent(image_dir)

            with open(image_path, 'wb') as outFile:
                outFile.write(image_data)

            chmod_as_parent(image_path)
        except IOError as e:
            sickrage.app.log.warning("Unable to write image to " + image_path + " - are you sure the show folder is writable? {}".format(e))
            return False

        return True

    def _retrieve_show_image(self, image_type, show_obj, which=0):
        """
        Gets an image URL from theTVDB.com and fanart.tv, downloads it and returns the data.

        image_type: type of image to retrieve (currently supported: fanart, poster, banner)
        show_obj: a TVShow object to use when searching for the image
        which: optional, a specific numbered poster to look for

        Returns: the binary image data if available, or else None
        """

        image_data = None

        if image_type not in ('fanart', 'poster', 'series', 'poster_thumb', 'series_thumb', 'fanart_thumb'):
            sickrage.app.log.warning(
                "Invalid image type " + str(image_type) + ", couldn't find it in the " + show_obj.series_provider.name + " object")
            return

        series_provider_language = show_obj.lang or sickrage.app.config.general.series_provider_default_language

        is_image_thumb = '_thumb' in image_type
        image_types = {
            '{}'.format(image_type): {
                'series_provider': lambda:
                show_obj.series_provider.images(show_obj.series_id, language=series_provider_language, key_type=image_type.replace('_thumb', ''))[which][
                    ('filename', 'thumbnail')[is_image_thumb]],
                'fanart': lambda: self._retrieve_show_images_from_fanart(show_obj, image_type.replace('_thumb', ''), is_image_thumb)
            }
        }

        for fname in ['series_provider', 'fanart']:
            try:
                image_url = image_types[image_type][fname]()
                if image_url:
                    image_data = self.get_show_image(image_url)
                    if image_data:
                        break
            except (KeyError, IndexError, TypeError) as e:
                pass

        return image_data

    @staticmethod
    def _retrieve_season_poster_image(show_obj, season, which=0):
        """
        Should return a dict like:

        result = {<season number>:
                    {1: '<url 1>', 2: <url 2>, ...},}
        """

        try:
            series_provider_language = show_obj.lang or sickrage.app.config.general.series_provider_default_language

            # Give us just the normal poster-style season graphics
            image_data = show_obj.series_provider.images(show_obj.series_id, language=series_provider_language, key_type='season', season=season)
            if image_data:
                return image_data[which]['filename']

            sickrage.app.log.debug("{}: No season {} poster images on {} to download found".format(show_obj.series_id, season, show_obj.series_provider.name))
        except (KeyError, IndexError):
            pass

    @staticmethod
    def _retrieve_season_banner_image(show_obj, season, which=0):
        """
        Should return a dict like:

        result = {<season number>:
                    {1: '<url 1>', 2: <url 2>, ...},}
        """

        try:
            series_provider_language = show_obj.lang or sickrage.app.config.general.series_provider_default_language

            # Give us just the normal season graphics
            image_data = show_obj.series_provider.images(show_obj.series_id, language=series_provider_language, key_type='seasonwide', season=season)
            if image_data:
                return image_data[which]['filename']

            sickrage.app.log.debug("{}: No season {} banner images on {} to download found".format(show_obj.series_id, season, show_obj.series_provider.name))
        except (KeyError, IndexError):
            pass

    def retrieve_show_metadata(self, folder) -> (int, str, int):
        """
        :param folder:
        :return:
        """

        empty_return = (None, None, None)

        metadata_path = os.path.join(folder, self._show_metadata_filename)

        if not os.path.isdir(folder) or not os.path.isfile(metadata_path):
            sickrage.app.log.debug("Can't load the metadata file from " + metadata_path + ", it doesn't exist")
            return empty_return

        try:
            sickrage.app.log.debug(f"Loading show info from SiCKRAGE metadata file in {folder}")

            with open(metadata_path, 'rb') as xmlFileObj:
                showXML = ElementTree(file=xmlFileObj)

            if showXML.findtext('title') is None or (
                    showXML.findtext('tvdbid') is None and showXML.findtext('id') is None):
                sickrage.app.log.info("Invalid info in tvshow.nfo (missing name or id): {} {} {}".format(showXML.findtext('title'),
                                                                                                         showXML.findtext('tvdbid'),
                                                                                                         showXML.findtext('id')))
                return empty_return

            name = showXML.findtext('title')

            series_id_text = showXML.findtext('tvdbid') or showXML.findtext('id')
            if series_id_text:
                series_id = try_int(series_id_text, None)
                if not series_id:
                    sickrage.app.log.debug("Invalid series id (" + str(series_id) + "), not using metadata file")
                    return empty_return
            else:
                sickrage.app.log.debug("Empty <id> or <tvdbid> field in NFO, unable to find a ID, not using metadata file")
                return empty_return

            if showXML.findtext('tvdbid') is not None:
                series_id = int(showXML.findtext('tvdbid'))
            elif showXML.findtext('id') is not None:
                series_id = int(showXML.findtext('id'))
            else:
                sickrage.app.log.warning("Empty <id> or <tvdbid> field in NFO, unable to find a ID")
                return empty_return

            epg_url_text = showXML.findtext('episodeguide/url')
            if epg_url_text:
                epg_url = epg_url_text.lower()
                if str(series_id) in epg_url and 'tvrage' in epg_url:
                    sickrage.app.log.warning("Invalid series id (" + str(series_id) + "), not using metadata file because it has TVRage info")
                    return empty_return

        except Exception as e:
            sickrage.app.log.warning("There was an error parsing your existing metadata file: '" + metadata_path + "' error: {}".format(e))
            return empty_return

        return series_id, name, SeriesProviderID.THETVDB

    @staticmethod
    def _retrieve_show_images_from_fanart(show, img_type, thumb=False):
        types = {
            'poster': fanart.TYPE.TV.POSTER,
            'series': fanart.TYPE.TV.BANNER,
            'fanart': fanart.TYPE.TV.BACKGROUND,
        }

        sickrage.app.log.debug("Searching for any " + img_type + " images on Fanart.tv for " + show.name)

        try:
            series_id = map_series_providers(show.series_provider_id, show.series_id, show.name)[SeriesProviderID.THETVDB.name]
            if series_id:
                request = fanart.Request(
                    apikey=sickrage.app.fanart_api_key,
                    id=series_id,
                    ws=fanart.WS.TV,
                    type=types[img_type],
                    sort=fanart.SORT.POPULAR,
                    limit=fanart.LIMIT.ONE,
                )

                resp = request.response()
                url = resp[types[img_type]][0]['url']
                if thumb:
                    url = re.sub('/fanart/', '/preview/', url)
                return url
        except Exception:
            pass

        sickrage.app.log.debug("Could not find any " + img_type + " images on Fanart.tv for " + show.name)

    @staticmethod
    def validate_show(show, season=None, episode=None):
        if season is None and episode is None:
            return

        try:
            series_provider_language = show.lang or sickrage.app.config.general.series_provider_default_language

            return show.series_provider.search(show.series_id, language=series_provider_language)[season][episode]
        except (SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound):
            pass

    @staticmethod
    def get_show_image(url):
        if url is None:
            return None

        sickrage.app.log.debug("Fetching image from " + url)

        try:
            return WebSession().get(url, verify=False).content
        except Exception:
            sickrage.app.log.debug("There was an error trying to retrieve the image, aborting")


class MetadataProviders(dict):
    def __init__(self):
        super(MetadataProviders, self).__init__()
        for (__, name, __) in pkgutil.iter_modules([os.path.dirname(__file__)]):
            imported_module = importlib.import_module('.' + name, package='sickrage.metadata_providers')
            for __, klass in inspect.getmembers(imported_module,
                                                predicate=lambda o: inspect.isclass(o) and issubclass(o, MetadataProvider) and o is not MetadataProvider):
                self[klass().id] = klass()
                break
