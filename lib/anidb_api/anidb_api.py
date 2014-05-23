#!/usr/bin/env python2
#encoding:utf-8-sig
#author: Daniel Joensson
#project:anidb_api
#repository:http://github.com/Ether009/SickRage
#license:unlicense (http://unlicense.org/)

"""
Modified from http://github.com/dbr/tvrage_api
Simple-to-use Python interface to The TVRage's API (tvrage.com)
"""

import sqlite3
from sickbeard import logger

__author__ = "Ether009"
__version__ = "1.0"

import time
import requests
import urllib2

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

from anidb_ui import BaseUI
from anidb_exceptions import (anidb_error, anidb_userabort, anidb_shownotfound,
                              anidb_seasonnotfound, anidb_episodenotfound, anidb_attributenotfound)


class ShowContainer(dict):
    """Simple dict that holds a series of Show instances
    """

    def __init__(self, **kwargs):
        super(ShowContainer, self).__init__(**kwargs)
        self._stack = []
        self._lastgc = time.time()

    def __setitem__(self, key, value):
        self._stack.append(key)

        #keep only the 100th latest results
        if time.time() - self._lastgc > 20:
            tbd = self._stack[:-100]
            i = 0
            for o in tbd:
                del self[o]
                del self._stack[i]
                i += 1

            _lastgc = time.time()
            del tbd
                    
        super(ShowContainer, self).__setitem__(key, value)


