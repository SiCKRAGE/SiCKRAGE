# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import unittest
import sys, os.path
import urlparse

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import test_lib as test
from bs4 import BeautifulSoup
from sickbeard.helpers import getURL

class TorrentBasicTests(test.SickbeardTestDBCase):

    def test_search(self):
        self.url = 'http://kickass.to/'
        searchURL = 'http://kickass.to/usearch/American%20Dad%21%20S08%20-S08E%20category%3Atv/?field=seeders&sorder=desc'

        html = getURL(searchURL)
        if not html:
            return

        soup = BeautifulSoup(html, features=["html5lib", "permissive"])

        torrent_table = soup.find('table', attrs={'class': 'data'})
        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

        #Continue only if one Release is found
        if len(torrent_rows) < 2:
            print(u"The data returned does not contain any torrents")
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
    print "STARTING - XEM Scene Numbering TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(TorrentBasicTests)