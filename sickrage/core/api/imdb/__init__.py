from sickrage.core.api import API


class IMDbAPI(API):
    def search_by_imdb_title(self, title):
        query = 'imdb/search-by-title/{}'.format(title)
        return self._request('GET', query)

    def search_by_imdb_id(self, id):
        query = 'imdb/search-by-id/{}'.format(id)
        return self._request('GET', query)
