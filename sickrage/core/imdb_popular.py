#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import datetime
import os
import re

import sickrage
from sickrage.core.helpers import bs4_parser



class imdbPopular(object):
    def __init__(self):
        """Gets a list of most popular TV series from imdb"""

        # Use akas.imdb.com, just like the imdb lib.
        self.url = 'http://akas.imdb.com/search/title'

        self.params = {
            'at': 0,
            'sort': 'moviemeter',
            'title_type': 'tv_series',
            'year': '%s,%s' % (datetime.date.today().year - 1, datetime.date.today().year + 1)
        }

        self.session = sickrage.srCore.srWebSession

    def fetch_popular_shows(self):
        """Get popular show information from IMDB"""

        popular_shows = []

        data = self.session.get(self.url, headers={'Referer': 'http://akas.imdb.com/'}, params=self.params).text
        if not data:
            return None

        with bs4_parser(data) as soup:
            results = soup.find("table", {"class": "results"}).find_all("tr")

            for result in results:
                show = {}
                image_td = result.find("td", {"class": "image"})

                if image_td:
                    image = image_td.find("img")
                    show['image_url_large'] = self.change_size(image['src'], 3)
                    show['image_path'] = os.path.join('images', 'imdb_popular',
                                                       os.path.basename(show['image_url_large']))

                    self.cache_image(show['image_url_large'])

                td = result.find("td", {"class": "title"})

                if td:
                    show['name'] = td.find("a").contents[0]
                    show['imdb_url'] = "http://www.imdb.com" + td.find("a")["href"]
                    show['imdb_tt'] = show['imdb_url'][-10:][0:9]
                    show['year'] = td.find("span", {"class": "year_type"}).contents[0].split(" ")[0][1:]

                    rating_all = td.find("div", {"class": "user_rating"})
                    if rating_all:
                        rating_string = rating_all.find("div", {"class": "rating rating-list"})
                        if rating_string:
                            rating_string = rating_string['title']

                            match = re.search(r".* (.*)\/10.*\((.*)\).*", rating_string)
                            if match:
                                matches = match.groups()
                                show['rating'] = matches[0]
                                show['votes'] = matches[1]
                            else:
                                show['rating'] = None
                                show['votes'] = None
                    else:
                        show['rating'] = None
                        show['votes'] = None

                    outline = td.find("span", {"class": "outline"})
                    if outline:
                        show['outline'] = outline.contents[0]
                    else:
                        show['outline'] = ''

                    popular_shows.append(show)

        return popular_shows

    @staticmethod
    def change_size(image_url, factor=3):
        match = re.search("^(.*)V1._(.{2})(.*?)_(.{2})(.*?),(.*?),(.*?),(.*?)_.jpg$", image_url)

        if match:
            matches = match.groups()
            os.path.basename(image_url)
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
        path = os.path.abspath(os.path.join(sickrage.srCore.srConfig.CACHE_DIR, 'images', 'imdb_popular'))

        if not os.path.exists(path):
            os.makedirs(path)

        full_path = os.path.join(path, os.path.basename(image_url))

        if not os.path.isfile(full_path):
            self.session.download(image_url, full_path)
