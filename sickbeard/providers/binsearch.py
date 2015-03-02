# Author: Nic Wolfe <nic@wolfeden.ca>
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

import urllib
import datetime

import sickbeard
import generic

from sickbeard import classes, show_name_helpers, helpers

from sickbeard import exceptions, logger
from sickbeard.common import *
from sickbeard import tvcache
from lib.dateutil.parser import parse as parseDate
from sickbeard.bs4_parser import BS4Parser
import re

class Binsearch(generic.NZBProvider):

    def __init__(self):

        generic.NZBProvider.__init__(self, "Binsearch")

        self.supportsBacklog = False

        self.enabled = False

        self.cache = BinsearchCache(self)

        self.urls = {'base_url': 'http://binsearch.info/'}

        self.url = self.urls['base_url']

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'binsearch.png'

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _get_title_and_url(self, row):
        if type(row) == tuple:
            title, url = row
            return (title, url)

        title = row.find('span', attrs = {'class': 's'})

        # try:
        nzb_id = row.find('input', attrs = {'type': 'checkbox'})['name']
        # info = row.find('span', attrs = {'class':'d'})
        # size_match = re.search('size:.(?P<size>[0-9\.]+.[GMB]+)', info.text)
        args = {"title": title.text, "id": nzb_id}
        url = "http://cytec.us/binsearch/index.php?" + urllib.urlencode(args)
        # except:
        #     return ("", "")

        age = 0

        try:
            age = re.search('(?P<size>\d+d)', row.find_all('td')[-1:][0].text).group('size')[:-1]
        except:
            pass

        return (title.text, url)

        def extra_check(item):
            parts = re.search('available:.(?P<parts>\d+)./.(?P<total>\d+)', info.text)
            total = float(tryInt(parts.group('total')))
            parts = float(tryInt(parts.group('parts')))

            if (total / parts) < 1 and ((total / parts) < 0.95 or ((total / parts) >= 0.95 and not ('par2' in info.text.lower() or 'pa3' in info.text.lower()))):
                log.info2('Wrong: \'%s\', not complete: %s out of %s', (item['name'], parts, total))
                return False

            if 'requires password' in info.text.lower():
                log.info2('Wrong: \'%s\', passworded', (item['name']))
                return False

            return True


    def _doSearch(self, search_string, search_mode='eponly', epcount=0, age=0):
        #https://github.com/RuudBurger/CouchPotatoServer/blob/e75a8529c99996a0ba20fdcf83d424b6597bc3f8/couchpotato/core/media/_base/providers/nzb/binsearch.py

        params = {
            "q": search_string.encode('utf-8'),
            "max": "250",
            "adv_age": "1100",
            # "adv_nfo": "on",
            "minsize": "100",
            "adv_col": "on"
        }
        #?q=German&max=100&adv_age=1100&server=
        search_url = self.url + "index.php?" + urllib.urlencode(params)

        logger.log(u"Search url: " + search_url, logger.DEBUG)

        results = []
        x = self.session.get(search_url)
        with BS4Parser(x.text, "html.parser") as html:
            main_table = html.find('table', attrs = {'id': 'r2'})

            if not main_table:
                return []

            items = main_table.find_all('tr')

            for curItem in items:
                (title, url) = self._get_title_and_url(curItem)

                if title and url:
                    i = (title, url)
                    results.append(i)
                else:
                    logger.log(
                        u"The data returned from the " + self.name + " is incomplete, this result is unusable",
                        logger.DEBUG)

            return results

    def findPropers(self, date=None):

        results = []

        for item in self._doSearch("v2|v3|v4|v5"):

            (title, url) = self._get_title_and_url(item)

            if item.has_key('published_parsed') and item['published_parsed']:
                result_date = item.published_parsed
                if result_date:
                    result_date = datetime.datetime(*result_date[0:6])
            else:
                logger.log(u"Unable to figure out the date for entry " + title + ", skipping it")
                continue

            if not date or result_date > date:
                search_result = classes.Proper(title, url, result_date, self.show)
                results.append(search_result)

        return results


class BinsearchCache(tvcache.TVCache):

    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll Fanzub every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):

        return {"entries": []}

provider = Binsearch()
