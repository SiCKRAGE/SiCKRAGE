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
