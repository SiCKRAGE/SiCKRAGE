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

from sickrage.core.api import API


class AccountAPI(API):
    def register_app_id(self):
        return self._request('GET', 'account/app-id')

    def unregister_app_id(self, app_id):
        data = {
            'app-id': app_id
        }

        return self._request('DELETE', 'account/app-id', data=data)

    def upload_config(self, app_id, pkey_sig, config):
        data = {
            'app-id': app_id,
            'pkey-sig': pkey_sig,
            'config': config
        }
        return self._request('POST', 'account/config', data=data)

    def download_config(self, pkey_sig):
        data = {
            'pkey-sig': pkey_sig
        }

        return self._request('GET', 'account/config', json=data)['config']
