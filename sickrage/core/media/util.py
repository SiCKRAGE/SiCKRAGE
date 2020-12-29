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
import enum
import os

import sickrage
from sickrage.core.caches.image_cache import ImageCache
from sickrage.core.enums import SeriesProviderID
from sickrage.core.media.banner import Banner
from sickrage.core.media.fanart import FanArt
from sickrage.core.media.network import Network
from sickrage.core.media.poster import Poster
from sickrage.core.websession import WebSession


class SeriesImageType(enum.Enum):
    BANNER = 'banner'
    POSTER = 'poster'
    FANART = 'fanart'
    NETWORK = 'network'
    SMALL = 'small'
    BANNER_THUMB = 'banner_thumb'
    POSTER_THUMB = 'poster_thumb'


def series_image(series_id=None, series_provider_id=None, which=None):
    media_format = ('normal', 'thumb')[which in (SeriesImageType.BANNER_THUMB, SeriesImageType.POSTER_THUMB, SeriesImageType.SMALL)]

    if which in (SeriesImageType.BANNER, SeriesImageType.BANNER_THUMB):
        return Banner(series_id, series_provider_id, media_format)
    elif which == SeriesImageType.FANART:
        return FanArt(series_id, series_provider_id, media_format)
    elif which in (SeriesImageType.POSTER, SeriesImageType.POSTER_THUMB):
        return Poster(series_id, series_provider_id, media_format)
    elif which == SeriesImageType.NETWORK:
        return Network(series_id, series_provider_id, media_format)


def series_provider_image(series_id=None, series_provider_id=None, which=None):
    media_format = ('normal', 'thumb')[which in (SeriesImageType.BANNER_THUMB, SeriesImageType.POSTER_THUMB, SeriesImageType.SMALL)]

    if which not in (SeriesImageType.FANART, SeriesImageType.POSTER, SeriesImageType.BANNER, SeriesImageType.BANNER_THUMB, SeriesImageType.POSTER_THUMB):
        sickrage.app.log.error(f"Invalid image type {which}, couldn't find it in the {sickrage.app.series_providers[SeriesProviderID.THETVDB].name} object")
        return

    try:
        image_name = str(id) + '.' + which.value + '.jpg'

        if media_format == "thumb":
            image_path = os.path.join(ImageCache()._thumbnails_dir(), image_name)
            if not os.path.exists(image_path):
                image_data = sickrage.app.series_providers[series_provider_id].images(int(series_id), key_type=which.value)
                if image_data:
                    image_url = image_data[0]['thumbnail']
                    WebSession().download(image_url, image_path)
        else:
            image_path = os.path.join(ImageCache()._cache_dir(), image_name)
            if not os.path.exists(image_path):
                image_data = sickrage.app.series_providers[series_provider_id].images(int(series_id), key_type=which.value)
                if image_data:
                    image_url = image_data[0]['filename']
                    WebSession().download(image_url, image_path)
    except (KeyError, IndexError):
        pass

    if which in [SeriesImageType.BANNER, SeriesImageType.BANNER_THUMB]:
        return Banner(int(series_id), series_provider_id, media_format)
    elif which == SeriesImageType.FANART:
        return FanArt(int(series_id), series_provider_id, media_format)
    elif which in [SeriesImageType.POSTER, SeriesImageType.POSTER_THUMB]:
        return Poster(int(series_id), series_provider_id, media_format)
