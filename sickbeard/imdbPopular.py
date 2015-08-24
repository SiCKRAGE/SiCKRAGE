import requests
from bs4 import BeautifulSoup
import re
from datetime import date
import sickbeard
from sickbeard import encodingKludge as ek
import os

url = "http://www.imdb.com/search/title?at=0&sort=moviemeter&title_type=tv_series&year=%s,%s" % \
      (date.today().year - 1, date.today().year + 1)

def fetch_popular_shows():
    popular_shows = []

    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text)
        results = soup.find("table", {"class": "results"})
        rows = results.find_all("tr");

        for row in rows:
            show = {}
            image_td = row.find("td", {"class": "image"})

            if image_td:
                image = image_td.find("img")
                show['image_url_large'] = embiggen(image['src'],3)
                show['image_path'] = os.path.join('images', 'imdb_popular', os.path.basename(show['image_url_large']))

                cache_image(show['image_url_large'])

            td = row.find("td", {"class": "title"})

            if td:
                show['name'] = td.find("a").contents[0]
                show['imdb_url'] = "http://www.imdb.com" + td.find("a")["href"]
                show['year'] = td.find("span", {"class": "year_type"}).contents[0].split(" ")[0][1:]

                rating_all = td.find("div", {"class": "user_rating"})
                if rating_all:
                    rating_string = rating_all.find("div", {"class": "rating rating-list"})
                    if rating_string:
                        rating_string = rating_string['title']

                        matches = re.search(".* (.*)\/10.*\((.*)\).*", rating_string).groups()
                        show['rating'] = matches[0]
                        show['votes'] = matches[1]

                else:
                    show['rating'] = None
                    show['votes'] = None

                show['outline'] = td.find("span", {"class": "outline"}).contents[0]
                popular_shows.append(show)

        return popular_shows
    else:
        return None


def embiggen(image_url, factor=3):
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


def cache_image(image_url):
    path = ek.ek(os.path.abspath, ek.ek(os.path.join, sickbeard.CACHE_DIR, 'images', 'imdb_popular'))

    if not os.path.exists(path):
        os.makedirs(path)

    full_path = os.path.join(path, os.path.basename(image_url))

    if not os.path.isfile(full_path):
        r = requests.get(image_url)
        if r.status_code == 200:
            with open(full_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)



