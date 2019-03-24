from sickrage.core.api import API


class GoogleDriveAPI(API):
    def is_connected(self):
        query = 'google-drive/is-connected'
        return self._request('GET', query)

    def upload(self, file, folder):
        query = 'google-drive/upload'
        return self._request('POST', query, files={'file': open(file, 'rb')}, params={'folder': folder})

    def download(self, id):
        query = 'google-drive/download/{id}'.format(id=id)
        return self._request('GET', query)

    def delete(self, id):
        query = 'google-drive/delete/{id}'.format(id=id)
        return self._request('GET', query)

    def search_files(self, id, term):
        query = 'google-drive/search-files/{id}/{term}'.format(id=id, term=term)
        return self._request('GET', query)

    def list_files(self, id):
        query = 'google-drive/list-files/{id}'.format(id=id)
        return self._request('GET', query)

    def clear_folder(self, id):
        query = 'google-drive/clear-folder/{id}'.format(id=id)
        return self._request('GET', query)
