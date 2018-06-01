from sickrage.core import API


class ProviderCacheAPI(API):
    def get(self, provider, indexerid, season, episode):
        query = 'api/v1/cache/providers/{}/indexerids/{}/seasons/()/episodes/()'.format(provider, indexerid, season,
                                                                                        episode)
        return self._request('GET', query)

    def add(self, data):
        self._request('POST', 'api/v1/cache/providers', json=data)


class TorrentCacheAPI(API):
    def get(self, hash):
        query = 'api/v1/cache/torrents/{}'.format(hash)
        return self._request('GET', query)

    def add(self, url):
        self._request('POST', 'api/v1/cache/torrents', data=dict({'url': url}))
