from __future__ import absolute_import, division, print_function

from trakt.mapper.core.base import Mapper


class SummaryMapper(Mapper):
    @classmethod
    def movies(cls, client, items, **kwargs):
        if not items:
            return None

        return [cls.movie(client, item, **kwargs) for item in items]

    @classmethod
    def movie(cls, client, item, **kwargs):
        if not item:
            return None

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

        # Update with root info
        if 'movie' in item:
            movie._update(item)

        return movie

    @classmethod
    def shows(cls, client, items, **kwargs):
        if not items:
            return None

        return [cls.show(client, item, **kwargs) for item in items]

    @classmethod
    def show(cls, client, item, **kwargs):
        if not item:
            return None

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
        if not items:
            return None

        return [cls.season(client, item, **kwargs) for item in items]

    @classmethod
    def season(cls, client, item, **kwargs):
        if not item:
            return None

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

        # Update with root info
        if 'season' in item:
            season._update(item)

        # Process any episodes in the item
        for i_episode in item.get('episodes', []):
            episode_num = i_episode.get('number')

            cls.season_episode(client, season, episode_num, i_episode, **kwargs)

        return season

    @classmethod
    def season_episode(cls, client, season, episode_num, item=None, **kwargs):
        if not item:
            return

        # Construct episode
        episode = cls.episode(client, item, **kwargs)
        episode.show = season.show
        episode.season = season

        # Store episode in `season`
        season.episodes[episode_num] = episode

    @classmethod
    def episodes(cls, client, items, **kwargs):
        if not items:
            return None

        return [cls.episode(client, item, **kwargs) for item in items]

    @classmethod
    def episode(cls, client, item, parse_show=False, **kwargs):
        if not item:
            return None

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

        if parse_show:
            episode.show = cls.show(client, item)

        # Update with root info
        if 'episode' in item:
            episode._update(item)

        return episode
