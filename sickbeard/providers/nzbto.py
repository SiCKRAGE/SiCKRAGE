#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Jordon Smith <smith@jordon.me.uk>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import urllib

import sickbeard
import generic

from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import classes
from sickbeard import logger
from sickrage.helper.exceptions import ex, AuthException
from sickbeard import show_name_helpers
from datetime import datetime

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree

try:
    import json
except ImportError:
    from lib import simplejson as json

import re
import time
from sickbeard.bs4_parser import BS4Parser

class NzbtoProvider(generic.NZBProvider):
    def __init__(self):
        generic.NZBProvider.__init__(self, "nzbto")
        self.enabled = False
        self.username = None
        self.api_key = None
        self.cache = NzbtoCache(self)

        self.urls = {'base_url': 'http://nzb.to/'}
        self.url = self.urls['base_url']
        self.session.headers["Referer"] = "http://nzb.to/login"
        self.session.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:20.0) Gecko/20100101 Firefox/20.0"

        self.supportsBacklog = True

    def isEnabled(self):
        return self.enabled

    def _checkAuth(self):

        if not self.username or not self.api_key:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _get_size(self, item):
        return -1

    def _get_title_and_url(self, item):
        if type(item) == tuple:
            title, url = item
            return title, url

        try:
            cur_el = item.tr.find("td", attrs={"class": "title"}).find("a")
            tmp_title = cur_el.text
            dl = item.find("a", attrs={"title": "NZB erstellen"})
            dl = cur_el
            tmp_url = "http://nzb.to/inc/ajax/popupdetails.php?n=" + cur_el["href"].split("nid=")[1]

            while True:
                x = self.session.get(tmp_url)

                if not x.status_code == 200:
                    logger.log('to much hits on nzb.to trying again in 5 seconds', logger.DEBUG)
                    time.sleep(5)

                if x.status_code == 200:
                    break

            x = self.session.get(tmp_url)
            pw = False
            p00_test3 = ""
            with BS4Parser(x.text, "html.parser") as html:
                pw = html.find('span', attrs={"style": "color:#ff0000"})
                if pw:
                    pw = pw.strong
                    #logger.log('Password Check: {{%s}}' %(pw.strip()), logger.DEBUG)
                    pw = pw.next
                    #logger.log('Password Check0: {{%s}}' %(pw.strip()), logger.DEBUG)
                    pw = pw.next
                    #logger.log('Password Check1: {{%s}}' %(pw.strip()), logger.DEBUG)
                    p00_test = unicode(pw.string)
                    #ogger.log('Password Check2: {{%s}}' %(p00_test), logger.DEBUG)
                    p00_test2 = p00_test.decode(encoding='ascii',errors='ignore')
                    #logger.log('Password Check3: {{%s}}' %(p00_test2), logger.DEBUG)
                    p00_test3 = self.strip_non_ascii(p00_test2)
                    #logger.log('Password Check4: {{%s}}' %(p00_test3), logger.DEBUG)

            if not pw or pw.strip() == "-":
                title = tmp_title
            else:
                #title = "%s{{%s}}" % (tmp_title, pw.strip())
                #logger.log('Password found: {{%s}}' %(pw.strip()), logger.DEBUG)
                title = "%s{{%s}}" % (tmp_title, p00_test3)
                logger.log('Password found: {{%s}}' %(p00_test3), logger.DEBUG)

            params = {"nid": dl["href"].split("nid=")[1], "user": self.username, "pass": self.api_key, "rel": title}
            url = 'http://cytec.us/nzbto/index.php?' + urllib.urlencode(params)

            logger.log( '_get_title_and_url(), returns (%s, %s)' %(title, url), logger.DEBUG)

            return (title, url)
        except AttributeError:
            return "", ""

    def _doSearch(self, search, search_mode='eponly', epcount=0, retention=0, epObj=None):

        self._checkAuth()
        self.session.post("http://nzb.to/login.php", data={"action": "login", "username": self.username, "password": self.api_key, "Submit": ".%3AEinloggen%3A.", "ret_url": ""})
        logger.log( 'sending login to nzb.to returned Cookie: {0}'.format(self.session.cookies.get_dict()), logger.DEBUG)

        term =  re.sub('[\.\-\:]', ' ', search).encode('utf-8')

        #http://nzb.to/?p=list&q=Shameless+S03E12+german&cat=13&sort=post_date&order=desc&amount=50
        params = {"q": term,
                  "sort": "post_date", #max 50
                  "order": "desc", #nospam
                  "amount": 25, #min 100MB
                  "retention": retention,
                  "cat": 13
                  }

        searchURL = "http://nzb.to/?p=list&" + urllib.urlencode(params)

        logger.log(u"Search string: " + searchURL)

        logger.log(u"Sleeping 10 seconds to respect NZBto's rules")
        time.sleep(10)

        #logger.log(u"CURRENT COOKIE: {0}".format(self.session.cookies.get_dict()))

        cookie_test = re.compile(r"[0-9]*-\d{1}-.*")
        if re.match(cookie_test, self.session.cookies.get("NZB_SID") ):
            logger.log("ERROR... COOKIE SEEMS NOT TO BE VALID", logger.ERROR)

        #searchResult = self.getURL(searchURL,[("User-Agent","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:5.0) Gecko/20100101 Firefox/5.0"),("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),("Accept-Language","de-de,de;q=0.8,en-us;q=0.5,en;q=0.3"),("Accept-Charset","ISO-8859-1,utf-8;q=0.7,*;q=0.7"),("Connection","keep-alive"),("Cache-Control","max-age=0")])
        if search == "cache":
            url = "http://nzb.to/?p=list&cat=13&sa_Video-Genre=3221225407&sort=post_date&order=desc&amount=50"
            logger.log(url)
            searchResult = self.session.get(url)
            #logger.log(u"{0}".format(searchResult))
        else:
            searchResult = self.session.get("http://nzb.to/?p=list", params=params)

        if not searchResult:
            logger.log("Search gave no results...")
            return []

        # x = open("test.html", "w")
        # x.write(searchResult.text)
        # x.close()
        # import sys
        # sys.exit(1)
        results = []
        try:
            with BS4Parser(searchResult.text, "html.parser") as html:
                table_regex = re.compile(r'tbody-.*')
                items = html.find_all('tbody', id=table_regex)

                if len(items) > 0:
                    # logger.log("found %d result/s" % len(items))
                    for curItem in items:
                        title, url = self._get_title_and_url(curItem)

                        if not title or not url:
                            logger.log(u"The XML returned from the NZBto HTML feed is incomplete, this result is unusable")
                            continue

                        if title != 'Not_Valid' and title != "":
                            i = title, url
                            results.append(i)

                #print results
                # print results
                return results


                #items = html.find_all("tbody", id=table_regex)
        except Exception, e:
            logger.log(u"Error trying to load NZBto HTML feed: " + ex(e), logger.ERROR)
            return []

        # print items
        # results = []

        # for curItem in items:
        #     print curItem
        #     print items
        #     (title, url) = self._get_title_and_url(curItem)

        #     if not title or not url:
        #         logger.log(u"The XML returned from the NZBto HTML feed is incomplete, this result is unusable", logger.ERROR)
        #         continue
        #     if not title == 'Not_Valid':
        #         results.append(curItem)

        return results

    def strip_non_ascii(self, string):
        ''' Returns the string without non ASCII characters'''
        stripped = (c for c in string if 0 < ord(c) < 127)
        return ''.join(stripped)

    def findPropers(self, search_date=None):
        search_terms = ['.PROPER.', '.REPACK.']
        results = []
        for term in search_terms:
            for item in self._doSearch(term, retention=4):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.today(), self.show))
        return results


class NzbtoCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)
        self.minTime = 20

    def _getRSSData(self):
        result = {'entries': self.provider._doSearch("cache")}
        return result

provider = NzbtoProvider()
