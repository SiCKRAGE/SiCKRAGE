# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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

import logging

import sickbeard

from sickbeard import common
from sickrage.helper.exceptions import ex

# parse_qsl moved to urlparse module in v2.6
try:
    from urlparse import parse_qsl  # @UnusedImport
except ImportError:
    from cgi import parse_qsl  # @Reimport

import oauth2 as oauth
import pythontwitter as twitter


class TwitterNotifier:
    consumer_key = "vHHtcB6WzpWDG6KYlBMr8g"
    consumer_secret = "zMqq5CB3f8cWKiRO2KzWPTlBanYmV0VYxSXZ0Pxds0E"

    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
    SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

    def notify_snatch(self, ep_name):
        if sickbeard.TWITTER_NOTIFY_ONSNATCH:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.TWITTER_NOTIFY_ONDOWNLOAD:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_TWITTER:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notifyTwitter(title + " - " + update_text + new_version)

    def test_notify(self):
        return self._notifyTwitter("This is a test notification from SiCKRAGE", force=True)

    def _get_authorization(self):

        signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()  # @UnusedVariable
        oauth_consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        oauth_client = oauth.Client(oauth_consumer)

        logging.debug('Requesting temp token from Twitter')

        resp, content = oauth_client.request(self.REQUEST_TOKEN_URL, 'GET')

        if resp[b'status'] != '200':
            logging.error('Invalid response from Twitter requesting temp token: %s' % resp[b'status'])
        else:
            request_token = dict(parse_qsl(content))

            sickbeard.TWITTER_USERNAME = request_token[b'oauth_token']
            sickbeard.TWITTER_PASSWORD = request_token[b'oauth_token_secret']

            return self.AUTHORIZATION_URL + "?oauth_token=" + request_token[b'oauth_token']

    def _get_credentials(self, key):
        request_token = {}

        request_token[b'oauth_token'] = sickbeard.TWITTER_USERNAME
        request_token[b'oauth_token_secret'] = sickbeard.TWITTER_PASSWORD
        request_token[b'oauth_callback_confirmed'] = 'true'

        token = oauth.Token(request_token[b'oauth_token'], request_token[b'oauth_token_secret'])
        token.set_verifier(key)

        logging.debug('Generating and signing request for an access token using key ' + key)

        signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()  # @UnusedVariable
        oauth_consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        logging.debug('oauth_consumer: ' + str(oauth_consumer))
        oauth_client = oauth.Client(oauth_consumer, token)
        logging.debug('oauth_client: ' + str(oauth_client))
        resp, content = oauth_client.request(self.ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % key)
        logging.debug('resp, content: ' + str(resp) + ',' + str(content))

        access_token = dict(parse_qsl(content))
        logging.debug('access_token: ' + str(access_token))

        logging.debug('resp[status] = ' + str(resp[b'status']))
        if resp[b'status'] != '200':
            logging.error('The request for a token with did not succeed: ' + str(resp[b'status']))
            return False
        else:
            logging.debug('Your Twitter Access Token key: %s' % access_token[b'oauth_token'])
            logging.debug('Access Token secret: %s' % access_token[b'oauth_token_secret'])
            sickbeard.TWITTER_USERNAME = access_token[b'oauth_token']
            sickbeard.TWITTER_PASSWORD = access_token[b'oauth_token_secret']
            return True

    def _send_tweet(self, message=None):

        username = self.consumer_key
        password = self.consumer_secret
        access_token_key = sickbeard.TWITTER_USERNAME
        access_token_secret = sickbeard.TWITTER_PASSWORD

        logging.debug("Sending tweet: " + message)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostUpdate(message.encode('utf8')[:139])
        except Exception as e:
            logging.error("Error Sending Tweet: {}".format(ex(e)))
            return False

        return True

    def _send_dm(self, message=None):

        username = self.consumer_key
        password = self.consumer_secret
        dmdest = sickbeard.TWITTER_DMTO
        access_token_key = sickbeard.TWITTER_USERNAME
        access_token_secret = sickbeard.TWITTER_PASSWORD

        logging.debug("Sending DM: " + dmdest + " " + message)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostDirectMessage(dmdest, message.encode('utf8')[:139])
        except Exception as e:
            logging.error("Error Sending Tweet (DM): {}".format(ex(e)))
            return False

        return True

    def _notifyTwitter(self, message='', force=False):
        prefix = sickbeard.TWITTER_PREFIX

        if not sickbeard.USE_TWITTER and not force:
            return False

        if sickbeard.TWITTER_USEDM and sickbeard.TWITTER_DMTO:
            return self._send_dm(prefix + ": " + message)
        else:
            return self._send_tweet(prefix + ": " + message)


notifier = TwitterNotifier
