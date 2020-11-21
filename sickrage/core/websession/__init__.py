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
import collections
import errno
import os
import traceback
from time import sleep
from urllib.parse import urlparse

import certifi
import requests
from cachecontrol import CacheControlAdapter
from cloudscraper import CloudScraper
from fake_useragent import UserAgent, FakeUserAgentError
from requests import Session
from requests.utils import dict_from_cookiejar
from urllib3 import disable_warnings

import sickrage


def _add_proxies():
    if sickrage.app.config.general.proxy_setting:
        sickrage.app.log.debug("Using global proxy: " + sickrage.app.config.general.proxy_setting)
        proxy = urlparse(sickrage.app.config.general.proxy_setting)
        address = sickrage.app.config.general.proxy_setting if proxy.scheme else 'http://{}'.format(sickrage.app.config.general.proxy_setting)
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
        self.proxies = proxies

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
        return certifi.where() if all([sickrage.app.config.general.ssl_verify, verify]) else False

    @staticmethod
    def _get_user_agent(random_ua=False):
        try:
            user_agent = (sickrage.app.user_agent, UserAgent().random)[random_ua]
        except FakeUserAgentError:
            user_agent = sickrage.app.user_agent

        return user_agent

    def request(self, method, url, verify=False, random_ua=False, timeout=15, *args, **kwargs):
        self.headers.update({'Accept-Encoding': 'gzip, deflate',
                             'User-Agent': self._get_user_agent(random_ua)})

        # add proxies
        self.proxies = self.proxies or _add_proxies()

        if not verify:
            disable_warnings()

        for i in range(5):
            resp = None

            try:
                resp = super(WebSession, self).request(method, url, verify=self._get_ssl_cert(verify), timeout=timeout, *args, **kwargs)

                # check of cloudflare handling is required
                if self.cloudflare:
                    resp = WebHelpers.cloudflare(self, resp, **kwargs)

                # check web response for exceptions
                resp.raise_for_status()

                return resp
            except requests.exceptions.HTTPError as e:
                sickrage.app.log.debug('The response returned a non-200 response while requesting url {url} Error: {err_msg!r}'.format(url=url, err_msg=e))
                return resp or e.response
            except requests.exceptions.ConnectionError as e:
                if i > 3:
                    sickrage.app.log.debug('Error connecting to url {url} Error: {err_msg}'.format(url=url, err_msg=e))
                    return resp or e.response

                # sleep 1s before retrying request
                sleep(1)
            except requests.exceptions.RequestException as e:
                sickrage.app.log.debug('Error requesting url {url} Error: {err_msg}'.format(url=url, err_msg=e))
                return resp or e.response
            except Exception as e:
                if (isinstance(e, collections.Iterable) and 'ECONNRESET' in e) or (getattr(e, 'errno', None) == errno.ECONNRESET):
                    sickrage.app.log.warning('Connection reset by peer accessing url {url} Error: {err_msg}'.format(url=url, err_msg=e))
                else:
                    sickrage.app.log.info('Unknown exception in url {url} Error: {err_msg}'.format(url=url, err_msg=e))
                    sickrage.app.log.debug(traceback.format_exc())

                return None

    def download(self, url, filename, **kwargs):
        try:
            r = self.get(url, timeout=10, stream=True, **kwargs)
            if r.status_code >= 400:
                return False

            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            from sickrage.core.helpers import chmod_as_parent
            chmod_as_parent(filename)
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

        # def is_cloudflare_challenge(resp):
        #     """Check if the response is a Cloudflare challange.
        #     Source: goo.gl/v8FvnD
        #     """
        #     try:
        #         return (resp.headers.get('Server', '').startswith('cloudflare')
        #                 and resp.status_code in [429, 503]
        #                 and re.search(r'action="/.*?__cf_chl_jschl_tk__=\S+".*?name="jschl_vc"\svalue=.*?', resp.text, re.M | re.DOTALL))
        #     except AttributeError:
        #         pass
        #
        #     return False

        if CloudScraper.is_IUAM_Challenge(resp):
            sickrage.app.log.debug('CloudFlare protection detected, trying to bypass it')

            # Get the original request
            original_request = resp.request

            # Get the CloudFlare tokens and original user-agent
            tokens, user_agent = CloudScraper.get_tokens(original_request.url)

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
            if CloudScraper.is_Captcha_Challenge(resp) or CloudScraper.is_Firewall_Blocked(resp):
                sickrage.app.log.warning("Cloudflare captcha challenge or firewall detected, it can't be bypassed.")

            return resp
