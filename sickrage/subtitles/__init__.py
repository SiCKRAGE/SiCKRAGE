# Author: echel0n <echel0n@sickrage.ca>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import io
import os
import re
import subprocess
import traceback

import subliminal
from babelfish import language_converters, Language
from guessit import guessit

import sickrage
from sickrage.core import makeDir
from sickrage.core.helpers import chmodAsParent, fixSetGroupID

if 'legendastv' not in subliminal.provider_manager.names():
    subliminal.provider_manager.register('legendastv = subliminal.providers.legendastv:LegendasTVProvider')
if 'itasa' not in subliminal.provider_manager.names():
    subliminal.provider_manager.register('itasa = sickrage.subtitles.providers.itasa:ItaSAProvider')

subliminal.region.configure('dogpile.cache.memory')

PROVIDER_URLS = {
    'addic7ed': 'http://www.addic7ed.com',
    'itasa': 'http://www.italiansubs.net/',
    'legendastv': 'http://www.legendas.tv',
    'napiprojekt': 'http://www.napiprojekt.pl',
    'opensubtitles': 'http://www.opensubtitles.org',
    'podnapisi': 'http://www.podnapisi.net',
    'subscenter': 'http://www.subscenter.org',
    'thesubdb': 'http://www.thesubdb.com',
    'tvsubtitles': 'http://www.tvsubtitles.net'
}
subtitle_extensions = ['srt', 'sub', 'ass', 'idx', 'ssa']


def sortedServiceList():
    newList = []
    lmgtfy = 'http://lmgtfy.com/?q=%s'

    curIndex = 0
    for curService in sickrage.app.config.SUBTITLES_SERVICES_LIST:
        if curService in subliminal.provider_manager.names():
            newList.append({'name': curService,
                            'url': PROVIDER_URLS[curService] if curService in PROVIDER_URLS else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': sickrage.app.config.SUBTITLES_SERVICES_ENABLED[curIndex] == 1
                            })
        curIndex += 1

    for curService in subliminal.provider_manager.names():
        if curService not in [x['name'] for x in newList]:
            newList.append({'name': curService,
                            'url': PROVIDER_URLS[curService] if curService in PROVIDER_URLS else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': False,
                            })

    return newList


def getEnabledServiceList():
    return [x['name'] for x in sortedServiceList() if x['enabled']]


def download_subtitles(episode):
    existing_subtitles = episode.subtitles

    # First of all, check if we need subtitles
    languages = get_needed_languages(existing_subtitles)
    if not languages:
        sickrage.app.log.debug('%s: No missing subtitles for S%02dE%02d' % (
            episode.show.indexerid, episode.season, episode.episode))
        return existing_subtitles, None

    subtitles_path = get_subtitles_path(episode.location)
    video_path = episode.location
    providers = getEnabledServiceList()

    video = get_video(video_path, subtitles_path=subtitles_path, episode=episode)
    if not video:
        sickrage.app.log.debug('%s: Exception caught in subliminal.scan_video for S%02dE%02d' %
                                       (episode.show.indexerid, episode.season,
                                        episode.episode))
        return existing_subtitles, None

    provider_configs = {
        'addic7ed': {'username': sickrage.app.config.ADDIC7ED_USER,
                     'password': sickrage.app.config.ADDIC7ED_PASS},
        'itasa': {'username': sickrage.app.config.ITASA_USER,
                  'password': sickrage.app.config.ITASA_PASS},
        'legendastv': {'username': sickrage.app.config.LEGENDASTV_USER,
                       'password': sickrage.app.config.LEGENDASTV_PASS},
        'opensubtitles': {'username': sickrage.app.config.OPENSUBTITLES_USER,
                          'password': sickrage.app.config.OPENSUBTITLES_PASS}}

    pool = subliminal.ProviderPool(providers=providers, provider_configs=provider_configs)

    try:
        subtitles_list = pool.list_subtitles(video, languages)
        if not subtitles_list:
            sickrage.app.log.debug('%s: No subtitles found for S%02dE%02d on any provider' % (
                episode.show.indexerid, episode.season, episode.episode))
            return existing_subtitles, None

        found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                       hearing_impaired=sickrage.app.config.SUBTITLES_HEARING_IMPAIRED,
                                                       only_one=not sickrage.app.config.SUBTITLES_MULTI)

        save_subtitles(video, found_subtitles, directory=subtitles_path,
                       single=not sickrage.app.config.SUBTITLES_MULTI)

        if not sickrage.app.config.EMBEDDED_SUBTITLES_ALL and sickrage.app.config.SUBTITLES_EXTRA_SCRIPTS and video_path.endswith(
                ('.mkv', '.mp4')):
            run_subs_extra_scripts(episode, found_subtitles, video,
                                   single=not sickrage.app.config.SUBTITLES_MULTI)

        new_subtitles = sorted({subtitle.language.opensubtitles for subtitle in found_subtitles})
        current_subtitles = sorted({subtitle for subtitle in new_subtitles + existing_subtitles if subtitle})
        if not sickrage.app.config.SUBTITLES_MULTI and len(found_subtitles) == 1:
            new_code = found_subtitles[0].language.opensubtitles
            if new_code not in existing_subtitles:
                current_subtitles.remove(new_code)
            current_subtitles.append('und')

    except Exception:
        sickrage.app.log.info("Error occurred when downloading subtitles for: %s" % video_path)
        sickrage.app.log.error(traceback.format_exc())
        return existing_subtitles, None

    if sickrage.app.config.SUBTITLES_HISTORY:
        from sickrage.core.tv.show.history import History
        for subtitle in found_subtitles:
            sickrage.app.log.debug(
                'history.logSubtitle %s, %s' % (subtitle.provider_name, subtitle.language.opensubtitles))
            History.logSubtitle(episode.show.indexerid,
                                episode.season,
                                episode.episode,
                                episode.status,
                                subtitle)

    return current_subtitles, new_subtitles


