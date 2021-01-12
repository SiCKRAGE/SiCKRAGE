# Author: Nyaran <nyayukko@gmail.com>, based on Antoine Bertin <diaoulael@gmail.com> work
# URL: https://sickrage.ca
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import os
import threading

from sqlalchemy import or_, and_

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.core.tv.show.helpers import get_show_list, find_show
from sickrage.subtitles import Subtitles


class SubtitleSearcher(object):
    """
    The SubtitleSearcher will be executed every hour but will not necessarly search
    and download subtitles. Only if the defined rule is true
    """

    def __init__(self, *args, **kwargs):
        self.name = "SUBTITLESEARCHER"
        self.running = False

    def task(self, force=False):
        if self.running or not sickrage.app.config.subtitles.enable and not force:
            return

        try:
            self.running = True

            # set thread name
            threading.currentThread().setName(self.name)

            if len(Subtitles().getEnabledServiceList()) < 1:
                sickrage.app.log.warning('Not enough services selected. At least 1 service is required to search subtitles in the background')
                return

            session = sickrage.app.main_db.session()

            sickrage.app.log.info('Checking for subtitles')

            # get episodes on which we want subtitles
            # criteria is:
            #  - show subtitles = 1
            #  - episode subtitles != config wanted languages or 'und' (depends on config multi)
            #  - search count < 2 and diff(airdate, now) > 1 week : now -> 1d
            #  - search count < 7 and diff(airdate, now) <= 1 week : now -> 4h -> 8h -> 16h -> 1d -> 1d -> 1d

            rules = self._get_rules()
            now = datetime.datetime.now()

            results = []
            for s in get_show_list():
                if s.subtitles != 1:
                    continue

                for e in session.query(MainDB.TVEpisode).filter_by(series_id=s.series_id).filter(MainDB.TVEpisode.location != '', ~MainDB.TVEpisode.subtitles.in_(
                        Subtitles().wanted_languages()), or_(MainDB.TVEpisode.subtitles_searchcount <= 2,
                                                             and_(MainDB.TVEpisode.subtitles_searchcount <= 7,
                                                                  datetime.date.today() - MainDB.TVEpisode.airdate))):
                    results += [{
                        'show_name': s.name,
                        'series_id': s.series_id,
                        'series_provider_id': s.series_provider_id,
                        'season': e.season,
                        'episode': e.episode,
                        'status': e.status,
                        'subtitles': e.subtitles,
                        'searchcount': e.subtitles_searchcount,
                        'lastsearch': e.subtitles_lastsearch,
                        'location': e.location,
                        'airdate_daydiff': (datetime.date.today() - e.airdate).days
                    }]

            if len(results) == 0:
                sickrage.app.log.info('No subtitles to download')
                return

            for epToSub in results:
                show_object = find_show(epToSub['series_id'], epToSub['series_provider_id'])
                episode_object = show_object.get_episode(epToSub['season'], epToSub['episode'])

                if not os.path.isfile(epToSub['location']):
                    sickrage.app.log.debug('Episode file does not exist, cannot download '
                                           'subtitles for episode %dx%d of show %s' % (episode_object.season, episode_object.episode, epToSub['show_name']))
                    continue

                if ((epToSub['airdate_daydiff'] > 7 and epToSub['searchcount'] < 2 and now - epToSub['lastsearch'] > datetime.timedelta(hours=rules['old'][epToSub['searchcount']])) or
                        (epToSub['airdate_daydiff'] <= 7 and epToSub['searchcount'] < 7 and
                         now - epToSub['lastsearch'] > datetime.timedelta(hours=rules['new'][epToSub['searchcount']]))):

                    sickrage.app.log.debug('Downloading subtitles for '
                                           'episode %dx%d of show %s' % (episode_object.season, episode_object.episode, epToSub['show_name']))

                    existing_subtitles = episode_object.subtitles

                    try:
                        episode_object.download_subtitles()

                        new_subtitles = frozenset(episode_object.subtitles).difference(existing_subtitles)
                        if new_subtitles:
                            sickrage.app.log.info('Downloaded subtitles '
                                                  'for S%02dE%02d in %s' % (episode_object.season, episode_object.episode, ', '.join(new_subtitles)))
                    except Exception as e:
                        sickrage.app.log.debug('Unable to find subtitles')
                        sickrage.app.log.debug(str(e))
        finally:
            self.running = False

    @staticmethod
    def _get_rules():
        """
        Define the hours to wait between 2 subtitles search depending on:
        - the episode: new or old
        - the number of searches done so far (search count), represented by the index of the list
        """
        return {'old': [0, 24], 'new': [0, 4, 8, 4, 16, 24, 24]}
