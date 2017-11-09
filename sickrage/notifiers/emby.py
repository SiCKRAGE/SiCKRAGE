# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

import json
import urllib
import urllib2

import sickrage
from sickrage.notifiers import Notifiers


class EMBYNotifier(Notifiers):
    def __init__(self):
        super(EMBYNotifier, self).__init__()
        self.name = 'emby'

    def _notify_emby(self, message, host=None, emby_apikey=None):
        """Handles notifying Emby host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        # fill in omitted parameters
        if not host:
            host = sickrage.app.config.emby_host
        if not emby_apikey:
            emby_apikey = sickrage.app.config.emby_apikey

        url = 'http://%s/emby/Notifications/Admin' % (host)
        values = {'Name': 'SiCKRAGE', 'Description': message,
                  'ImageUrl': 'https://www.sickrage.ca/favicon.ico'}
        data = json.dumps(values)
        try:
            req = urllib2.Request(url, data)
            req.add_header('X-MediaBrowser-Token', emby_apikey)
            req.add_header('Content-Type', 'application/json')

            response = urllib2.urlopen(req)
            result = response.read()
            response.close()

            sickrage.app.log.debug('EMBY: HTTP response: ' + result.replace('\n', ''))
            return True

        except (urllib2.URLError, IOError) as e:
            sickrage.app.log.warning('EMBY: Warning: Couldn\'t contact Emby at ' + url + ' ' + e)
            return False


            ##############################################################################
            # Public functions
            ##############################################################################

    def test_notify(self, host, emby_apikey):
        return self._notify_emby('This is a test notification from SiCKRAGE', host, emby_apikey)

    def update_library(self, show=None):
        """Handles updating the Emby Media Server host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        if sickrage.app.config.use_emby:

            if not sickrage.app.config.emby_host:
                sickrage.app.log.debug('EMBY: No host specified, check your settings')
                return False

            if show:
                if show.indexer == 1:
                    provider = 'tvdb'
                elif show.indexer == 2:
                    sickrage.app.log.warning('EMBY: TVRage Provider no longer valid')
                    return False
                else:
                    sickrage.app.log.warning('EMBY: Provider unknown')
                    return False
                query = '?%sid=%s' % (provider, show.indexerid)
            else:
                query = ''

            url = 'http://%s/emby/Library/Series/Updated%s' % (sickrage.app.config.emby_host, query)
            values = {}
            data = urllib.urlencode(values)
            try:
                req = urllib2.Request(url, data)
                req.add_header('X-MediaBrowser-Token', sickrage.app.config.emby_apikey)

                response = urllib2.urlopen(req)
                result = response.read()
                response.close()

                sickrage.app.log.debug('EMBY: HTTP response: ' + result.replace('\n', ''))
                return True

            except (urllib2.URLError, IOError) as e:
                sickrage.app.log.warning('EMBY: Warning: Couldn\'t contact Emby at ' + url + ' ' + e)
                return False
