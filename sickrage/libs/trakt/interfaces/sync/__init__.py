from __future__ import absolute_import, division, print_function

from trakt.core.helpers import deprecated, popitems
from trakt.interfaces.base import Interface, authenticated
# Import child interfaces
from trakt.interfaces.sync.collection import SyncCollectionInterface
from trakt.interfaces.sync.history import SyncHistoryInterface
from trakt.interfaces.sync.playback import SyncPlaybackInterface
from trakt.interfaces.sync.ratings import SyncRatingsInterface
from trakt.interfaces.sync.watched import SyncWatchedInterface
from trakt.interfaces.sync.watchlist import SyncWatchlistInterface

__all__ = (
    'SyncInterface',
    'SyncCollectionInterface',
    'SyncHistoryInterface',
    'SyncPlaybackInterface',
    'SyncRatingsInterface',
    'SyncWatchedInterface',
    'SyncWatchlistInterface'
)


class SyncInterface(Interface):
    path = 'sync'

    @authenticated
    def last_activities(self, **kwargs):
        return self.get_data(
            self.http.get(
                'last_activities',
                **popitems(kwargs, [
                    'authenticated',
                    'validate_token'
                ])
            ),
            **kwargs
        )

    @deprecated("Trakt['sync'].playback() has been moved to Trakt['sync/playback'].get()")
    def playback(self, store=None, **kwargs):
        raise NotImplementedError()
