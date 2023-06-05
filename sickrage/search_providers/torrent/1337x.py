import re
from urllib.parse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import try_int, convert_size, validate_url, bs4_parser
from sickrage.search_providers import TorrentProvider


class LeetxProvider(TorrentProvider):
    def __init__(self):
        super().__init__("1337x", "https://1337x.to", False)

        # custom settings
        self.custom_settings = {
            'custom_url': '',
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self)

    @property
    def urls(self):
        return {
            "search": f'{self.url}/sort-search/%s/seeders/desc/',
            'rss': f'{self.url}/cat/TV/'
        }

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {mode}".format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    sickrage.app.log.debug("Search String: {search_string}".format(search_string=search_string))
                    search_url = self.urls['search'] % search_string
                else:
                    search_url = self.urls["rss"]

                if self.custom_settings['custom_url']:
                    if not validate_url(self.custom_settings['custom_url']):
                        sickrage.app.log.warning("Invalid custom url: {0}".format(self.custom_settings['custom_url']))
                        return results
                    search_url = urljoin(self.custom_settings['custom_url'], search_url.split(self.url)[1])

                page = 0
                while page <= 10:
                    page += 1
                    resp = self.session.get(urljoin(search_url, f'{page}/'))
                    if not resp or not resp.text:
                        sickrage.app.log.debug("No data returned from provider")
                        continue

                    results += self.parse(resp.text, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find('table', {'class': 'table-list'})
            if not torrent_table:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            rows = torrent_table.tbody.find_all('tr')
            for row in rows:
                try:
                    name_col = row.find('td', {'class': 'coll-1 name'})
                    title = name_col.a.next_sibling.get_text(strip=True)
                    magnet = self.extract_magnet_link(self.url + name_col.a.next_sibling['href'])
                    seeders = try_int(row.find('td', {'class': 'coll-2 seeds'}).get_text(strip=True))
                    leechers = try_int(row.find('td', {'class': 'coll-3 leeches'}).get_text(strip=True))
                    size = convert_size(row.find('td', {'class': 'coll-4'}).get_text(strip=True), -1)

                    if not all([title, magnet]):
                        continue

                    results += [
                        {"title": title, "link": magnet, "size": size, "seeders": seeders, "leechers": leechers}
                    ]

                    if mode != "RSS":
                        sickrage.app.log.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))
                except Exception as error:
                    sickrage.app.log.debug(f"Failed parsing provider. Traceback: {error}")
                    continue

        return results

    def extract_magnet_link(self, url):
        resp = self.session.get(url)
        with bs4_parser(resp.text) as html:
            magnet_link = html.find('a', href=re.compile(r'^magnet:\?')).get('href')
            return magnet_link
