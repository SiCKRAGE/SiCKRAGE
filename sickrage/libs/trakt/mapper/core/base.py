from __future__ import absolute_import, division, print_function

from trakt.objects import Movie, Show, Episode, Season, CustomList, Comment, Person

IDENTIFIERS = {
    'movie': [
        'imdb',
        'tmdb',

        'slug',
        'trakt'
    ],
    'show': [
        'tvdb',
        'tmdb',
        'imdb',
        'tvrage',

        'slug',
        'trakt'
    ],
    'season': [
        'tvdb',
        'tmdb',

        'trakt'
    ],
    'episode': [
        'tvdb',
        'tmdb',
        'imdb',
        'tvrage',

        'trakt'
    ],
    'custom_list': [
        'trakt',
        'slug'
    ],
    'person': [
        'tmdb',
        'imdb',
        'tvrage',

        'slug',
        'trakt'
    ]
}


class Mapper(object):
    @staticmethod
    def get_ids(media, item, parent=None):
        if not item:
            return None, []

        ids = item.get('ids', {})

        keys = []
        for key in IDENTIFIERS.get(media, []):
            value = ids.get(key)

            if not value:
                continue

            keys.append((key, str(value)))

        if media == 'season' and 'number' in item:
            keys.insert(0, item.get('number'))

        if media == 'episode':
            # Special seasons are typically represented as Season '0'
            # so using a simple 'or' condition to use parent will result
            # in an attribute error if parent is None
            season_no = item.get('season')
            if season_no is None and parent is not None:
                season_no = parent.pk

            keys.insert(0, (
                season_no,
                item.get('number')
            ))

        if media == 'comment':
            keys.insert(0, ('trakt', item.get('id')))

        if not len(keys):
            return None, []

        return keys[0], keys

    @classmethod
    def construct(cls, client, media, item, keys=None, **kwargs):
        if keys is None:
            __, keys = cls.get_ids(media, item)

        if media == 'movie':
            return Movie._construct(client, keys, item, **kwargs)

        if media == 'show':
            return Show._construct(client, keys, item, **kwargs)

        if media == 'season':
            return Season._construct(client, keys, item, **kwargs)

        if media == 'episode':
            return Episode._construct(client, keys, item, **kwargs)

        if media == 'comment':
            return Comment._construct(client, keys, item, **kwargs)

        if media == 'custom_list':
            return CustomList._construct(client, keys, item, **kwargs)

        if media == 'person':
            return Person._construct(client, keys, item, **kwargs)

        raise ValueError('Unknown media type provided')
