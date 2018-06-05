from sickrage.core import API


class GoogleDriveAPI(API):
    def is_connected(self):
        query = 'api/v1/google-drive/is-connected'
        return self._request('GET', query)

    def upload(self, file, folder):
        query = 'api/v1/google-drive/upload'
        return self._request('POST', query, files={'file': open(file, 'rb')}, params={'folder': folder})

    def download(self, id):
        query = 'api/v1/google-drive/download/{id}'.format(id=id)
        return self._request('GET', query)

    def list_appdata(self):
        query = 'api/v1/google-drive/appdata'
        return self._request('GET', query)

    def clear_appdata(self):
        query = 'api/v1/google-drive/appdata/clear'
        return self._request('GET', query)
