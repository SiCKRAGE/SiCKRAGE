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

import sickrage.metadata.fanart
from sickrage.metadata.fanart.items import LeafItem, Immutable, ResourceItem
__all__ = (
    'ArtItem',
    'DiscItem',
    'LogoItem',
    'PosterItem',
    'BackgroundItem',
    'HdLogoItem',
    'HdArtItem',
    'BannerItem',
    'ThumbItem',
    'Movie',
)


class MovieItem(LeafItem):

    @Immutable.mutablemethod
    def __init__(self, id, url, likes, lang):
        super(MovieItem, self).__init__(id, url, likes)
        self.lang = lang


class DiscItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.DISC

    @Immutable.mutablemethod
    def __init__(self, id, url, likes, lang, disc, disc_type):
        super(DiscItem, self).__init__(id, url, likes, lang)
        self.disc = int(disc)
        self.disc_type = disc_type


class ArtItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.ART


class LogoItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.LOGO


class PosterItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.POSTER


class BackgroundItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.BACKGROUND


class HdLogoItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.HDLOGO


class HdArtItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.HDART


class BannerItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.BANNER


class ThumbItem(MovieItem):
    KEY = sickrage.metadata.fanart.TYPE.MOVIE.THUMB


class Movie(ResourceItem):
    WS = sickrage.metadata.fanart.WS.MOVIE

    @Immutable.mutablemethod
    def __init__(self, name, imdbid, tmdbid, arts, logos, discs, posters, backgrounds, hdlogos, hdarts,
                 banners, thumbs):
        self.name = name
        self.imdbid = imdbid
        self.tmdbid = tmdbid
        self.arts = arts
        self.posters = posters
        self.logos = logos
        self.discs = discs
        self.backgrounds = backgrounds
        self.hdlogos = hdlogos
        self.hdarts = hdarts
        self.banners = banners
        self.thumbs = thumbs

    @classmethod
    def from_dict(cls, resource):
        assert len(resource) == 1, 'Bad Format Map'
        name, resource = resource.items()[0]
        return cls(
            name=name,
            imdbid=resource['imdb_id'],
            tmdbid=resource['tmdb_id'],
            arts=ArtItem.extract(resource),
            logos=LogoItem.extract(resource),
            discs=DiscItem.extract(resource),
            posters=PosterItem.extract(resource),
            backgrounds=BackgroundItem.extract(resource),
            hdlogos=HdLogoItem.extract(resource),
            hdarts=HdArtItem.extract(resource),
            banners=BannerItem.extract(resource),
            thumbs=ThumbItem.extract(resource),
        )
