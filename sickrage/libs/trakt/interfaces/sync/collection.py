from __future__ import absolute_import, division, print_function

from trakt.interfaces.sync.core.mixins import Get, Add, Remove


class SyncCollectionInterface(Get, Add, Remove):
    path = 'sync/collection'
    flags = {'is_collected': True}

    def get(self, media=None, store=None, params=None, **kwargs):
        if media is None:
            raise ValueError('Invalid value provided for the "media" parameter')

        return super(SyncCollectionInterface, self).get(
            media=media,
            store=store,
            params=params,
            **kwargs
        )
