from sickrage.core import API


class GoogleDriveAPI(API):
    def is_connected(self):
        query = 'api/v1/google-drive/is-connected'
        return self._request('GET', query)

    def clear_appdata(self):
        query = 'api/v1/google-drive/appdata/clear'
        return self._request('GET', query)

    def upload_appdata(self, name, file):
        query = 'api/v1/google-drive/appdata/upload'
        return self._request('POST', query)

    def download_appdata(self):
        query = 'api/v1/google-drive/appdata/download'
        return self._request('GET', query)