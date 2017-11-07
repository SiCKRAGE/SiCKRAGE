# Author: Nyaran <nyayukko@gmail.com>, based on Antoine Bertin <diaoulael@gmail.com> work
# URL: https://sickrage.ca
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

from __future__ import unicode_literals

import datetime
import os
import threading

import sickrage
import sickrage.subtitles
from sickrage.core.common import dateTimeFormat
from sickrage.core.helpers import findCertainShow


class srSubtitleSearcher(object):
    """
    The SubtitleSearcher will be executed every hour but will not necessarly search
    and download subtitles. Only if the defined rule is true
    """

    def __init__(self, *args, **kwargs):
        self.name = "SUBTITLESEARCHER"
        self.amActive = False

    def run(self, force=False):
        if self.amActive or sickrage.app.srConfig.DEVELOPER:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        if len(sickrage.subtitles.getEnabledServiceList()) < 1:
            sickrage.app.srLogger.warning(
                'Not enough services selected. At least 1 service is required to search subtitles in the background'
            )
            return

        sickrage.app.srLogger.info('Checking for subtitles')

        # get episodes on which we want subtitles
        # criteria is:
        #  - show subtitles = 1
        #  - episode subtitles != config wanted languages or 'und' (depends on config multi)
        #  - search count < 2 and diff(airdate, now) > 1 week : now -> 1d
        #  - search count < 7 and diff(airdate, now) <= 1 week : now -> 4h -> 8h -> 16h -> 1d -> 1d -> 1d

        today = datetime.date.today().toordinal()

        results = []
        for s in [s['doc'] for s in sickrage.app.mainDB.db.all('tv_shows', with_doc=True)]:
            for e in [e['doc'] for e in
                      sickrage.app.mainDB.db.get_many('tv_episodes', s['indexer_id'], with_doc=True)
                      if s['subtitles'] == 1
                      and e['doc']['location'] != ''
                      and e['doc']['subtitles'] not in sickrage.subtitles.wanted_languages()
                      and (e['doc']['subtitles_searchcount'] <= 2 or (
                                        e['doc']['subtitles_searchcount'] <= 7 and (today - e['doc']['airdate'])))]:
                results += [{
                    'show_name': s['show_name'],
                    'showid': e['showid'],
                    'season': e['season'],
                    'episode': e['episode'],
                    'status': e['status'],
                    'subtitles': e['subtitles'],
                    'searchcount': e['subtitles_searchcount'],
                    'lastsearch': e['subtitles_lastsearch'],
                    'location': e['location'],
                    'airdate_daydiff': (today - e['airdate'])
                }]

        if len(results) == 0:
            sickrage.app.srLogger.info('No subtitles to download')
            return

        rules = self._getRules()
        now = datetime.datetime.now()
        for epToSub in results:
            if not os.path.isfile(epToSub['location']):
                sickrage.app.srLogger.debug(
                    'Episode file does not exist, cannot download subtitles for episode %dx%d of show %s' % (
                        epToSub['season'], epToSub['episode'], epToSub['show_name']))
                continue

            # http://bugs.python.org/issue7980#msg221094
            # I dont think this needs done here, but keeping to be safe
            datetime.datetime.strptime('20110101', '%Y%m%d')
            if (
                        (epToSub['airdate_daydiff'] > 7 and epToSub[
                            'searchcount'] < 2 and now - datetime.datetime.strptime(
                            epToSub['lastsearch'], dateTimeFormat) > datetime.timedelta(
                            hours=rules['old'][epToSub['searchcount']])) or
                        (
                                            epToSub['airdate_daydiff'] <= 7 and
                                            epToSub['searchcount'] < 7 and
                                            now - datetime.datetime.strptime(
                                            epToSub['lastsearch'], dateTimeFormat) > datetime.timedelta
                                        (
                                        hours=rules['new'][epToSub['searchcount']]
                                    )
                        )
            ):

                sickrage.app.srLogger.debug('Downloading subtitles for episode %dx%d of show %s' % (
                    epToSub['season'], epToSub['episode'], epToSub['show_name']))

                showObj = findCertainShow(sickrage.app.SHOWLIST, int(epToSub['showid']))
                if not showObj:
                    sickrage.app.srLogger.debug('Show not found')
                    return

                epObj = showObj.getEpisode(int(epToSub["season"]), int(epToSub["episode"]))
                if isinstance(epObj, str):
                    sickrage.app.srLogger.debug('Episode not found')
                    return

                existing_subtitles = epObj.subtitles

                try:
                    epObj.downloadSubtitles()
                except Exception as e:
                    sickrage.app.srLogger.debug('Unable to find subtitles')
                    sickrage.app.srLogger.debug(str(e))
                    return

                newSubtitles = frozenset(epObj.subtitles).difference(existing_subtitles)
                if newSubtitles:
                    sickrage.app.srLogger.info('Downloaded subtitles for S%02dE%02d in %s' % (
                        epToSub["season"], epToSub["episode"], ', '.join(newSubtitles)))

        self.amActive = False

    @staticmethod
    def _getRules():
        """
        Define the hours to wait between 2 subtitles search depending on:
        - the episode: new or old
        - the number of searches done so far (searchcount), represented by the index of the list
        """
        return {'old': [0, 24], 'new': [0, 4, 8, 4, 16, 24, 24]}
