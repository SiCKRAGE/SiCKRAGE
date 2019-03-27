from sickrage.core.api import API


class ProviderCacheAPI(API):
    def get(self, provider, indexerid, season, episode):
        query = 'cache/providers/{}/indexerids/{}/seasons/{}/episodes/{}'.format(provider, indexerid, season, episode)
        return self._request('GET', query)

    def add(self, data):
        return self._request('POST', 'cache/providers', json=data)


class TorrentCacheAPI(API):
    def get(self, hash):
        query = 'cache/torrents/{}'.format(hash)
        return self._request('GET', query)

    def add(self, url):
        return self._request('POST', 'cache/torrents', data=dict({'url': url}))
