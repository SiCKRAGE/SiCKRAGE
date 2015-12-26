# -*- coding: utf-8 -*-

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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

from __future__ import unicode_literals

import os
import io
import re

from sickrage.helper.encoding import ek

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

import sickbeard

from sickbeard import helpers
import logging
from sickbeard.metadata import helpers as metadata_helpers
from sickbeard.show_name_helpers import allPossibleShowNames
from sickrage.helper.exceptions import ex

from tmdb_api.tmdb_api import TMDB

import fanart
from fanart.core import Request as fanartRequest


class GenericMetadata(object):
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

    def __init__(self, show_metadata=False, episode_metadata=False, fanart=False,
                 poster=False, banner=False, episode_thumbnails=False,
                 season_posters=False, season_banners=False,
                 season_all_poster=False, season_all_banner=False):

        self.name = "Generic"

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

    def get_config(self):
        config_list = [self.show_metadata, self.episode_metadata, self.fanart, self.poster, self.banner,
                       self.episode_thumbnails, self.season_posters, self.season_banners, self.season_all_poster,
                       self.season_all_banner]
        return '|'.join([str(int(x)) for x in config_list])

    def get_id(self):
        return GenericMetadata.makeID(self.name)

    @staticmethod
    def makeID(name):
        name_id = re.sub(r"[+]", "plus", name)
        name_id = re.sub(r"[^\w\d_]", "_", name_id).lower()
        return name_id

    def set_config(self, string):
        config_list = [bool(int(x)) for x in string.split('|')]
        self.show_metadata = config_list[0]
        self.episode_metadata = config_list[1]
        self.fanart = config_list[2]
        self.poster = config_list[3]
        self.banner = config_list[4]
        self.episode_thumbnails = config_list[5]
        self.season_posters = config_list[6]
        self.season_banners = config_list[7]
        self.season_all_poster = config_list[8]
        self.season_all_banner = config_list[9]

    @staticmethod
    def _check_exists(location):
        if location:
            result = ek(os.path.isfile, location)
            logging.debug("Checking if " + location + " exists: " + str(result))
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
        return ek(os.path.join, show_obj.location, self._show_metadata_filename)

    def get_episode_file_path(self, ep_obj):
        return helpers.replaceExtension(ep_obj.location, self._ep_nfo_extension)

    def get_fanart_path(self, show_obj):
        return ek(os.path.join, show_obj.location, self.fanart_name)

    def get_poster_path(self, show_obj):
        return ek(os.path.join, show_obj.location, self.poster_name)

    def get_banner_path(self, show_obj):
        return ek(os.path.join, show_obj.location, self.banner_name)

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns the path where the episode thumbnail should be stored.
        ep_obj: a TVEpisode instance for which to create the thumbnail
        """
        if ek(os.path.isfile, ep_obj.location):

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

        return ek(os.path.join, show_obj.location, season_poster_filename + '-poster.jpg')

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

        return ek(os.path.join, show_obj.location, season_banner_filename + '-banner.jpg')

    def get_season_all_poster_path(self, show_obj):
        return ek(os.path.join, show_obj.location, self.season_all_poster_name)

    def get_season_all_banner_path(self, show_obj):
        return ek(os.path.join, show_obj.location, self.season_all_banner_name)

    # pylint: disable=W0613,R0201
    def _show_data(self, show_obj):
        """
        This should be overridden by the implementing class. It should
        provide the content of the show metadata file.
        """
        return None

    # pylint: disable=W0613,R0201
    def _ep_data(self, ep_obj):
        """
        This should be overridden by the implementing class. It should
        provide the content of the episode metadata file.
        """
        return None

    def create_show_metadata(self, show_obj):
        if self.show_metadata and show_obj and not self._has_show_metadata(show_obj):
            logging.debug("Metadata provider " + self.name + " creating show metadata for " + show_obj.name)
            return self.write_show_file(show_obj)
        return False

    def create_episode_metadata(self, ep_obj):
        if self.episode_metadata and ep_obj and not self._has_episode_metadata(ep_obj):
            logging.debug("Metadata provider " + self.name + " creating episode metadata for " + ep_obj.prettyName())
            return self.write_ep_file(ep_obj)
        return False

    def update_show_indexer_metadata(self, show_obj):
        if self.show_metadata and show_obj and self._has_show_metadata(show_obj):
            logging.debug(
                    "Metadata provider " + self.name + " updating show indexer info metadata file for " + show_obj.name)

            nfo_file_path = self.get_show_file_path(show_obj)

            try:
                with ek(io.open, nfo_file_path, 'rb') as xmlFileObj:
                    showXML = etree.ElementTree(file=xmlFileObj)

                indexerid = showXML.find('id')

                root = showXML.getroot()
                if indexerid is not None:
                    indexerid.text = str(show_obj.indexerid)
                else:
                    etree.SubElement(root, "id").text = str(show_obj.indexerid)

                # Make it purdy
                helpers.indentXML(root)

                showXML.write(nfo_file_path, encoding='UTF-8')
                helpers.chmodAsParent(nfo_file_path)

                return True
            except IOError as e:
                logging.error(
                        "Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? {}".format(
                            ex(e)))

    def create_fanart(self, show_obj):
        if self.fanart and show_obj and not self._has_fanart(show_obj):
            logging.debug("Metadata provider " + self.name + " creating fanart for " + show_obj.name)
            return self.save_fanart(show_obj)
        return False

    def create_poster(self, show_obj):
        if self.poster and show_obj and not self._has_poster(show_obj):
            logging.debug("Metadata provider " + self.name + " creating poster for " + show_obj.name)
            return self.save_poster(show_obj)
        return False

    def create_banner(self, show_obj):
        if self.banner and show_obj and not self._has_banner(show_obj):
            logging.debug("Metadata provider " + self.name + " creating banner for " + show_obj.name)
            return self.save_banner(show_obj)
        return False

    def create_episode_thumb(self, ep_obj):
        if self.episode_thumbnails and ep_obj and not self._has_episode_thumb(ep_obj):
            logging.debug("Metadata provider " + self.name + " creating episode thumbnail for " + ep_obj.prettyName())
            return self.save_thumbnail(ep_obj)
        return False

    def create_season_posters(self, show_obj):
        if self.season_posters and show_obj:
            result = []
            for season, _ in show_obj.episodes.iteritems():  # @UnusedVariable
                if not self._has_season_poster(show_obj, season):
                    logging.debug("Metadata provider " + self.name + " creating season posters for " + show_obj.name)
                    result = result + [self.save_season_posters(show_obj, season)]
            return all(result)
        return False

    def create_season_banners(self, show_obj):
        if self.season_banners and show_obj:
            result = []
            logging.debug("Metadata provider " + self.name + " creating season banners for " + show_obj.name)
            for season, _ in show_obj.episodes.iteritems():  # @UnusedVariable
                if not self._has_season_banner(show_obj, season):
                    result = result + [self.save_season_banners(show_obj, season)]
            return all(result)
        return False

    def create_season_all_poster(self, show_obj):
        if self.season_all_poster and show_obj and not self._has_season_all_poster(show_obj):
            logging.debug("Metadata provider " + self.name + " creating season all poster for " + show_obj.name)
            return self.save_season_all_poster(show_obj)
        return False

    def create_season_all_banner(self, show_obj):
        if self.season_all_banner and show_obj and not self._has_season_all_banner(show_obj):
            logging.debug("Metadata provider " + self.name + " creating season all banner for " + show_obj.name)
            return self.save_season_all_banner(show_obj)
        return False

    def _get_episode_thumb_url(self, ep_obj):
        """
        Returns the URL to use for downloading an episode's thumbnail. Uses
        theTVDB.com data.

        ep_obj: a TVEpisode object for which to grab the thumb URL
        """
        all_eps = [ep_obj] + ep_obj.relatedEps

        # validate show
        if not helpers.validateShow(ep_obj.show):
            return None

        # try all included episodes in case some have thumbs and others don't
        for cur_ep in all_eps:
            myEp = helpers.validateShow(cur_ep.show, cur_ep.season, cur_ep.episode)
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
        nfo_file_dir = ek(os.path.dirname, nfo_file_path)

        try:
            if not ek(os.path.isdir, nfo_file_dir):
                logging.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                ek(os.makedirs, nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logging.debug("Writing show nfo file to " + nfo_file_path)

            nfo_file = ek(io.open, nfo_file_path, 'wb')
            data.write(nfo_file, encoding='UTF-8')
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError as e:
            logging.error(
                "Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? {}".format(ex(e)))
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
        nfo_file_dir = ek(os.path.dirname, nfo_file_path)

        try:
            if not ek(os.path.isdir, nfo_file_dir):
                logging.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                ek(os.makedirs, nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logging.debug("Writing episode nfo file to " + nfo_file_path)
            nfo_file = ek(io.open, nfo_file_path, 'wb')
            data.write(nfo_file, encoding='UTF-8')
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError as e:
            logging.error(
                "Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? {}".format(ex(e)))
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
            logging.debug("Unable to find a file path to use for this thumbnail, not generating it")
            return False

        thumb_url = self._get_episode_thumb_url(ep_obj)

        # if we can't find one then give up
        if not thumb_url:
            logging.debug("No thumb is available for this episode, not creating a thumb")
            return False

        thumb_data = metadata_helpers.getShowImage(thumb_url)

        result = self._write_image(thumb_data, file_path)

        if not result:
            return False

        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            cur_ep.hastbn = True

        return True

    def save_fanart(self, show_obj, which=None):
        """
        Downloads a fanart image and saves it to the filename specified by fanart_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download fanart
        """

        # use the default fanart name
        fanart_path = self.get_fanart_path(show_obj)

        fanart_data = self._retrieve_show_image('fanart', show_obj, which)

        if not fanart_data:
            logging.debug("No fanart image was retrieved, unable to write fanart")
            return False

        return self._write_image(fanart_data, fanart_path)

    def save_poster(self, show_obj, which=None):
        """
        Downloads a poster image and saves it to the filename specified by poster_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download a poster
        """

        # use the default poster name
        poster_path = self.get_poster_path(show_obj)

        poster_data = self._retrieve_show_image('poster', show_obj, which)

        if not poster_data:
            logging.debug("No show poster image was retrieved, unable to write poster")
            return False

        return self._write_image(poster_data, poster_path)

    def save_banner(self, show_obj, which=None):
        """
        Downloads a banner image and saves it to the filename specified by banner_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download a banner
        """

        # use the default banner name
        banner_path = self.get_banner_path(show_obj)

        banner_data = self._retrieve_show_image('banner', show_obj, which)

        if not banner_data:
            logging.debug("No show banner image was retrieved, unable to write banner")
            return False

        return self._write_image(banner_data, banner_path)

    def save_season_posters(self, show_obj, season):
        """
        Saves all season posters to disk for the given show.

        show_obj: a TVShow object for which to save the season thumbs

        Cycles through all seasons and saves the season posters if possible. This
        method should not need to be overridden by implementing classes, changing
        _season_posters_dict and get_season_poster_path should be good enough.
        """

        season_dict = self._season_posters_dict(show_obj, season)
        result = []

        # Returns a nested dictionary of season art with the season
        # number as primary key. It's really overkill but gives the option
        # to present to user via ui to pick down the road.
        for cur_season in season_dict:

            cur_season_art = season_dict[cur_season]

            if len(cur_season_art) == 0:
                continue

            # Just grab whatever's there for now
            _, season_url = cur_season_art.popitem()  # @UnusedVariable

            season_poster_file_path = self.get_season_poster_path(show_obj, cur_season)

            if not season_poster_file_path:
                logging.debug("Path for season " + str(cur_season) + " came back blank, skipping this season")
                continue

            seasonData = metadata_helpers.getShowImage(season_url)

            if not seasonData:
                logging.debug("No season poster data available, skipping this season")
                continue

            result = result + [self._write_image(seasonData, season_poster_file_path)]

        if result:
            return all(result)
        else:
            return False

    def save_season_banners(self, show_obj, season):
        """
        Saves all season banners to disk for the given show.

        show_obj: a TVShow object for which to save the season thumbs

        Cycles through all seasons and saves the season banners if possible. This
        method should not need to be overridden by implementing classes, changing
        _season_banners_dict and get_season_banner_path should be good enough.
        """

        season_dict = self._season_banners_dict(show_obj, season)
        result = []

        # Returns a nested dictionary of season art with the season
        # number as primary key. It's really overkill but gives the option
        # to present to user via ui to pick down the road.
        for cur_season in season_dict:

            cur_season_art = season_dict[cur_season]

            if len(cur_season_art) == 0:
                continue

            # Just grab whatever's there for now
            _, season_url = cur_season_art.popitem()  # @UnusedVariable

            season_banner_file_path = self.get_season_banner_path(show_obj, cur_season)

            if not season_banner_file_path:
                logging.debug("Path for season " + str(cur_season) + " came back blank, skipping this season")
                continue

            seasonData = metadata_helpers.getShowImage(season_url)

            if not seasonData:
                logging.debug("No season banner data available, skipping this season")
                continue

            result = result + [self._write_image(seasonData, season_banner_file_path)]

        if result:
            return all(result)
        else:
            return False

    def save_season_all_poster(self, show_obj, which=None):
        # use the default season all poster name
        poster_path = self.get_season_all_poster_path(show_obj)

        poster_data = self._retrieve_show_image('poster', show_obj, which)

        if not poster_data:
            logging.debug("No show poster image was retrieved, unable to write season all poster")
            return False

        return self._write_image(poster_data, poster_path)

    def save_season_all_banner(self, show_obj, which=None):
        # use the default season all banner name
        banner_path = self.get_season_all_banner_path(show_obj)

        banner_data = self._retrieve_show_image('banner', show_obj, which)

        if not banner_data:
            logging.debug("No show banner image was retrieved, unable to write season all banner")
            return False

        return self._write_image(banner_data, banner_path)

    def _write_image(self, image_data, image_path, obj=None):
        """
        Saves the data in image_data to the location image_path. Returns True/False
        to represent success or failure.

        image_data: binary image data to write to file
        image_path: file location to save the image to
        """

        # don't bother overwriting it
        if ek(os.path.isfile, image_path):
            logging.debug("Image already exists, not downloading")
            return False

        image_dir = ek(os.path.dirname, image_path)

        if not image_data:
            logging.debug("Unable to retrieve image to save in %s, skipping" % image_path)
            return False

        try:
            if not ek(os.path.isdir, image_dir):
                logging.debug("Metadata dir didn't exist, creating it at " + image_dir)
                ek(os.makedirs, image_dir)
                helpers.chmodAsParent(image_dir)

            outFile = ek(io.open, image_path, 'wb')
            outFile.write(image_data)
            outFile.close()
            helpers.chmodAsParent(image_path)
        except IOError as e:
            logging.error(
                    "Unable to write image to " + image_path + " - are you sure the show folder is writable? {}".format(
                        ex(e)))
            return False

        return True

    def _retrieve_show_image(self, image_type, show_obj, which=None):
        """
        Gets an image URL from theTVDB.com and TMDB.com, downloads it and returns the data.

        image_type: type of image to retrieve (currently supported: fanart, poster, banner)
        show_obj: a TVShow object to use when searching for the image
        which: optional, a specific numbered poster to look for

        Returns: the binary image data if available, or else None
        """
        image_url = None
        indexer_lang = show_obj.lang

        try:
            # There's gotta be a better way of doing this but we don't wanna
            # change the language value elsewhere
            lINDEXER_API_PARMS = sickbeard.indexerApi(show_obj.indexer).api_params.copy()

            lINDEXER_API_PARMS[b'banners'] = True

            if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
                lINDEXER_API_PARMS[b'language'] = indexer_lang

            if show_obj.dvdorder != 0:
                lINDEXER_API_PARMS[b'dvdorder'] = True

            t = sickbeard.indexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)
            indexer_show_obj = t[show_obj.indexerid]
        except (sickbeard.indexer_error, IOError) as e:
            logging.warning("Unable to look up show on " + sickbeard.indexerApi(
                    show_obj.indexer).name + ", not downloading images: {}".format(ex(e)))
            logging.debug("Indexer " + sickbeard.indexerApi(
                show_obj.indexer).name + "maybe experiencing some problems. Try again later")
            return None

        if image_type not in ('fanart', 'poster', 'banner', 'poster_thumb', 'banner_thumb'):
            logging.error("Invalid image type " + str(image_type) + ", couldn't find it in the " + sickbeard.indexerApi(
                    show_obj.indexer).name + " object")
            return None

        if image_type == 'poster_thumb':
            if getattr(indexer_show_obj, 'poster', None):
                image_url = re.sub('posters', '_cache/posters', indexer_show_obj[b'poster'])
            if not image_url:
                # Try and get images from Fanart.TV
                image_url = self._retrieve_show_images_from_fanart(show_obj, image_type)
            if not image_url:
                # Try and get images from TMDB
                image_url = self._retrieve_show_images_from_tmdb(show_obj, image_type)
        elif image_type == 'banner_thumb':
            if getattr(indexer_show_obj, 'banner', None):
                image_url = re.sub('graphical', '_cache/graphical', indexer_show_obj[b'banner'])
            if not image_url:
                # Try and get images from Fanart.TV
                image_url = self._retrieve_show_images_from_fanart(show_obj, image_type)
        else:
            if getattr(indexer_show_obj, image_type, None):
                image_url = indexer_show_obj[image_type]
            if not image_url:
                # Try and get images from Fanart.TV
                image_url = self._retrieve_show_images_from_fanart(show_obj, image_type)
            if not image_url:
                # Try and get images from TMDB
                image_url = self._retrieve_show_images_from_tmdb(show_obj, image_type)

        if image_url:
            image_data = metadata_helpers.getShowImage(image_url, which)
            return image_data

        return None

    def _season_posters_dict(self, show_obj, season):
        """
        Should return a dict like:

        result = {<season number>:
                    {1: '<url 1>', 2: <url 2>, ...},}
        """

        # This holds our resulting dictionary of season art
        result = {}

        indexer_lang = show_obj.lang

        try:
            # There's gotta be a better way of doing this but we don't wanna
            # change the language value elsewhere
            lINDEXER_API_PARMS = sickbeard.indexerApi(show_obj.indexer).api_params.copy()

            lINDEXER_API_PARMS[b'banners'] = True

            if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
                lINDEXER_API_PARMS[b'language'] = indexer_lang

            if show_obj.dvdorder != 0:
                lINDEXER_API_PARMS[b'dvdorder'] = True

            t = sickbeard.indexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)
            indexer_show_obj = t[show_obj.indexerid]
        except (sickbeard.indexer_error, IOError) as e:
            logging.warning("Unable to look up show on " + sickbeard.indexerApi(
                    show_obj.indexer).name + ", not downloading images: {}".format(ex(e)))
            logging.debug("Indexer " + sickbeard.indexerApi(
                show_obj.indexer).name + "maybe experiencing some problems. Try again later")
            return result

        # if we have no season banners then just finish
        if not getattr(indexer_show_obj, '_banners', None):
            return result

        if 'season' not in indexer_show_obj[b'_banners'] or 'season' not in indexer_show_obj[b'_banners'][b'season']:
            return result

        # Give us just the normal poster-style season graphics
        seasonsArtObj = indexer_show_obj[b'_banners'][b'season'][b'season']

        # Returns a nested dictionary of season art with the season
        # number as primary key. It's really overkill but gives the option
        # to present to user via ui to pick down the road.

        result[season] = {}

        # find the correct season in the TVDB object and just copy the dict into our result dict
        for seasonArtID in seasonsArtObj.keys():
            if int(seasonsArtObj[seasonArtID][b'season']) == season and seasonsArtObj[seasonArtID][
                'language'] == sickbeard.INDEXER_DEFAULT_LANGUAGE:
                result[season][seasonArtID] = seasonsArtObj[seasonArtID][b'_bannerpath']

        return result

    def _season_banners_dict(self, show_obj, season):
        """
        Should return a dict like:

        result = {<season number>:
                    {1: '<url 1>', 2: <url 2>, ...},}
        """

        # This holds our resulting dictionary of season art
        result = {}

        indexer_lang = show_obj.lang

        try:
            # There's gotta be a better way of doing this but we don't wanna
            # change the language value elsewhere
            lINDEXER_API_PARMS = sickbeard.indexerApi(show_obj.indexer).api_params.copy()

            lINDEXER_API_PARMS[b'banners'] = True

            if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
                lINDEXER_API_PARMS[b'language'] = indexer_lang

            t = sickbeard.indexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)
            indexer_show_obj = t[show_obj.indexerid]
        except (sickbeard.indexer_error, IOError) as e:
            logging.warning("Unable to look up show on " + sickbeard.indexerApi(
                    show_obj.indexer).name + ", not downloading images: {}".format(ex(e)))
            logging.debug("Indexer " + sickbeard.indexerApi(
                show_obj.indexer).name + "maybe experiencing some problems. Try again later")
            return result

        # if we have no season banners then just finish
        if not getattr(indexer_show_obj, '_banners', None):
            return result

        # if we have no season banners then just finish
        if 'season' not in indexer_show_obj[b'_banners'] or 'seasonwide' not in indexer_show_obj[b'_banners'][b'season']:
            return result

        # Give us just the normal season graphics
        seasonsArtObj = indexer_show_obj[b'_banners'][b'season'][b'seasonwide']

        # Returns a nested dictionary of season art with the season
        # number as primary key. It's really overkill but gives the option
        # to present to user via ui to pick down the road.

        result[season] = {}

        # find the correct season in the TVDB object and just copy the dict into our result dict
        for seasonArtID in seasonsArtObj.keys():
            if int(seasonsArtObj[seasonArtID][b'season']) == season and seasonsArtObj[seasonArtID][
                'language'] == sickbeard.INDEXER_DEFAULT_LANGUAGE:
                result[season][seasonArtID] = seasonsArtObj[seasonArtID][b'_bannerpath']

        return result

    def retrieveShowMetadata(self, folder):
        """
        Used only when mass adding Existing Shows, using previously generated Show metadata to reduce the need to query TVDB.
        """

        empty_return = (None, None, None)

        metadata_path = ek(os.path.join, folder, self._show_metadata_filename)

        if not ek(os.path.isdir, folder) or not ek(os.path.isfile, metadata_path):
            logging.debug("Can't load the metadata file from " + metadata_path + ", it doesn't exist")
            return empty_return

        try:
            logging.debug("Loading show info from metadata file in {}".format(folder))
        except:
            pass

        try:
            with ek(io.open, metadata_path, 'rb') as xmlFileObj:
                showXML = etree.ElementTree(file=xmlFileObj)

            if showXML.findtext('title') is None or (
                    showXML.findtext('tvdbid') is None and showXML.findtext('id') is None):
                logging.info("Invalid info in tvshow.nfo (missing name or id): %s %s %s" % (
                showXML.findtext('title'), showXML.findtext('tvdbid'), showXML.findtext('id')))
                return empty_return

            name = showXML.findtext('title')

            if showXML.findtext('tvdbid') is not None:
                indexer_id = int(showXML.findtext('tvdbid'))
            elif showXML.findtext('id') is not None:
                indexer_id = int(showXML.findtext('id'))
            else:
                logging.warning("Empty <id> or <tvdbid> field in NFO, unable to find a ID")
                return empty_return

            if indexer_id is None:
                logging.warning("Invalid Indexer ID (" + str(indexer_id) + "), not using metadata file")
                return empty_return

            indexer = None
            if showXML.find('episodeguide/url') is not None:
                epg_url = showXML.findtext('episodeguide/url').lower()
                if str(indexer_id) in epg_url:
                    if 'thetvdb.com' in epg_url:
                        indexer = 1
                    elif 'tvrage' in epg_url:
                        logging.warning("Invalid Indexer ID (" + str(
                            indexer_id) + "), not using metadata file because it has TVRage info")
                        return empty_return

        except Exception as e:
            logging.warning(
                    "There was an error parsing your existing metadata file: '" + metadata_path + "' error: {}".format(
                        ex(e)))
            return empty_return

        return indexer_id, name, indexer

    def _retrieve_show_images_from_tmdb(self, show, img_type):
        types = {'poster': 'poster_path',
                 'banner': None,
                 'fanart': 'backdrop_path',
                 'poster_thumb': 'poster_path',
                 'banner_thumb': None}

        # get TMDB configuration info
        tmdb = TMDB(sickbeard.TMDB_API_KEY)
        config = tmdb.Configuration()
        response = config.info()
        base_url = response[b'images'][b'base_url']
        sizes = response[b'images'][b'poster_sizes']

        def size_str_to_int(x):
            return float("inf") if x == 'original' else int(x[1:])

        max_size = max(sizes, key=size_str_to_int)

        try:
            search = tmdb.Search()
            for show_name in set(allPossibleShowNames(show)):
                for result in search.collection({'query': show_name})['results'] + search.tv({'query': show_name})[
                    'results']:
                    if types[img_type] and getattr(result, types[img_type]):
                        return "{0}{1}{2}".format(base_url, max_size, result[types[img_type]])

        except Exception:
            pass

        logging.info("Could not find any " + img_type + " images on TMDB for " + show.name)

    def _retrieve_show_images_from_fanart(self, show, img_type, thumb=False):
        types = {
            'poster': fanart.TYPE.TV.POSTER,
            'banner': fanart.TYPE.TV.BANNER,
            'poster_thumb': fanart.TYPE.TV.POSTER,
            'banner_thumb': fanart.TYPE.TV.BANNER,
            'fanart': fanart.TYPE.TV.BACKGROUND,
        }

        try:
            indexerid = helpers.mapIndexersToShow(show)[1]
            if indexerid:
                request = fanartRequest(
                        apikey=sickbeard.FANART_API_KEY,
                        id=indexerid,
                        ws=fanart.WS.TV,
                        type=types[img_type],
                        sort=fanart.SORT.POPULAR,
                        limit=fanart.LIMIT.ONE,
                )

                resp = request.response()
                url = resp[types[img_type]][0][b'url']
                if thumb:
                    url = re.sub('/fanart/', '/preview/', url)
                return url
        except Exception:
            pass

        logging.info("Could not find any " + img_type + " images on Fanart.tv for " + show.name)
