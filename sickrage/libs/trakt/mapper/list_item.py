from __future__ import absolute_import, division, print_function

from trakt.mapper.core.base import Mapper


class ListItemMapper(Mapper):
    @classmethod
    def process(cls, client, item, media=None, **kwargs):
        if media is None:
            # Retrieve `media` from `item`
            media = item.get('type')

        if not media:
            return ValueError()

        # Find function for `media`
        func = getattr(cls, media, None)

        if not func:
            raise ValueError('Unknown media type: %r', media)

        # Map item
        return func(client, item, **kwargs)

    @classmethod
    def movie(cls, client, item, **kwargs):
        if 'movie' in item:
            i_movie = item['movie']
        else:
            i_movie = item

        # Retrieve item keys
        pk, keys = cls.get_ids('movie', i_movie)

        if pk is None:
            return None

        # Create object
        movie = cls.construct(client, 'movie', i_movie, keys, **kwargs)

        if 'movie' in item:
            movie._update(item)

        return movie

    @classmethod
    def list(cls, client, item, **kwargs):
        return None

    @classmethod
    def officiallist(cls, client, item, **kwargs):
        return None

    @classmethod
    def person(cls, client, item, **kwargs):
        if 'person' in item:
            i_person = item['person']
        else:
            i_person = item

        # Retrieve item keys
        pk, keys = cls.get_ids('person', i_person)

        if pk is None:
            return None

        # Create object
        person = cls.construct(client, 'person', i_person, keys, **kwargs)

        # Update with root info
        if 'person' in item:
            person._update(item)

        return person

    @classmethod
    def show(cls, client, item, **kwargs):
        if 'show' in item:
            i_show = item['show']
        else:
            i_show = item

        # Retrieve item keys
        pk, keys = cls.get_ids('show', i_show)

        if pk is None:
            return None

        # Create object
        show = cls.construct(client, 'show', i_show, keys, **kwargs)

        # Update with root info
        if 'show' in item:
            show._update(item)

        return show

    @classmethod
    def seasons(cls, client, items, **kwargs):
        return [cls.season(client, item, **kwargs) for item in items]

    @classmethod
    def season(cls, client, item, **kwargs):
        if 'season' in item:
            i_season = item['season']
        else:
            i_season = item

        # Retrieve item keys
        pk, keys = cls.get_ids('season', i_season)

        if pk is None:
            return None

        # Create object
        season = cls.construct(client, 'season', i_season, keys, **kwargs)

        if 'show' in item:
            season.show = cls.show(client, item['show'])

        return season

    @classmethod
    def episodes(cls, client, items, **kwargs):
        return [cls.episode(client, item, **kwargs) for item in items]

    @classmethod
    def episode(cls, client, item, **kwargs):
        if 'episode' in item:
            i_episode = item['episode']
        else:
            i_episode = item

        # Retrieve item keys
        pk, keys = cls.get_ids('episode', i_episode)

        if pk is None:
            return None

        # Create object
        episode = cls.construct(client, 'episode', i_episode, keys, **kwargs)

        if 'show' in item:
            episode.show = cls.show(client, item['show'])

        if 'season' in item:
            episode.season = cls.season(client, item['season'])

        # Update with root info
        if 'episode' in item:
            episode._update(item)

        return episode
