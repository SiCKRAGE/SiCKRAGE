# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca/
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
import re
import sys

import sickrage
from apscheduler.triggers.interval import IntervalTrigger
from dateutil import parser
from sickrage.core.common import Quality, dateFormat, dateTimeFormat


class SearchResult(object):
    """
    Represents a search result from an indexer.
    """

    def __init__(self, episodes):
        self.provider = None

        # release show object
        self.show = None

        # URL to the NZB/torrent file
        self.url = ""

        # used by some providers to store extra info associated with the result
        self.extraInfo = []

        # list of TVEpisode objects that this result is associated with
        self.episodes = episodes

        # quality of the release
        self.quality = Quality.UNKNOWN

        # release name
        self.name = ""

        # size of the release (-1 = n/a)
        self.size = -1

        # release group
        self.release_group = ""

        # version
        self.version = -1

        # hash
        self.hash = None

        # content
        self.content = None

        # ratio
        self.ratio = None

        # result type
        self.resultType = ''

        # dict of files and their sizes
        self.files = {}

    def __str__(self):

        if self.provider is None:
            return "Invalid provider, unable to print self"

        myString = self.provider.name + " @ " + self.url + "\n"
        myString += "Extra Info:\n"
        for extra in self.extraInfo:
            myString += "  " + extra + "\n"

        myString += "Episodes:\n"
        for ep in self.episodes:
            myString += "  " + str(ep) + "\n"

        myString += "Quality: " + Quality.qualityStrings[self.quality] + "\n"
        myString += "Name: " + self.name + "\n"
        myString += "Size: " + str(self.size) + "\n"
        myString += "Release Group: " + str(self.release_group) + "\n"

        return myString

    def fileName(self):
        return self.episodes[0].prettyName() + "." + self.resultType


class NZBSearchResult(SearchResult):
    """
    Regular NZB result with an URL to the NZB
    """

    def __init__(self, episodes):
        super(NZBSearchResult, self).__init__(episodes)
        self.resultType = "nzb"


class NZBDataSearchResult(SearchResult):
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """

    def __init__(self, episodes):
        super(NZBDataSearchResult, self).__init__(episodes)
        self.resultType = "nzbdata"


class TorrentSearchResult(SearchResult):
    """
    Torrent result with an URL to the torrent
    """

    def __init__(self, episodes):
        super(TorrentSearchResult, self).__init__(episodes)
        self.resultType = "torrent"


class AllShowsListUI(object):
    """
    This class is for indexer api. Instead of prompting with a UI to pick the
    desired result out of a list of shows it tries to be smart about it
    based on what shows are in SB.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries, series):
        searchResults = []
        seriesnames = []

        # get all available shows
        for curShow in allSeries:
            try:
                if not curShow['seriesname'] or curShow in searchResults:
                    continue

                if 'firstaired' not in curShow:
                    curShow['firstaired'] = datetime.datetime.now().strftime("%Y-%m-%d")
                    curShow['firstaired'] = re.sub("([-]0{2})+", "", curShow['firstaired'])
                    fixDate = parser.parse(curShow['firstaired'], fuzzy=True).date()
                    curShow['firstaired'] = fixDate.strftime(dateFormat)

                searchResults += [curShow]
            except Exception as e:
                continue

        return searchResults


class ShowListUI(object):
    """
    This class is for tvdb-api. Instead of prompting with a UI to pick the
    desired result out of a list of shows it tries to be smart about it
    based on what shows are in SiCKRAGE.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries):
        try:
            # try to pick a show that's in my show list
            showIDList = [int(x.indexerid) for x in sickrage.srCore.SHOWLIST]
            for curShow in allSeries:
                if int(curShow['id']) in showIDList:
                    return curShow
        except Exception:
            pass

        # if nothing matches then return first result
        return allSeries[0]


class Proper(object):
    def __init__(self, name, url, date, show):
        self.name = name
        self.url = url
        self.date = date
        self.provider = None
        self.quality = Quality.UNKNOWN
        self.release_group = None
        self.version = -1

        self.show = show
        self.indexer = None
        self.indexerid = -1
        self.season = -1
        self.episode = -1
        self.scene_season = -1
        self.scene_episode = -1

    def __str__(self):
        return str(self.date) + " " + self.name + " " + str(self.season) + "x" + str(self.episode) + " of " + str(
            self.indexerid)


class UIError(object):
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
        self.title = sys.exc_info()[-2] or message
        self.message = message


class UIWarning(object):
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
        self.title = sys.exc_info()[-2] or message
        self.message = message


class ErrorViewer(object):
    """
    Keeps a static list of UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    errors = []

    def add(self, error, ui=False):
        self.errors += [(error, UIError(error))[ui]]

    @classmethod
    def clear(cls):
        cls.errors = []

    def get(self):
        return self.errors


class WarningViewer(object):
    """
    Keeps a static list of (warning) UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    errors = []

    def add(self, error, ui=False):
        self.errors += [(error, UIWarning(error))[ui]]

    @classmethod
    def clear(cls):
        cls.errors = []

    def get(self):
        return self.errors


class AttrDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

class srIntervalTrigger(IntervalTrigger):
    def __init__(self, weeks=0, days=0, hours=0, minutes=0, seconds=0, start_date=None, end_date=None, timezone=None,
                 **kwargs):
        min = kwargs.pop('min', 0)
        if min <= weeks + days + hours + minutes + seconds:
            super(srIntervalTrigger, self).__init__(weeks, days, hours, minutes, seconds, start_date, end_date,
                                                    timezone)