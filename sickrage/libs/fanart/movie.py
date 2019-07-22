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



from . import TYPE, WS
from .immutable import Immutable
from .items import LeafItem, ResourceItem

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
    KEY = TYPE.MOVIE.DISC

    @Immutable.mutablemethod
    def __init__(self, id, url, likes, lang, disc, disc_type):
        super(DiscItem, self).__init__(id, url, likes, lang)
        self.disc = int(disc)
        self.disc_type = disc_type


class ArtItem(MovieItem):
    KEY = TYPE.MOVIE.ART


class LogoItem(MovieItem):
    KEY = TYPE.MOVIE.LOGO


class PosterItem(MovieItem):
    KEY = TYPE.MOVIE.POSTER


class BackgroundItem(MovieItem):
    KEY = TYPE.MOVIE.BACKGROUND


class HdLogoItem(MovieItem):
    KEY = TYPE.MOVIE.HDLOGO


class HdArtItem(MovieItem):
    KEY = TYPE.MOVIE.HDART


class BannerItem(MovieItem):
    KEY = TYPE.MOVIE.BANNER


class ThumbItem(MovieItem):
    KEY = TYPE.MOVIE.THUMB


class Movie(ResourceItem):
    WS = WS.MOVIE

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
