# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import json
from urllib.parse import urlencode

import sickrage
from sickrage.core.enums import SeriesProviderID
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class EMBYNotification(NotificationProvider):
    def __init__(self):
        super(EMBYNotification, self).__init__()
        self.name = 'emby'

    def notify_snatch(self, ep_name):
        if sickrage.app.config.emby.notify_on_snatch:
            self._notify_emby(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.emby.notify_on_download:
            self._notify_emby(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.emby.notify_on_subtitle_download:
            self._notify_emby(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.emby.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notify_emby(title + " - " + update_text + new_version)

    def _notify_emby(self, message, host=None, emby_apikey=None):
        """Handles notifying Emby host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        # fill in omitted parameters
        if not host:
            host = sickrage.app.config.emby.host
        if not emby_apikey:
            emby_apikey = sickrage.app.config.emby.apikey

        url = 'http://%s/emby/Notifications/Admin' % (host)
        values = {'Name': 'SiCKRAGE', 'Description': message,
                  'ImageUrl': 'https://www.sickrage.ca/favicon.ico'}
        data = json.dumps(values)

        headers = {
            'X-MediaBrowser-Token': emby_apikey,
            'Content-Type': 'application/json'
        }

        try:
            resp = WebSession().get(url, data=data, headers=headers)
            sickrage.app.log.debug('EMBY: HTTP response: {}'.format(resp.text.replace('\n', '')))
        except Exception as e:
            sickrage.app.log.warning('EMBY: Warning: Couldn\'t contact Emby at {}: {}'.format(url, e))
            return False

        return True

    def test_notify(self, host, emby_apikey):
        return self._notify_emby('This is a test notification from SiCKRAGE', host, emby_apikey)

    def mass_notify_login(self, ipaddress=""):
        if sickrage.app.config.emby.enable:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notify_emby(title + " - " + update_text.format(ipaddress))

    def update_library(self, show=None):
        """Handles updating the Emby Media Server host via HTTP API
        Returns: True for no issue or False if there was an error
        """

        if sickrage.app.config.emby.enable:
            if not sickrage.app.config.emby.host:
                sickrage.app.log.debug('EMBY: No host specified, check your settings')
                return False

            if show:
                if show.series_provider_id == SeriesProviderID.THETVDB:
                    provider = 'tvdb'
                else:
                    sickrage.app.log.warning('EMBY: Series provider unknown')
                    return False
                query = '?%sid=%s' % (provider, show.series_id)
            else:
                query = ''

            url = 'http://%s/emby/Library/Series/Updated%s' % (sickrage.app.config.emby.host, query)
            values = {}
            data = urlencode(values)

            headers = {
                'X-MediaBrowser-Token': sickrage.app.config.emby.apikey,
                'Content-Type': 'application/json'
            }

            try:
                resp = WebSession().get(url, data=data, headers=headers)
                sickrage.app.log.debug('EMBY: HTTP response: ' + resp.text.replace('\n', ''))
            except Exception as e:
                sickrage.app.log.warning('EMBY: Warning: Couldn\'t contact Emby at {}: {}'.format(url, e))
                return False

            return True
