#!/usr/bin/env python2
# -*- coding: utf-8 -*-
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

import re
import time
from hashlib import sha1
from base64 import b16encode, b32decode

import sickbeard
import logging
from sickbeard.clients import http_error_code
from bencode import bencode, bdecode
import requests
from bencode.BTL import BTFailure


class GenericClient(object):
    def __init__(self, name, host=None, username=None, password=None):

        self.name = name
        self.username = sickbeard.TORRENT_USERNAME if username is None else username
        self.password = sickbeard.TORRENT_PASSWORD if password is None else password
        self.host = sickbeard.TORRENT_HOST if host is None else host
        self.rpcurl = sickbeard.TORRENT_RPCURL

        self.url = None
        self.response = None
        self.auth = None
        self.last_time = time.time()
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def _request(self, method='get', params=None, data=None, files=None):

        if time.time() > self.last_time + 1800 or not self.auth:
            self.last_time = time.time()
            self._get_auth()

        logging.debug(
                self.name + ': Requested a ' + method.upper() + ' connection to url ' + self.url +
                ' with Params: ' + str(params) + ' Data: ' + str(data)[0:99] + ('...' if len(str(data)) > 200 else ''))

        if not self.auth:
            logging.warning(self.name + ': Authentication Failed')
            return False
        try:
            self.response = self.session.__getattribute__(method)(self.url, params=params, data=data, files=files,
                                                                  timeout=120, verify=False)
        except requests.exceptions.ConnectionError as e:
            logging.error(self.name + ': Unable to connect ' + str(e))
            return False
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
            logging.error(self.name + ': Invalid Host')
            return False
        except requests.exceptions.HTTPError as e:
            logging.error(self.name + ': Invalid HTTP Request ' + str(e))
            return False
        except requests.exceptions.Timeout as e:
            logging.warning(self.name + ': Connection Timeout ' + str(e))
            return False
        except Exception as e:
            logging.error(self.name + ': Unknown exception raised when send torrent to ' + self.name + ': ' + str(e))
            return False

        if self.response.status_code == 401:
            logging.error(self.name + u': Invalid Username or Password, check your config')
            return False

        if self.response.status_code in http_error_code.keys():
            logging.debug(self.name + ': ' + http_error_code[self.response.status_code])
            return False

        logging.debug(self.name + ': Response to ' + method.upper() + ' request is ' + self.response.text)

        return True

    def _get_auth(self):
        """
        This should be overridden and should return the auth_id needed for the client
        """
        return None

    def _add_torrent_uri(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is added via url (magnet or .torrent link)
        """
        return False

    def _add_torrent_file(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is added via result.content (only .torrent file)
        """
        return False

    def _set_torrent_label(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with label
        """
        return True

    def _set_torrent_ratio(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with ratio
        """
        return True

    def _set_torrent_seed_time(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with a seed time
        """
        return True

    def _set_torrent_priority(self, result):
        """
        This should be overriden should return the True/False from the client
        when a torrent is set with result.priority (-1 = low, 0 = normal, 1 = high)
        """
        return True

    def _set_torrent_path(self, torrent_path):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with path
        """
        return True

    def _set_torrent_pause(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with pause
        """
        return True

    def _get_torrent_hash(self, result):

        if result.url.startswith('magnet'):
            result.hash = re.findall(r'urn:btih:([\w]{32,40})', result.url)[0]
            if len(result.hash) == 32:
                result.hash = b16encode(b32decode(result.hash)).lower()
        else:
            if not result.content:
                logging.error('Torrent without content')
                raise Exception('Torrent without content')

            try:
                torrent_bdecode = bdecode(result.content)
            except BTFailure:
                logging.error('Unable to bdecode torrent')
                logging.debug('Torrent bencoded data: %r' % result.content)
                raise
            try:
                info = torrent_bdecode[b"info"]
            except Exception:
                logging.error('Unable to find info field in torrent')
                raise
            result.hash = sha1(bencode(info)).hexdigest()

        return result

    def sendTORRENT(self, result):

        r_code = False

        logging.debug('Calling ' + self.name + ' Client')

        if not self._get_auth():
            logging.error(self.name + ': Authentication Failed')
            return r_code

        try:
            # Sets per provider seed ratio
            result.ratio = result.provider.seedRatio()

            # lazy fix for now, I'm sure we already do this somewhere else too
            result = self._get_torrent_hash(result)

            if result.url.startswith('magnet'):
                r_code = self._add_torrent_uri(result)
            else:
                r_code = self._add_torrent_file(result)

            if not r_code:
                logging.error(self.name + ': Unable to send Torrent: Return code undefined')
                return False

            if not self._set_torrent_pause(result):
                logging.error(self.name + ': Unable to set the pause for Torrent')

            if not self._set_torrent_label(result):
                logging.error(self.name + ': Unable to set the label for Torrent')

            if not self._set_torrent_ratio(result):
                logging.error(self.name + ': Unable to set the ratio for Torrent')

            if not self._set_torrent_seed_time(result):
                logging.error(self.name + ': Unable to set the seed time for Torrent')

            if not self._set_torrent_path(result):
                logging.error(self.name + ': Unable to set the path for Torrent')

            if result.priority != 0 and not self._set_torrent_priority(result):
                logging.error(self.name + ': Unable to set priority for Torrent')

        except Exception as e:
            logging.error(self.name + ': Failed Sending Torrent')
            logging.debug(self.name + ': Exception raised when sending torrent: ' + str(result) + '. Error: ' + str(e))
            return r_code

        return r_code

    def testAuthentication(self):

        try:
            self.response = self.session.get(self.url, timeout=120, verify=False)
        except requests.exceptions.ConnectionError:
            return False, 'Error: ' + self.name + ' Connection Error'
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
            return False, 'Error: Invalid ' + self.name + ' host'

        if self.response.status_code == 401:
            return False, 'Error: Invalid ' + self.name + ' Username or Password, check your config!'

        try:
            self._get_auth()
            if self.response.status_code == 200 and self.auth:
                return True, 'Success: Connected and Authenticated'
            else:
                return False, 'Error: Unable to get ' + self.name + ' Authentication, check your config!'
        except Exception:
            return False, 'Error: Unable to connect to ' + self.name
