# Author: Daniel Joensson <nightrun@nightrun.org>
# URL: https://github.com/echel0n/SickRage/
#
# This file is part of Sick Rage.
#
# Sick Rage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Rage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Rage.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
import gzip
import xml.etree.ElementTree as EleTree
import sqlite3
import time

import sickbeard
from sickbeard import logger
from sickbeard import db


class UpdateTitles():
    def __init__(self):
        logger.log(u"Initializing AniDB Titles Cache Scheduler", logger.DEBUG)

    @staticmethod
    def download_xmlgz():
        logger.log(u"Downloading the titles data dump as gzipped XML")
        _return = urllib2.urlopen(sickbeard.ANIDB_CACHE_RELOAD_URL)
        if _return.getcode() == 200:
            _file = open('anime_titles.xml.gz', 'wb')
            _file.write(_return.read())
            _file.close()
            return True
        else:
            return False

    @staticmethod
    def uncompress_xmlgz():
        _uncompressed = gzip.open('anime_titles.xml.gz', 'rb')
        _uncompressed_xml = _uncompressed.read()
        return _uncompressed_xml

    def run(self):
        cachedb = db.DBConnection('cache.db')

        try:
            _last_time = int(cachedb.connection.execute("SELECT * FROM anime_titles_last_update;").fetchone()['time'])
        except (sqlite3.OperationalError, TypeError):
            _last_time = 0
        if int(time.time()) > _last_time + int(float(sickbeard.ANIDB_CACHE_RELOAD_TIME*24*60*60)):
            logger.log(u"Deleting old time record and creating a new one.", logger.DEBUG)
            cachedb.connection.execute("DELETE FROM anime_titles_last_update;")
            cachedb.connection.execute("INSERT INTO anime_titles_last_update VALUES("+str(int(time.time()))+");")
            cachedb.connection.commit()

            if self.download_xmlgz():
                cachedb.connection.execute("DELETE FROM anime_titles;")

            _root = EleTree.fromstring(self.uncompress_xmlgz())

            for _anime in _root:
                for _aname in _anime:
                    _sql = "INSERT INTO anime_titles VALUES ('"+_aname.text+"', '"+str(_anime.attrib['aid'])+"'); "
                    cachedb.connection.execute(_sql)
            cachedb.connection.commit()
        else:
            logger.log(u"Not time yet. Skipping", logger.DEBUG)
            return False