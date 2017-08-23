from __future__ import absolute_import, division, print_function

import requests
from trakt.core.helpers import clean_username
from trakt.interfaces.base import Interface
# Import child interfaces
from trakt.interfaces.users.lists.list_ import UsersListInterface  # noqa: I100
from trakt.mapper import ListMapper

__all__ = (
    'UsersListsInterface',
    'UsersListInterface'
)


class UsersListsInterface(Interface):
    path = 'users/*/lists'

    def create(self, username, name, description=None, privacy='private',
               display_numbers=False, allow_comments=True, **kwargs):
        data = {
            'name': name,
            'description': description,

            'privacy': privacy,
            'allow_comments': allow_comments,
            'display_numbers': display_numbers
        }

        # Remove attributes with `None` values
        for key in list(data.keys()):
            if data[key] is not None:
                continue

            del data[key]

        # Send request
        response = self.http.post(
            '/users/%s/lists' % username,
            data=data
        )

        # Parse response
        item = self.get_data(response, **kwargs)

        if isinstance(item, requests.Response):
            return item

        if not item:
            return None

        # Map item to list object
        return ListMapper.custom_list(
            self.client, item,
            username=username
        )

    def get(self, username, **kwargs):
        if kwargs.get('parse') is False:
            raise ValueError('Parse can\'t be disabled on this method')

        # Send request
        response = self.http.get(
            '/users/%s/lists' % clean_username(username),
        )

        # Parse response
        items = self.get_data(response, **kwargs)

        if not items:
            return

        # Map items to list objects
        for item in items:
            yield ListMapper.custom_list(
                self.client, item,
                username=username
            )
