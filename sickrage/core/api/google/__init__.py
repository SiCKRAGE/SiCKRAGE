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

    def delete(self, id):
        query = 'api/v1/google-drive/delete/{id}'.format(id=id)
        return self._request('GET', query)

    def search_files(self, id, term):
        query = 'api/v1/google-drive/search-files/{id}/{term}'.format(id=id, term=term)
        return self._request('GET', query)

    def list_files(self, id):
        query = 'api/v1/google-drive/list-files/{id}'.format(id=id)
        return self._request('GET', query)

    def clear_folder(self, id):
        query = 'api/v1/google-drive/clear-folder/{id}'.format(id=id)
        return self._request('GET', query)
