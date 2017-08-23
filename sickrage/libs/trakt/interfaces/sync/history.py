from __future__ import absolute_import, division, print_function

from trakt.core.helpers import to_iso8601_datetime
from trakt.interfaces.base import authenticated
from trakt.interfaces.sync.core.mixins import Get, Add, Remove


class SyncHistoryInterface(Get, Add, Remove):
    path = 'sync/history'
    flags = {'is_watched': True}

    def get(self, media=None, id=None, page=1, per_page=10, start_at=None, end_at=None, store=None, **kwargs):
        if not media and id:
            raise ValueError('The "id" parameter also requires the "media" parameter to be defined')

        # Build parameters
        params = []

        if id:
            params.append(id)

        # Build query
        query = {}

        if page:
            query['page'] = page

        if per_page:
            query['limit'] = per_page

        if start_at:
            query['start_at'] = to_iso8601_datetime(start_at)

        if end_at:
            query['end_at'] = to_iso8601_datetime(end_at)

        # Request watched history
        return super(SyncHistoryInterface, self).get(
            media, store, params,
            query=query,
            flat=True,
            **kwargs
        )

    @authenticated
    def shows(self, *args, **kwargs):
        return self.get(
            'shows',
            *args,
            **kwargs
        )

    @authenticated
    def movies(self, *args, **kwargs):
        return self.get(
            'movies',
            *args,
            **kwargs
        )
