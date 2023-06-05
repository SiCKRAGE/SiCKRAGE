from urllib.parse import urljoin

from markdown2 import _slugify as slugify

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import try_int, convert_size, validate_url, bs4_parser
from sickrage.search_providers import TorrentProvider


class MagnetDLProvider(TorrentProvider):
    def __init__(self):
        super().__init__("MagnetDL", "https://www.magnetdl.com", False)

        # custom settings
        self.custom_settings = {
            'custom_url': '',
            'confirmed': False,
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self)

    @property
    def urls(self):
        return {
            'rss': f'{self.url}/download/tv/age/desc/'
        }

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {mode}".format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    sickrage.app.log.debug("Search String: {search_string}".format(search_string=search_string))
                    search = slugify(search_string)
                    search_url = urljoin(self.url, "{}/{}/".format(search[0], search))
                else:
                    search_url = self.urls["rss"]

                if self.custom_settings['custom_url']:
                    if not validate_url(self.custom_settings['custom_url']):
                        sickrage.app.log.warning("Invalid custom url: {0}".format(self.custom_settings['custom_url']))
                        return results
                    search_url = urljoin(self.custom_settings['custom_url'], search_url.split(self.url)[1])

                resp = self.session.get(search_url, headers={"Accept": "application/html"})
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
            torrent_table = html.find("table", class_="download")
            torrent_body = torrent_table.find("tbody") if torrent_table else []
            torrent_rows = torrent_body("tr") if torrent_body else []

            # Continue only if at least one Release is found
            if not torrent_rows:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            labels = [x.get_text(strip=True) for x in torrent_table.find("thead").find("tr")("th")]

            # Skip column headers
            for result in torrent_rows[0:-1:2]:
                try:
                    if len(result("td")) < len(labels):
                        continue

                    title = result.find("td", class_="n").find("a")["title"]
                    magnet = result.find("td", class_="m").find("a")["href"]
                    seeders = try_int(result.find("td", class_="s").get_text(strip=True))
                    leechers = try_int(result.find("td", class_="l").get_text(strip=True))
                    size = convert_size(result("td")[labels.index("Size")].get_text(strip=True) or "", -1)

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
