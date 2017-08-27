from __future__ import absolute_import, division, print_function

import requests
from trakt.core.helpers import deprecated
from trakt.helpers import build_url
from trakt.interfaces.base import Interface
# Import child interfaces
from trakt.interfaces.oauth.device import DeviceOAuthInterface  # noqa: I100
from trakt.interfaces.oauth.pin import PinOAuthInterface  # noqa: I100

__all__ = (
    'OAuthInterface',
    'DeviceOAuthInterface',
    'PinOAuthInterface'
)


class OAuthInterface(Interface):
    path = 'oauth'

    def authorize_url(self, redirect_uri, response_type='code', state=None, username=None):
        client_id = self.client.configuration['client.id']

        if not client_id:
            raise ValueError('"client.id" configuration parameter is required to generate the OAuth authorization url')

        return build_url(
            self.client.site_url,
            self.path, 'authorize',

            client_id=client_id,

            redirect_uri=redirect_uri,
            response_type=response_type,
            state=state,
            username=username
        )

    @deprecated("Trakt['oauth'].pin_url() method has been moved to Trakt['oauth/pin'].url()")
    def pin_url(self):
        return self.client['oauth/pin'].url()

    @deprecated("Trakt['oauth'].token() method has been moved to Trakt['oauth'].token_exchange()")
    def token(self, code=None, redirect_uri=None, grant_type='authorization_code'):
        return self.token_exchange(code, redirect_uri, grant_type)

    def token_exchange(self, code=None, redirect_uri=None, grant_type='authorization_code', **kwargs):
        client_id = self.client.configuration['client.id']
        client_secret = self.client.configuration['client.secret']

        if not client_id or not client_secret:
            raise ValueError('"client.id" and "client.secret" configuration parameters are required for token exchange')

        response = self.http.post(
            'token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,

                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': grant_type
            },
            authenticated=False
        )

        data = self.get_data(response, **kwargs)

        if isinstance(data, requests.Response):
            return data

        if not data:
            return None

        return data

    def token_refresh(self, refresh_token=None, redirect_uri=None, grant_type='refresh_token', **kwargs):
        client_id = self.client.configuration['client.id']
        client_secret = self.client.configuration['client.secret']

        if not client_id or not client_secret:
            raise ValueError('"client.id" and "client.secret" configuration parameters are required for token refresh')

        response = self.http.post(
            'token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,

                'refresh_token': refresh_token,
                'redirect_uri': redirect_uri,
                'grant_type': grant_type
            },
            authenticated=False
        )

        data = self.get_data(response, **kwargs)

        if isinstance(data, requests.Response):
            return data

        if not data:
            return None

        return data
