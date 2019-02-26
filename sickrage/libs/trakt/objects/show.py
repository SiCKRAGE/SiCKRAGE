from __future__ import absolute_import, division, print_function

from trakt.core.helpers import from_iso8601_datetime, to_iso8601_datetime, deprecated
from trakt.objects.core.helpers import update_attributes
from trakt.objects.media import Media


class Show(Media):
    def __init__(self, client, keys, index=None):
        super(Show, self).__init__(client, keys, index)

        self.title = None
        """
        :type: :class:`~python:str`

        Title
        """

        self.year = None
        """
        :type: :class:`~python:int`

        Year
        """

        self.seasons = {}
        """
        :type: :class:`~python:dict`

        Seasons, defined as :code:`{season_num: Season}`

        **Note:** this field might not be available with some methods
        """

        self.watchers = None
        """
        :type: :class:`~python:int`

        Number of active watchers (returned by the :code:`Trakt['movies'].trending()`
        and :code:`Trakt['shows'].trending()` methods)
        """

        self.first_aired = None
        """
        :type: :class:`~python:datetime.datetime`

        First air date
        """

        self.airs = None
        """
        :type: :class:`~python:dict`

        Dictionary with day, time and timezone in which the show airs
        """

        self.runtime = None
        """
        :type: :class:`~python:int`

        Duration (in minutes)
        """

        self.certification = None
        """
        :type: :class:`~python:str`

        Content certification (e.g :code:`TV-MA`)
        """

        self.network = None
        """
        :type: :class:`~python:str`

        Network in which the show is aired
        """

        self.country = None
        """
        :type: :class:`~python:str`

        Country in which the show is aired
        """

        self.updated_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Updated date/time
        """

        self.status = None
        """
        :type: :class:`~python:str`

        Value of :code:`returning series` (airing right now),
        :code:`in production` (airing soon), :code:`planned` (in development),
        :code:`canceled`, or :code:`ended`
        """

        self.homepage = None
        """
        :type: :class:`~python:str`

        Homepage URL
        """

        self.language = None
        """
        :type: :class:`~python:str`

        Language (for title, overview, etc..)
        """

        self.available_translations = None
        """
        :type: :class:`~python:list`

        Available translations (for title, overview, etc..)
        """

        self.genres = None
        """
        :type: :class:`~python:list`

        Genres
        """

        self.aired_episodes = None
        """
        :type: :class:`~python:int`

        Aired episode count
        """

        self.ids = None
        """
        :type: :class:`~python:dict`

        Show IDs
        """

    def episodes(self):
        """Return a flat episode iterator.

        :returns: Iterator :code:`((season_num, episode_num), Episode)`
        :rtype: iterator
        """

        for sk, season in self.seasons.items():
            # Yield each episode in season
            for ek, episode in season.episodes.items():
                yield (sk, ek), episode

    def to_identifier(self):
        """Return the show identifier which is compatible with requests that require show definitions.

        :return: Show identifier/definition
        :rtype: :class:`~python:dict`
        """

        return {
            'ids': dict(self.keys),
            'title': self.title,
            'year': self.year
        }

    @deprecated('Show.to_info() has been moved to Show.to_dict()')
    def to_info(self):
        """**Deprecated:** use the :code:`to_dict()` method instead."""
        return self.to_dict()

    def to_dict(self):
        """Dump show to a dictionary.

        :return: Show dictionary
        :rtype: :class:`~python:dict`
        """

        result = self.to_identifier()

        result['seasons'] = [
            season.to_dict()
            for season in self.seasons.values()
        ]

        result['in_watchlist'] = self.in_watchlist if self.in_watchlist is not None else 0

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601_datetime(self.rating.timestamp)

        if self.votes:
            result['votes'] = self.votes

        # Extended Info
        if self.first_aired:
            result['first_aired'] = to_iso8601_datetime(self.first_aired)

        if self.updated_at:
            result['updated_at'] = to_iso8601_datetime(self.updated_at)

        if self.overview:
            result['overview'] = self.overview

        if self.airs:
            result['airs'] = self.airs

        if self.runtime:
            result['runtime'] = self.runtime

        if self.certification:
            result['certification'] = self.certification

        if self.network:
            result['network'] = self.network

        if self.country:
            result['country'] = self.country

        if self.status:
            result['status'] = self.status

        if self.homepage:
            result['homepage'] = self.homepage

        if self.language:
            result['language'] = self.language

        if self.available_translations:
            result['available_translations'] = self.available_translations

        if self.genres:
            result['genres'] = self.genres

        if self.aired_episodes:
            result['aired_episodes'] = self.aired_episodes

        return result

    def _update(self, info=None, **kwargs):
        if not info:
            return

        super(Show, self)._update(info, **kwargs)

        update_attributes(self, info, [
            'title',

            # Trending
            'watchers',

            # Extended Info
            'airs',
            'runtime',
            'certification',
            'network',
            'country',
            'status',
            'homepage',
            'language',
            'available_translations',
            'genres',
            'aired_episodes',
            'votes'
        ])

        # Show IDs
        self.ids = dict(self.keys)

        # Ensure `year` attribute is an integer (fixes incorrect type returned by search)
        if info.get('year'):
            self.year = int(info['year'])

        # Extended Info
        if 'first_aired' in info:
            self.first_aired = from_iso8601_datetime(info.get('first_aired'))

        if 'updated_at' in info:
            self.updated_at = from_iso8601_datetime(info.get('updated_at'))

    @classmethod
    def _construct(cls, client, keys, info=None, index=None, **kwargs):
        show = cls(client, keys, index=index)
        show._update(info, **kwargs)

        return show

    def __repr__(self):
        return '<Show %r (%s)>' % (self.title, self.year)
