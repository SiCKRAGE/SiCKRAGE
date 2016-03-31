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
import urllib
import urllib2
import urlparse
from _socket import timeout as SocketTimeout
from contextlib import closing

import cachecontrol
import certifi
import requests
from cachecontrol.caches import FileCache

import sickrage
from sickrage.core.helpers import remove_file_failed, chmodAsParent


class srSession(object):
    USER_AGENTS = [
        {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:5.0) Gecko/20100101 Firefox/5.0"},
        {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1) Gecko/20090624 Firefox/3.5"},
        {'User-Agent': "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6"},
        {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1"},
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11"},
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER"},
        {
            "User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)"},
        {
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)"},
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER"},
        {
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)"},
        {
            "User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)"},
        {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)"},
        {
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)"},
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"},
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"},
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0"},
        {
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:16.0) Gecko/20121026 Firefox/16.0"},
        {
            "User-Agent": "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre"},
        {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0"},
        {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15"},
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"},
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"},
        {
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133"},
        {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)"},
        {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"},
        {
            "User-Agent": "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"},
        {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"},
        {"User-Agent": "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)"},
        {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)"},
        {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"},
        {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"}
    ]

    def __init__(self, session=None, headers=None, params=None):
        """
        Returns a session initialized with default cache and parameter settings

        :param session: existing session to pass in
        :param headers: Headers to pass to session
        :param params: Params to pass to session
        :return: session object
        """

        urlparse.uses_netloc.append('scgi')
        urllib.FancyURLopener.version = random.choice(self.USER_AGENTS)

        self.session = cachecontrol.CacheControl(
            session or requests.session(), cache=FileCache(
                os.path.join(tempfile.gettempdir(), 'cachecontrol'), use_dir_lock=True
            ), cache_etags=False
        )

        # request session headers
        self.session.headers.update(headers or {})
        self.session.headers.update({'Accept-Encoding': 'gzip,deflate'})
        self.session.headers.update(random.choice(self.USER_AGENTS))

        # request session clear residual referer
        if 'Referer' in self.session.headers and 'Referer' not in headers:
            self.session.headers.pop('Referer')

        try:
            # request session ssl verify
            self.session.verify = False
            if sickrage.srConfig.SSL_VERIFY:
                self.session.verify = certifi.where()
        except:
            pass

        # request session proxies
        if 'Referer' not in self.session.headers and sickrage.srConfig.PROXY_SETTING:
            sickrage.srLogger.debug("Using global proxy: " + sickrage.srConfig.PROXY_SETTING)
            scheme, address = urllib2.splittype(sickrage.srConfig.PROXY_SETTING)
            address = ('http://{}'.format(sickrage.srConfig.PROXY_SETTING), sickrage.srConfig.PROXY_SETTING)[scheme]
            self.session.proxies = {
                "http": address,
                "https": address,
            }
            self.session.headers.update({'Referer': address})

        if 'Content-Type' in self.session.headers:
            self.session.headers.pop('Content-Type')

        if isinstance(params, (list, dict)):
            self.session.params = params

    def request(self, *args, **kwargs):
        return self.session.request(*args, **kwargs)

    def get(self, url, post_data=None, timeout=None, json=False, needBytes=False):
        """
        Returns a byte-string retrieved from the url provider.
        """
        if not requests.__version__ < (2, 8):
            sickrage.srLogger.debug(
                "Requests version 2.8+ needed to avoid SSL cert verify issues, please upgrade your copy")

        # normalize url
        url = self.normalize_url(url)

        try:
            # decide if we get or post data to server
            if post_data:
                if isinstance(post_data, (list, dict)):
                    for param in post_data:
                        if isinstance(post_data[param], unicode):
                            post_data[param] = post_data[param].encode('utf-8')

                self.session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
                resp = self.session.post(url, data=post_data, timeout=timeout, allow_redirects=True,
                                         verify=self.session.verify)
            else:
                resp = self.session.get(url, timeout=timeout, allow_redirects=True, verify=self.session.verify)

            if resp.ok:
                return (resp.text, resp.content)[needBytes] if not json else resp.json()

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

    def download(self, url, filename):
        """
        Downloads a file specified

        :param url: Source URL
        :param filename: Target file on filesystem
        :return: True on success, False on failure
        """

        # normalize url
        url = self.normalize_url(url)

        self.session.stream = True

        try:
            with closing(self.session.get(url, allow_redirects=True, verify=self.session.verify)) as resp:
                if not resp.ok:
                    return False

                try:
                    with io.open(filename, 'wb') as fp:
                        for chunk in resp.iter_content(chunk_size=1024):
                            if chunk:
                                fp.write(chunk)
                                fp.flush()

                    chmodAsParent(filename)

                    [i.raw.release_conn() for i in resp.history]
                    resp.raw.release_conn()

                    return True
                except Exception:
                    sickrage.srLogger.warning("Problem setting permissions or writing file to: %s" % filename)

        except (SocketTimeout, TypeError) as e:
            remove_file_failed(filename)
            sickrage.srLogger.warning(
                "Connection timed out (sockets) while loading download URL %s Error: %r" % (url, e))
        except requests.exceptions.HTTPError as e:
            remove_file_failed(filename)
            sickrage.srLogger.warning("HTTP error %r while loading download URL %s " % e, url)
        except requests.exceptions.ConnectionError as e:
            remove_file_failed(filename)
            sickrage.srLogger.warning("Connection error %r while loading download URL %s " % e, url)
        except requests.exceptions.Timeout as e:
            remove_file_failed(filename)
            sickrage.srLogger.warning("Connection timed out %r while loading download URL %s " % e, url)
        except EnvironmentError as e:
            remove_file_failed(filename)
            sickrage.srLogger.warning("Unable to save the file: %r " % e)
        except Exception:
            remove_file_failed(filename)
            sickrage.srLogger.warning(
                "Unknown exception while loading download URL %s : %r" % (url, traceback.format_exc()))

    @staticmethod
    def normalize_url(url):
        url = str(url)
        segments = url.split('/')
        correct_segments = []

        for segment in segments:
            if segment != '':
                correct_segments.append(segment)

        first_segment = str(correct_segments[0])
        if first_segment.find('http') == -1:
            correct_segments = ['http:'] + correct_segments

        correct_segments[0] += '/'

        return '/'.join(correct_segments)
