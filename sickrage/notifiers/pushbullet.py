#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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
import traceback

import sickrage
from sickrage.core.common import NOTIFY_DOWNLOAD, NOTIFY_GIT_UPDATE, \
    NOTIFY_GIT_UPDATE_TEXT, NOTIFY_SNATCH, NOTIFY_SUBTITLE_DOWNLOAD, \
    notifyStrings
from sickrage.notifiers import srNotifiers


class PushbulletNotifier(srNotifiers):
    TEST_EVENT = 'Test'

    def test_notify(self, pushbullet_api):
        sickrage.srCore.srLogger.debug("Sending a test Pushbullet notification.")
        return self._sendPushbullet(pushbullet_api, event=self.TEST_EVENT,
                                    message="Testing Pushbullet settings from SiCKRAGE")

    def get_devices(self, pushbullet_api):
        sickrage.srCore.srLogger.debug("Testing Pushbullet authentication and retrieving the device list.")
        return self._sendPushbullet(pushbullet_api)

    def _notify_snatch(self, ep_name):
        if sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONSNATCH:
            self._sendPushbullet(pushbullet_api=None, event=notifyStrings[NOTIFY_SNATCH] + " : " + ep_name,
                                 message=ep_name)

    def _notify_download(self, ep_name):
        if sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONDOWNLOAD:
            self._sendPushbullet(pushbullet_api=None, event=notifyStrings[NOTIFY_DOWNLOAD] + " : " + ep_name,
                                 message=ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendPushbullet(pushbullet_api=None,
                                 event=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD] + " : " + ep_name + " : " + lang,
                                 message=ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.srCore.srConfig.USE_PUSHBULLET:
            self._sendPushbullet(pushbullet_api=None, event=notifyStrings[NOTIFY_GIT_UPDATE],
                                 message=notifyStrings[NOTIFY_GIT_UPDATE_TEXT] + new_version)

    def _sendPushbullet(self, pushbullet_api=None, pushbullet_device=None, event=None, message=None):

        if not (sickrage.srCore.srConfig.USE_PUSHBULLET or event.lower() == 'test' or event is None):
            return False

        pushbullet_api = pushbullet_api or sickrage.srCore.srConfig.PUSHBULLET_API
        pushbullet_device = pushbullet_device or sickrage.srCore.srConfig.PUSHBULLET_DEVICE

        sickrage.srCore.srLogger.debug("Pushbullet event: %r" % event)
        sickrage.srCore.srLogger.debug("Pushbullet message: %r" % message)
        sickrage.srCore.srLogger.debug("Pushbullet api: %r" % pushbullet_api)
        sickrage.srCore.srLogger.debug("Pushbullet devices: %r" % pushbullet_device)
        sickrage.srCore.srLogger.debug("Pushbullet notification type: %r" % 'note' if event else 'None')

        url = 'https://api.pushbullet.com/v2/%s' % ('devices', 'pushes')[event is not None]

        data = json.dumps({
            'title': event.encode('utf-8'),
            'body': message.encode('utf-8'),
            'device_iden': pushbullet_device.encode('utf-8'),
            'type': 'note'
        }) if event else None

        method = 'GET' if data is None else 'POST'
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % pushbullet_api}

        try:
            response = self.session.request(method, url, data=data, headers=headers)
        except Exception:
            sickrage.srCore.srLogger.debug('Pushbullet authorization failed with exception: %r' % traceback.format_exc())
            return False

        if response.status_code == 410:
            sickrage.srCore.srLogger.debug('Pushbullet authorization failed')
            return False

        if response.status_code != 200:
            sickrage.srCore.srLogger.debug('Pushbullet call failed with error code %r' % response.status_code)
            return False

        sickrage.srCore.srLogger.debug("Pushbullet response: %r" % response.text)

        if not response.text:
            sickrage.srCore.srLogger.error("Pushbullet notification failed.")
            return False

        sickrage.srCore.srLogger.debug("Pushbullet notifications sent.")
        return (True, response.text)[event is self.TEST_EVENT or event is None]
