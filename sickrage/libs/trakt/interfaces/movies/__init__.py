from __future__ import absolute_import, division, print_function

import requests
from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class MoviesInterface(Interface):
    path = 'movies'

    def get(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        # Parse response
        return SummaryMapper.movie(self.client, items)

    def trending(self, extended=None, **kwargs):
        response = self.http.get('trending', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.movies(self.client, items)
