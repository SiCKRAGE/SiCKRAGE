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

import re

from subliminal.video import Episode

import sickrage
from sickrage.core.common import Quality

SHOW_MAPPING = {
    'series_tvdb_id': 'tvdb_id',
    'series_imdb_id': 'imdb_id',
    'year': 'startyear'
}

EPISODE_MAPPING = {
    'tvdb_id': 'tvdb_id',
    'size': 'file_size',
    'title': 'name',
}

ADDITIONAL_MAPPING = {
    'season': 'season',
    'episode': 'episode',
    'release_group': 'release_group',
}

series_re = re.compile(r'^(?P<series>.*?)(?: \((?:(?P<year>\d{4})|(?P<country>[A-Z]{2}))\))?$')


def refine(video, tv_episode=None, **kwargs):
    """Refine a video by using TVEpisode information.

    :param video: the video to refine.
    :type video: Episode
    :param tv_episode: the TVEpisode to be used.
    :type tv_episode: medusa.tv.Episode
    :param kwargs:
    """
    if video.series_tvdb_id and video.tvdb_id:
        sickrage.app.log.debug('No need to refine with Episode')
        return

    if not tv_episode:
        sickrage.app.log.debug('No Episode to be used to refine')
        return

    if not isinstance(video, Episode):
        sickrage.app.log.debug(f'Video {video.name!r} is not an episode. Skipping refiner...')
        return

    if tv_episode.show:
        sickrage.app.log.debug('Refining using Series information.')
        series, year, _ = series_re.match(tv_episode.show.name).groups()
        enrich({'series': series, 'year': int(year) if year else None}, video)
        enrich(SHOW_MAPPING, video, tv_episode.show)

    sickrage.app.log.debug('Refining using Episode information.')
    enrich(EPISODE_MAPPING, video, tv_episode)
    enrich(ADDITIONAL_MAPPING, video, tv_episode, overwrite=False)
    guess = Quality.to_guessit(tv_episode.quality)
    enrich({'resolution': guess.get('screen_size'), 'source': guess.get('source')}, video, overwrite=False)


def enrich(attributes, target, source=None, overwrite=True):
    """Copy attributes from source to target.

    :param attributes: the attributes mapping
    :type attributes: dict(str -> str)
    :param target: the target object
    :param source: the source object. If None, the value in attributes dict will be used as new_value
    :param overwrite: if source field should be overwritten if not already set
    :type overwrite: bool
    """
    for key, value in attributes.items():
        old_value = getattr(target, key)
        if old_value and old_value != '' and not overwrite:
            continue

        new_value = getattr(source, value) if source else value

        if new_value and old_value != new_value:
            setattr(target, key, new_value)
            sickrage.app.log.debug(f'Attribute {key} changed from {old_value!r} to {new_value!r}')