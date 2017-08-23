from __future__ import absolute_import, division, print_function

from trakt.objects.core.helpers import update_attributes
from trakt.objects.list.base import List


class CustomList(List):
    def __init__(self, client, keys, username=None):
        super(CustomList, self).__init__(client, keys)

        self.username = username
        """
        :type: :class:`~python:str`

        Author username
        """

        self.privacy = None
        """
        :type: :class:`~python:str`

        Privacy mode

        **Possible values:**
         - :code:`private`
         - :code:`friends`
         - :code:`public`
        """

    def _update(self, info=None):
        if not info:
            return

        super(CustomList, self)._update(info)

        update_attributes(self, info, [
            'privacy'
        ])

        # Update with user details
        user = info.get('user', {})

        if user.get('username'):
            self.username = user['username']

    @classmethod
    def _construct(cls, client, keys, info, **kwargs):
        if not info:
            return None

        l = cls(client, keys, **kwargs)
        l._update(info)
        return l

    def items(self, **kwargs):
        """Retrieve list items.

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Current list items
        :rtype: :class:`~python:list` of :class:`trakt.objects.media.Media`
        """

        return self._client['users/*/lists/*'].items(self.username, self.id, **kwargs)

    #
    # Owner actions
    #

    def add(self, items, **kwargs):
        """Add specified items to the list.

        :param items: Items that should be added to the list
        :type items: :class:`~python:list`

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Response
        :rtype: :class:`~python:dict`
        """

        return self._client['users/*/lists/*'].add(self.username, self.id, items, **kwargs)

    def delete(self, **kwargs):
        """Delete the list.

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Boolean to indicate if the request was successful
        :rtype: :class:`~python:bool`
        """

        return self._client['users/*/lists/*'].delete(self.username, self.id, **kwargs)

    def update(self, **kwargs):
        """Update the list with the current object attributes.

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Boolean to indicate if the request was successful
        :rtype: :class:`~python:bool`
        """

        item = self._client['users/*/lists/*'].update(self.username, self.id, return_type='data', **kwargs)

        if not item:
            return False

        self._update(item)
        return True

    def remove(self, items, **kwargs):
        """Remove specified items from the list.

        :param items: Items that should be removed from the list
        :type items: :class:`~python:list`

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Response
        :rtype: :class:`~python:dict`
        """

        return self._client['users/*/lists/*'].remove(self.username, self.id, items, **kwargs)

    #
    # Actions
    #

    def like(self, **kwargs):
        """Like the list.

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Boolean to indicate if the request was successful
        :rtype: :class:`~python:bool`
        """

        return self._client['users/*/lists/*'].like(self.username, self.id, **kwargs)

    def unlike(self, **kwargs):
        """Un-like the list.

        :param kwargs: Extra request options
        :type kwargs: :class:`~python:dict`

        :return: Boolean to indicate if the request was successful
        :rtype: :class:`~python:bool`
        """

        return self._client['users/*/lists/*'].unlike(self.username, self.id, **kwargs)
