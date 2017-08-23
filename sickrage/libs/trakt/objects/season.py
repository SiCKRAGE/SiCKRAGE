from __future__ import absolute_import, division, print_function

from trakt.core.helpers import to_iso8601_datetime, from_iso8601_datetime, deprecated
from trakt.objects.core.helpers import update_attributes
from trakt.objects.media import Media


class Season(Media):
    def __init__(self, client, keys=None, index=None):
        super(Season, self).__init__(client, keys, index)

        self.show = None
        """
        :type: :class:`trakt.objects.show.Show`

        Show
        """

        self.episodes = {}
        """
        :type: :class:`~python:dict`

        Episodes, defined as :code:`{episode_num: Episode}`

        **Note:** this field might not be available with some methods
        """

        self.first_aired = None
        """
        :type: :class:`~python:datetime.datetime`

        First air date
        """

        self.episode_count = None
        """
        :type: :class:`~python:int`

        Total episode count
        """

        self.aired_episodes = None
        """
        :type: :class:`~python:int`

        Aired episode count
        """

    def to_identifier(self):
        """Return the season identifier which is compatible with requests that require season definitions.

        :return: Season identifier/definition
        :rtype: :class:`~python:dict`
        """

        return {
            'number': self.pk,
            'episodes': [
                episode.to_dict()
                for episode in self.episodes.values()
            ]
        }

    @deprecated('Season.to_info() has been moved to Season.to_dict()')
    def to_info(self):
        """**Deprecated:** use the :code:`to_dict()` method instead."""
        return self.to_dict()

    def to_dict(self):
        """Dump season to a dictionary.

        :return: Season dictionary
        :rtype: :class:`~python:dict`
        """

        result = self.to_identifier()

        result.update({
            'ids': dict([
                (key, value) for (key, value) in self.keys[1:]  # NOTE: keys[0] is the season identifier
            ])
        })

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601_datetime(self.rating.timestamp)

        result['in_watchlist'] = self.in_watchlist if self.in_watchlist is not None else 0

        # Extended Info
        if self.first_aired:
            result['first_aired'] = to_iso8601_datetime(self.first_aired)

        if self.episode_count:
            result['episode_count'] = self.episode_count

        if self.aired_episodes:
            result['aired_episodes'] = self.aired_episodes

        return result

    def _update(self, info=None, **kwargs):
        if not info:
            return

        super(Season, self)._update(info, **kwargs)

        update_attributes(self, info, [
            # Extended Info
            'episode_count',
            'aired_episodes'
        ])

        # Extended Info
        if 'first_aired' in info:
            self.first_aired = from_iso8601_datetime(info.get('first_aired'))

    @classmethod
    def _construct(cls, client, keys, info=None, index=None, **kwargs):
        season = cls(client, keys, index=index)
        season._update(info, **kwargs)

        return season

    def __repr__(self):
        if self.show:
            return '<Season %r - S%02d>' % (self.show.title, self.pk)

        return '<Season S%02d>' % self.pk
