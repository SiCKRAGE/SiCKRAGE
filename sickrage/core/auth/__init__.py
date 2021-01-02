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


import requests
from keycloak.openid_connect import KeycloakOpenidConnect
from keycloak.realm import KeycloakRealm

import sickrage


class AuthServer(object):
    __server = {}
    __client = {}

    def __init__(self):
        self.server_url = 'https://auth.sickrage.ca'
        self.server_realm = 'sickrage'
        self.client_id = 'sickrage-app'
        self._certs = None

    @property
    def client(self):
        return self.__get_client()

    @property
    def health(self):
        for i in range(3):
            try:
                health = requests.get("{base}/auth/realms/{realm}".format(base=self.server_url, realm=self.server_realm), verify=False, timeout=30).ok
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                pass
            else:
                break
        else:
            health = False

        if not health:
            sickrage.app.log.debug("SiCKRAGE authorization server is currently unreachable")
            return False

        return True

    def get_url(self, *args, **kwargs):
        try:
            return self.client.get_url(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            return

    def certs(self):
        try:
            if not self._certs and self.health:
                self._certs = self.client.certs()
            return self._certs
        except requests.exceptions.ConnectionError as e:
            return

    def logout(self, *args, **kwargs):
        if not self.health:
            return

        return self.client.logout(*args, **kwargs)

    def decode_token(self, *args, **kwargs):
        return self.client.decode_token(*args, **kwargs)

    def refresh_token(self, *args, **kwargs):
        if not self.health:
            return

        return self.client.refresh_token(*args, **kwargs)

    def authorization_code(self, *args, **kwargs):
        if not self.health:
            return

        return self.client.authorization_code(*args, **kwargs)

    def authorization_url(self, **kwargs):
        if not self.health:
            return

        return self.client.authorization_url(**kwargs)

    def token_exchange(self, access_token, scope='offline_access'):
        if not self.health:
            return

        exchange = {'scope': scope, 'subject_token': access_token}
        return self.client.token_exchange(**exchange)

    def __get_client(self) -> KeycloakOpenidConnect:
        client = self.__client.get('client', None)
        if client is None:
            self.__client.update({'client': self.__get_server().open_id_connect(self.client_id, '')})
            client = self.__client.get('client', None)
        return client

    def __get_server(self) -> KeycloakRealm:
        server = self.__server.get('server', None)
        if server is None:
            self.__server.update({'server': KeycloakRealm(server_url=self.server_url, realm_name=self.server_realm)})
            server = self.__server.get('server', None)
        return server
