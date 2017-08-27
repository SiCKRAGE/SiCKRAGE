from __future__ import absolute_import, division, print_function

from trakt.core.helpers import popitems
from trakt.interfaces.base import Interface, authenticated, application


class ScrobbleInterface(Interface):
    path = 'scrobble'

    @application
    @authenticated
    def action(self, action, movie=None, show=None, episode=None, progress=0.0, **kwargs):
        """Perform scrobble action.

        :param action: Action to perform (either :code:`start`, :code:`pause` or :code:`stop`)
        :type action: :class:`~python:str`

        :param movie: Movie definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Guardians of the Galaxy',
                    'year': 2014,

                    'ids': {
                        'tmdb': 118340
                    }
                }

        :type movie: :class:`~python:dict`

        :param show: Show definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Breaking Bad',
                    'year': 2008,

                    'ids': {
                        'tvdb': 81189
                    }
                }


        :type show: :class:`~python:dict`

        :param episode: Episode definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    "season": 3,
                    "number": 11
                }

        :type episode: :class:`~python:dict`

        :param progress: Current movie/episode progress percentage
        :type progress: :class:`~python:float`

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Response (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'action': 'start',
                    'progress': 1.25,

                    'sharing': {
                        'facebook': true,
                        'twitter': true,
                        'tumblr': false
                    },

                    'movie': {
                        'title': 'Guardians of the Galaxy',
                        'year': 2014,

                        'ids': {
                            'trakt': 28,
                            'slug': 'guardians-of-the-galaxy-2014',
                            'imdb': 'tt2015381',
                            'tmdb': 118340
                        }
                    }
                }

        :rtype: :class:`~python:dict`
        """
        if movie and (show or episode):
            raise ValueError('Only one media type should be provided')

        if not movie and not episode:
            raise ValueError('Missing media item')

        data = {
            'progress': progress,
            'app_version': kwargs.pop('app_version', self.client.version),
            'app_date': kwargs.pop('app_date', None)
        }

        if movie:
            # TODO validate
            data['movie'] = movie
        elif episode:
            if show:
                data['show'] = show

            # TODO validate
            data['episode'] = episode

        response = self.http.post(
            action,
            data=data,
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        return self.get_data(response, **kwargs)

    @application
    @authenticated
    def start(self, movie=None, show=None, episode=None, progress=0.0, **kwargs):
        """Send the scrobble "start" action.

        Use this method when the video initially starts playing or is un-paused. This will
        remove any playback progress if it exists.

        **Note:** A watching status will auto expire after the remaining runtime has elapsed.
        There is no need to re-send every 15 minutes.

        :param movie: Movie definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Guardians of the Galaxy',
                    'year': 2014,

                    'ids': {
                        'tmdb': 118340
                    }
                }

        :type movie: :class:`~python:dict`

        :param show: Show definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Breaking Bad',
                    'year': 2008,

                    'ids': {
                        'tvdb': 81189
                    }
                }


        :type show: :class:`~python:dict`

        :param episode: Episode definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    "season": 3,
                    "number": 11
                }

        :type episode: :class:`~python:dict`

        :param progress: Current movie/episode progress percentage
        :type progress: :class:`~python:float`

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Response (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'action': 'start',
                    'progress': 1.25,

                    'sharing': {
                        'facebook': true,
                        'twitter': true,
                        'tumblr': false
                    },

                    'movie': {
                        'title': 'Guardians of the Galaxy',
                        'year': 2014,

                        'ids': {
                            'trakt': 28,
                            'slug': 'guardians-of-the-galaxy-2014',
                            'imdb': 'tt2015381',
                            'tmdb': 118340
                        }
                    }
                }

        :rtype: :class:`~python:dict`
        """
        return self.action(
            'start',
            movie, show, episode,
            progress,

            **kwargs
        )

    @application
    @authenticated
    def pause(self, movie=None, show=None, episode=None, progress=0.0, **kwargs):
        """Send the scrobble "pause' action.

        Use this method when the video is paused. The playback progress will be saved and
        :code:`Trakt['sync/playback'].get()` can be used to resume the video from this exact
        position. Un-pause a video by calling the :code:`Trakt['scrobble'].start()` method again.

        :param movie: Movie definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Guardians of the Galaxy',
                    'year': 2014,

                    'ids': {
                        'tmdb': 118340
                    }
                }

        :type movie: :class:`~python:dict`

        :param show: Show definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Breaking Bad',
                    'year': 2008,

                    'ids': {
                        'tvdb': 81189
                    }
                }


        :type show: :class:`~python:dict`

        :param episode: Episode definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    "season": 3,
                    "number": 11
                }

        :type episode: :class:`~python:dict`

        :param progress: Current movie/episode progress percentage
        :type progress: :class:`~python:float`

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Response (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'action': 'pause',
                    'progress': 75,

                    'sharing': {
                        'facebook': true,
                        'twitter': true,
                        'tumblr': false
                    },

                    'movie': {
                        'title': 'Guardians of the Galaxy',
                        'year': 2014,

                        'ids': {
                            'trakt': 28,
                            'slug': 'guardians-of-the-galaxy-2014',
                            'imdb': 'tt2015381',
                            'tmdb': 118340
                        }
                    }
                }

        :rtype: :class:`~python:dict`
        """
        return self.action(
            'pause',
            movie, show, episode,
            progress,

            **kwargs
        )

    @application
    @authenticated
    def stop(self, movie=None, show=None, episode=None, progress=0.0, **kwargs):
        """Send the scrobble "stop" action.

        Use this method when the video is stopped or finishes playing on its own. If the
        progress is above 80%, the video will be scrobbled and the :code:`action` will be set
        to **scrobble**.

        If the progress is less than 80%, it will be treated as a *pause* and the :code:`action`
        will be set to **pause**. The playback progress will be saved and :code:`Trakt['sync/playback'].get()`
        can be used to resume the video from this exact position.

        **Note:** If you prefer to use a threshold higher than 80%, you should use :code:`Trakt['scrobble'].pause()`
        yourself so it doesn't create duplicate scrobbles.

        :param movie: Movie definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Guardians of the Galaxy',
                    'year': 2014,

                    'ids': {
                        'tmdb': 118340
                    }
                }

        :type movie: :class:`~python:dict`

        :param show: Show definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'title': 'Breaking Bad',
                    'year': 2008,

                    'ids': {
                        'tvdb': 81189
                    }
                }


        :type show: :class:`~python:dict`

        :param episode: Episode definition (or `None`)

            **Example:**

            .. code-block:: python

                {
                    "season": 3,
                    "number": 11
                }

        :type episode: :class:`~python:dict`

        :param progress: Current movie/episode progress percentage
        :type progress: :class:`~python:float`

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Response (or `None`)

            **Example:**

            .. code-block:: python

                {
                    'action': 'scrobble',
                    'progress': 99.9,

                    'sharing': {
                        'facebook': true,
                        'twitter': true,
                        'tumblr': false
                    },

                    'movie': {
                        'title': 'Guardians of the Galaxy',
                        'year': 2014,

                        'ids': {
                            'trakt': 28,
                            'slug': 'guardians-of-the-galaxy-2014',
                            'imdb': 'tt2015381',
                            'tmdb': 118340
                        }
                    }
                }

        :rtype: :class:`~python:dict`
        """
        return self.action(
            'stop',
            movie, show, episode,
            progress,

            **kwargs
        )
