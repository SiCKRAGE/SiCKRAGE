# Author: Nyaran <nyayukko@gmail.com>, based on Antoine Bertin <diaoulael@gmail.com> work
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import time
import datetime
import sickbeard
from sickbeard.common import *
from sickbeard import notifiers
from sickbeard import logger
from sickbeard import helpers
from sickbeard import encodingKludge as ek
from sickbeard import db
from sickbeard import history
import subliminal
import babelfish

subliminal.cache_region.configure('dogpile.cache.memory')

provider_urls = {'addic7ed': 'http://www.addic7ed.com',
                 'opensubtitles': 'http://www.opensubtitles.org',
                 'podnapisi': 'http://www.podnapisi.net',
                 'thesubdb': 'http://www.thesubdb.com',
                 'tvsubtitles': 'http://www.tvsubtitles.net'
                }

SINGLE = 'und'
def sortedServiceList():
    newList = []
    lmgtfy = 'http://lmgtfy.com/?q='

    curIndex = 0
    for curService in sickbeard.SUBTITLES_SERVICES_LIST:
        if curService in subliminal.provider_manager.available_providers:
            newList.append({'name': curService,
                            'url': provider_urls[curService] if curService in provider_urls else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': sickbeard.SUBTITLES_SERVICES_ENABLED[curIndex] == 1
                           })
        curIndex += 1

    for curService in subliminal.provider_manager.available_providers:
        if curService not in [x['name'] for x in newList]:
            newList.append({'name': curService,
                            'url': provider_urls[curService] if curService in provider_urls else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': False,
                           })

    return newList

def getEnabledServiceList():
    return [x['name'] for x in sortedServiceList() if x['enabled']]

def isValidLanguage(language):
    try:
        langObj = babelfish.Language.fromietf(language)
    except:
        return False
    return True

def getLanguageName(language):
    return babelfish.Language.fromietf(language).name

# TODO: Filter here for non-languages in sickbeard.SUBTITLES_LANGUAGES
def wantedLanguages(sqlLike = False):
    wantedLanguages = sorted(sickbeard.SUBTITLES_LANGUAGES)
    if sqlLike:
        return '%' + ','.join(wantedLanguages) + '%'
    return wantedLanguages

def subtitlesLanguages(video_path):
    """Return a list detected subtitles for the given video file"""
    resultList = []
    languages = subliminal.video.scan_subtitle_languages(video_path)

    for language in languages:
        if hasattr(language, 'alpha3') and language.alpha3:
                resultList.append(language.alpha3)
        elif hasattr(language, 'alpha2') and language.alpha2:
            resultList.append(language.alpha2)

    defaultLang = wantedLanguages()
    if len(resultList) is 1 and len(defaultLang) is 1:
        return defaultLang

    return sorted(resultList)

# TODO: Return only languages our providers allow
def subtitleLanguageFilter():
    return [language for language in babelfish.LANGUAGE_MATRIX if hasattr(language, 'alpha2') and language.alpha2]

class SubtitlesFinder():
    """
    The SubtitlesFinder will be executed every hour but will not necessarly search
    and download subtitles. Only if the defined rule is true
    """

    def run(self, force=False):
        if not sickbeard.USE_SUBTITLES:
            return

        if len(sickbeard.subtitles.getEnabledServiceList()) < 1:
            logger.log(u'Not enough services selected. At least 1 service is required to search subtitles in the background', logger.ERROR)
            return

        logger.log(u'Checking for subtitles', logger.INFO)

        # get episodes on which we want subtitles
        # criteria is: 
        #  - show subtitles = 1
        #  - episode subtitles != config wanted languages or SINGLE (depends on config multi)
        #  - search count < 2 and diff(airdate, now) > 1 week : now -> 1d
        #  - search count < 7 and diff(airdate, now) <= 1 week : now -> 4h -> 8h -> 16h -> 1d -> 1d -> 1d

        today = datetime.date.today().toordinal()

        # you have 5 minutes to understand that one. Good luck
        myDB = db.DBConnection()

        sqlResults = myDB.select('SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.subtitles, ' +
        'e.subtitles_searchcount AS searchcount, e.subtitles_lastsearch AS lastsearch, e.location, (? - e.airdate) AS airdate_daydiff ' +
        'FROM tv_episodes AS e INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id) ' +
        'WHERE s.subtitles = 1 AND e.subtitles NOT LIKE (?) ' +
        'AND (e.subtitles_searchcount <= 2 OR (e.subtitles_searchcount <= 7 AND airdate_daydiff <= 7)) ' +
        'AND e.location != ""', [today, wantedLanguages(True)])

        if len(sqlResults) == 0:
            logger.log('No subtitles to download', logger.INFO)
            return

        rules = self._getRules()
        now = datetime.datetime.now()
        for epToSub in sqlResults:

            if not ek.ek(os.path.isfile, epToSub['location']):
                logger.log('Episode file does not exist, cannot download subtitles for episode %dx%d of show %s' % (epToSub['season'], epToSub['episode'], epToSub['show_name']), logger.DEBUG)
                continue

            # Old shows rule
            throwaway = datetime.datetime.strptime('20110101', '%Y%m%d')
            if ((epToSub['airdate_daydiff'] > 7 and epToSub['searchcount'] < 2 and now - datetime.datetime.strptime(epToSub['lastsearch'], '%Y-%m-%d %H:%M:%S') > datetime.timedelta(hours=rules['old'][epToSub['searchcount']])) or
                # Recent shows rule 
                (epToSub['airdate_daydiff'] <= 7 and epToSub['searchcount'] < 7 and now - datetime.datetime.strptime(epToSub['lastsearch'], '%Y-%m-%d %H:%M:%S') > datetime.timedelta(hours=rules['new'][epToSub['searchcount']]))):
                logger.log('Downloading subtitles for episode %dx%d of show %s' % (epToSub['season'], epToSub['episode'], epToSub['show_name']), logger.DEBUG)
                
                showObj = helpers.findCertainShow(sickbeard.showList, int(epToSub['showid']))
                if not showObj:
                    logger.log(u'Show not found', logger.DEBUG)
                    return
                
                epObj = showObj.getEpisode(int(epToSub["season"]), int(epToSub["episode"]))
                if isinstance(epObj, str):
                    logger.log(u'Episode not found', logger.DEBUG)
                    return

                previous_subtitles = epObj.subtitles
                
                try:
                    epObj.downloadSubtitles()
                except Exception as e:
                    logger.log(u'Unable to find subtitles', logger.DEBUG)
                    logger.log(str(e), logger.DEBUG)
                    return

                newSubtitles = frozenset(epObj.subtitles).difference(previous_subtitles)
                if newSubtitles:
                    logger.log(u'Downloaded subtitles for S%02dE%02d in %s' % (epToSub["season"], epToSub["episode"], ', '.join(newSubtitles)))

    def _getRules(self):
        """
        Define the hours to wait between 2 subtitles search depending on:
        - the episode: new or old
        - the number of searches done so far (searchcount), represented by the index of the list
        """
        return {'old': [0, 24], 'new': [0, 4, 8, 4, 16, 24, 24]}
