from __future__ import absolute_import, division, print_function

import requests
from trakt.core.helpers import clean_username, popitems
from trakt.interfaces.base import Interface, authenticated
from trakt.mapper import ListMapper, ListItemMapper


class UsersListInterface(Interface):
    path = 'users/*/lists/*'

    def get(self, username, id, **kwargs):
        # Send request
        response = self.http.get(
            '/users/%s/lists/%s' % (clean_username(username), id),
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

    def items(self, username, id, **kwargs):
        # Send request
        response = self.http.get(
            '/users/%s/lists/%s/items' % (clean_username(username), id),
        )

        # Parse response
        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        if not items or type(items) is not list:
            return None

        return [
            ListItemMapper.process(self.client, item, index=x + 1)
            for x, item in enumerate(items)
        ]

    #
    # Owner actions
    #

    @authenticated
    def add(self, username, id, items, **kwargs):
        # Send request
        response = self.http.post(
            '/users/%s/lists/%s/items' % (clean_username(username), id),
            data=items,
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        # Parse response
        return self.get_data(response, **kwargs)

    @authenticated
    def delete(self, username, id, **kwargs):
        # Send request
        response = self.http.delete(
            '/users/%s/lists/%s' % (clean_username(username), id),
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        return 200 <= response.status_code < 300

    @authenticated
    def update(self, username, id, name=None, description=None, privacy=None, display_numbers=None,
               allow_comments=None, return_type='object', **kwargs):
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
        response = self.http.put(
            '/users/%s/lists/%s' % (clean_username(username), id),
            data=data,
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        # Parse response
        item = self.get_data(response, **kwargs)

        if isinstance(item, requests.Response):
            return item

        if not item:
            return None

        if return_type == 'data':
            return item

        if return_type == 'object':
            # Map item to list object
            return ListMapper.custom_list(
                self.client, item,
                username=username
            )

        raise ValueError('Unsupported value for "return_type": %r', return_type)

    @authenticated
    def remove(self, username, id, items, **kwargs):
        # Send request
        response = self.http.post(
            '/users/%s/lists/%s/items/remove' % (clean_username(username), id),
            data=items,
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        # Parse response
        return self.get_data(response, **kwargs)

    #
    # Actions
    #

    @authenticated
    def like(self, username, id, **kwargs):
        # Send request
        response = self.http.post(
            '/users/%s/lists/%s/like' % (clean_username(username), id),
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        return 200 <= response.status_code < 300

    @authenticated
    def unlike(self, username, id, **kwargs):
        # Send request
        response = self.http.delete(
            '/users/%s/lists/%s/like' % (clean_username(username), id),
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        return 200 <= response.status_code < 300
