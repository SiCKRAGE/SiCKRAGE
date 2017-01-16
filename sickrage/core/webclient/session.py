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
import random
import shelve
import ssl
import threading
import urllib2
from contextlib import closing

import cachecontrol
import certifi
import cfscrape as cfscrape
import requests
from cachecontrol.heuristics import ExpiresAfter

import sickrage
from sickrage.core.helpers import chmodAsParent, remove_file_failed
from sickrage.core.webclient.useragents import USER_AGENTS


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
    def request(self, method, url, headers=None, params=None, proxies=None, cache=True, verify=False, *args, **kwargs):
        if headers is None: headers = {}
        if params is None: params = {}
        if proxies is None: proxies = {}

        url = self.normalize_url(url)

        headers.update({'Accept-Encoding': 'gzip, deflate'})
        headers.update(random.choice(USER_AGENTS))

        # request session ssl verify
        if sickrage.srCore.srConfig.SSL_VERIFY:
            try:
                verify = certifi.where()
            except:
                pass

        # request session proxies
        if 'Referer' not in headers and sickrage.srCore.srConfig.PROXY_SETTING:
            sickrage.srCore.srLogger.debug("Using global proxy: " + sickrage.srCore.srConfig.PROXY_SETTING)
            scheme, address = urllib2.splittype(sickrage.srCore.srConfig.PROXY_SETTING)
            address = ('http://{}'.format(sickrage.srCore.srConfig.PROXY_SETTING),
                       sickrage.srCore.srConfig.PROXY_SETTING)[scheme]
            proxies.update({"http": address, "https": address})
            headers.update({'Referer': address})

        # setup session caching
        if cache:
            cache_file = os.path.abspath(os.path.join(sickrage.DATA_DIR, 'sessions.db'))
            self.__class__ = cachecontrol.CacheControl(self,
                                                       cache=DBCache(cache_file),
                                                       heuristic=ExpiresAfter(days=7)).__class__

        # get web response
        response = super(srSession, self).request(method,
                                                  url,
                                                  headers=headers,
                                                  params=params,
                                                  verify=verify,
                                                  proxies=proxies,
                                                  *args, **kwargs)

        try:
            # check web response for errors
            response.raise_for_status()
        except requests.exceptions.SSLError as e:
            if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
                sickrage.srCore.srLogger.info(
                    "SSL Error requesting url: '{}' You have {}, try upgrading OpenSSL to 1.0.1e+".format(
                        e.request.url, ssl.OPENSSL_VERSION))

            if sickrage.srCore.srConfig.SSL_VERIFY:
                sickrage.srCore.srLogger.info(
                    "SSL Error requesting url: '{}', try disabling cert verification in advanced settings".format(
                        e.request.url))
        except Exception:
            pass

        return response

    def download(self, url, filename, **kwargs):
        """
        Downloads a file specified

        :param url: Source URL
        :param filename: Target file on filesystem
        :return: True on success, False on failure
        """

        try:
            with io.open(filename, 'wb') as fp:
                for chunk in self.get(url, stream=True, **kwargs).iter_content(chunk_size=1024):
                    if chunk:
                        fp.write(chunk)
                        fp.flush()

            chmodAsParent(filename)
        except Exception:
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

        return '/'.join(correct_segments)
