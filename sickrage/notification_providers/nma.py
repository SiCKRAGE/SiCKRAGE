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
from urllib.parse import urljoin, urlencode
from xml.dom.minidom import parseString

from requests import request

import sickrage
from sickrage.notification_providers import NotificationProvider


class NMA_Notification(NotificationProvider):
    def __init__(self):
        super(NMA_Notification, self).__init__()
        self.name = 'nma'
        self.url = 'https://www.notifymyandroid.com'
        self._developerkey = None
        self._apikey = None

    def uniq_preserve(self, seq):  # Dave Kirby
        # Order preserving
        seen = set()
        return [x for x in seq if x not in seen and not seen.add(x)]

    def uniq(self, seq):
        # Not order preserving
        return list({}.fromkeys(seq).keys())

    def addkey(self, key):
        """Add a key (register ?)"""
        self._apikey = self.uniq(key)
        if type(key) == str:
            if not key in self._apikey:
                self._apikey.append(key)
        elif type(key) == list:
            for k in key:
                if not k in self._apikey:
                    self._apikey.append(k)

    def delkey(self, key):
        """
        Removes a key (unregister ?)
        """
        if type(key) == str:
            if key in self._apikey:
                self._apikey.remove(key)
        elif type(key) == list:
            for k in key:
                if key in self._apikey:
                    self._apikey.remove(k)

    def developerkey(self, developerkey):
        "Sets the developer key (and check it has the good length)"
        if type(developerkey) == str and len(developerkey) == 48:
            self._developerkey = developerkey

    def push(self, application="", event="", description="", url="", contenttype=None, priority=0, batch_mode=False,
             html=False):
        """Pushes a message on the registered API keys.
        """
        datas = {
            'application': application[:256].encode('utf8'),
            'event': event[:1024].encode('utf8'),
            'description': description[:10000].encode('utf8'),
            'priority': priority
        }

        if url:
            datas['url'] = url[:512]

        if contenttype == "text/html" or html == True:  # Currently only accepted content type
            datas['content-type'] = "text/html"

        if self._developerkey:
            datas['developerkey'] = self._developerkey

        results = {}

        if not batch_mode:
            for key in self._apikey:
                datas['apikey'] = key
                res = self.callapi('POST', datas)
                results[key] = res
        else:
            datas['apikey'] = ",".join(self._apikey)
            res = self.callapi('POST', datas)
            results[datas['apikey']] = res

        return results

    def callapi(self, method, args):
        headers = {'User-Agent': sickrage.app.user_agent}
        if method == "POST":
            headers['Content-type'] = "application/x-www-form-urlencoded"

        resp = request(method, url=urljoin(self.url, '/publicapi/notify'), headers=headers, data=urlencode(args))

        try:
            res = self._parse_reponse(resp.content)
        except Exception as e:
            res = {'type': "pynmaerror",
                   'code': 600,
                   'message': str(e)
                   }
            pass

        return res

    def _parse_reponse(self, response):
        root = parseString(response).firstChild
        for elem in root.childNodes:
            if elem.nodeType == elem.TEXT_NODE: continue
            if elem.tagName == 'success':
                res = dict(list(elem.attributes.items()))
                res['message'] = ""
                res['type'] = elem.tagName
                return res
            if elem.tagName == 'error':
                res = dict(list(elem.attributes.items()))
                res['message'] = elem.firstChild.nodeValue
                res['type'] = elem.tagName
                return res

    def test_notify(self, nma_api, nma_priority):
        return self._sendNMA(nma_api, nma_priority, event="Test", message="Testing NMA settings from SiCKRAGE",
                             force=True)

    def notify_snatch(self, ep_name):
        if sickrage.app.config.nma.notify_on_snatch:
            self._sendNMA(event=self.notifyStrings[self.NOTIFY_SNATCH], message=ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.nma.notify_on_download:
            self._sendNMA(event=self.notifyStrings[self.NOTIFY_DOWNLOAD], message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.nma.notify_on_subtitle_download:
            self._sendNMA(event=self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD], message=ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.nma.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._sendNMA(event=title, message=update_text + new_version)

    def _sendNMA(self, nma_api=None, nma_priority=None, event=None, message=None, force=False):

        title = 'SiCKRAGE'

        if not sickrage.app.config.nma.enable and not force:
            return False

        if nma_api is None:
            nma_api = sickrage.app.config.nma.api_keys

        if nma_priority is None:
            nma_priority = sickrage.app.config.nma.priority

        batch = False

        keys = nma_api.split(',')
        self.addkey(keys)

        if len(keys) > 1: batch = True

        sickrage.app.log.debug(
            "NMA: Sending notice with details: event=\"%s\", message=\"%s\", priority=%s, batch=%s" % (
                event, message, nma_priority, batch))

        response = self.push(
            application=title,
            event=event,
            description=message,
            priority=nma_priority,
            batch_mode=batch
        )

        if not response[nma_api]['code'] == '200':
            sickrage.app.log.warning('Could not send notification to NotifyMyAndroid')
            return False
        else:
            sickrage.app.log.info("NMA: Notification sent to NotifyMyAndroid")
            return True
