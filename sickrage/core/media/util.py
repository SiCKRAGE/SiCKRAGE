#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

from tornado.escape import url_escape

from sickrage.core.media.banner import Banner
from sickrage.core.media.fanart import FanArt
from sickrage.core.media.network import Network
from sickrage.core.media.poster import Poster


def showImage(show=None, which=None):
    media = None
    media_format = ('normal', 'thumb')[which in ('banner_thumb', 'poster_thumb', 'small')]

    try:
        if which[0:6] == 'banner':
            media = Banner(show, media_format)
        elif which[0:6] == 'fanart':
            media = FanArt(show, media_format)
        elif which[0:6] == 'poster':
            media = Poster(show, media_format)
        elif which[0:7] == 'network':
            media = Network(show, media_format)

        static_url = url_escape(media.get_media, False)
        return static_url
    except:
        pass
