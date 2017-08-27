from __future__ import absolute_import, division, print_function

from trakt.core.helpers import from_iso8601_datetime
from trakt.objects.core.helpers import update_attributes
from trakt.objects.rating import Rating


class Media(object):
    def __init__(self, client, keys=None, index=None):
        self._client = client

        self.keys = keys
        """
        :type: :class:`~python:list` of :class:`~python:tuple`

        Keys (for imdb, tvdb, etc..), defined as:

        ..code-block::

            [
                (<service>, <id>)
            ]

        """

        self.index = index
        """
        :type: :class:`~python:int`

        Playlist item index
        """

        self.images = None
        """
        :type: :class:`~python:dict`

        Images (or `None`), defined as:

        .. code-block:: python

            {
                <type>: {
                    <size>: <url>
                }
            }

        +------------------+----------------+---------------------------------------+
        | Type             | Size           | Dimensions                            |
        +==================+================+=======================================+
        | :code:`banner`   | :code:`full`   | 1000x185 (movie/show), 758x140 (show) |
        +------------------+----------------+---------------------------------------+
        | :code:`clearart` | :code:`full`   | 1000x562                              |
        +------------------+----------------+---------------------------------------+
        | :code:`fanart`   | :code:`full`   | 1920x1080 (typical), 1280x720         |
        +------------------+----------------+---------------------------------------+
        |                  | :code:`medium` | 1280x720                              |
        +------------------+----------------+---------------------------------------+
        |                  | :code:`thumb`  | 853x480                               |
        +------------------+----------------+---------------------------------------+
        | :code:`logo`     | :code:`full`   | 800x310                               |
        +------------------+----------------+---------------------------------------+
        | :code:`poster`   | :code:`full`   | 1000x1500                             |
        +------------------+----------------+---------------------------------------+
        |                  | :code:`medium` | 600x900                               |
        +------------------+----------------+---------------------------------------+
        |                  | :code:`thumb`  | 300x450                               |
        +------------------+----------------+---------------------------------------+
        | :code:`thumb`    | :code:`full`   | 1000x562 (movie), 500x281 (show)      |
        +------------------+----------------+---------------------------------------+

        """

        self.overview = None
        """
        :type: :class:`~python:str`

        Overview (or `None`)
        """

        self.rating = None
        """
        :type: :class:`~python:int`

        Community rating (0 - 10) (or `None`)
        """

        self.votes = None
        """
        :type: :class:`~python:int`

        Community votes (0 - 10) (or `None`)
        """

        self.score = None
        """
        :type: :class:`~python:float`

        Search score (or `None`)
        """

        # Flags
        self.in_watchlist = None
        """
        :type: :class:`~python:bool`

        Flag indicating this item is in your watchlist (or `None`)
        """

        # Timestamps
        self.listed_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was added to the list (or `None`)
        """

    @property
    def pk(self):
        """Retrieve the primary key (unique identifier for the item).

        Provides the following identifiers (by media type):
         - **movie:** imdb
         - **show:** tvdb
         - **season:** tvdb
         - **episode:** tvdb
         - **custom_list:** trakt
         - **person:** tmdb

        :return: :code:`(<service>, <value>)` or :code:`None` if no primary key is available
        :rtype: :class:`~python:tuple`
        """
        if not self.keys:
            return None

        return self.keys[0]

    def get_key(self, service):
        for k_service, k_value in self.keys:
            if k_service == service:
                return k_value

        return None

    def _update(self, info=None, in_watchlist=None, **kwargs):
        if not info:
            return

        update_attributes(self, info, [
            # Extended Info
            'overview',

            # Search
            'score'
        ])

        if 'images' in info:
            self.images = info['images']

        # Set timestamps
        if 'listed_at' in info:
            self.listed_at = from_iso8601_datetime(info.get('listed_at'))

        # Set flags
        if in_watchlist is not None:
            self.in_watchlist = in_watchlist

        self.rating = Rating._construct(self._client, info) or self.rating

    def __getstate__(self):
        state = self.__dict__

        if hasattr(self, '_client'):
            del state['_client']

        return state

    def __str__(self):
        return self.__repr__()
