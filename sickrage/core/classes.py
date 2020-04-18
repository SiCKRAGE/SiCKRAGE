# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca/
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import sys
from collections import deque

from sickrage.core.common import Quality, dateTimeFormat


class SearchResult(object):
    """
    Represents a search result from an indexer.
    """

    def __init__(self, season, episodes):
        self.provider = None

        # release name
        self.name = ""

        # release show ID
        self.show_id = None

        # URL to the NZB/torrent file
        self.url = ""

        # used by some providers to store extra info associated with the result
        self.extraInfo = []

        # season that this result is associated with
        self.season = season

        # list of episodes that this result is associated with
        self.episodes = episodes

        # quality of the release
        self.quality = Quality.UNKNOWN

        # size of the release (-1 = n/a)
        self.size = -1

        # seeders of the release
        self.seeders = -1

        # leechers of the release
        self.leechers = -1

        # update date
        self.date = None

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
        self.type = ''

        # dict of files and their sizes
        self.files = {}

    def __str__(self):

        if self.provider is None:
            return "Invalid provider, unable to print self"

        myString = self.provider.name + " @ " + self.url + "\n"

        myString += "Extra Info:\n"
        myString += "  ".join(self.extraInfo) + "\n"

        myString += "Season: " + str(self.season) + "\n"

        myString += "Episodes:\n"
        myString += "  ".join(map(str, self.episodes)) + "\n"

        myString += "Quality: " + Quality.qualityStrings[self.quality] + "\n"
        myString += "Name: " + self.name + "\n"
        myString += "Size: " + str(self.size) + "\n"
        myString += "Release Group: " + str(self.release_group) + "\n"

        return myString


class NZBSearchResult(SearchResult):
    """
    Regular NZB result with an URL to the NZB
    """

    def __init__(self, season, episodes):
        super(NZBSearchResult, self).__init__(season, episodes)
        self.type = "nzb"


class NZBDataSearchResult(SearchResult):
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """

    def __init__(self, season, episodes):
        super(NZBDataSearchResult, self).__init__(season, episodes)
        self.type = "nzbdata"


class TorrentSearchResult(SearchResult):
    """
    Torrent result with an URL to the torrent
    """

    def __init__(self, season, episodes):
        super(TorrentSearchResult, self).__init__(season, episodes)
        self.type = "torrent"


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

    def __init__(self):
        self.errors = deque(maxlen=100)

    def add(self, error, ui=False):
        self.errors += [(error, UIError(error))[ui]]

    def clear(self):
        self.errors.clear()

    def get(self):
        return self.errors

    def count(self):
        return len(self.errors)


class WarningViewer(object):
    """
    Keeps a static list of (warning) UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    def __init__(self):
        self.warnings = deque(maxlen=100)

    def add(self, warning, ui=False):
        self.warnings += [(warning, UIWarning(warning))[ui]]

    def clear(self):
        self.warnings.clear()

    def get(self):
        return self.warnings

    def count(self):
        return len(self.warnings)
