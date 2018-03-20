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

import io
import ssl
import urllib2

import certifi
import cfscrape as cfscrape
import requests
from cachecontrol import CacheControlAdapter
from requests import Session
from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.helpers import chmodAsParent, remove_file_failed
from sickrage.core.helpers.encoding import to_unicode


def _add_proxies():
    if sickrage.app.config.proxy_setting:
        sickrage.app.log.debug("Using global proxy: " + sickrage.app.config.proxy_setting)
        scheme, address = urllib2.splittype(sickrage.app.config.proxy_setting)
        address = ('http://{}'.format(sickrage.app.config.proxy_setting),
                   sickrage.app.config.proxy_setting)[scheme]
        return {"http": address, "https": address}


class WebSession(Session):
    def __init__(self, proxies=None, cache=True):
        super(WebSession, self).__init__()

        # setup caching adapter
        if cache:
            adapter = CacheControlAdapter()
            self.mount('http://', adapter)
            self.mount('https://', adapter)

        # add proxies
        self.proxies = proxies or _add_proxies()

        # add hooks
        self.hooks['response'] += [WebHooks.log_url, WebHooks.cloudflare]

        # add headers
        self.headers.update({'Accept-Encoding': 'gzip, deflate', 'User-Agent': sickrage.app.user_agent})

    @staticmethod
    def _get_ssl_cert(verify):
        """
        Configure the ssl verification.

        We need to overwrite this in the request method. As it's not available in the session init.
        :param verify: SSL verification on or off.
        """
        return certifi.where() if all([sickrage.app.config.ssl_verify, verify]) else False

    def request(self, method, url, verify=False, *args, **kwargs):
        response = super(WebSession, self).request(method, url, verify=self._get_ssl_cert(verify), *args, **kwargs)

        try:
            # check web response for errors
            response.raise_for_status()
        except requests.exceptions.SSLError as e:
            if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
                sickrage.app.log.info(
                    "SSL Error requesting url: '{}' You have {}, try upgrading OpenSSL to 1.0.1e+".format(
                        e.request.url, ssl.OPENSSL_VERSION))

            if sickrage.app.config.ssl_verify:
                sickrage.app.log.info(
                    "SSL Error requesting url: '{}', try disabling cert verification in advanced settings".format(
                        e.request.url))
        except Exception:
            pass

        return response

    def download(self, url, filename, **kwargs):
        try:
            r = self.get(url, timeout=10, stream=True, **kwargs)
            if r.status_code >= 400:
                return False

            with io.open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            chmodAsParent(filename)
        except Exception as e:
            sickrage.app.log.debug("Failed to download file from {} - ERROR: {}".format(url, e.message))
            remove_file_failed(filename)
            return False

        return True

    @staticmethod
    def normalize_url(url, secure=False):
        url = str(url)
        segments = url.split('/')
        correct_segments = []

        for segment in segments:
            if segment != '':
                correct_segments.append(segment)

        first_segment = str(correct_segments[0])
        if first_segment.find(('http', 'https')[secure]) == -1:
            correct_segments = [('http:', 'https:')[secure]] + correct_segments

        correct_segments[0] += '/'

        return '/'.join(correct_segments) + '/'


class WebHooks(object):
    @staticmethod
    def log_url(response, **kwargs):
        """Response hook to log request URL."""
        request = response.request
        sickrage.app.log.debug('{} URL: {} [Status: {}]'.format(request.method, request.url, response.status_code))
        sickrage.app.log.debug('User-Agent: {}'.format(request.headers['User-Agent']))

        if request.method.upper() == 'POST':
            if isinstance(request.body, unicode):
                sickrage.app.log.debug('With post data: {}'.format(request.body))
            else:
                sickrage.app.log.debug('With post data: {}'.format(to_unicode(request.body)))

    @staticmethod
    def cloudflare(resp, **kwargs):
        """
        Bypass CloudFlare's anti-bot protection.
        """
        if all([resp.status_code == 503, 'cloudflare' in resp.headers.get('server')]):
            sickrage.app.log.debug('CloudFlare protection detected, trying to bypass it')

            # Get the session used or create a new one
            session = getattr(resp, 'session', requests.Session())

            # Get the original request
            original_request = resp.request

            # Get the CloudFlare tokens and original user-agent
            tokens, user_agent = cfscrape.get_tokens(original_request.url)

            # Add CloudFlare tokens to the session cookies
            session.cookies.update(tokens)

            # Add CloudFlare Tokens to the original request
            original_cookies = dict_from_cookiejar(original_request._cookies)
            original_cookies.update(tokens)
            original_request.prepare_cookies(original_cookies)

            # The same User-Agent must be used for the retry
            # Update the session with the CloudFlare User-Agent
            session.headers['User-Agent'] = user_agent

            # Update the original request with the CloudFlare User-Agent
            original_request.headers['User-Agent'] = user_agent

            # Resend the request
            cf_resp = session.send(
                original_request,
                allow_redirects=True,
                **kwargs
            )

            if cf_resp.ok:
                sickrage.app.log.debug('CloudFlare successfully bypassed.')
            return cf_resp
        else:
            return resp
