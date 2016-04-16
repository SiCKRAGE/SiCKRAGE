#!/usr/bin/env python2
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

import io
import os
import random
import tempfile
import traceback
import urllib2
from _socket import timeout as SocketTimeout

import cachecontrol
import certifi
import requests
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import ExpiresAfter
from requests_futures.sessions import FuturesSession

import sickrage
from sickrage.core.helpers import chmodAsParent, remove_file_failed
from sickrage.core.webclient.useragents import USER_AGENTS

class srFuturesSession(FuturesSession):
    def __init__(self):
        super(srFuturesSession, self).__init__(max_workers=10, session=requests.Session())

    def request(self, method, url, headers=None, params=None, cache=True, *args, **kwargs):
        url = self.normalize_url(url)
        kwargs.setdefault('params', {}).update(params or {})
        kwargs.setdefault('headers', {}).update(headers or {})

        # if method == 'POST':
        #    self.session.headers.update({"Content-type": "application/x-www-form-urlencoded"})
        kwargs.setdefault('headers', {}).update({'Accept-Encoding': 'gzip, deflate'})
        kwargs.setdefault('headers', {}).update(random.choice(USER_AGENTS))

        # request session ssl verify
        kwargs['verify'] = False
        if sickrage.srConfig.SSL_VERIFY:
            try:
                kwargs['verify'] = certifi.where()
            except:
                pass
        # request session proxies
        if 'Referer' not in kwargs.get('headers', {}) and sickrage.srConfig.PROXY_SETTING:
            sickrage.srLogger.debug("Using global proxy: " + sickrage.srConfig.PROXY_SETTING)
            scheme, address = urllib2.splittype(sickrage.srConfig.PROXY_SETTING)
            address = ('http://{}'.format(sickrage.srConfig.PROXY_SETTING), sickrage.srConfig.PROXY_SETTING)[scheme]
            kwargs.setdefault('proxies', {}).update({"http": address, "https": address})
            kwargs.setdefault('headers', {}).update({'Referer': address})

        try:
            # setup session caching
            if cache:
                self.session = cachecontrol.CacheControl(
                    self.session,
                    cache=FileCache(os.path.join(tempfile.gettempdir(), 'cachecontrol')),
                    heuristic=ExpiresAfter(days=7))

            # get result
            return super(srFuturesSession, self).request(method, url, *args, **kwargs).result()
        except (SocketTimeout, TypeError) as e:
            sickrage.srLogger.warning("Connection timed out (sockets) accessing url %s Error: %r" % (url, e))
        except requests.exceptions.HTTPError as e:
            sickrage.srLogger.debug("HTTP error in url %s Error: %r" % (url, e))
        except requests.exceptions.ConnectionError as e:
            sickrage.srLogger.debug("Connection error to url %s Error: %r" % (url, e))
        except requests.exceptions.Timeout as e:
            sickrage.srLogger.warning("Connection timed out accessing url %s Error: %r" % (url, e))
        except requests.exceptions.ContentDecodingError:
            sickrage.srLogger.debug("Content-Encoding was gzip, but content was not compressed. url: %s" % url)
            sickrage.srLogger.debug(traceback.format_exc())
        except Exception as e:
            sickrage.srLogger.debug("Unknown exception in url %s Error: %r" % (url, e))
            sickrage.srLogger.debug(traceback.format_exc())

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