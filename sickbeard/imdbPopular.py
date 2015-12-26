#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: Nic Wolfe <nic@wolfeden.ca>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
import os
import requests
import sickbeard

from datetime import date
from bs4 import BeautifulSoup
from sickbeard import helpers
from sickrage.helper.encoding import ek


class imdbPopular(object):
    def __init__(self):
        """Gets a list of most popular TV series from imdb"""

        # Use akas.imdb.com, just like the imdb lib.
        self.url = 'http://akas.imdb.com/search/title'

        self.params = {
            'at': 0,
            'sort': 'moviemeter',
            'title_type': 'tv_series',
            'year': '%s,%s' % (date.today().year - 1, date.today().year + 1)
        }

        self.session = requests.Session()

    def fetch_popular_shows(self):
        """Get popular show information from IMDB"""

        popular_shows = []

        data = helpers.getURL(self.url, session=self.session, params=self.params,
                              headers={'Referer': 'http://akas.imdb.com/'})
        if not data:
            return None

        soup = BeautifulSoup(data, 'html.parser')
        results = soup.find("table", {"class": "results"})
        rows = results.find_all("tr")

        for row in rows:
            show = {}
            image_td = row.find("td", {"class": "image"})

            if image_td:
                image = image_td.find("img")
                show[b'image_url_large'] = self.change_size(image[b'src'], 3)
                show[b'image_path'] = ek(os.path.join, 'images', 'imdb_popular',
                                        ek(os.path.basename, show[b'image_url_large']))

                self.cache_image(show[b'image_url_large'])

            td = row.find("td", {"class": "title"})

            if td:
                show[b'name'] = td.find("a").contents[0]
                show[b'imdb_url'] = "http://www.imdb.com" + td.find("a")["href"]
                show[b'imdb_tt'] = show[b'imdb_url'][-10:][0:9]
                show[b'year'] = td.find("span", {"class": "year_type"}).contents[0].split(" ")[0][1:]

                rating_all = td.find("div", {"class": "user_rating"})
                if rating_all:
                    rating_string = rating_all.find("div", {"class": "rating rating-list"})
                    if rating_string:
                        rating_string = rating_string[b'title']

                        match = re.search(r".* (.*)\/10.*\((.*)\).*", rating_string)
                        if match:
                            matches = match.groups()
                            show[b'rating'] = matches[0]
                            show[b'votes'] = matches[1]
                        else:
                            show[b'rating'] = None
                            show[b'votes'] = None
                else:
                    show[b'rating'] = None
                    show[b'votes'] = None

                outline = td.find("span", {"class": "outline"})
                if outline:
                    show[b'outline'] = outline.contents[0]
                else:
                    show[b'outline'] = ''

                popular_shows.append(show)

        return popular_shows

    @staticmethod
    def change_size(image_url, factor=3):
        match = re.search("^(.*)V1._(.{2})(.*?)_(.{2})(.*?),(.*?),(.*?),(.*?)_.jpg$", image_url)

        if match:
            matches = match.groups()
            ek(os.path.basename, image_url)
            matches = list(matches)
            matches[2] = int(matches[2]) * factor
            matches[4] = int(matches[4]) * factor
            matches[5] = int(matches[5]) * factor
            matches[6] = int(matches[6]) * factor
            matches[7] = int(matches[7]) * factor

            return "%sV1._%s%s_%s%s,%s,%s,%s_.jpg" % (matches[0], matches[1], matches[2], matches[3], matches[4],
                                                      matches[5], matches[6], matches[7])
        else:
            return image_url

    def cache_image(self, image_url):
        """
        Store cache of image in cache dir
        :param image_url: Source URL
        """
        path = ek(os.path.abspath, ek(os.path.join, sickbeard.CACHE_DIR, 'images', 'imdb_popular'))

        if not ek(os.path.exists, path):
            ek(os.makedirs, path)

        full_path = ek(os.path.join, path, ek(os.path.basename, image_url))

        if not ek(os.path.isfile, full_path):
            helpers.download_file(image_url, full_path, session=self.session)


imdb_popular = imdbPopular()
