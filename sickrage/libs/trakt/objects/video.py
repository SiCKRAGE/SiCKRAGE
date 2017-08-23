from __future__ import absolute_import, division, print_function

from trakt.core.helpers import from_iso8601_datetime
from trakt.objects.core.helpers import update_attributes
from trakt.objects.media import Media


class Video(Media):
    def __init__(self, client, keys=None, index=None):
        super(Video, self).__init__(client, keys, index)

        self.action = None
        """
        :type: :class:`~python:str`

        Item action (e.g. history action: "checkin", "scrobble" or "watch")
        """

        self.id = None
        """
        :type: :class:`~python:long`

        Item id (e.g. history id)
        """

        self.last_watched_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was last watched (or `None`)
        """

        self.collected_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was added to your collection (or `None`)
        """

        self.paused_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was paused (or `None`)
        """

        self.watched_at = None
        """
        :type: :class:`~python:datetime.datetime`

        Timestamp of when this item was watched (or `None`)
        """

        self.plays = None
        """
        :type: :class:`~python:int`

        Number of plays (or `None`)
        """

        self.progress = None
        """
        :type: :class:`~python:float`

        Playback progress for item (or `None`)
        """

        # Flags
        self.is_watched = None
        """
        :type: :class:`~python:bool`

        Flag indicating this item has been watched (or `None`)
        """

        self.is_collected = None
        """
        :type: :class:`~python:bool`

        Flag indicating this item has been collected (or `None`)
        """

    def _update(self, info=None, is_watched=None, is_collected=None, **kwargs):
        if not info:
            return

        super(Video, self)._update(info, **kwargs)

        update_attributes(self, info, [
            'plays',
            'progress'
        ])

        if 'action' in info:
            self.action = info.get('action')

        if 'id' in info:
            self.id = info.get('id')

        # Set timestamps
        if 'last_watched_at' in info:
            self.last_watched_at = from_iso8601_datetime(info.get('last_watched_at'))

        if 'collected_at' in info:
            self.collected_at = from_iso8601_datetime(info.get('collected_at'))

        if 'paused_at' in info:
            self.paused_at = from_iso8601_datetime(info.get('paused_at'))

        if 'watched_at' in info:
            self.watched_at = from_iso8601_datetime(info.get('watched_at'))

        # Set flags
        if is_watched is not None:
            self.is_watched = is_watched

        if is_collected is not None:
            self.is_collected = is_collected