class Show(dict):
    """Holds a dict of seasons, and show data.
    """
    def __init__(self):
        dict.__init__(self)
        self.data = {}

    def __repr__(self):
        return "<Show %s (containing %s seasons)>" % (
            self.data.get(u'seriesname', 'instance'),
            len(self)
        )

    def __getattr__(self, key):
        if key in self:
            # Key is an episode, return it
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
            # Episode number x was not found
            raise anidb_seasonnotfound("Could not find season %s" % (repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise anidb_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def airedOn(self, date):
        ret = self.search(str(date), 'firstaired')
        if len(ret) == 0:
            raise anidb_episodenotfound("Could not find any episodes that aired on %s" % date)
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


class Season(dict):
    def __init__(self, show=None, **kwargs):
        """The show attribute points to the parent show
            """
        super(Season, self).__init__(**kwargs)
        self.show = show

    def __repr__(self):
        return "<Season instance (containing %s episodes)>" % (
            len(self.keys())
        )

    def __getattr__(self, episode_number):
        if episode_number in self:
            return self[episode_number]
        raise AttributeError

    def __getitem__(self, episode_number):
        if episode_number not in self:
            raise anidb_episodenotfound("Could not find episode %s" % (repr(episode_number)))
        else:
            return dict.__getitem__(self, episode_number)

    def search(self, term=None, key=None):
        """Search all episodes in season, returns a list of matching Episode
        instances.
        """
        results = []
        for ep in self.values():
            searchresult = ep.search(term=term, key=key)
            if searchresult is not None:
                results.append(
                    searchresult
                )
        return results


class Episode(dict):
    def __init__(self, season=None, **kwargs):
        """The season attribute points to the parent season
            """
        super(Episode, self).__init__(**kwargs)
        self.season = season

    def __repr__(self):
        seasno = int(self.get(u'seasonnumber', 0))
        epno = int(self.get(u'episodenumber', 0))
        epname = self.get(u'episodename')
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
            raise anidb_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def search(self, term=None, key=None):
        """Search episode data for term, if it matches, return the Episode (self).
        The key parameter can be used to limit the search to a specific element,
        for example, episodename.
        
        This primarily for use use by Show.search and Season.search.
        """
        if term is None:
            raise TypeError("must supply string to search for (contents)")

        term = unicode(term).lower()
        for cur_key, cur_value in self.items():
            cur_key, cur_value = unicode(cur_key).lower(), unicode(cur_value).lower()
            if key is not None and cur_key != key:
                # Do not search this key
                continue
            if cur_value.find(unicode(term).lower()) > -1:
                return self


class AniDB:
    """Create easy-to-use interface to name of season/episode name"""
    def __init__(self,
                 interactive=False,
                 select_first=False,
                 debug=False,
                 cache=True,
                 banners=False,
                 actors=False,
                 custom_ui=None,
                 language=None,
                 search_all_languages=False,
                 apikey=None,
                 forceconnect=False,
                 usezip=False,
                 dvdorder=False):

        """
        cache (True/False/str/unicode/urllib2 opener):
            Retrieved XML are persisted to to disc. If true, stores in
            tvrage_api folder under your systems TEMP_DIR, if set to
            str/unicode instance it will use this as the cache
            location. If False, disables caching.  Can also be passed
            an arbitrary Python object, which is used as a urllib2
            opener, which should be created by urllib2.build_opener

        forceconnect (bool):
            If true it will always try to connect to tvrage.com even if we
            recently timed out. By default it will wait one minute before
            trying again, and any requests within that one minute window will
            return an exception immediately.
        """

        self.shows = ShowContainer()  # Holds all Show classes
        self.corrections = {}  # Holds show-name to show_id mapping
        self.sess = requests.session()  # HTTP Session

        self.config = {}

        if interactive is True:
            self.config['interactive'] = True

        if select_first is True:
            self.config['select_first'] = True

        if debug is True:
            self.config['debug'] = True

        if cache is not False:  # Treat anything but False to be to use cache. Will not use custom cache locations.
            self.config['cache'] = True

        if banners is True:
            self.config['banners'] = True

        if actors is True:
            self.config['actors'] = True

        if custom_ui is not None:
            self.config['custom_ui'] = custom_ui

        # List of language on anidb.info. Hopefully all used but since more can be added
        # at any time it might have to be added to at a later stage.
        self.config['valid_languages'] = [
            "en", "ja", "x-jat", "de", "fr", "it", "cs", "sv", "ca", "ru", "pl",
            "es", "ko", "zh-Hans", "hu", "vi", "tr", "sl", "pt", "pt-BR", "ly", "lt", "hr",
            "sk", "fi", "ro", "et", "ar", "he", "el", "bg", "uk", "zh", "bg"
        ]

        if language is not None:
            self.config['language'] = 'en'
        elif language not in self.config['valid_languages']:
            raise ValueError("Invalid language %s, options are: %s" % (
                language, self.config['valid_languages']
            ))
        else:
            self.config['language'] = language

        if search_all_languages is True:
            self.config['search_all_languages'] = True

        if apikey is not None:
            self.config['apikey'] = apikey

        if forceconnect is True:
            self.config['forceconnect'] = True

        if usezip is True:
            self.config['usezip'] = True

        if dvdorder is True:
            self.config['dvdorder'] = True

        self.config['clientname'] = "sickrage"
        self.config['clientver'] = "1"
        self.config['protover'] = "1"

        self.config['base_url'] = "http://api.anidb.net:9001/httpapi"

        self.config['url_seriesInfo'] = \
            u"%(base_url)s?client=%(clientname)s&clientver=%(clientver)s&protover=%(protover)s&request=anime&aid=" \
            % self.config
        self.config['url_animetitles'] = u"http://anidb.net/api/anime-titles.xml.gz"

    @staticmethod
    def strip_namespace_inplace(etree, namespace=None, remove_from_attr=True):
        """ Takes a parsed ET structure and does an in-place removal,
        by default of all namespaces, optionally a specific namespace (by its URL).

        Can make node searches simpler in structures with unpredictable namespaces
        and in content given to be non-mixed.

        By default does so for node names as well as attribute names.
        (doesn't remove the namespace definitions, but apparently
         ElementTree serialization omits any that are unused)

        Note that for attributes that are unique only because of namespace,
        this may attributes to be overwritten.
        For example: <e p:at="bar" at="quu">   would become: <e at="bar">
        I don't think I've seen any XML where this matters, though.
        """
        if namespace is None:  # all namespaces
            for elem in etree.getiterator():
                tagname = elem.tag
                if tagname[0] == '{':
                    elem.tag = tagname[tagname.index('}', 1)+1:]

                if remove_from_attr:
                    to_delete = []
                    to_set = {}
                    for attr_name in elem.attrib:
                        if attr_name[0] == '{':
                            old_val = elem.attrib[attr_name]
                            to_delete.append(attr_name)
                            attr_name = attr_name[attr_name.index('}', 1)+1:]
                            to_set[attr_name] = old_val
                    for key in to_delete:
                        elem.attrib.pop(key)
                    elem.attrib.update(to_set)

        else:  # asked to remove specific namespace.
            ns = '{%s}' % namespace
            nsl = len(ns)
            for elem in etree.getiterator():
                if elem.tag.startswith(ns):
                    elem.tag = elem.tag[nsl:]

                if remove_from_attr:
                    to_delete = []
                    to_set = {}
                    for attr_name in elem.attrib:
                        if attr_name.startswith(ns):
                            old_val = elem.attrib[attr_name]
                            to_delete.append(attr_name)
                            attr_name = attr_name[nsl:]
                            to_set[attr_name] = old_val
                    for key in to_delete:
                        elem.attrib.pop(key)
                    elem.attrib.update(to_set)

    @staticmethod
    def _loadurl(url):

        try:
            cachedb = sqlite3.connect('cache.db')
            cachedb.text_factory = str
            cachecur = cachedb.cursor()
            cachecur.execute('SELECT lastfetched, response FROM AniDBCache WHERE URL = "'+url+'"')
            try:
                lastfetched, response = cachecur.fetchone()
            except TypeError:
                lastfetched, response = '0', ''
        except Exception as e:
            logger.log(str(e))

        curtime = time.time()
        if lastfetched is not None:
            if curtime < int(lastfetched)+(7*24*60*60):
                validcache = True
            else:
                validcache = False
        else:
            validcache = False

        if validcache:
            resp = response.decode('utf8')
        else:
            try:
                response = urllib2.urlopen(url)
                if 'Content-encoding: gzip\r\n' in response.headers.headers or url.endswith('.gz'):
                    compresseddata = response.read()
                    import StringIO
                    compressedstream = StringIO.StringIO(compresseddata)
                    import gzip
                    gzipper = gzip.GzipFile(fileobj=compressedstream)
                    resp = gzipper.read()
                    resp = resp.decode('UTF-8')
                else:
                    resp = response.read()
                cachecur.execute('DELETE FROM AniDBCache WHERE URL = ?', (url,))
                cachecur.execute('INSERT INTO AniDBCache VALUES (?, ?, ?)', (url, str(curtime), resp))
                cachedb.commit()
            except requests.HTTPError, e:
                raise anidb_error("HTTP error " + str(e.errno) + " while loading URL " + str(url))
            except requests.ConnectionError, e:
                raise anidb_error("Connection error " + str(e.message) + " while loading URL " + str(url))
            except requests.Timeout, e:
                raise anidb_error("Connection timed out " + str(e.message) + " while loading URL " + str(url))
            except sqlite3.OperationalError, e:
                raise anidb_error("DB Operational Error: " + str(e.message) + " while loading URL " + str(url))

        return resp

    def _getetsrc(self, url, params=None):
        """Loads a URL using caching, returns an ElementTree of the source
        """
        src = self._loadurl(url)

        try:
            etree = ElementTree.fromstring(src.encode('utf8'))
        except SyntaxError, exceptionmsg:
            raise anidb_error("There was an error with the XML retrieved from anidb.info:\n%s" % exceptionmsg)

        if etree is not None:
            self.strip_namespace_inplace(etree)
            return etree
        else:
            raise anidb_error("There was an error with the XML retrieved from anidb.info")

    def _setitem(self, sid, seas, ep, attrib, value):
        """Creates a new episode, creating Show(), Season() and
        Episode()s as required. Called by _getShowData to populate show

        Since the nice-to-use tvrage[1][24]['name] interface
        makes it impossible to do tvrage[1][24]['name] = "name"
        and still be capable of checking if an episode exists
        so we can raise tvrage_shownotfound, we have a slightly
        less pretty method of setting items.. but since the API
        is supposed to be read-only, this is the best way to
        do it!
        The problem is that calling tvrage[1][24]['episodename'] = "name"
        calls __getitem__ on tvrage[1], there is no way to check if
        tvrage.__dict__ should have a key "1" before we auto-create it
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        if seas not in self.shows[sid]:
            self.shows[sid][seas] = Season(show=self.shows[sid])
        if ep not in self.shows[sid][seas]:
            self.shows[sid][seas][ep] = Episode(season=self.shows[sid][seas])
        self.shows[sid][seas][ep][attrib] = value

    def _setShowData(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        self.shows[sid].data[key] = value

    def search(self, series):
        """This searches tvrage.com for the series name
        and returns the result list
        """
        series = series.encode("utf-8")
        try:
            etsrc = self._loadurl(self.config['url_animetitles'])
            etree = ElementTree.fromstring(etsrc.encode('utf8'))
            self.strip_namespace_inplace(etree)
        except Exception as e:
            logger.log(str(e))

        allseries = []
        cachedb = sqlite3.connect('cache.db')
        cachedb.text_factory = str
        cachecur = cachedb.cursor()
        if etree is not None:
            cachecur.execute('DELETE FROM AnimeTitles')
        try:
            for anime in etree:
                for title in anime:
                    cachecur.execute('INSERT INTO AnimeTitles VALUES (?, ?, ?)',
                                     (title.text, anime.attrib['aid'], title.attrib['lang']))
            cachedb.commit()
        except Exception as e:
            logger.log(str(e))

        cachecur.execute('SELECT anime, aid FROM AnimeTitles WHERE lang=? AND anime LIKE ?',
                         (self.config['language'], series))
        for row in cachecur:
            currec = {'seriesname': row[0], 'id': row[1]}
            allseries.append(currec)
            logger.log(str(currec))
        logger.log(str(allseries))
        return allseries

    def _getSeries(self, series):
        """This searches tvrage.com for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not, and interactive == True, ConsoleUI is used, if not
        BaseUI is used to select the first result.
        """
        try:
            allseries = self.search(series)
        except Exception as e:
            logger.log(str(e))

        if len(allseries) == 0:

            raise anidb_shownotfound("Show-name search returned zero results (cannot find show on TVRAGE)")

        if self.config['custom_ui'] is not None:

            ui = self.config['custom_ui'](config=self.config)
        else:

            ui = BaseUI(config=self.config)

        return ui.selectSeries(allseries)

    def startdate(self, sid, tag):
        self._setShowData(sid, 'firstaired', tag.text)
        return

    def titles(self, sid, tag):
        for title in tag:
            if title.attrib['type'] == 'main':
                self._setShowData(sid, 'seriesname', title.text)   # Always set to main title.
        return

    def url(self, sid, tag):
        self._setShowData(sid, 'showlink', tag.text)
        return

    def description(self, sid, tag):
        self._setShowData(sid, 'overview', tag.text)
        return

    def categories(self, sid, tag):
        _allCategories = u'| '
        for category in tag:
            _allCategories = _allCategories + category[0].text + u' | '
        self._setShowData(sid, 'genre', _allCategories)
        return

    def picture(self, sid, tag):
        picurl = 'http://img7.anidb.net/pics/anime/%s' % (tag.text,)
        self._setShowData(sid, 'poster', picurl)

    def episodes(self, sid, tag):
        for episode in tag:
            epdata = {}
            for child in episode:
                if child.tag == 'epno':
                    if child.attrib['type'] == '1':
                        epdata['epnr'] = child.text
                        epdata['seasonnr'] = 1
                    else:
                        epdata['epnr'] = child.text[1:]
                        epdata['seasonnr'] = 0
                elif child.tag == 'airdate':
                    epdata['firstaired'] = child.text
                elif child.tag == 'rating':
                    epdata['rating'] = child.text
                elif child.tag == 'title':
                    if child.attrib['lang'] == self.config['language']:
                        epdata['episodename'] = child.text

            if 'firstaired' not in epdata.keys():
                epdata['firstaired'] = '0000-00-00'
            if 'rating' not in epdata.keys():
                epdata['rating'] = '0'
            if 'episodename' not in epdata.keys():
                if epdata['seasonnr'] == '1':
                    epdata['episodename'] = 'Episode '+epdata['epnr']
                if epdata['seasonnr'] == '0':
                    epdata['episodename'] = 'Special '+epdata['epnr']
            self._setitem(sid, epdata['seasonnr'], epdata['epnr'], 'seasonnumber', epdata['seasonnr'])
            self._setitem(sid, epdata['seasonnr'], epdata['epnr'], 'episodenumber', epdata['epnr'])
            self._setitem(sid, epdata['seasonnr'], epdata['epnr'], 'firstaired', epdata['firstaired'])
            self._setitem(sid, epdata['seasonnr'], epdata['epnr'], 'rating', epdata['rating'])
            self._setitem(sid, epdata['seasonnr'], epdata['epnr'], 'episodename', epdata['episodename'])
            self._setitem(sid, epdata['seasonnr'], epdata['epnr'], 'id', episode.attrib['id'])

    def _getShowData(self, sid, seriessearch=False):
        """Takes a series ID, gets the epInfo URL and parses the ANIDB
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        # Parse show information
        seriesInfoEt = self._getetsrc(self.config['url_seriesInfo']+str(sid))

        if seriesInfoEt is None:
            return False

        # Set some assumed data
        self._setShowData(sid, 'classification', 'Animation')
        self._setShowData(sid, 'poster', None)

        # Look up this information from the external resources. TODO: Add an external lookup of this data.
        self._setShowData(sid, 'network', 'NA')
        self._setShowData(sid, 'imdb_id', None)
        self._setShowData(sid, 'airs_dayofweek', None)
        self._setShowData(sid, 'banner', None)

        # Parse Show Data
        tagstoprocess = ['startdate', 'titles', 'url', 'description', 'categories', 'episodes', 'picture']
        for tag in seriesInfoEt:
            if tag.tag in tagstoprocess:
                getattr(self, tag.tag)(sid, tag)

        # Calculate this based on episode data. TODO: Calculate this based on the episodes.
        self._setShowData(sid, 'runtime', '25')
        self._setShowData(sid, 'status', 'Continuing')

        return True

    def _nameToSid(self, name):
        """Takes show name, returns the correct series ID (if the show has
        already been grabbed), or grabs all episodes and returns
        the correct SID.
        """
        if name in self.corrections:
            logger.log('Correcting %s to %s' % (name, self.corrections[name]))
            return self.corrections[name]
        else:
            logger.log('Getting show %s' % name)
            selected_series = self._getSeries(name)
            if isinstance(selected_series, dict):
                selected_series = [selected_series]
            sids = list(int(x['id']) for x in selected_series if self._getShowData(int(x['id']), seriesSearch=True))
            self.corrections.update(dict((x['seriesname'], int(x['id'])) for x in selected_series))
            return sids

    def __getitem__(self, key):
        """Handles anidb_instance['seriesname'] calls.
        The dict index should be the show id
        """
        if isinstance(key, (int, long)):
            # Item is integer, treat as show id
            if key not in self.shows:
                self._getShowData(key)
            return self.shows[key]

        key = str(key).lower()
        self.config['searchterm'] = key
        selected_series = self._getSeries(key)
        if isinstance(selected_series, dict):
            selected_series = [selected_series]
        [[self._setShowData(show['id'], k, v) for k, v in show.items()] for show in selected_series]
        return selected_series
        #test = self._getSeries(key)
        #sids = self._nameToSid(key)
        #return list(self.shows[sid] for sid in sids)

    def __repr__(self):
        return str(self.shows)