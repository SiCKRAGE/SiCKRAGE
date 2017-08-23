from __future__ import absolute_import, division, print_function

import requests
from trakt.interfaces.base import Interface


class AuthInterface(Interface):
    path = 'auth'

    def login(self, login, password, **kwargs):
        response = self.http.post('login', data={
            'login': login,
            'password': password
        })

        data = self.get_data(response, **kwargs)

        if isinstance(data, requests.Response):
            return data

        if not data:
            return None

        return data.get('token')

    def logout(self):
        pass
