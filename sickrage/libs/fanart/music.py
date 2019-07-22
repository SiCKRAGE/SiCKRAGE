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
from .items import LeafItem, ResourceItem, CollectableItem

__all__ = (
    'BackgroundItem',
    'CoverItem',
    'LogoItem',
    'ThumbItem',
    'DiscItem',
    'Artist',
    'Album',
)


class BackgroundItem(LeafItem):
    KEY = TYPE.MUSIC.BACKGROUND


class CoverItem(LeafItem):
    KEY = TYPE.MUSIC.COVER


class LogoItem(LeafItem):
    KEY = TYPE.MUSIC.LOGO


class ThumbItem(LeafItem):
    KEY = TYPE.MUSIC.THUMB


class DiscItem(LeafItem):
    KEY = TYPE.MUSIC.DISC

    @Immutable.mutablemethod
    def __init__(self, id, url, likes, disc, size):
        super(DiscItem, self).__init__(id, url, likes)
        self.disc = int(disc)
        self.size = int(size)


class Artist(ResourceItem):
    WS = WS.MUSIC

    @Immutable.mutablemethod
    def __init__(self, name, mbid, albums, backgrounds, logos, thumbs):
        self.name = name
        self.mbid = mbid
        self.albums = albums
        self.backgrounds = backgrounds
        self.logos = logos
        self.thumbs = thumbs

    @classmethod
    def from_dict(cls, resource):
        assert len(resource) == 1, 'Bad Format Map'
        name, resource = resource.items()[0]
        return cls(
            name=name,
            mbid=resource['mbid_id'],
            albums=Album.collection_from_dict(resource.get('albums', {})),
            backgrounds=BackgroundItem.extract(resource),
            thumbs=ThumbItem.extract(resource),
            logos=LogoItem.extract(resource),
        )


class Album(CollectableItem):

    @Immutable.mutablemethod
    def __init__(self, mbid, covers, arts):
        self.mbid = mbid
        self.covers = covers
        self.arts = arts

    @classmethod
    def from_dict(cls, key, resource):
        return cls(
            mbid=key,
            covers=CoverItem.extract(resource),
            arts=DiscItem.extract(resource),
        )
