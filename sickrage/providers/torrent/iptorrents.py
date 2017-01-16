# Author: seedboy
# URL: https://github.com/seedboy
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.providers import TorrentProvider


class IPTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(IPTorrentsProvider, self).__init__("IPTorrents", 'iptorrents.eu', True)

        self.supports_backlog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.enable_cookies = True

        self.cache = TVCache(self, min_time=10)

        self.urls.update({
            'login': '{base_url}/take_login.php'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/t?%s%s&q=%s&qf=#torrents'.format(base_url=self.urls['base_url'])
        })

        self.categories = '73=&60='

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        cookie_dict = dict_from_cookiejar(self.cookie_jar)
        if cookie_dict.get('uid') and cookie_dict.get('pass'):
            return True

        if not self.add_cookies_from_ui():
            return False

        login_params = {'username': self.username, 'password': self.password, 'login': 'submit'}

        response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30)
        if not response.ok:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        # Invalid username and password combination
        if re.search('Invalid username and password combination', response.text):
            sickrage.srCore.srLogger.warning(u"Invalid username or password. Check your settings")
            return False

        # You tried too often, please try again after 2 hours!
        if re.search('You tried too often', response.text):
            sickrage.srCore.srLogger.warning(u"You tried too often, please try again after 2 hours! Disable IPTorrents for at least 2 hours")
            return False

        # Captcha!
        if re.search('Captcha verification failed.', response.text):
            sickrage.srCore.srLogger.warning(u"Stupid captcha")
            return False

        return True

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        freeleech = '&free=on' if self.freeleech else ''

        if not self.login():
            return results

        for mode in search_params.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                # URL with 50 tv-show results, or max 150 if adjusted in IPTorrents profile
                searchURL = self.urls['search'] % (self.categories, freeleech, search_string)
                searchURL += ';o=seeders' if mode != 'RSS' else ''
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    data = re.sub(r'(?im)<button.+?<[/]button>', '', data, 0)
                    with bs4_parser(data) as html:
                        if not html:
                            sickrage.srCore.srLogger.debug("No data returned from provider")
                            continue

                        if html.find(text='No Torrents Found!'):
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        torrent_table = html.find('table', attrs={'class': 'torrents'})
                        torrents = torrent_table.find_all('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrents) < 2:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        for result in torrents[1:]:
                            try:
                                title = result.find_all('td')[1].find('a').text
                                download_url = self.urls['base_url'] + result.find_all('td')[3].find('a')['href']
                                size = convert_size(result.find_all('td')[5].text)
                                seeders = int(result.find('td', attrs={'class': 'ac t_seeders'}).text)
                                leechers = int(result.find('td', attrs={'class': 'ac t_leechers'}).text)
                            except (AttributeError, TypeError, KeyError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    sickrage.srCore.srLogger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers))
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug("Found result: %s " % title)

                            items[mode].append(item)

                except Exception as e:
                    sickrage.srCore.srLogger.error("Failed parsing provider. Error: %r" % e)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio
