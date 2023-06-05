import re
import traceback
import urllib
from collections import OrderedDict
from urllib.parse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size, validate_url
from sickrage.core.tv.show.helpers import find_show
from sickrage.search_providers import TorrentProvider


class KickAssTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(KickAssTorrentsProvider, self).__init__('KickAssTorrents', 'https://kickasskat.org', False)

        # custom settings
        self.custom_settings = {
            'custom_url': '',
            'confirmed': False,
            'minseed': 0,
            'minleech': 0
        }

        self.mirrors = []
        self.disabled_mirrors = []

        # https://kickasskat.org/tv?field=time_add&sorder=desc
        # https://kickasskat.org/usearch/{query} category:tv/?field=seeders&sorder=desc

        self.cache = TVCache(self)

        self.rows_selector = dict(class_=re.compile(r"even|odd"), id=re.compile(r"torrent_.*_torrents"))

    @property
    def urls(self):
        return {
            "search": f'{self.url}/usearch/%s/',
            "rss": f'{self.url}/tv/'
        }

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []
        if not (self.url and self.urls):
            self.find_domain()
            if not (self.url and self.urls):
                return results

        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return results

        search_params = OrderedDict(field="seeders", sorder="desc")

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {mode}".format(mode=mode))
            for search_string in {*search_strings[mode]}:
                # search_params["q"] = (search_string, None)[mode == "RSS"]
                search_params["field"] = ("seeders", "time_add")[mode == "RSS"]

                if mode != "RSS":
                    if show_object.anime:
                        continue

                    sickrage.app.log.debug(f"Search String: {search_string}")

                    search_url = self.urls['search'] % search_string + f' category:{("tv", "anime")[show_object.anime]}'
                else:
                    search_url = self.urls["rss"]

                if self.custom_settings['custom_url']:
                    if not validate_url(self.custom_settings['custom_url']):
                        sickrage.app.log.warning("Invalid custom url: {0}".format(self.custom_settings['custom_url']))
                        return results
                    search_url = urljoin(self.custom_settings['custom_url'], search_url.split(self.url)[1])

                resp = self.session.get(search_url, params=search_params, random_ua=True)
                if not resp or not resp.text:
                    sickrage.app.log.info("{url} did not return any data, it may be disabled. Trying to get a new domain".format(url=self.url))
                    self.disabled_mirrors.append(self.url)
                    self.find_domain()
                    if self.url in self.disabled_mirrors:
                        sickrage.app.log.info("Could not find a better mirror to try.")
                        sickrage.app.log.info("The search did not return data, if the results are on the site maybe try a custom url, or a different one")
                        return results

                    # This will recurse a few times until all of the mirrors are exhausted if none of them work.
                    return self.search(search_strings, age, series_id, series_provider_id, season, episode)

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
            labels = [cell.get_text() for cell in html.find(class_="firstr")("th")]
            sickrage.app.log.info("Found {} results".format(len(html("tr", **self.rows_selector))))
            for result in html("tr", **self.rows_selector):
                try:
                    download_url = urllib.parse.unquote_plus(result.find(title="Torrent magnet link")["href"].split("url=")[1])
                    parsed_magnet = urllib.parse.parse_qs(download_url)
                    title = result.find(class_="torrentname").find(class_="cellMainLink").get_text(strip=True)
                    if title.endswith("..."):
                        title = parsed_magnet["dn"][0]

                    if not (title and download_url):
                        if mode != "RSS":
                            sickrage.app.log.debug("Discarding torrent because We could not parse the title and url")
                        continue

                    seeders = try_int(result.find(class_="green").get_text(strip=True))
                    leechers = try_int(result.find(class_="red").get_text(strip=True))

                    if self.custom_settings['confirmed'] and not result.find(class_="ka-green"):
                        if mode != "RSS":
                            sickrage.app.log.debug("Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it")
                        continue

                    torrent_size = result("td")[labels.index("size")].get_text(strip=True)
                    size = convert_size(torrent_size, -1)

                    results += [
                        {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers}
                    ]

                    if mode != "RSS":
                        sickrage.app.log.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))
                except (AttributeError, TypeError, KeyError, ValueError, Exception):
                    sickrage.app.log.info(traceback.format_exc())
                    continue

        return results

    def find_domain(self):
        resp = self.session.get("https://ww1.kickass.help/")
        if not resp or not resp.text:
            return self.url

        with bs4_parser(resp.text) as html:
            mirrors = html(class_="domainLink")
            if mirrors:
                self.mirrors = []

            for mirror in mirrors:
                domain = mirror["href"].rstrip('/')
                if domain and domain not in self.disabled_mirrors:
                    self.mirrors.append(domain)

        if self.mirrors:
            self.url = self.mirrors[0]
            sickrage.app.log.info("Setting mirror to use to {url}".format(url=self.url))
        else:
            sickrage.app.log.warning(
                "Unable to get a working mirror for KickassTorrent. You might need to enable another provider and disable KAT until it starts working again."
            )

        return self.url
