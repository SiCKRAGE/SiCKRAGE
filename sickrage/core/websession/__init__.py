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
import os
import ssl
from urllib.parse import urlparse

import certifi
import cfscrape
import requests
from cachecontrol import CacheControlAdapter
from fake_useragent import UserAgent
from requests import Session
from requests.utils import dict_from_cookiejar
from urllib3 import disable_warnings

import sickrage
from sickrage.core import helpers


def _add_proxies():
    if sickrage.app.config.proxy_setting:
        sickrage.app.log.debug("Using global proxy: " + sickrage.app.config.proxy_setting)
        proxy = urlparse(sickrage.app.config.proxy_setting)
        address = sickrage.app.config.proxy_setting if proxy.scheme else 'http://{}'.format(sickrage.app.config.proxy_setting)
        return {"http": address, "https": address}


class WebSession(Session):
    def __init__(self, proxies=None, cache=True, cloudflare=False):
        super(WebSession, self).__init__()

        # setup caching adapter
        if cache:
            adapter = CacheControlAdapter()
            self.mount('http://', adapter)
            self.mount('https://', adapter)

        # add proxies
        self.proxies = proxies or _add_proxies()

        # cloudflare
        self.cloudflare = cloudflare

        # add hooks
        self.hooks['response'] += [WebHooks.log_url]

    @staticmethod
    def _get_ssl_cert(verify):
        """
        Configure the ssl verification.

        We need to overwrite this in the request method. As it's not available in the session init.
        :param verify: SSL verification on or off.
        """
        return certifi.where() if all([sickrage.app.config.ssl_verify, verify]) else False

    def request(self, method, url, verify=False, random_ua=False, allow_post_redirects=False, *args, **kwargs):
        self.headers.update({'Accept-Encoding': 'gzip, deflate',
                             'User-Agent': (sickrage.app.user_agent, UserAgent().random)[random_ua]})

        if not verify:
            disable_warnings()

        if allow_post_redirects and method == 'POST':
            sickrage.app.log.debug('Retrieving redirect URL for {url}'.format(**{'url': url}))
            response = super(WebSession, self).request(method, url, allow_redirects=False)
            url = self.get_redirect_target(response) or url

        try:
            response = super(WebSession, self).request(method, url, verify=self._get_ssl_cert(verify), *args, **kwargs)

            # check of cloudflare handling is required
            if self.cloudflare:
                response = WebHelpers.cloudflare(self, response, **kwargs)

            # check web response for errors
            response.raise_for_status()

            return response
        except requests.exceptions.SSLError as e:
            if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
                sickrage.app.log.info(
                    "SSL Error requesting url: '{}' You have {}, try upgrading OpenSSL to 1.0.1e+".format(e.request.url, ssl.OPENSSL_VERSION)
                )

            if sickrage.app.config.ssl_verify:
                sickrage.app.log.info(
                    "SSL Error requesting url: '{}', try disabling cert verification in advanced settings".format(e.request.url)
                )

    def download(self, url, filename, **kwargs):
        try:
            r = self.get(url, timeout=10, stream=True, **kwargs)
            if r.status_code >= 400:
                return False

            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            helpers.chmod_as_parent(filename)
        except Exception as e:
            sickrage.app.log.debug("Failed to download file from {} - ERROR: {}".format(url, e))
            if os.path.exists(filename):
                os.remove(filename)
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
            sickrage.app.log.debug('With post data: {!r}'.format(request.body.decode() if isinstance(request.body, bytes) else request.body))


class WebHelpers(object):
    @staticmethod
    def cloudflare(session, resp, **kwargs):
        """
        Bypass CloudFlare's anti-bot protection.
        """

        def filtered_kwargs(kwargs):
            """Filter kwargs to only contain arguments accepted by `requests.Session.send`."""
            return {
                k: v for k, v in kwargs.items()
                if k in ('stream', 'timeout', 'verify', 'cert', 'proxies', 'allow_redirects')
            }

        def is_cloudflare_challenge(resp):
            """Check if the response is a Cloudflare challange.
            Source: goo.gl/v8FvnD
            """
            return (
                    resp.status_code == 503
                    and resp.headers.get('Server', '').startswith('cloudflare')
                    and b'jschl_vc' in resp.content
                    and b'jschl_answer' in resp.content
            )

        if is_cloudflare_challenge(resp):
            sickrage.app.log.debug('CloudFlare protection detected, trying to bypass it')

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

            # Remove hooks from original request
            original_hooks = original_request.hooks
            original_request.hooks = []

            # Resend the request
            kwargs['allow_redirects'] = True
            cf_resp = session.send(original_request, **filtered_kwargs(kwargs))

            if cf_resp.ok:
                sickrage.app.log.debug('CloudFlare successfully bypassed.')

            # Add original hooks back to original request
            cf_resp.hooks = original_hooks

            return cf_resp
        else:
            return resp
