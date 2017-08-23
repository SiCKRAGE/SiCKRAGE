from __future__ import absolute_import, division, print_function

from trakt.interfaces.base import authenticated
from trakt.interfaces.sync.core.mixins import Get, Add, Remove


class SyncWatchlistInterface(Get, Add, Remove):
    path = 'sync/watchlist'
    flags = {'in_watchlist': True}

    def get(self, media=None, page=1, per_page=10, start_at=None, end_at=None, store=None, **kwargs):
        # Build query
        query = {}

        if page:
            query['page'] = page

        if per_page:
            query['limit'] = per_page

        # Request watched history
        return super(SyncWatchlistInterface, self).get(
            media, store,
            query=query,
            flat=media is None,
            **kwargs
        )

    @authenticated
    def seasons(self, store=None, **kwargs):
        return self.get(
            'seasons',
            store,
            **kwargs
        )

    @authenticated
    def episodes(self, store=None, **kwargs):
        return self.get(
            'episodes',
            store,
            **kwargs
        )
