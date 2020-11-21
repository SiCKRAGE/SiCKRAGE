# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import sickrage
from trakt import Trakt


class TraktAPI(object):
    def __init__(self):
        # Set trakt app id
        Trakt.configuration.defaults.app(
            id=sickrage.app.trakt_app_id
        )

        # Set trakt client id/secret
        Trakt.configuration.defaults.client(
            id=sickrage.app.trakt_api_key,
            secret=sickrage.app.trakt_api_secret
        )

        # Bind trakt events
        Trakt.on('oauth.token_refreshed', self.on_token_refreshed)

        Trakt.configuration.defaults.oauth(
            refresh=True
        )

        if sickrage.app.config.trakt.oauth_token:
            Trakt.configuration.defaults.oauth.from_response(
                sickrage.app.config.trakt.oauth_token
            )

    @staticmethod
    def authenticate(pin):
        # Exchange `code` for `access_token`
        sickrage.app.config.trakt.oauth_token = Trakt['oauth'].token_exchange(pin, 'urn:ietf:wg:oauth:2.0:oob')
        if not sickrage.app.config.trakt.oauth_token:
            return False

        sickrage.app.log.debug('Token exchanged - auth: %r' % sickrage.app.config.trakt.oauth_token)
        sickrage.app.config.save()

        return True

    @staticmethod
    def on_token_refreshed(response):
        # OAuth token refreshed, save token for future calls
        sickrage.app.config.trakt.oauth_token = response

        sickrage.app.log.debug('Token refreshed - auth: %r' % sickrage.app.config.trakt.oauth_token)
        sickrage.app.config.save()

    def __getattr__(self, name):
        if hasattr(self, name):
            return super(TraktAPI, self).__getattribute__(name)

        return getattr(Trakt, name)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            return super(TraktAPI, self).__setattr__(name, value)

        setattr(Trakt, name, value)

    def __getitem__(self, key):
        return Trakt[key]


class TraktException(Exception):
    pass


class TraktAuthException(TraktException):
    pass


class TraktServerBusy(TraktException):
    pass
