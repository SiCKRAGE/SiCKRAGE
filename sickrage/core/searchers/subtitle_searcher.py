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
import io
import os
import re
import subprocess
import threading
import traceback

import babelfish
import pkg_resources
import subliminal
from guessit import guessit

import sickrage
from sickrage.core.common import dateTimeFormat, Quality
from sickrage.core.helpers import findCertainShow, chmodAsParent, fixSetGroupID, makeDir

distribution = pkg_resources.Distribution(location=os.path.dirname(os.path.dirname(__file__)),
                                          project_name='fake_entry_points', version='1.0.0')

entry_points = {
    'subliminal.providers': [
        'addic7ed = subliminal.providers.addic7ed:Addic7edProvider',
        'legendastv = subliminal.providers.legendastv:LegendasTvProvider',
        'napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider',
        'opensubtitles = subliminal.providers.opensubtitles:OpenSubtitlesProvider',
        'podnapisi = subliminal.providers.podnapisi:PodnapisiProvider',
        'thesubdb = subliminal.providers.thesubdb:TheSubDBProvider',
        'tvsubtitles = subliminal.providers.tvsubtitles:TVsubtitlesProvider'
    ],
    'babelfish.language_converters': [
        'addic7ed = subliminal.converters.addic7ed:Addic7edConverter',
        'legendastv = subliminal.converters.legendastv:LegendasTvConverter',
        'thesubdb = subliminal.converters.thesubdb:TheSubDBConverter',
        'tvsubtitles = subliminal.converters.tvsubtitles:TVsubtitlesConverter'
    ]
}

distribution._ep_map = pkg_resources.EntryPoint.parse_map(entry_points, distribution)
pkg_resources.working_set.add(distribution)

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


