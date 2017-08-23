from __future__ import absolute_import, division, print_function

from trakt.interfaces.sync.core.mixins import Get


class SyncWatchedInterface(Get):
    path = 'sync/watched'
    flags = {'is_watched': True}

    def get(self, media=None, store=None, params=None, **kwargs):
        if media is None:
            raise ValueError('Invalid value provided for the "media" parameter')

        return super(SyncWatchedInterface, self).get(
            media=media,
            store=store,
            params=params,
            **kwargs
        )
