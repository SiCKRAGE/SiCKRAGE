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



import os

import sickrage
from sickrage.core.caches.image_cache import ImageCache
from sickrage.core.media.banner import Banner
from sickrage.core.media.fanart import FanArt
from sickrage.core.media.network import Network
from sickrage.core.media.poster import Poster
from sickrage.core.websession import WebSession
from sickrage.indexers import IndexerApi
from sickrage.indexers.config import INDEXER_TVDB


def showImage(show=None, which=None):
    media_format = ('normal', 'thumb')[which in ('banner_thumb', 'poster_thumb', 'small')]

    if which[0:6] == 'banner':
        return Banner(show, media_format)
    elif which[0:6] == 'fanart':
        return FanArt(show, media_format)
    elif which[0:6] == 'poster':
        return Poster(show, media_format)
    elif which[0:7] == 'network':
        return Network(show, media_format)


def indexerImage(id=None, which=None):
    media_format = ('normal', 'thumb')[which in ('banner_thumb', 'poster_thumb', 'small')]
    image_type = which[0:6]

    if image_type not in ('fanart', 'poster', 'banner'):
        sickrage.app.log.error("Invalid image type " + str(image_type) + ", couldn't find it in the " + IndexerApi(INDEXER_TVDB).name + " object")
        return

    try:
        lINDEXER_API_PARMS = IndexerApi(INDEXER_TVDB).api_params.copy()
        t = IndexerApi(INDEXER_TVDB).indexer(**lINDEXER_API_PARMS)

        image_name = str(id) + '.' + image_type + '.jpg'

        if media_format == "thumb":
            image_path = os.path.join(ImageCache()._thumbnails_dir(), image_name)
            if not os.path.exists(image_path):
                image_data = t.images(int(id), key_type=image_type)
                if image_data:
                    image_url = image_data[0]['thumbnail']
                    WebSession().download(image_url, image_path)
        else:
            image_path = os.path.join(ImageCache()._cache_dir(), image_name)
            if not os.path.exists(image_path):
                image_data = t.images(int(id), key_type=image_type)
                if image_data:
                    image_url = image_data[0]['filename']
                    WebSession().download(image_url, image_path)
    except (KeyError, IndexError):
        pass

    if image_type == 'banner':
        return Banner(int(id), media_format)
    elif image_type == 'fanart':
        return FanArt(int(id), media_format)
    elif image_type == 'poster':
        return Poster(int(id), media_format)