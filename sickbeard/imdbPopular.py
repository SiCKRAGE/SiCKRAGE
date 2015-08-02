import requests
from bs4 import BeautifulSoup
import re

url = "http://www.imdb.com/search/title?at=0&sort=moviemeter&title_type=tv_series&year=2014,2016"

def fetch_popular_shows():
    popular_shows = []

    r = requests.get(url)
    if r.status_code == 200:
        html = r.text

        soup = BeautifulSoup(html)
        results = soup.find("table", {"class": "results"})
        rows = results.find_all("tr");

        for row in rows:
            show = {}
            image_td = row.find("td", {"class": "image"})

            if image_td:
                image = image_td.find("img")
                show['image_url'] =  image['src']

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



