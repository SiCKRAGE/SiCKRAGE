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



import datetime
import os
import threading

import sickrage
import sickrage.subtitles
from sickrage.core.common import dateTimeFormat
from sickrage.core.helpers import findCertainShow


class SubtitleSearcher(object):
    """
    The SubtitleSearcher will be executed every hour but will not necessarly search
    and download subtitles. Only if the defined rule is true
    """

    def __init__(self, *args, **kwargs):
        self.name = "SUBTITLESEARCHER"
        self.amActive = False

    def run(self, force=False):
        if self.amActive or (not sickrage.app.config.use_subtitles or sickrage.app.developer) and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        if len(sickrage.subtitles.getEnabledServiceList()) < 1:
            sickrage.app.log.warning(
                'Not enough services selected. At least 1 service is required to search subtitles in the background'
            )
            return

        sickrage.app.log.info('Checking for subtitles')

        # get episodes on which we want subtitles
        # criteria is:
        #  - show subtitles = 1
        #  - episode subtitles != config wanted languages or 'und' (depends on config multi)
        #  - search count < 2 and diff(airdate, now) > 1 week : now -> 1d
        #  - search count < 7 and diff(airdate, now) <= 1 week : now -> 4h -> 8h -> 16h -> 1d -> 1d -> 1d

        today = datetime.date.today().toordinal()

        results = []
        for s in sickrage.app.showlist:
            for e in (e for e in sickrage.app.main_db.get_many('tv_episodes', s.indexerid)
                      if s.subtitles == 1
                         and e['location'] != ''
                         and e['subtitles'] not in sickrage.subtitles.wanted_languages()
                         and (e['subtitles_searchcount'] <= 2 or (
                        e['subtitles_searchcount'] <= 7 and (today - e['airdate'])))):
                results += [{
                    'show_name': s.name,
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
            sickrage.app.log.info('No subtitles to download')
            return

        rules = self._getRules()
        now = datetime.datetime.now()
        for epToSub in results:
            if not os.path.isfile(epToSub['location']):
                sickrage.app.log.debug(
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

                sickrage.app.log.debug('Downloading subtitles for episode %dx%d of show %s' % (
                    epToSub['season'], epToSub['episode'], epToSub['show_name']))

                showObj = findCertainShow(int(epToSub['showid']))
                if not showObj:
                    sickrage.app.log.debug('Show not found')
                    return

                epObj = showObj.get_episode(int(epToSub["season"]), int(epToSub["episode"]))
                if isinstance(epObj, str):
                    sickrage.app.log.debug('Episode not found')
                    return

                existing_subtitles = epObj.subtitles

                try:
                    epObj.download_subtitles()
                except Exception as e:
                    sickrage.app.log.debug('Unable to find subtitles')
                    sickrage.app.log.debug(str(e))
                    return

                newSubtitles = frozenset(epObj.subtitles).difference(existing_subtitles)
                if newSubtitles:
                    sickrage.app.log.info('Downloaded subtitles for S%02dE%02d in %s' % (
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
