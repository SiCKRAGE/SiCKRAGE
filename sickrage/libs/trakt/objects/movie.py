from __future__ import absolute_import, division, print_function

from trakt.core.helpers import from_iso8601_datetime, to_iso8601_datetime, \
    from_iso8601_date, to_iso8601_date, deprecated
from trakt.objects.core.helpers import update_attributes
from trakt.objects.video import Video


class Movie(Video):
    def __init__(self, client, keys, index=None):
        super(Movie, self).__init__(client, keys, index)

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

        self.watchers = None  # trending
        """
        :type: :class:`~python:int`

        Number of active watchers (returned by the :code:`Trakt['movies'].trending()`
        and :code:`Trakt['shows'].trending()` methods)
        """

        self.tagline = None
        """
        :type: :class:`~python:str`

        Tagline
        """

        self.released = None
        """
        :type: :class:`~python:datetime.date`

        Release date
        """

        self.runtime = None
        """
        :type: :class:`~python:int`

        Duration (in minutes)
        """

        self.certification = None
        """
        :type: :class:`~python:str`

        Content certification (e.g :code:`PG-13`)
        """

        self.updated_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Updated date/time
        """

        self.homepage = None
        """
        :type: :class:`~python:str`

        Homepage URL
        """

        self.trailer = None
        """
        :type: :class:`~python:str`

        Trailer URL
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

    def to_identifier(self):
        """Return the movie identifier which is compatible with requests that require movie definitions.

        :return: Movie identifier/definition
        :rtype: :class:`~python:dict`
        """

        return {
            'ids': dict(self.keys),
            'title': self.title,
            'year': self.year
        }

    @deprecated('Movie.to_info() has been moved to Movie.to_dict()')
    def to_info(self):
        """**Deprecated:** use the :code:`to_dict()` method instead."""
        return self.to_dict()

    def to_dict(self):
        """Dump movie to a dictionary.

        :return: Movie dictionary
        :rtype: :class:`~python:dict`
        """

        result = self.to_identifier()

        result.update({
            'watched': 1 if self.is_watched else 0,
            'collected': 1 if self.is_collected else 0,

            'plays': self.plays if self.plays is not None else 0,
            'in_watchlist': self.in_watchlist if self.in_watchlist is not None else 0,
            'progress': self.progress,

            'last_watched_at': to_iso8601_datetime(self.last_watched_at),
            'collected_at': to_iso8601_datetime(self.collected_at),
            'paused_at': to_iso8601_datetime(self.paused_at)
        })

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601_datetime(self.rating.timestamp)

        # Extended Info
        if self.released:
            result['released'] = to_iso8601_date(self.released)

        if self.updated_at:
            result['updated_at'] = to_iso8601_datetime(self.updated_at)

        if self.overview:
            result['overview'] = self.overview

        if self.tagline:
            result['tagline'] = self.tagline

        if self.runtime:
            result['runtime'] = self.runtime

        if self.certification:
            result['certification'] = self.certification

        if self.homepage:
            result['homepage'] = self.homepage

        if self.trailer:
            result['trailer'] = self.trailer

        if self.language:
            result['language'] = self.language

        if self.available_translations:
            result['available_translations'] = self.available_translations

        if self.genres:
            result['genres'] = self.genres

        return result

    def _update(self, info=None, **kwargs):
        if not info:
            return

        super(Movie, self)._update(info, **kwargs)

        update_attributes(self, info, [
            'title',

            # Trending
            'watchers',

            # Extended Info
            'tagline',
            'certification',
            'homepage',
            'trailer',
            'language',
            'available_translations',
            'genres'
        ])

        # Ensure `year` attribute is an integer (fixes incorrect type returned by search)
        if info.get('year'):
            self.year = int(info['year'])

        # Extended Info
        if info.get('runtime'):
            self.runtime = info['runtime']

        if 'released' in info:
            self.released = from_iso8601_date(info.get('released'))

        if 'updated_at' in info:
            self.updated_at = from_iso8601_datetime(info.get('updated_at'))

    @classmethod
    def _construct(cls, client, keys, info, index=None, **kwargs):
        movie = cls(client, keys, index=index)
        movie._update(info, **kwargs)

        return movie

    def __repr__(self):
        return '<Movie %r (%s)>' % (self.title, self.year)
