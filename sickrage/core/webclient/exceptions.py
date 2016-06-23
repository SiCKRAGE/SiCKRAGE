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

import ssl
import traceback
from functools import wraps

import requests

import sickrage


def handle_exception(func):
    @wraps(func)
    def handle(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.SSLError as e:
            if ssl.OPENSSL_VERSION_INFO < (1, 0, 1, 5):
                sickrage.srCore.srLogger.info(
                    "SSL Error requesting url: '{}' You have {}, try upgrading OpenSSL to 1.0.1e+".format(e.request.url,
                                                                                                          ssl.OPENSSL_VERSION))

            if sickrage.srCore.srConfig.SSL_VERIFY:
                sickrage.srCore.srLogger.info(
                    "SSL Error requesting url: '{}' Try disabling Cert Verification under advanced settings")

            sickrage.srCore.srLogger.exception("SSL Error: {}".format(e))
            sickrage.srCore.srLogger.debug(traceback.format_exc())
        except requests.exceptions.RequestException as e:
            sickrage.srCore.srLogger.exception("Request failed: {}".format(e))
            sickrage.srCore.srLogger.debug(traceback.format_exc())

    return handle
