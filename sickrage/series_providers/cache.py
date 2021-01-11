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
from collections import OrderedDict

import sickrage
from sickrage.series_providers.exceptions import SeriesProviderAttributeNotFound, SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound


class SeriesProviderShowCache(OrderedDict):
    def __init__(self, *args, **kwargs):
        self.maxsize = 100
        super(SeriesProviderShowCache, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        super(SeriesProviderShowCache, self).__setitem__(key, value)
        while len(self) > self.maxsize:
            self.pop(list(self.keys())[0], None)

    def add_item(self, sid, seas, ep, attrib, value):
        if sid not in self:
            self[sid] = SeriesProviderShow()
        if seas not in self[sid]:
            self[sid][seas] = SeriesProviderSeason()
        if ep not in self[sid][seas]:
            self[sid][seas][ep] = SeriesProviderEpisode()
        self[sid][seas][ep][attrib] = value

    def add_show_data(self, sid, key, value):
        if sid not in self:
            self[sid] = SeriesProviderShow()

        self[sid].data[key] = value


class SeriesProviderShow(dict):
    """Holds a dict of seasons, and show data.
    """

    def __init__(self, **kwargs):
        super(SeriesProviderShow, self).__init__(**kwargs)
        self.data = {}

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __repr__(self):
        return "<Show {} (containing {} seasons)>".format(
            self.data.get('seriesname', 'instance'),
            len(self)
        )

    def __getattr__(self, key):
        if key in self:
            # Key is an season, return it
            return self[key]

        if key in self.data:
            # Non-numeric request is for show-data
            return self.data[key]

        raise AttributeError

    def __getitem__(self, key):
        if key in self:
            # Key is an episode, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for show-data
            return dict.__getitem__(self.data, key)

        # Data wasn't found, raise appropriate error
        if isinstance(key, int) or key.isdigit():
            # Season number x was not found
            raise SeriesProviderSeasonNotFound("Could not find season {}".format(repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise SeriesProviderAttributeNotFound("Cannot find show attribute {}".format(repr(key)))

    def aired_on(self, date):
        ret = self.search(str(date), 'firstaired')
        if len(ret) == 0:
            sickrage.app.log.debug("Could not find any episodes on TheTVDB that aired on {}".format(date))
            return None
        return ret

    def search(self, term=None, key=None):
        """
        Search all episodes in show. Can search all data, or a specific key (for
        example, episodename)

        Always returns an array (can be empty). First index contains the first
        match, and so on.

        Each array index is an Episode() instance, so doing
        search_results[0]['episodename'] will retrieve the episode name of the
        first match.

        Search terms are converted to lower case (unicode) strings.
        """
        results = []

        for cur_season in self.values():
            searchresult = cur_season.search(term=term, key=key)
            if len(searchresult) != 0:
                results.extend(searchresult)

        return results


class SeriesProviderSeason(dict):
    def __init__(self):
        super(SeriesProviderSeason, self).__init__()
        self.data = {}

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __repr__(self):
        return "<Season instance (containing {} episodes)>".format(
            len(self.keys())
        )

    def __getattr__(self, key):
        if key in self:
            return self[key]

        if key in self.data:
            # Non-numeric request is for season-data
            return self.data[key]

        raise AttributeError

    def __getitem__(self, key):
        if key in self:
            # Key is an episode, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for season-data
            return dict.__getitem__(self.data, key)

        if isinstance(key, int) or key.isdigit():
            raise SeriesProviderEpisodeNotFound("Could not find episode {}".format(repr(key)))
        else:
            raise SeriesProviderAttributeNotFound("Cannot find season attribute {}".format(repr(key)))

    def search(self, term=None, key=None):
        """Search all episodes in season, returns a list of matching Episode
        instances.
        """
        results = []
        for ep in self.values():
            result = ep.search(term=term, key=key)
            if result is not None:
                results.append(result)

        return results


class SeriesProviderEpisode(dict):
    def __init__(self):
        super(SeriesProviderEpisode, self).__init__()

    def __repr__(self):
        seasno = int(self.get('airedseason', 0))
        epno = int(self.get('airedepisodenumber', 0))
        epname = self.get('episodename')
        if epname is not None:
            return "<Episode %02dx%02d - %s>" % (seasno, epno, epname)
        else:
            return "<Episode %02dx%02d>" % (seasno, epno)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            raise SeriesProviderAttributeNotFound("Cannot find episode attribute {}".format(repr(key)))

    def search(self, term=None, key=None):
        """Search episode data for term, if it matches, return the Episode (self).
        The key parameter can be used to limit the search to a specific element,
        for example, episodename.

        This primarily for use use by Show.search and Season.search. See
        Show.search for further information on search
        """
        if term is None:
            raise TypeError("must supply string to search for (contents)")

        for cur_key, cur_value in self.items():
            if isinstance(cur_value, dict) or key is None or cur_value is None:
                continue

            cur_key, cur_value = str(cur_key).lower(), str(cur_value).lower()
            if cur_key != key:
                continue
            if cur_value.find(term.lower()) > -1:
                return self