def sortedServiceList():
    newList = []
    lmgtfy = 'http://lmgtfy.com/?q=%s'

    curIndex = 0
    for curService in sickrage.srCore.srConfig.SUBTITLES_SERVICES_LIST:
        if curService in subliminal.provider_manager.names():
            newList.append({'name': curService,
                            'url': PROVIDER_URLS[curService] if curService in PROVIDER_URLS else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': sickrage.srCore.srConfig.SUBTITLES_SERVICES_ENABLED[curIndex] == 1
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


# Hack around this for now.
def fromietf(language):
    return babelfish.Language.fromopensubtitles(language)


def isValidLanguage(language):
    try:
        fromietf(language)
    except Exception:
        return False
    return True


def getLanguageName(language):
    return fromietf(language).name


def download_subtitles(episode):
    existing_subtitles = episode.subtitles

    # First of all, check if we need subtitles
    languages = get_needed_languages(existing_subtitles)
    if not languages:
        sickrage.srCore.srLogger.debug('%s: No missing subtitles for S%02dE%02d' % (
            episode.show.indexerid, episode.season, episode.episode))
        return existing_subtitles, None

    subtitles_path = get_subtitles_path(episode.location)
    video_path = episode.location
    providers = getEnabledServiceList()

    video = get_video(video_path, subtitles_path=subtitles_path, episode=episode)
    if not video:
        sickrage.srCore.srLogger.debug('%s: Exception caught in subliminal.scan_video for S%02dE%02d' %
                                       (episode.show.indexerid, episode.season,
                                        episode.episode))
        return existing_subtitles, None

    provider_configs = {
        'addic7ed': {'username': sickrage.srCore.srConfig.ADDIC7ED_USER,
                     'password': sickrage.srCore.srConfig.ADDIC7ED_PASS},
        'itasa': {'username': sickrage.srCore.srConfig.ITASA_USER,
                  'password': sickrage.srCore.srConfig.ITASA_PASS},
        'legendastv': {'username': sickrage.srCore.srConfig.LEGENDASTV_USER,
                       'password': sickrage.srCore.srConfig.LEGENDASTV_PASS},
        'opensubtitles': {'username': sickrage.srCore.srConfig.OPENSUBTITLES_USER,
                          'password': sickrage.srCore.srConfig.OPENSUBTITLES_PASS}}

    pool = subliminal.ProviderPool(providers=providers, provider_configs=provider_configs)

    try:
        subtitles_list = pool.list_subtitles(video, languages)
        if not subtitles_list:
            sickrage.srCore.srLogger.debug('%s: No subtitles found for S%02dE%02d on any provider' % (
                episode.show.indexerid, episode.season, episode.episode))
            return existing_subtitles, None

        found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                       hearing_impaired=sickrage.srCore.srConfig.SUBTITLES_HEARING_IMPAIRED,
                                                       only_one=not sickrage.srCore.srConfig.SUBTITLES_MULTI)

        save_subtitles(video, found_subtitles, directory=subtitles_path,
                       single=not sickrage.srCore.srConfig.SUBTITLES_MULTI)

        if not sickrage.srCore.srConfig.EMBEDDED_SUBTITLES_ALL and sickrage.srCore.srConfig.SUBTITLES_EXTRA_SCRIPTS and video_path.endswith(
                ('.mkv', '.mp4')):
            run_subs_extra_scripts(episode, found_subtitles, video,
                                   single=not sickrage.srCore.srConfig.SUBTITLES_MULTI)

        new_subtitles = sorted(
            {subtitle.language.opensubtitles for subtitle in found_subtitles}
        )

        current_subtitles = sorted(
            {subtitle for subtitle in new_subtitles + existing_subtitles}
        ) if existing_subtitles else new_subtitles

        if not sickrage.srCore.srConfig.SUBTITLES_MULTI and len(found_subtitles) == 1:
            new_code = found_subtitles[0].language.opensubtitles
            if new_code not in existing_subtitles:
                current_subtitles.remove(new_code)
            current_subtitles.append('und')

    except Exception:
        sickrage.srCore.srLogger.info("Error occurred when downloading subtitles for: %s" % video_path)
        sickrage.srCore.srLogger.error(traceback.format_exc())
        return existing_subtitles, None

    if sickrage.srCore.srConfig.SUBTITLES_HISTORY:
        from sickrage.core.tv.show.history import History
        for subtitle in found_subtitles:
            sickrage.srCore.srLogger.debug(
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
            sickrage.srCore.srLogger.debug("Skipping subtitle for %s: no content" % video.name)
            continue

        # check language
        if subtitle.language in set(s.language for s in saved_subtitles):
            sickrage.srCore.srLogger.debug("Skipping subtitle for %s: language already saved" % video.name)
            continue

        # create subtitle path
        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)
        if directory is not None:
            subtitle_path = os.path.join(directory, os.path.split(subtitle_path)[1])

        # save content as is or in the specified encoding
        sickrage.srCore.srLogger.debug("Saving subtitle for %s to %s" % (video.name, subtitle_path))
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


def get_needed_languages(current_subtitles):
    languages = set()
    for language in frozenset(wantedLanguages()).difference(current_subtitles):
        languages.add(fromietf(language))

    return languages


# TODO: Filter here for non-languages in SUBTITLES_LANGUAGES
def wantedLanguages(sqlLike=False):
    wanted = [x for x in sorted(sickrage.srCore.srConfig.SUBTITLES_LANGUAGES) if x in subtitleCodeFilter()]
    if sqlLike:
        return '%' + ','.join(wanted) + '%'

    return wanted


def refresh_subtitles(episode):
    video = get_video(episode.location)
    if not video:
        sickrage.srCore.srLogger.debug("Exception caught in subliminal.scan_video, subtitles couldn't be refreshed")
        return episode.subtitles, None
    current_subtitles = get_subtitles(video)
    if episode.subtitles == current_subtitles:
        sickrage.srCore.srLogger.debug('No changed subtitles for {}'.format(episode.prettyName()))
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
        video_path = video_path.encode(sickrage.SYS_ENCODING)
        subtitles_path = subtitles_path.encode(sickrage.SYS_ENCODING)

    try:
        video = subliminal.scan_video(video_path)

        # external subtitles
        if subtitles:
            video.subtitle_languages |= \
                set(subliminal.core.search_external_subtitles(video_path, directory=subtitles_path).values())

        if embedded_subtitles is None:
            embedded_subtitles = bool(
                not sickrage.srCore.srConfig.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'))

        # Let sickrage add more information to video file, based on the metadata.
        if episode:
            refine_video(video, episode)

        subliminal.refine(video, embedded_subtitles=embedded_subtitles)
    except Exception as error:
        sickrage.srCore.srLogger.debug('Exception: {}'.format(error))
        return None

    return video


def get_subtitles_path(video_path):
    if os.path.isabs(sickrage.srCore.srConfig.SUBTITLES_DIR):
        new_subtitles_path = sickrage.srCore.srConfig.SUBTITLES_DIR
    elif sickrage.srCore.srConfig.SUBTITLES_DIR:
        new_subtitles_path = os.path.join(os.path.dirname(video_path), sickrage.srCore.srConfig.SUBTITLES_DIR)
        dir_exists = makeDir(new_subtitles_path)
        if not dir_exists:
            sickrage.srCore.srLogger.error('Unable to create subtitles folder {}'.format(new_subtitles_path))
        else:
            chmodAsParent(new_subtitles_path)
    else:
        new_subtitles_path = os.path.dirname(video_path)

    try:
        # Encode path to UTF-8 to ensure subliminal support.
        new_subtitles_path = new_subtitles_path.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback to system encoding. This should never happen.
        new_subtitles_path = new_subtitles_path.encode(sickrage.SYS_ENCODING)

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
    language_extensions = tuple('.' + c for c in babelfish.language_converters['opensubtitles'].codes)
    dirpath, filename = os.path.split(path)
    subtitles = set()
    for p in os.listdir(dirpath):
        if not isinstance(p, bytes) and p.startswith(os.path.splitext(filename)[0]) and p.endswith(
                subliminal.SUBTITLE_EXTENSIONS):
            if os.path.splitext(p)[0].endswith(language_extensions) and len(
                    os.path.splitext(p)[0].rsplit('.', 1)[1]) is 2:
                subtitles.add(babelfish.Language.fromopensubtitles(os.path.splitext(p)[0][-2:]))
            elif os.path.splitext(p)[0].endswith(language_extensions) and len(
                    os.path.splitext(p)[0].rsplit('.', 1)[1]) is 3:
                subtitles.add(babelfish.Language.fromopensubtitles(os.path.splitext(p)[0][-3:]))
            elif os.path.splitext(p)[0].endswith('pt-BR') and len(
                    os.path.splitext(p)[0].rsplit('.', 1)[1]) is 5:
                subtitles.add(babelfish.Language.fromopensubtitles('pob'))
            else:
                subtitles.add(babelfish.Language('und'))

    return subtitles


# TODO: Return only languages our providers allow
def subtitleLanguageFilter():
    return [babelfish.Language.fromopensubtitles(language) for language in
            babelfish.language_converters['opensubtitles'].codes if
            len(language) == 3]


def subtitleCodeFilter():
    return [babelfish.Language.fromopensubtitles(language).opensubtitles for language in
            babelfish.language_converters['opensubtitles'].codes if len(language) == 3]


def run_subs_extra_scripts(episode, found_subtitles, video, single=False):
    for curScriptName in sickrage.srCore.srConfig.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", curScriptName) if piece.strip()]
        script_cmd[0] = os.path.abspath(script_cmd[0])
        sickrage.srCore.srLogger.debug("Absolute path to script: " + script_cmd[0])

        for subtitle in found_subtitles:
            subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

            inner_cmd = script_cmd + [video.name, subtitle_path, subtitle.language.opensubtitles, episode.show.name,
                                      str(episode.season), str(episode.episode), episode.name,
                                      str(episode.show.indexerid)]

            # use subprocess to run the command and capture output
            sickrage.srCore.srLogger.info("Executing command: %s" % inner_cmd)
            try:
                p = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, cwd=sickrage.PROG_DIR)
                out, _ = p.communicate()  # @UnusedVariable
                sickrage.srCore.srLogger.debug("Script result: %s" % out)

            except Exception as e:
                sickrage.srCore.srLogger.info("Unable to run subs_extra_script: {}".format(e.message))


def refine_video(video, episode):
    # try to enrich video object using information in original filename
    if episode.release_name:
        guess_ep = subliminal.Episode.fromguess(None, guessit(episode.release_name))
        for name in vars(guess_ep):
            if getattr(guess_ep, name) and not getattr(video, name):
                setattr(video, name, getattr(guess_ep, name))

    # Use sickbeard metadata
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

    # Set quality from metadata
    _, quality = Quality.splitCompositeStatus(episode.status)
    if not video.format or episode.show.subtitles_sr_metadata:
        if quality & Quality.ANYHDTV:
            video.format = Quality.combinedQualityStrings.get(Quality.ANYHDTV)
        elif quality & Quality.ANYWEBDL:
            video.format = Quality.combinedQualityStrings.get(Quality.ANYWEBDL)
        elif quality & Quality.ANYBLURAY:
            video.format = Quality.combinedQualityStrings.get(Quality.ANYBLURAY)

    if not video.resolution or episode.show.subtitles_sr_metadata:
        if quality & (Quality.HDTV | Quality.HDWEBDL | Quality.HDBLURAY):
            video.resolution = '720p'
        elif quality & Quality.RAWHDTV:
            video.resolution = '1080i'
        elif quality & (Quality.FULLHDTV | Quality.FULLHDWEBDL | Quality.FULLHDBLURAY):
            video.resolution = '1080p'
        elif quality & (Quality.UHD_4K_TV | Quality.UHD_4K_WEBDL | Quality.UHD_4K_BLURAY):
            video.resolution = '4K'
        elif quality & (Quality.UHD_8K_TV | Quality.UHD_8K_WEBDL | Quality.UHD_8K_BLURAY):
            video.resolution = '8K'


class srSubtitleSearcher(object):
    """
    The SubtitleSearcher will be executed every hour but will not necessarly search
    and download subtitles. Only if the defined rule is true
    """

    def __init__(self, *args, **kwargs):
        self.name = "SUBTITLESEARCHER"
        self.amActive = False

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        if len(getEnabledServiceList()) < 1:
            sickrage.srCore.srLogger.warning(
                'Not enough services selected. At least 1 service is required to search subtitles in the background'
            )
            return

        sickrage.srCore.srLogger.info('Checking for subtitles')

        # get episodes on which we want subtitles
        # criteria is:
        #  - show subtitles = 1
        #  - episode subtitles != config wanted languages or 'und' (depends on config multi)
        #  - search count < 2 and diff(airdate, now) > 1 week : now -> 1d
        #  - search count < 7 and diff(airdate, now) <= 1 week : now -> 4h -> 8h -> 16h -> 1d -> 1d -> 1d

        today = datetime.date.today().toordinal()

        results = []
        for s in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for e in [e['doc'] for e in
                      sickrage.srCore.mainDB.db.get_many('tv_episodes', s['indexer_id'], with_doc=True)
                      if s['subtitles'] == 1
                      and e['doc']['location'] != ''
                      and e['doc']['subtitles'] not in wantedLanguages()
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
            sickrage.srCore.srLogger.info('No subtitles to download')
            return

        rules = self._getRules()
        now = datetime.datetime.now()
        for epToSub in results:
            if not os.path.isfile(epToSub['location']):
                sickrage.srCore.srLogger.debug(
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

                sickrage.srCore.srLogger.debug('Downloading subtitles for episode %dx%d of show %s' % (
                    epToSub['season'], epToSub['episode'], epToSub['show_name']))

                showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(epToSub['showid']))
                if not showObj:
                    sickrage.srCore.srLogger.debug('Show not found')
                    return

                epObj = showObj.getEpisode(int(epToSub["season"]), int(epToSub["episode"]))
                if isinstance(epObj, str):
                    sickrage.srCore.srLogger.debug('Episode not found')
                    return

                existing_subtitles = epObj.subtitles

                try:
                    epObj.downloadSubtitles()
                except Exception as e:
                    sickrage.srCore.srLogger.debug('Unable to find subtitles')
                    sickrage.srCore.srLogger.debug(str(e))
                    return

                newSubtitles = frozenset(epObj.subtitles).difference(existing_subtitles)
                if newSubtitles:
                    sickrage.srCore.srLogger.info('Downloaded subtitles for S%02dE%02d in %s' % (
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
