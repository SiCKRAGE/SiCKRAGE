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
    'CharacterItem',
    'ArtItem',
    'LogoItem',
    'BackgroundItem',
    'SeasonItem',
    'ThumbItem',
    'HdLogoItem',
    'HdArtItem',
    'PosterItem',
    'BannerItem',
    'TvShow',
)


class TvItem(LeafItem):
    @Immutable.mutablemethod
    def __init__(self, id, url, likes, lang):
        super(TvItem, self).__init__(id, url, likes)
        self.lang = lang


class SeasonedTvItem(TvItem):
    @Immutable.mutablemethod
    def __init__(self, id, url, likes, lang, season):
        super(SeasonedTvItem, self).__init__(id, url, likes, lang)
        self.season = 0 if season == 'all' else int(season or 0)


class CharacterItem(TvItem):
    KEY = TYPE.TV.CHARACTER


class ArtItem(TvItem):
    KEY = TYPE.TV.ART


class LogoItem(TvItem):
    KEY = TYPE.TV.LOGO


class BackgroundItem(SeasonedTvItem):
    KEY = TYPE.TV.BACKGROUND


class SeasonItem(SeasonedTvItem):
    KEY = TYPE.TV.SEASONTHUMB


class ThumbItem(TvItem):
    KEY = TYPE.TV.THUMB


class HdLogoItem(TvItem):
    KEY = TYPE.TV.HDLOGO


class HdArtItem(TvItem):
    KEY = TYPE.TV.HDART


class PosterItem(TvItem):
    KEY = TYPE.TV.POSTER


class BannerItem(TvItem):
    KEY = TYPE.TV.BANNER


class TvShow(ResourceItem):
    WS = WS.TV

    @Immutable.mutablemethod
    def __init__(self, name, tvdbid, backgrounds, characters, arts, logos, seasons, thumbs, hdlogos, hdarts, posters,
                 banners):
        self.name = name
        self.tvdbid = tvdbid
        self.backgrounds = backgrounds
        self.characters = characters
        self.arts = arts
        self.logos = logos
        self.seasons = seasons
        self.thumbs = thumbs
        self.hdlogos = hdlogos
        self.hdarts = hdarts
        self.posters = posters
        self.banners = banners

    @classmethod
    def from_dict(cls, resource):
        assert len(resource) == 1, 'Bad Format Map'
        name, resource = resource.items()[0]
        return cls(
            name=name,
            tvdbid=resource['thetvdb_id'],
            backgrounds=BackgroundItem.extract(resource),
            characters=CharacterItem.extract(resource),
            arts=ArtItem.extract(resource),
            logos=LogoItem.extract(resource),
            seasons=SeasonItem.extract(resource),
            thumbs=ThumbItem.extract(resource),
            hdlogos=HdLogoItem.extract(resource),
            hdarts=HdArtItem.extract(resource),
            posters=PosterItem.extract(resource),
            banners=BannerItem.extract(resource),
        )
