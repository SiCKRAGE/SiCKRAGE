from __future__ import absolute_import, division, print_function

import requests
from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class ShowsInterface(Interface):
    path = 'shows'

    def get(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), query={
            'extended': extended
        })

        item = self.get_data(response, **kwargs)

        if isinstance(item, requests.Response):
            return item

        return SummaryMapper.show(self.client, item)

    def played(self, extended=None, **kwargs):
        response = self.http.get('played', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.shows(self.client, items)

    def watched(self, extended=None, **kwargs):
        response = self.http.get('watched', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.shows(self.client, items)

    def collected(self, extended=None, **kwargs):
        response = self.http.get('collected', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.shows(self.client, items)

    def anticipated(self, extended=None, **kwargs):
        response = self.http.get('anticipated', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.shows(self.client, items)

    def popular(self, extended=None, **kwargs):
        response = self.http.get('popular', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.shows(self.client, items)

    def trending(self, extended=None, **kwargs):
        response = self.http.get('trending', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.shows(self.client, items)

    def next_episode(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), 'next_episode', query={
            'extended': extended
        })

        item = self.get_data(response, **kwargs)

        if isinstance(item, requests.Response):
            return item

        return SummaryMapper.episode(self.client, item)

    def last_episode(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), 'last_episode', query={
            'extended': extended
        })

        item = self.get_data(response, **kwargs)

        if isinstance(item, requests.Response):
            return item

        return SummaryMapper.episode(self.client, item)

    def seasons(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), [
            'seasons'
        ], query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.seasons(self.client, items)

    def season(self, id, season, extended=None, **kwargs):
        response = self.http.get(str(id), [
            'seasons', str(season)
        ], query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.episodes(self.client, items)

    def episode(self, id, season, episode, extended=None, **kwargs):
        response = self.http.get(str(id), [
            'seasons', str(season),
            'episodes', str(episode)
        ], query={
            'extended': extended
        })

        item = self.get_data(response, **kwargs)

        if isinstance(item, requests.Response):
            return item

        return SummaryMapper.episode(self.client, item)
