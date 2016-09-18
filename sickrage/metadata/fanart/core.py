import requests
import sickrage.metadata.fanart
from sickrage.metadata.fanart.errors import RequestFanartError, ResponseFanartError


class Request(object):
    def __init__(self, apikey, id, ws, type=None, sort=None, limit=None):
        self._apikey = apikey
        self._id = id
        self._ws = ws
        self._type = type or sickrage.metadata.fanart.TYPE.ALL
        self._sort = sort or sickrage.metadata.fanart.SORT.POPULAR
        self._limit = limit or sickrage.metadata.fanart.LIMIT.ALL
        self.validate()
        self._response = None

    def validate(self):
        for attribute_name in ('ws', 'type', 'sort', 'limit'):
            attribute = getattr(self, '_' + attribute_name)
            choices = getattr(sickrage.metadata.fanart, attribute_name.upper() + '_LIST')
            if attribute not in choices:
                raise RequestFanartError('Not allowed {0}: {1} [{2}]'.format(attribute_name, attribute, ', '.join(choices)))

    def __str__(self):
        return '/'.join(map(str, [
            sickrage.metadata.fanart.BASEURL,
            self._ws,
            self._id,
            sickrage.metadata.fanart.FORMAT.JSON,
            self._type,
            self._sort,
            self._limit,
        ])) + '?api_key={}'.format(self._apikey)

    def response(self):
        try:
            response = requests.get(str(self))
            rjson = response.json()
            if not isinstance(rjson, dict):
                raise Exception(response.text)
            return rjson
        except Exception as e:
            raise ResponseFanartError(str(e))
