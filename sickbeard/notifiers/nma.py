#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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

import logging

import sickbeard

from sickbeard import common
from pynma import pynma


class NMA_Notifier:
    def test_notify(self, nma_api, nma_priority):
        return self._sendNMA(nma_api, nma_priority, event="Test", message="Testing NMA settings from SiCKRAGE",
                             force=True)

    def notify_snatch(self, ep_name):
        if sickbeard.NMA_NOTIFY_ONSNATCH:
            self._sendNMA(nma_api=None, nma_priority=None, event=common.notifyStrings[common.NOTIFY_SNATCH],
                          message=ep_name)

    def notify_download(self, ep_name):
        if sickbeard.NMA_NOTIFY_ONDOWNLOAD:
            self._sendNMA(nma_api=None, nma_priority=None, event=common.notifyStrings[common.NOTIFY_DOWNLOAD],
                          message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendNMA(nma_api=None, nma_priority=None, event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD],
                          message=ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_NMA:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._sendNMA(nma_api=None, nma_priority=None, event=title, message=update_text + new_version)

    def _sendNMA(self, nma_api=None, nma_priority=None, event=None, message=None, force=False):

        title = 'SiCKRAGE'

        if not sickbeard.USE_NMA and not force:
            return False

        if nma_api == None:
            nma_api = sickbeard.NMA_API

        if nma_priority == None:
            nma_priority = sickbeard.NMA_PRIORITY

        batch = False

        p = pynma.PyNMA()
        keys = nma_api.split(',')
        p.addkey(keys)

        if len(keys) > 1: batch = True

        logging.debug("NMA: Sending notice with details: event=\"%s\", message=\"%s\", priority=%s, batch=%s" % (
        event, message, nma_priority, batch))
        response = p.push(application=title, event=event, description=message, priority=nma_priority, batch_mode=batch)

        if not response[nma_api][b'code'] == '200':
            logging.error('Could not send notification to NotifyMyAndroid')
            return False
        else:
            logging.info("NMA: Notification sent to NotifyMyAndroid")
            return True


notifier = NMA_Notifier
