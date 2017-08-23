from __future__ import absolute_import, division, print_function

from trakt.helpers import build_url
from trakt.interfaces.base import Interface


class PinOAuthInterface(Interface):
    path = 'oauth/pin'

    def url(self):
        app_id = self.client.configuration['app.id']

        if not app_id:
            raise ValueError('"app.id" configuration parameter is required to generate the PIN authentication url')

        return build_url(
            self.client.site_url,
            'pin', app_id
        )
