from sickrage.core import API


class ProviderCacheAPI(API):
    def get(self, provider, indexerid, season, episode):
        query = 'cache/providers/{}/indexerids/{}/seasons/()/episodes/()'.format(provider, indexerid, season,
                                                                                        episode)
        return self._request('GET', query)

    def add(self, data):
        self._request('POST', 'cache/providers', json=data)


class TorrentCacheAPI(API):
    def get(self, hash):
        query = 'cache/torrents/{}'.format(hash)
        return self._request('GET', query)

    def add(self, url):
        self._request('POST', 'cache/torrents', data=dict({'url': url}))
