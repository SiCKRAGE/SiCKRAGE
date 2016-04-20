# Author: Nyaran <nyayukko@gmail.com>, based on Antoine Bertin <diaoulael@gmail.com> work
# URL: http://github.com/SiCKRAGETV/SickRage/
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
from enzyme import MKV, MalformedMKVError

import sickrage
from sickrage.core.common import dateTimeFormat
from sickrage.core.databases import main_db
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

# pylint: disable=W0212
# Access to a protected member of a client class
distribution._ep_map = pkg_resources.EntryPoint.parse_map(entry_points, distribution)
pkg_resources.working_set.add(distribution)

# provider_manager.ENTRY_POINT_CACHE.pop('subliminal.providers')

# subliminal.region.configure('dogpile.cache.memory')

provider_urls = {
    'addic7ed': 'http://www.addic7ed.com',
    'legendastv': 'http://www.legendas.tv',
    'napiprojekt': 'http://www.napiprojekt.pl',
    'opensubtitles': 'http://www.opensubtitles.org',
    'podnapisi': 'http://www.podnapisi.net',
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
                            'url': provider_urls[curService] if curService in provider_urls else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': sickrage.srCore.srConfig.SUBTITLES_SERVICES_ENABLED[curIndex] == 1
                            })
        curIndex += 1

    for curService in subliminal.provider_manager.names():
        if curService not in [x['name'] for x in newList]:
            newList.append({'name': curService,
                            'url': provider_urls[curService] if curService in provider_urls else lmgtfy % curService,
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


def downloadSubtitles(subtitles_info):
    existing_subtitles = subtitles_info['subtitles']
    # First of all, check if we need subtitles
    languages = getNeededLanguages(existing_subtitles)
    if not languages:
        sickrage.srCore.srLogger.debug('%s: No missing subtitles for S%02dE%02d' % (
            subtitles_info['show.indexerid'], subtitles_info['season'], subtitles_info['episode']))
        return existing_subtitles, None

    subtitles_path = getSubtitlesPath(subtitles_info['location']).encode(sickrage.SYS_ENCODING)
    video_path = subtitles_info['location'].encode(sickrage.SYS_ENCODING)
    providers = getEnabledServiceList()

    try:
        video = subliminal.scan_video(video_path, subtitles=False, embedded_subtitles=False)
    except Exception:
        sickrage.srCore.srLogger.debug('%s: Exception caught in subliminal.scan_video for S%02dE%02d' %
                                     (subtitles_info['show.indexerid'], subtitles_info['season'], subtitles_info['episode']))
        return existing_subtitles, None

    provider_configs = {
        'addic7ed': {'username': sickrage.srCore.srConfig.ADDIC7ED_USER, 'password': sickrage.srCore.srConfig.ADDIC7ED_PASS},
        'legendastv': {'username': sickrage.srCore.srConfig.LEGENDASTV_USER, 'password': sickrage.srCore.srConfig.LEGENDASTV_PASS},
        'opensubtitles': {'username': sickrage.srCore.srConfig.OPENSUBTITLES_USER,
                          'password': sickrage.srCore.srConfig.OPENSUBTITLES_PASS}}

    pool = subliminal.api.ProviderPool(providers=providers, provider_configs=provider_configs)

    try:
        subtitles_list = pool.list_subtitles(video, languages)
        if not subtitles_list:
            sickrage.srCore.srLogger.debug('%s: No subtitles found for S%02dE%02d on any provider' % (
                subtitles_info['show.indexerid'], subtitles_info['season'], subtitles_info['episode']))
            return existing_subtitles, None

        found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                       hearing_impaired=sickrage.srCore.srConfig.SUBTITLES_HEARING_IMPAIRED,
                                                       only_one=not sickrage.srCore.srConfig.SUBTITLES_MULTI)

        save_subtitles(video, found_subtitles, directory=subtitles_path, single=not sickrage.srCore.srConfig.SUBTITLES_MULTI)

        if not sickrage.srCore.srConfig.EMBEDDED_SUBTITLES_ALL and sickrage.srCore.srConfig.SUBTITLES_EXTRA_SCRIPTS and video_path.endswith(
                ('.mkv', '.mp4')):
            run_subs_extra_scripts(subtitles_info, found_subtitles, video, single=not sickrage.srCore.srConfig.SUBTITLES_MULTI)

        current_subtitles = subtitlesLanguages(video_path)[0]
        new_subtitles = frozenset(current_subtitles).difference(existing_subtitles)

    except Exception:
        sickrage.srCore.srLogger.info("Error occurred when downloading subtitles for: %s" % video_path)
        sickrage.srCore.srLogger.error(traceback.format_exc())
        return existing_subtitles, None

    if sickrage.srCore.srConfig.SUBTITLES_HISTORY:
        from sickrage.core.tv.show.history import History
        for subtitle in found_subtitles:
            sickrage.srCore.srLogger.debug(
                'history.logSubtitle %s, %s' % (subtitle.provider_name, subtitle.language.opensubtitles))
            History.logSubtitle(subtitles_info['show.indexerid'], subtitles_info['season'],
                                subtitles_info['episode'],
                                subtitles_info['status'], subtitle)

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


def getNeededLanguages(current_subtitles):
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


def getSubtitlesPath(video_path):
    if os.path.isabs(sickrage.srCore.srConfig.SUBTITLES_DIR):
        new_subtitles_path = sickrage.srCore.srConfig.SUBTITLES_DIR
    elif sickrage.srCore.srConfig.SUBTITLES_DIR:
        new_subtitles_path = os.path.join(os.path.dirname(video_path), sickrage.srCore.srConfig.SUBTITLES_DIR)
        dir_exists = makeDir(new_subtitles_path)
        if not dir_exists:
            sickrage.srCore.srLogger.error('Unable to create subtitles folder ' + new_subtitles_path)
        else:
            chmodAsParent(new_subtitles_path)
    else:
        new_subtitles_path = os.path.join(os.path.dirname(video_path))

    return new_subtitles_path


def subtitlesLanguages(video_path):
    """Return a list detected subtitles for the given video file"""
    resultList = []
    should_save_subtitles = None
    embedded_subtitle_languages = set()

    if not sickrage.srCore.srConfig.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'):
        embedded_subtitle_languages = getEmbeddedLanguages(video_path.encode(sickrage.SYS_ENCODING))

    # Search subtitles with the absolute path
    if os.path.isabs(sickrage.srCore.srConfig.SUBTITLES_DIR):
        video_path = os.path.join(sickrage.srCore.srConfig.SUBTITLES_DIR, os.path.basename(video_path))
    # Search subtitles with the relative path
    elif sickrage.srCore.srConfig.SUBTITLES_DIR:
        check_subtitles_path = os.path.join(os.path.dirname(video_path), sickrage.srCore.srConfig.SUBTITLES_DIR)
        if not os.path.exists(check_subtitles_path):
            getSubtitlesPath(video_path)
        video_path = os.path.join(os.path.dirname(video_path), sickrage.srCore.srConfig.SUBTITLES_DIR,
                                  os.path.basename(video_path))
    else:
        video_path = os.path.join(os.path.dirname(video_path), os.path.basename(video_path))

    if not sickrage.srCore.srConfig.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'):
        external_subtitle_languages = scan_subtitle_languages(video_path)
        subtitle_languages = external_subtitle_languages.union(embedded_subtitle_languages)
        if not sickrage.srCore.srConfig.SUBTITLES_MULTI:
            currentWantedLanguages = wantedLanguages()
            if len(currentWantedLanguages) == 1 and babelfish.Language('und') in external_subtitle_languages:
                if embedded_subtitle_languages not in currentWantedLanguages and babelfish.Language(
                        'und') in embedded_subtitle_languages:
                    subtitle_languages.add(fromietf(currentWantedLanguages[0]))
                    should_save_subtitles = True
                elif embedded_subtitle_languages not in currentWantedLanguages and babelfish.Language(
                        'und') not in embedded_subtitle_languages:
                    subtitle_languages.remove(babelfish.Language('und'))
                    subtitle_languages.add(fromietf(currentWantedLanguages[0]))
                    should_save_subtitles = True
    else:
        subtitle_languages = scan_subtitle_languages(video_path)
        if not sickrage.srCore.srConfig.SUBTITLES_MULTI:
            if len(wantedLanguages()) == 1 and babelfish.Language('und') in subtitle_languages:
                subtitle_languages.remove(babelfish.Language('und'))
                subtitle_languages.add(fromietf(wantedLanguages()[0]))
                should_save_subtitles = True

    for language in subtitle_languages:
        if hasattr(language, 'opensubtitles') and language.opensubtitles:
            resultList.append(language.opensubtitles)
        elif hasattr(language, 'alpha3b') and language.alpha3b:
            resultList.append(language.alpha3b)
        elif hasattr(language, 'alpha3t') and language.alpha3t:
            resultList.append(language.alpha3t)
        elif hasattr(language, 'alpha2') and language.alpha2:
            resultList.append(language.alpha2)

    return sorted(resultList), should_save_subtitles


def getEmbeddedLanguages(video_path):
    embedded_subtitle_languages = set()
    try:
        with io.open(video_path, 'rb') as f:
            mkv = MKV(f)
            if mkv.subtitle_tracks:
                for st in mkv.subtitle_tracks:
                    if st.language:
                        try:
                            embedded_subtitle_languages.add(babelfish.Language.fromalpha3b(st.language))
                        except babelfish.Error:
                            sickrage.srCore.srLogger.debug('Embedded subtitle track is not a valid language')
                            embedded_subtitle_languages.add(babelfish.Language('und'))
                    elif st.name:
                        try:
                            embedded_subtitle_languages.add(babelfish.Language.fromname(st.name))
                        except babelfish.Error:
                            sickrage.srCore.srLogger.debug('Embedded subtitle track is not a valid language')
                            embedded_subtitle_languages.add(babelfish.Language('und'))
                    else:
                        embedded_subtitle_languages.add(babelfish.Language('und'))
            else:
                sickrage.srCore.srLogger.debug('MKV has no subtitle track')
    except MalformedMKVError:
        sickrage.srCore.srLogger.info('MKV seems to be malformed ( %s ), ignoring embedded subtitles' % video_path)

    return embedded_subtitle_languages


def scan_subtitle_languages(path):
    language_extensions = tuple('.' + c for c in babelfish.language_converters['opensubtitles'].codes)
    dirpath, filename = os.path.split(path)
    subtitles = set()
    for p in os.listdir(dirpath):
        if not isinstance(p, bytes) and p.startswith(os.path.splitext(filename)[0]) and p.endswith(
                subliminal.video.SUBTITLE_EXTENSIONS):
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

        # you have 5 minutes to understand that one. Good luck


        sqlResults = main_db.MainDB().select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.subtitles, ' +
            'e.subtitles_searchcount AS searchcount, e.subtitles_lastsearch AS lastsearch, e.location, (? - e.airdate) AS airdate_daydiff ' +
            'FROM tv_episodes AS e INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id) ' +
            'WHERE s.subtitles = 1 AND e.subtitles NOT LIKE (?) ' +
            'AND (e.subtitles_searchcount <= 2 OR (e.subtitles_searchcount <= 7 AND airdate_daydiff <= 7)) ' +
            'AND e.location != ""', [today, wantedLanguages(True)])

        if len(sqlResults) == 0:
            sickrage.srCore.srLogger.info('No subtitles to download')
            return

        rules = self._getRules()
        now = datetime.datetime.now()
        for epToSub in sqlResults:

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


def run_subs_extra_scripts(epObj, found_subtitles, video, single=False):
    for curScriptName in sickrage.srCore.srConfig.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", curScriptName) if piece.strip()]
        script_cmd[0] = os.path.abspath(script_cmd[0])
        sickrage.srCore.srLogger.debug("Absolute path to script: " + script_cmd[0])

        for subtitle in found_subtitles:
            subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

            inner_cmd = script_cmd + [video.name, subtitle_path, subtitle.language.opensubtitles, epObj['show.name'],
                                      str(epObj['season']), str(epObj['episode']), epObj['name'],
                                      str(epObj['show.indexerid'])]

            # use subprocess to run the command and capture output
            sickrage.srCore.srLogger.info("Executing command: %s" % inner_cmd)
            try:
                p = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, cwd=sickrage.PROG_DIR)
                out, _ = p.communicate()  # @UnusedVariable
                sickrage.srCore.srLogger.debug("Script result: %s" % out)

            except Exception as e:
                sickrage.srCore.srLogger.info("Unable to run subs_extra_script: {}".format(e.message))
