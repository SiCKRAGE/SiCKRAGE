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
import traceback
from urllib.parse import urljoin

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class PushbulletNotification(NotificationProvider):
    def __init__(self):
        super(PushbulletNotification, self).__init__()
        self.name = 'pushbullet'
        self.url = 'https://api.pushbullet.com/v2/'
        self.TEST_EVENT = 'Test'

    def test_notify(self, pushbullet_api):
        sickrage.app.log.debug("Sending a test Pushbullet notification.")
        return self._sendPushbullet(
            pushbullet_api,
            event=self.TEST_EVENT,
            message="Testing Pushbullet settings from SiCKRAGE",
            force=True
        )

    def get_devices(self, pushbullet_api):
        sickrage.app.log.debug("Retrieving Pushbullet device list.")
        headers = {'Content-Type': 'application/json', 'Access-Token': pushbullet_api}

        try:
            return WebSession().get(urljoin(self.url, 'devices'), headers=headers).text
        except Exception:
            sickrage.app.log.debug(
                'Pushbullet authorization failed with exception: %r' % traceback.format_exc())
            return False

    def notify_snatch(self, ep_name):
        if sickrage.app.config.pushbullet.notify_on_snatch:
            self._sendPushbullet(pushbullet_api=None, event=self.notifyStrings[self.NOTIFY_SNATCH] + " : " + ep_name,
                                 message=ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.pushbullet.notify_on_download:
            self._sendPushbullet(pushbullet_api=None, event=self.notifyStrings[self.NOTIFY_DOWNLOAD] + " : " + ep_name,
                                 message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.pushbullet.notify_on_subtitle_download:
            self._sendPushbullet(pushbullet_api=None,
                                 event=self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + " : " + ep_name + " : " + lang,
                                 message=ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.pushbullet.enable:
            self._sendPushbullet(pushbullet_api=None, event=self.notifyStrings[self.NOTIFY_GIT_UPDATE],
                                 message=self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT] + new_version)

    def _sendPushbullet(self, pushbullet_api=None, pushbullet_device=None, event=None, message=None, force=False):
        if not (sickrage.app.config.pushbullet.enable or force):
            return False

        pushbullet_api = pushbullet_api or sickrage.app.config.pushbullet.api_key
        pushbullet_device = pushbullet_device or sickrage.app.config.pushbullet.device

        sickrage.app.log.debug("Pushbullet event: %r" % event)
        sickrage.app.log.debug("Pushbullet message: %r" % message)
        sickrage.app.log.debug("Pushbullet api: %r" % pushbullet_api)
        sickrage.app.log.debug("Pushbullet devices: %r" % pushbullet_device)

        post_data = {
            'title': event,
            'body': message,
            'type': 'note'
        }

        if pushbullet_device:
            post_data['device_iden'] = pushbullet_device.encode('utf8')

        headers = {'Content-Type': 'application/json', 'Access-Token': pushbullet_api}

        try:
            response = WebSession().post(
                urljoin(self.url, 'pushes'),
                data=json.dumps(post_data),
                headers=headers
            )
        except Exception:
            sickrage.app.log.debug('Pushbullet authorization failed with exception: %r' % traceback.format_exc())
            return False

        if response.status_code == 410:
            sickrage.app.log.debug('Pushbullet authorization failed')
            return False

        if not response.ok:
            sickrage.app.log.debug('Pushbullet call failed with error code %r' % response.status_code)
            return False

        sickrage.app.log.debug("Pushbullet response: %r" % response.text)

        if not response.text:
            sickrage.app.log.error("Pushbullet notification failed.")
            return False

        sickrage.app.log.debug("Pushbullet notifications sent.")
        return (True, response.text)[event is self.TEST_EVENT or event is None]
