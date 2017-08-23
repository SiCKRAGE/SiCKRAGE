from __future__ import absolute_import, division, print_function

from trakt.core.helpers import from_iso8601_datetime


class Rating(object):
    def __init__(self, client, value=None, timestamp=None):
        self._client = client

        self.value = value
        """
        :type: :class:`~python:int`

        Rating value (0 - 10)
        """

        self.timestamp = timestamp
        """
        :type: :class:`~python:datetime.datetime`

        Rating timestamp
        """

    @classmethod
    def _construct(cls, client, info):
        if not info or 'rating' not in info:
            return

        r = cls(client)
        r.value = info.get('rating')
        r.timestamp = from_iso8601_datetime(info.get('rated_at'))
        return r

    def __getstate__(self):
        state = self.__dict__

        if hasattr(self, '_client'):
            del state['_client']

        return state

    def __eq__(self, other):
        if not isinstance(other, Rating):
            return NotImplemented

        return self.value == other.value and self.timestamp == other.timestamp

    def __repr__(self):
        return '<Rating %s/10 (%s)>' % (self.value, self.timestamp)

    def __str__(self):
        return self.__repr__()
