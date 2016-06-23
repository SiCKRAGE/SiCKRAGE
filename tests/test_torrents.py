#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import unittest
import urlparse

from sickrage.core import srSession
from sickrage.core.helpers import bs4_parser
from tests import SiCKRAGETestDBCase


class TorrentBasicTests(SiCKRAGETestDBCase):
    def test_search(self):
        self.url = 'kickass.unblocked.li'
        searchURL = '{}/usearch/American%20Dad%20S08/'.format(self.url)

        data = srSession().get(searchURL)
        if not data:
            return

        with bs4_parser(data) as html:
            torrent_table = html.find('table', attrs={'class': 'data'})

        # Continue only if one Release is found
        torrent_rows = torrent_table.find_all('tr') if torrent_table else []
        if len(torrent_rows) < 2:
            print("The data returned does not contain any torrents")
            return

        for tr in torrent_rows[1:]:
            try:
                link = urlparse.urljoin(self.url, (tr.find('div', {'class': 'torrentname'}).find_all('a')[1])['href'])
                id = tr.get('id')[-7:]
                title = (tr.find('div', {'class': 'torrentname'}).find_all('a')[1]).text \
                        or (tr.find('div', {'class': 'torrentname'}).find_all('a')[2]).text
                url = tr.find('a', 'imagnet')['href']
                verified = True if tr.find('a', 'iverify') else False
                trusted = True if tr.find('img', {'alt': 'verified'}) else False
                seeders = int(tr.find_all('td')[-2].text)
                leechers = int(tr.find_all('td')[-1].text)
            except (AttributeError, TypeError):
                continue

            print title


if __name__ == "__main__":
    print "=================="
    print "STARTING - TORRENT TESTS"
    print "=================="
    print "######################################################################"
    unittest.main()
