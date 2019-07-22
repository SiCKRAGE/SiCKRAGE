# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################
import datetime
import re

from dateutil import parser

from sickrage.core.common import dateFormat
from sickrage.core.tv.show.helpers import get_show_list


class AllShowsUI(object):
    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries, *args, **kwargs):
        shows = []

        # get all available shows
        for curShow in allSeries:
            try:
                if not curShow['seriesname'] or curShow in shows:
                    continue

                if 'firstaired' not in curShow:
                    curShow['firstaired'] = datetime.datetime.now().strftime("%Y-%m-%d")
                    curShow['firstaired'] = re.sub("([-]0{2})+", "", curShow['firstaired'])
                    fixDate = parser.parse(curShow['firstaired'], fuzzy=True).date()
                    curShow['firstaired'] = fixDate.strftime(dateFormat)

                shows += [curShow]
            except Exception as e:
                continue

        return shows


class ShowListUI(object):
    """
    Instead of prompting with a UI to pick the
    desired result out of a list of shows it tries to be smart about it
    based on what shows are in SiCKRAGE.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries, *args, **kwargs):
        try:
            # try to pick a show that's in my show list
            showIDList = [int(x.indexer_id) for x in get_show_list()]
            for curShow in allSeries:
                if int(curShow['id']) in showIDList:
                    return curShow
        except Exception:
            pass

        # if nothing matches then return first result
        return allSeries[0]