def save_subtitles(video, subtitles, single=False, directory=None):
    saved_subtitles = []
    for subtitle in subtitles:
        # check content
        if subtitle.content is None:
            sickrage.app.log.debug("Skipping subtitle for %s: no content" % video.name)
            continue

        # check language
        if subtitle.language in set(s.language for s in saved_subtitles):
            sickrage.app.log.debug("Skipping subtitle for %s: language already saved" % video.name)
            continue

        # create subtitle path
        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)
        if directory is not None:
            subtitle_path = os.path.join(directory, os.path.split(subtitle_path)[1])

        # save content as is or in the specified encoding
        sickrage.app.log.debug("Saving subtitle for %s to %s" % (video.name, subtitle_path))
        if subtitle.encoding:
            with io.open(subtitle_path, 'w', encoding=subtitle.encoding) as f:
                f.write(subtitle.text)
        else:
            with io.open(subtitle_path, 'wb') as f:
                f.write(subtitle.content)

        # chmod and set group for the saved subtitle
        chmodAsParent(subtitle_path)
        fixSetGroupID(subtitle_path)

        # check single
        if single:
            break

    return saved_subtitles


def wanted_languages():
    return frozenset(sickrage.app.config.SUBTITLES_LANGUAGES).intersection(subtitle_code_filter())


def get_needed_languages(subtitles):
    if not sickrage.app.config.SUBTITLES_MULTI:
        return set() if 'und' in subtitles else {from_code(language) for language in wanted_languages()}
    return {from_code(language) for language in wanted_languages().difference(subtitles)}


def refresh_subtitles(episode):
    video = get_video(episode.location)
    if not video:
        sickrage.app.log.debug("Exception caught in subliminal.scan_video, subtitles couldn't be refreshed")
        return episode.subtitles, None
    current_subtitles = get_subtitles(video)
    if episode.subtitles == current_subtitles:
        sickrage.app.log.debug('No changed subtitles for {}'.format(episode.prettyName()))
        return episode.subtitles, None
    else:
        return current_subtitles, True


