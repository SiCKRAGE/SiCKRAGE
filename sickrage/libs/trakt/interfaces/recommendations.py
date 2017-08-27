from __future__ import absolute_import, division, print_function

import requests
from trakt.interfaces.base import Interface, authenticated
from trakt.mapper.summary import SummaryMapper


class RecommendationsInterface(Interface):
    path = 'recommendations'

    @authenticated
    def shows(self, extended=None, **kwargs):
        response = self.http.get('shows', query={
            'extended': extended
        })

        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        return SummaryMapper.shows(self.client, items)