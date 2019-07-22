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



import json
import os

import requests

from . import Request
from .immutable import Immutable


class LeafItem(Immutable):
    KEY = NotImplemented

    @Immutable.mutablemethod
    def __init__(self, id, url, likes):
        self.id = int(id)
        self.url = url
        self.likes = int(likes)
        self._content = None

    @classmethod
    def from_dict(cls, resource):
        return cls(**dict([(str(k), v) for k, v in resource.items()]))

    @classmethod
    def extract(cls, resource):
        return [cls.from_dict(i) for i in resource.get(cls.KEY, {})]

    @Immutable.mutablemethod
    def content(self):
        if not self._content:
            self._content = requests.get(self.url).content
        return self._content

    def __str__(self):
        return self.url


class ResourceItem(Immutable):
    WS = NotImplemented
    request_cls = Request

    @classmethod
    def from_dict(cls, map):
        raise NotImplementedError

    @classmethod
    def get(cls, id):
        return cls.from_dict(cls.request_cls(
            apikey=os.environ.get('FANART_APIKEY'),
            id=id,
            ws=cls.WS
        ).response())

    def json(self, **kw):
        return json.dumps(
            self,
            default=lambda o: dict([(k, v) for k, v in o.__dict__.items() if not k.startswith('_')]),
            **kw
        )


class CollectableItem(Immutable):
    @classmethod
    def from_dict(cls, key, map):
        raise NotImplementedError

    @classmethod
    def collection_from_dict(cls, map):
        return [cls.from_dict(k, v) for k, v in map.items()]
