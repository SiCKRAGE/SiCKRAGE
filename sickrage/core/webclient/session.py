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
import os
import shelve
import ssl
import threading
import urllib2
from contextlib import closing

import certifi
import cfscrape as cfscrape
import requests
from cachecontrol import CacheControlAdapter

import sickrage
from sickrage.core.helpers import chmodAsParent, remove_file_failed


class DBCache(object):
    def __init__(self, filename):
        self.filename = filename
        self.lock = threading.Lock()

    def get(self, key):
        with closing(shelve.open(self.filename)) as cache:
            if key in cache:
                return cache.get(key)

    def set(self, key, value):
        with self.lock:
            with closing(shelve.open(self.filename)) as cache:
                cache.setdefault(key, value)

    def delete(self, key):
        with self.lock:
            with closing(shelve.open(self.filename)) as cache:
                if key in cache:
                    del cache[key]

    def clear(self):
        with self.lock:
            with closing(shelve.open(self.filename)) as cache:
                cache.clear()


class srSession(cfscrape.CloudflareScraper):
    def __init__(self):
        super(srSession, self).__init__()

    def request(self, method, url, headers=None, params=None, proxies=None, cache=True, verify=False, *args, **kwargs):
        if headers is None: headers = {}
        if params is None: params = {}
        if proxies is None: proxies = {}

        headers['Accept-Encoding'] = 'gzip, deflate'
        headers["User-Agent"] = sickrage.app.USER_AGENT

        # request session ssl verify
        if sickrage.app.srConfig.SSL_VERIFY:
            try:
                verify = certifi.where()
            except:
                pass

        # request session proxies
        if 'Referer' not in headers and sickrage.app.srConfig.PROXY_SETTING:
            sickrage.app.srLogger.debug("Using global proxy: " + sickrage.app.srConfig.PROXY_SETTING)
            scheme, address = urllib2.splittype(sickrage.app.srConfig.PROXY_SETTING)
            address = ('http://{}'.format(sickrage.app.srConfig.PROXY_SETTING),
                       sickrage.app.srConfig.PROXY_SETTING)[scheme]
            proxies.update({"http": address, "https": address})
            headers.update({'Referer': address})

        # setup caching adapter
        if cache:
            adapter = CacheControlAdapter(DBCache(os.path.abspath(os.path.join(sickrage.DATA_DIR, 'sessions.db'))))
            self.mount('http://', adapter)
            self.mount('https://', adapter)

        # get web response
        response = super(srSession, self).request(
            method,
            url,
            headers=headers,
            params=params,
            verify=verify,
            proxies=proxies,
            *args, **kwargs
        )

        try:
            # check web response for errors
            response.raise_for_status()
        except requests.exceptions.SSLError as e:
            if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
                sickrage.app.srLogger.info(
                    "SSL Error requesting url: '{}' You have {}, try upgrading OpenSSL to 1.0.1e+".format(
                        e.request.url, ssl.OPENSSL_VERSION))

            if sickrage.app.srConfig.SSL_VERIFY:
                sickrage.app.srLogger.info(
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
            sickrage.app.srLogger.debug("Failed to download file from {} - ERROR: {}".format(url, e.message))
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
