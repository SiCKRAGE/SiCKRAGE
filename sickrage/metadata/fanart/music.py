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
from sickrage.metadata.fanart.items import Immutable, LeafItem, ResourceItem, CollectableItem

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
    KEY = sickrage.metadata.fanart.TYPE.MUSIC.BACKGROUND


class CoverItem(LeafItem):
    KEY = sickrage.metadata.fanart.TYPE.MUSIC.COVER


class LogoItem(LeafItem):
    KEY = sickrage.metadata.fanart.TYPE.MUSIC.LOGO


class ThumbItem(LeafItem):
    KEY = sickrage.metadata.fanart.TYPE.MUSIC.THUMB


class DiscItem(LeafItem):
    KEY = sickrage.metadata.fanart.TYPE.MUSIC.DISC

    @Immutable.mutablemethod
    def __init__(self, id, url, likes, disc, size):
        super(DiscItem, self).__init__(id, url, likes)
        self.disc = int(disc)
        self.size = int(size)


class Artist(ResourceItem):
    WS = sickrage.metadata.fanart.WS.MUSIC

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
