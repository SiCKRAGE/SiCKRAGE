# -*- coding: utf-8 -*-
# Author: echel0n <echel0n@sickrage.ca>
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE. If not, see <http://www.gnu.org/licenses/>.


import bisect
import io
import logging
import os
import re
import zipfile

from babelfish import Language, language_converters
from guessit import guessit
from requests import Session
from subliminal import Provider
from subliminal.exceptions import ProviderError
from subliminal.matches import guess_matches
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import Subtitle, fix_line_ending
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)

language_converters.register('subscene = sickrage.subtitles.converters.subscene:SubsceneConverter')


class SubsceneSubtitle(Subtitle):
    """Subscene Subtitle."""
    provider_name = 'subscene'

    def __init__(self, language, hearing_impaired, series, season, episode, title, sub_id, releases):
        super(SubsceneSubtitle, self).__init__(language, hearing_impaired)
        self.series = series
        self.season = season
        self.episode = episode
        self.title = title
        self.sub_id = sub_id
        self.downloaded = 0
        self.releases = releases

    @property
    def id(self):
        return str(self.sub_id)

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.series) == sanitize(video.series):
                matches.add('series')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {'type': 'episode'}))
        # movie
        elif isinstance(video, Movie):
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {'type': 'movie'}))

        # title
        if video.title and sanitize(self.title) == sanitize(video.title):
            matches.add('title')

        return matches


class SubsceneProvider(Provider):
    """Subscene Provider."""
    languages = {Language.fromsubscene(l) for l in language_converters['subscene'].codes}
    server_url = 'https://subscene.com'

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()

    def terminate(self):
        self.session.close()

    def query(self, title, season=None, episode=None):
        url = '{}/subtitles/release'.format(self.server_url)
        params = {
            'q': '{0} S{1:02}E{2:02}'.format(title, season, episode),
            'r': 'true'
        }

        # get the list of subtitles
        logger.debug('Getting the list of subtitles')

        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content, ['html5lib', 'html.parser'])

        # loop over results
        subtitles = {}

        subtitle_table = soup.find('table')
        subtitle_rows = subtitle_table('tr') if subtitle_table else []

        # Continue only if one subtitle is found
        if len(subtitle_rows) < 2:
            return subtitles.values()

        for row in subtitle_rows[1:]:
            cells = row('td')

            language = Language.fromsubscene(cells[0].find_all('span')[0].get_text(strip=True))
            hearing_impaired = (False, True)[list(cells[2].attrs.values())[0] == 41]
            page_link = cells[0].find('a')['href']
            release = cells[0].find_all('span')[1].get_text(strip=True)

            # guess from name
            guess = guessit(release, {'type': 'episode'})
            if guess.get('season') != season and guess.get('episode') != episode:
                continue

            r = self.session.get(self.server_url + page_link, timeout=30)
            r.raise_for_status()
            soup2 = ParserBeautifulSoup(r.content, ['html5lib', 'html.parser'])

            try:
                sub_id = re.search(r'\?mac=(.*)', soup2.find('a', id='downloadButton')['href']).group(1)
            except AttributeError:
                continue

            # add the release and increment downloaded count if we already have the subtitle
            if sub_id in subtitles:
                logger.debug('Found additional release %r for subtitle %d', release, sub_id)
                bisect.insort_left(subtitles[sub_id].releases, release)  # deterministic order
                subtitles[sub_id].downloaded += 1
                continue

            # otherwise create it
            subtitle = SubsceneSubtitle(language, hearing_impaired, title, season, episode, title, sub_id, [release])

            logger.debug('Found subtitle %r', subtitle)
            subtitles[sub_id] = subtitle

        return subtitles.values()

    def list_subtitles(self, video, languages):
        return [s for s in self.query(video.series, video.season, video.episode)
                if s is not None and s.language in languages]

    def download_subtitle(self, subtitle):
        # download the subtitle
        logger.info('Downloading subtitle %r', subtitle.sub_id)

        params = {
            'mac': subtitle.sub_id
        }

        r = self.session.get(self.server_url + '/subtitle/download', params=params, timeout=30)
        r.raise_for_status()

        # open the zip
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            # remove some filenames from the namelist
            namelist = [n for n in zf.namelist() if os.path.splitext(n)[1] in ['.srt', '.sub']]
            if len(namelist) > 1:
                raise ProviderError('More than one file to unzip')

            subtitle.content = fix_line_ending(zf.read(namelist[0]))
