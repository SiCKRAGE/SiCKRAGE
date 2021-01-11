# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import datetime
import re

from sickrage.core.caches.tv_cache import TVCache
from sickrage.search_providers import NZBProvider


class BinSearchProvider(NZBProvider):
    def __init__(self):
        super(BinSearchProvider, self).__init__("BinSearch", 'http://www.binsearch.info', False)
        self.supports_backlog = False

        self._urls.update({
            'rss': '{base_url}/rss.php'.format(**self._urls)
        })

        self.cache = BinSearchCache(self)


class BinSearchCache(TVCache):
    def __init__(self, provider_obj):
        TVCache.__init__(self, provider_obj, min_time=30)
        # only poll Binsearch every 30 minutes max

        # compile and save our regular expressions

        # this pulls the title from the URL in the description
        self.descTitleStart = re.compile(r'^.*https?://www\.binsearch\.info/.b=')
        self.descTitleEnd = re.compile('&amp;.*$')

        # these clean up the horrible mess of a title if the above fail
        self.titleCleaners = [
            re.compile(r'.?yEnc.?\(\d+/\d+\)$'),
            re.compile(r' \[\d+/\d+\] '),
        ]

    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

        title = item.get('description', '')
        if self.descTitleStart.match(title):
            title = self.descTitleStart.sub('', title)
            title = self.descTitleEnd.sub('', title)
            title = title.replace('+', '.')
        else:
            # just use the entire title, looks hard/impossible to parse
            title = item.get('title', '')
            for titleCleaner in self.titleCleaners:
                title = titleCleaner.sub('', title)

        url = item.get('link', '').replace('&amp;', '&')

        return title, url

    def update(self, force=False):
        # check if we should update
        if self.should_update() or force:
            # clear cache
            self.clear()

            # set updated
            self.last_update = datetime.datetime.today()

            for group in ['alt.binaries.hdtv', 'alt.binaries.hdtv.x264', 'alt.binaries.tv', 'alt.binaries.tvseries']:
                search_params = {'max': 50, 'g': group}
                for item in self.get_rss_feed(self.provider.urls['rss'], search_params).get('entries', []):
                    self._parseItem(item)

        return True

    def _check_auth(self, data):
        return data if data['feed'] and data['feed']['title'] != 'Invalid Link' else None
