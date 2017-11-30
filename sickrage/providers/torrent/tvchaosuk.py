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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import sanitizeSceneName, show_names, bs4_parser
from sickrage.providers import TorrentProvider


class TVChaosUKProvider(TorrentProvider):
    def __init__(self):
        super(TVChaosUKProvider, self).__init__('TvChaosUK', 'https://www.tvchaosuk.com', True)

        self.urls.update({
            'login': '{base_url}/takelogin.php'.format(**self.urls),
            'index': '{base_url}/index.php'.format(**self.urls),
            'search': '{base_url}/browse.php'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self, min_time=20)

    def _check_auth(self):
        if self.username and self.password:
            return True

        raise AuthException('Your authentication credentials for ' + self.name + ' are missing, check your config.')

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}

        for show_name in set(show_names.allPossibleShowNames(ep_obj.show)):
            for sep in ' ', ' - ':
                season_string = show_name + sep + 'Series '
                if ep_obj.show.air_by_date or ep_obj.show.sports:
                    season_string += str(ep_obj.airdate).split('-')[0]
                elif ep_obj.show.anime:
                    season_string += '%d' % ep_obj.scene_absolute_number
                else:
                    season_string += '%d' % int(ep_obj.scene_season)

                search_string['Season'].append(re.sub(r'\s+', ' ', season_string.replace('.', ' ').strip()))

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        for show_name in set(show_names.allPossibleShowNames(ep_obj.show)):
            for sep in ' ', ' - ':
                ep_string = sanitizeSceneName(show_name) + sep
                if ep_obj.show.air_by_date:
                    ep_string += str(ep_obj.airdate).replace('-', '|')
                elif ep_obj.show.sports:
                    ep_string += str(ep_obj.airdate).replace('-', '|') + '|' + ep_obj.airdate.strftime('%b')
                elif ep_obj.show.anime:
                    ep_string += '%i' % int(ep_obj.scene_absolute_number)
                else:
                    ep_string += sickrage.app.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                               'episodenumber': ep_obj.scene_episode}

                if add_string:
                    ep_string += ' %s' % add_string

                search_string['Episode'].append(re.sub(r'\s+', ' ', ep_string.replace('.', ' ').strip()))

        return [search_string]

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username, 'password': self.password}

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider".format(self.name))
            return False

        if re.search('Error: Username or password incorrect!', response):
            sickrage.app.log.warning(
                "Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        search_params = {
            'do': 'search',
            'keywords': '',
            'search_type': 't_name',
            'category': 0,
            'include_dead_torrents': 'no',
        }

        if not self.login():
            return results

        for mode in search_strings.keys():
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                search_params['keywords'] = search_string.strip()

                try:
                    data = self.session.get(self.urls['search'], params=search_params).text
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                with bs4_parser(data) as html:
                    torrent_table = html.find(id='listtorrents').find_all('tr')
                    for torrent in torrent_table:
                        try:
                            title = torrent.find(attrs={'class': 'tooltip-content'}).text.strip()
                            download_url = torrent.find(title="Click to Download this Torrent!").parent['href'].strip()
                            seeders = int(torrent.find(title='Seeders').text.strip())
                            leechers = int(torrent.find(title='Leechers').text.strip())

                            if not all([title, download_url]):
                                continue

                            # Chop off tracker/channel prefix or we cant parse the result!
                            show_name_first_word = re.search(r'^[^ .]+', search_params['keywords']).group()
                            if not title.startswith(show_name_first_word):
                                title = re.match(r'(.*)(' + show_name_first_word + '.*)', title).group(2)

                            # Change title from Series to Season, or we can't parse
                            if 'Series' in search_params['keywords']:
                                title = re.sub(r'(?i)series', 'Season', title)

                            # Strip year from the end or we can't parse it!
                            title = re.sub(r'[. ]?\(\d{4}\)', '', title)

                            # FIXME
                            size = -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                    'leechers': leechers}

                            if mode != 'RSS':
                                sickrage.app.log.debug("Found result: {}".format(title))

                            results.append(item)
                        except Exception:
                            sickrage.app.log.error("Failed parsing provider.")

        return results
