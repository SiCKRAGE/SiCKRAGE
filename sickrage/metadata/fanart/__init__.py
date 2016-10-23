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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

def values(obj):
    return [v for k, v in obj.__dict__.iteritems() if not k.startswith('_')]

BASEURL = 'http://webservice.fanart.tv/v3'


class FORMAT(object):
    JSON = 'JSON'
    XML = 'XML'
    PHP = 'PHP'


class WS(object):
    MUSIC = 'music'
    MOVIE = 'movies'
    TV = 'tv'


class TYPE(object):
    ALL = 'all'

    class TV(object):
        ART = 'clearart'
        LOGO = 'clearlogo'
        CHARACTER = 'characterart'
        THUMB = 'tvthumb'
        SEASONTHUMB = 'seasonthumb'
        BACKGROUND = 'showbackground'
        HDLOGO = 'hdtvlogo'
        HDART = 'hdclearart'
        POSTER = 'tvposter'
        BANNER = 'tvbanner'

    class MUSIC(object):
        DISC = 'cdart'
        LOGO = 'musiclogo'
        BACKGROUND = 'artistbackground'
        COVER = 'albumcover'
        THUMB = 'artistthumb'

    class MOVIE(object):
        ART = 'movieart'
        LOGO = 'movielogo'
        DISC = 'moviedisc'
        POSTER = 'movieposter'
        BACKGROUND = 'moviebackground'
        HDLOGO = 'hdmovielogo'
        HDART = 'hdmovieclearart'
        BANNER = 'moviebanner'
        THUMB = 'moviethumb'


class SORT(object):
    POPULAR = 1
    NEWEST = 2
    OLDEST = 3


class LIMIT(object):
    ONE = 1
    ALL = 2

FORMAT_LIST = values(FORMAT)
WS_LIST = values(WS)
TYPE_LIST = values(TYPE.MUSIC) + values(TYPE.TV) + values(TYPE.MOVIE) + [TYPE.ALL]
MUSIC_TYPE_LIST = values(TYPE.MUSIC) + [TYPE.ALL]
TV_TYPE_LIST = values(TYPE.TV) + [TYPE.ALL]
MOVIE_TYPE_LIST = values(TYPE.MOVIE) + [TYPE.ALL]
SORT_LIST = values(SORT)
LIMIT_LIST = values(LIMIT)
