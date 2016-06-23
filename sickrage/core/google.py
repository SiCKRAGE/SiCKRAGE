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

import os
import pickle

from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials

import sickrage


class googleAuth(object):
    def __init__(self):
        self.filename = 'google.db'

        self.client_id = '48901323822-ebum0n1ago1bo2dku4mqm9l6kl2j60uv.apps.googleusercontent.com'
        self.client_secret = 'vFQy_bojwJ1f2X0hYD3wPu7U'
        self.scopes = ['https://www.googleapis.com/auth/drive.file',
                       'email',
                       'profile']

        self.credentials = self.load()

        self.flow = OAuth2WebServerFlow(self.client_id, self.client_secret, ' '.join(self.scopes))

    def get_user_code(self):
        return self.flow.step1_get_device_and_user_codes()

    def get_credentials(self, flow_info):
        self.credentials = self.flow.step2_exchange(device_flow_info=flow_info)
        self.save()

        return self.credentials

    def refresh_credentials(self):
        if isinstance(self.credentials, OAuth2Credentials):
            self.credentials.refresh(sickrage.srCore.srWebSession)

    def logout(self):
        self.credentials = ""
        self.save()

    def save(self):
        pickle.dump(self.credentials, open(os.path.join(sickrage.DATA_DIR, self.filename), 'wb'))

    def load(self):
        if os.path.isfile(os.path.join(sickrage.DATA_DIR, self.filename)):
            return pickle.load(open(os.path.join(sickrage.DATA_DIR, self.filename), 'rb'))
        return ""
