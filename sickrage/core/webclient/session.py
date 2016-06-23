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

import io
import os
import random
import shelve
import tempfile
import threading
import urllib2
from contextlib import closing

import cachecontrol
import certifi
from cachecontrol.heuristics import ExpiresAfter
from requests_futures.sessions import FuturesSession

import sickrage
from sickrage.core.helpers import chmodAsParent, remove_file_failed
from sickrage.core.webclient.exceptions import handle_exception
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


class srSession(FuturesSession):
    @handle_exception
    def request(self, method, url, headers=None, params=None, cache=True, raise_exceptions=True, *args, **kwargs):
        url = self.normalize_url(url)
        kwargs.setdefault('params', {}).update(params or {})
        kwargs.setdefault('headers', {}).update(headers or {})

        # if method == 'POST':
        #    self.session.headers.update({"Content-type": "application/x-www-form-urlencoded"})
        kwargs.setdefault('headers', {}).update({'Accept-Encoding': 'gzip, deflate'})
        kwargs.setdefault('headers', {}).update(random.choice(USER_AGENTS))

        # request session ssl verify
        kwargs['verify'] = False
        if sickrage.srCore.srConfig.SSL_VERIFY:
            try:
                kwargs['verify'] = certifi.where()
            except:
                pass

        # request session proxies
        if 'Referer' not in kwargs.get('headers', {}) and sickrage.srCore.srConfig.PROXY_SETTING:
            sickrage.srCore.srLogger.debug("Using global proxy: " + sickrage.srCore.srConfig.PROXY_SETTING)
            scheme, address = urllib2.splittype(sickrage.srCore.srConfig.PROXY_SETTING)
            address = ('http://{}'.format(sickrage.srCore.srConfig.PROXY_SETTING), sickrage.srCore.srConfig.PROXY_SETTING)[scheme]
            kwargs.setdefault('proxies', {}).update({"http": address, "https": address})
            kwargs.setdefault('headers', {}).update({'Referer': address})

        # setup session caching
        if cache:
            cachecontrol.CacheControl(self,
                                      cache=DBCache(os.path.join(tempfile.gettempdir(), 'cachecontrol.db')),
                                      heuristic=ExpiresAfter(days=7))

        # get result
        response = super(srSession, self).request(method, url, *args, **kwargs).result()
        if raise_exceptions:
            response.raise_for_status()
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