def get_video(video_path, subtitles_path=None, subtitles=True, embedded_subtitles=None, episode=None):
    if not subtitles_path:
        subtitles_path = get_subtitles_path(video_path)

    try:
        # Encode paths to UTF-8 to ensure subliminal support.
        video_path = video_path.encode('utf-8')
        subtitles_path = subtitles_path.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback to system encoding. This should never happen.
        video_path = video_path.encode(sickrage.app.SYS_ENCODING)
        subtitles_path = subtitles_path.encode(sickrage.app.SYS_ENCODING)

    try:
        video = subliminal.scan_video(video_path)

        # external subtitles
        if subtitles:
            video.subtitle_languages |= \
                set(subliminal.core.search_external_subtitles(video_path, directory=subtitles_path).values())

        if embedded_subtitles is None:
            embedded_subtitles = bool(
                not sickrage.app.config.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'))

        # Let sickrage add more information to video file, based on the metadata.
        if episode:
            refine_video(video, episode)

        subliminal.refine(video, embedded_subtitles=embedded_subtitles)
    except Exception as error:
        sickrage.app.log.debug('Exception: {}'.format(error))
        return None

    # remove format metadata
    video.format = ""

    return video


def get_subtitles_path(video_path):
    if os.path.isabs(sickrage.app.config.SUBTITLES_DIR):
        new_subtitles_path = sickrage.app.config.SUBTITLES_DIR
    elif sickrage.app.config.SUBTITLES_DIR:
        new_subtitles_path = os.path.join(os.path.dirname(video_path), sickrage.app.config.SUBTITLES_DIR)
        dir_exists = makeDir(new_subtitles_path)
        if not dir_exists:
            sickrage.app.log.error('Unable to create subtitles folder {}'.format(new_subtitles_path))
        else:
            chmodAsParent(new_subtitles_path)
    else:
        new_subtitles_path = os.path.dirname(video_path)

    try:
        # Encode path to UTF-8 to ensure subliminal support.
        new_subtitles_path = new_subtitles_path.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback to system encoding. This should never happen.
        new_subtitles_path = new_subtitles_path.encode(sickrage.app.SYS_ENCODING)

    return new_subtitles_path


def get_subtitles(video):
    """Return a sorted list of detected subtitles for the given video file."""
    result_list = []

    if not video.subtitle_languages:
        return result_list

    for language in video.subtitle_languages:
        if hasattr(language, 'opensubtitles') and language.opensubtitles:
            result_list.append(language.opensubtitles)

    return sorted(result_list)


def scan_subtitle_languages(path):
    language_extensions = tuple('.' + c for c in language_converters['opensubtitles'].codes)
    dirpath, filename = os.path.split(path)
    subtitles = set()
    for p in os.listdir(dirpath):
        if not isinstance(p, bytes) and p.startswith(os.path.splitext(filename)[0]) and p.endswith(
                subliminal.SUBTITLE_EXTENSIONS):
            if os.path.splitext(p)[0].endswith(language_extensions) and len(
                    os.path.splitext(p)[0].rsplit('.', 1)[1]) is 2:
                subtitles.add(Language.fromopensubtitles(os.path.splitext(p)[0][-2:]))
            elif os.path.splitext(p)[0].endswith(language_extensions) and len(
                    os.path.splitext(p)[0].rsplit('.', 1)[1]) is 3:
                subtitles.add(Language.fromopensubtitles(os.path.splitext(p)[0][-3:]))
            elif os.path.splitext(p)[0].endswith('pt-BR') and len(
                    os.path.splitext(p)[0].rsplit('.', 1)[1]) is 5:
                subtitles.add(Language.fromopensubtitles('pob'))
            else:
                subtitles.add(Language('und'))

    return subtitles


def subtitle_code_filter():
    return {code for code in language_converters['opensubtitles'].codes if len(code) == 3}


def from_code(language):
    language = language.strip()
    if language and language in language_converters['opensubtitles'].codes:
        return Language.fromopensubtitles(language)

    return Language('und')


def name_from_code(code):
    return from_code(code).name


def code_from_code(code):
    return from_code(code).opensubtitles


def run_subs_extra_scripts(episode, found_subtitles, video, single=False):
    for curScriptName in sickrage.app.config.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", curScriptName) if piece.strip()]
        script_cmd[0] = os.path.abspath(script_cmd[0])
        sickrage.app.log.debug("Absolute path to script: " + script_cmd[0])

        for subtitle in found_subtitles:
            subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

            inner_cmd = script_cmd + [video.name, subtitle_path, subtitle.language.opensubtitles, episode.show.name,
                                      str(episode.season), str(episode.episode), episode.name,
                                      str(episode.show.indexerid)]

            # use subprocess to run the command and capture output
            sickrage.app.log.info("Executing command: %s" % inner_cmd)
            try:
                p = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, cwd=sickrage.PROG_DIR)
                out, __ = p.communicate()
                sickrage.app.log.debug("Script result: %s" % out)

            except Exception as e:
                sickrage.app.log.info("Unable to run subs_extra_script: {}".format(e.message))


def refine_video(video, episode):
    # try to enrich video object using information in original filename
    if episode.release_name:
        guess_ep = subliminal.Episode.fromguess(None, guessit(episode.release_name))
        for name in vars(guess_ep):
            if getattr(guess_ep, name) and not getattr(video, name):
                setattr(video, name, getattr(guess_ep, name))

    # Use sickrage metadata
    metadata_mapping = {
        'episode': 'episode',
        'release_group': 'release_group',
        'season': 'season',
        'series': 'show.name',
        'series_imdb_id': 'show.imdbid',
        'size': 'file_size',
        'title': 'name',
        'year': 'show.startyear'
    }

    def get_attr_value(obj, name):
        value = None
        for attr in name.split('.'):
            if not value:
                value = getattr(obj, attr, None)
            else:
                value = getattr(value, attr, None)

        return value

    for name in metadata_mapping:
        if not getattr(video, name) and get_attr_value(episode, metadata_mapping[name]):
            setattr(video, name, get_attr_value(episode, metadata_mapping[name]))
        elif episode.show.subtitles_sr_metadata and get_attr_value(episode, metadata_mapping[name]):
            setattr(video, name, get_attr_value(episode, metadata_mapping[name]))