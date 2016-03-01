# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from urlparse import parse_qsl

import oauth2
import twitter

import sickrage
from core.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, \
    NOTIFY_GIT_UPDATE_TEXT, NOTIFY_GIT_UPDATE
from notifiers import srNotifiers


class TwitterNotifier(srNotifiers):
    consumer_key = "vHHtcB6WzpWDG6KYlBMr8g"
    consumer_secret = "zMqq5CB3f8cWKiRO2KzWPTlBanYmV0VYxSXZ0Pxds0E"

    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
    SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

    def _notify_snatch(self, ep_name):
        if sickrage.srConfig.TWITTER_NOTIFY_ONSNATCH:
            self._notifyTwitter(notifyStrings[NOTIFY_SNATCH] + ': ' + ep_name)

    def _notify_download(self, ep_name):
        if sickrage.srConfig.TWITTER_NOTIFY_ONDOWNLOAD:
            self._notifyTwitter(notifyStrings[NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srConfig.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTwitter(notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.srConfig.USE_TWITTER:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyTwitter(title + " - " + update_text + new_version)

    def test_notify(self):
        return self._notifyTwitter("This is a test notification from SiCKRAGE", force=True)

    def _get_authorization(self):

        signature_method_hmac_sha1 = oauth2.SignatureMethod_HMAC_SHA1()  # @UnusedVariable
        oauth_consumer = oauth2.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        oauth_client = oauth2.Client(oauth_consumer)

        sickrage.srLogger.debug('Requesting temp token from Twitter')

        resp, content = oauth_client.request(self.REQUEST_TOKEN_URL, 'GET')

        if resp[b'status'] != '200':
            sickrage.srLogger.error('Invalid response from Twitter requesting temp token: %s' % resp[b'status'])
        else:
            request_token = dict(parse_qsl(content))

            sickrage.srConfig.TWITTER_USERNAME = request_token[b'oauth_token']
            sickrage.srConfig.TWITTER_PASSWORD = request_token[b'oauth_token_secret']

            return self.AUTHORIZATION_URL + "?oauth_token=" + request_token[b'oauth_token']

    def _get_credentials(self, key):
        request_token = {}

        request_token[b'oauth_token'] = sickrage.srConfig.TWITTER_USERNAME
        request_token[b'oauth_token_secret'] = sickrage.srConfig.TWITTER_PASSWORD
        request_token[b'oauth_callback_confirmed'] = 'true'

        token = oauth2.Token(request_token[b'oauth_token'], request_token[b'oauth_token_secret'])
        token.set_verifier(key)

        sickrage.srLogger.debug('Generating and signing request for an access token using key ' + key)

        signature_method_hmac_sha1 = oauth2.SignatureMethod_HMAC_SHA1()  # @UnusedVariable
        oauth_consumer = oauth2.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        sickrage.srLogger.debug('oauth_consumer: ' + str(oauth_consumer))
        oauth_client = oauth2.Client(oauth_consumer, token)
        sickrage.srLogger.debug('oauth_client: ' + str(oauth_client))
        resp, content = oauth_client.request(self.ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % key)
        sickrage.srLogger.debug('resp, content: ' + str(resp) + ',' + str(content))

        access_token = dict(parse_qsl(content))
        sickrage.srLogger.debug('access_token: ' + str(access_token))

        sickrage.srLogger.debug('resp[status] = ' + str(resp[b'status']))
        if resp[b'status'] != '200':
            sickrage.srLogger.error('The request for a token with did not succeed: ' + str(resp[b'status']))
            return False
        else:
            sickrage.srLogger.debug('Your Twitter Access Token key: %s' % access_token[b'oauth_token'])
            sickrage.srLogger.debug('Access Token secret: %s' % access_token[b'oauth_token_secret'])
            sickrage.srConfig.TWITTER_USERNAME = access_token[b'oauth_token']
            sickrage.srConfig.TWITTER_PASSWORD = access_token[b'oauth_token_secret']
            return True

    def _send_tweet(self, message=None):

        username = self.consumer_key
        password = self.consumer_secret
        access_token_key = sickrage.srConfig.TWITTER_USERNAME
        access_token_secret = sickrage.srConfig.TWITTER_PASSWORD

        sickrage.srLogger.debug("Sending tweet: " + message)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostUpdate(message.encode('utf8')[:139])
        except Exception as e:
            sickrage.srLogger.error("Error Sending Tweet: {}".format(e.message))
            return False

        return True

    def _send_dm(self, message=None):

        username = self.consumer_key
        password = self.consumer_secret
        dmdest = sickrage.srConfig.TWITTER_DMTO
        access_token_key = sickrage.srConfig.TWITTER_USERNAME
        access_token_secret = sickrage.srConfig.TWITTER_PASSWORD

        sickrage.srLogger.debug("Sending DM: " + dmdest + " " + message)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostDirectMessage(dmdest, message.encode('utf8')[:139])
        except Exception as e:
            sickrage.srLogger.error("Error Sending Tweet (DM): {}".format(e.message))
            return False

        return True

    def _notifyTwitter(self, message='', force=False):
        prefix = sickrage.srConfig.TWITTER_PREFIX

        if not sickrage.srConfig.USE_TWITTER and not force:
            return False

        if sickrage.srConfig.TWITTER_USEDM and sickrage.srConfig.TWITTER_DMTO:
            return self._send_dm(prefix + ": " + message)
        else:
            return self._send_tweet(prefix + ": " + message)
