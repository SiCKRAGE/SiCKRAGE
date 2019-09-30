from sickrage.core.api import API


class ProviderCacheAPI(API):
    def get(self, provider, series_id, season, episode):
        query = 'cache/provider/{}/series-id/{}/season/{}/episode/{}'.format(provider, series_id, season, episode)
        return self._request('GET', query)

    def add(self, data):
        return self._request('POST', 'cache/provider', json=data)


class TorrentCacheAPI(API):
    def get(self, hash):
        query = 'cache/torrent/{}'.format(hash)
        return self._request('GET', query)

    def add(self, url):
        return self._request('POST', 'cache/torrent', json={'url': url})
