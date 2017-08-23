# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from trakt import Trakt

import sickrage


class srTraktAPI(object):
    def __init__(self):
        # Set trakt app id
        Trakt.configuration.defaults.app(
            id=sickrage.srCore.srConfig.TRAKT_APP_ID
        )

        # Set trakt client id/secret
        Trakt.configuration.defaults.client(
            id=sickrage.srCore.srConfig.TRAKT_API_KEY,
            secret=sickrage.srCore.srConfig.TRAKT_API_SECRET
        )

        # Bind trakt events
        Trakt.on('oauth.token_refreshed', self.on_token_refreshed)

    @staticmethod
    def authenticate(pin):
        # Exchange `code` for `access_token`
        sickrage.srCore.srConfig.TRAKT_OAUTH_TOKEN = Trakt['oauth'].token_exchange(pin, 'urn:ietf:wg:oauth:2.0:oob')
        if not sickrage.srCore.srConfig.TRAKT_OAUTH_TOKEN:
            return False

        sickrage.srCore.srLogger.debug('Token exchanged - auth: %r' % sickrage.srCore.srConfig.TRAKT_OAUTH_TOKEN)

        return True

    @staticmethod
    def on_token_refreshed(response):
        # OAuth token refreshed, save token for future calls
        sickrage.srCore.srConfig.TRAKT_OAUTH_TOKEN = response

        sickrage.srCore.srLogger.debug('Token refreshed - auth: %r' % sickrage.srCore.srConfig.TRAKT_OAUTH_TOKEN)

    def __getattr__(self, name):
        if hasattr(self, name):
            return super(srTraktAPI, self).__getattribute__(name)

        return getattr(Trakt, name)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            return super(srTraktAPI, self).__setattr__(name, value)

        setattr(Trakt, name, value)

    def __getitem__(self, key):
        with Trakt.configuration.oauth.from_response(sickrage.srCore.srConfig.TRAKT_OAUTH_TOKEN, refresh=True):
            return Trakt[key]


class traktException(Exception):
    pass


class traktAuthException(traktException):
    pass


class traktServerBusy(traktException):
    pass
