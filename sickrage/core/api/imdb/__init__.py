from sickrage.core import API


class IMDbAPI(API):
    def search_by_imdb_title(self, title):
        query = 'api/v1/imdb/search-by-title/{}'.format(title)
        return self._request('GET', query)

    def search_by_imdb_id(self, id):
        query = 'api/v1/imdb/search-by-id/{}'.format(id)
        return self._request('GET', query)