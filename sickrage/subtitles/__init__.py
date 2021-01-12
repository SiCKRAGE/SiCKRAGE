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


import os
import pathlib
import re
import subprocess

import subliminal
from babelfish import language_converters, Language
from subliminal import save_subtitles

import sickrage
from sickrage.core.helpers import chmod_as_parent, make_dir
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.tv.show.history import History
from sickrage.subtitles.providers.utils import hash_itasa


class Subtitles(object):
    def __init__(self):
        # add subtitle providers
        for provider in ('itasa = sickrage.subtitles.providers.itasa:ItaSAProvider',
                         'legendastv = subliminal.providers.legendastv:LegendasTVProvider',
                         'wizdom = sickrage.subtitles.providers.wizdom:WizdomProvider',
                         'subscene = sickrage.subtitles.providers.subscene:SubsceneProvider',
                         'napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider'):
            if provider not in subliminal.provider_manager.registered_extensions + subliminal.provider_manager.internal_extensions:
                subliminal.provider_manager.register(str(provider))

        # add subtitle refiners
        for refiner in ('release = sickrage.subtitles.refiners.release:refine',
                        'tvepisode = sickrage.subtitles.refiners.tv_episode:refine'):
            if refiner not in subliminal.refiner_manager.registered_extensions + subliminal.refiner_manager.internal_extensions:
                subliminal.refiner_manager.register(str(refiner))

        # configure subtitle cache
        subliminal.region.configure('dogpile.cache.memory', replace_existing_backend=True)

        self.PROVIDER_URLS = {
            'addic7ed': 'http://www.addic7ed.com',
            'itasa': 'http://www.italiansubs.net/',
            'legendastv': 'http://www.legendas.tv',
            'napiprojekt': 'http://www.napiprojekt.pl',
            'opensubtitles': 'http://www.opensubtitles.org',
            'podnapisi': 'http://www.podnapisi.net',
            'subscenter': 'http://www.subscenter.org',
            'thesubdb': 'http://www.thesubdb.com',
            'tvsubtitles': 'http://www.tvsubtitles.net',
            'wizdom': 'http://wizdom.xyz',
            'subscene': 'https://subscene.com'
        }

        self.subtitle_extensions = [
            'srt',
            'sub',
            'ass',
            'idx',
            'ssa'
        ]

        self.episode_refiners = (
            'metadata',
            'release',
            'tvepisode',
            'tvdb',
            'omdb'
        )

    def sortedServiceList(self):
        newList = []
        lmgtfy = 'http://lmgtfy.com/?q=%s'

        curIndex = 0
        for curService in sickrage.app.config.subtitles.services_list.split(','):
            if curService in subliminal.provider_manager.names():
                newList.append({'name': curService,
                                'url': self.PROVIDER_URLS[curService] if curService in self.PROVIDER_URLS else lmgtfy % curService,
                                'image': curService + '.png',
                                'enabled': [int(x) for x in sickrage.app.config.subtitles.services_enabled.split('|') if x][curIndex] == 1
                                })
            curIndex += 1

        for curService in subliminal.provider_manager.names():
            if curService not in [x['name'] for x in newList]:
                newList.append({'name': curService,
                                'url': self.PROVIDER_URLS[curService] if curService in self.PROVIDER_URLS else lmgtfy % curService,
                                'image': curService + '.png',
                                'enabled': False,
                                })

        return newList

    def getEnabledServiceList(self):
        return [x['name'] for x in self.sortedServiceList() if x['enabled']]

    def download_subtitles(self, series_id, series_provider_id, season, episode):
        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return [], None

        episode_object = show_object.get_episode(season, episode)

        existing_subtitles = episode_object.subtitles
        if not isinstance(existing_subtitles, list):
            existing_subtitles = []

        # First of all, check if we need subtitles
        languages = self.get_needed_languages(existing_subtitles)
        if not languages:
            sickrage.app.log.debug('%s: No missing subtitles for S%02dE%02d' % (series_id, season, episode))
            return existing_subtitles, None

        subtitles_path = self.get_subtitles_path(episode_object.location)
        video_path = episode_object.location
        providers = self.getEnabledServiceList()

        video = self.get_video(video_path, subtitles_path=subtitles_path, episode_object=episode_object)
        if not video:
            sickrage.app.log.debug('%s: Exception caught in subliminal.scan_video for S%02dE%02d' % (series_id, season, episode))
            return existing_subtitles, None

        provider_configs = {
            'addic7ed': {
                'username': sickrage.app.config.subtitles.addic7ed_user,
                'password': sickrage.app.config.subtitles.addic7ed_pass
            },
            'itasa': {
                'username': sickrage.app.config.subtitles.itasa_user,
                'password': sickrage.app.config.subtitles.itasa_pass
            },
            'legendastv': {
                'username': sickrage.app.config.subtitles.legendastv_user,
                'password': sickrage.app.config.subtitles.legendastv_pass
            },
            'opensubtitles': {
                'username': sickrage.app.config.subtitles.opensubtitles_user,
                'password': sickrage.app.config.subtitles.opensubtitles_pass
            }
        }

        pool = subliminal.ProviderPool(providers=providers, provider_configs=provider_configs)

        try:
            subtitles_list = pool.list_subtitles(video, languages)
            if not subtitles_list:
                sickrage.app.log.debug('%s: No subtitles found for S%02dE%02d on any provider' % (series_id, season, episode))
                return existing_subtitles, None

            found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                           hearing_impaired=sickrage.app.config.subtitles.hearing_impaired,
                                                           only_one=not sickrage.app.config.subtitles.multi)

            save_subtitles(video, found_subtitles, directory=subtitles_path, single=not sickrage.app.config.subtitles.multi)

            if not sickrage.app.config.subtitles.enable_embedded and sickrage.app.config.subtitles.extra_scripts and video_path.endswith(('.mkv', '.mp4')):
                self.run_subs_extra_scripts(episode_object, found_subtitles, video, single=not sickrage.app.config.subtitles.multi)

            new_subtitles = sorted({subtitle.language.opensubtitles for subtitle in found_subtitles})
            current_subtitles = sorted({subtitle for subtitle in new_subtitles + existing_subtitles if subtitle})
            if not sickrage.app.config.subtitles.multi and len(found_subtitles) == 1:
                new_code = found_subtitles[0].language.opensubtitles
                if new_code not in existing_subtitles:
                    current_subtitles.remove(new_code)
                current_subtitles.append('und')

        except Exception as e:
            sickrage.app.log.error("Error occurred when downloading subtitles for {}: {}".format(video_path, e))
            return existing_subtitles, None

        if sickrage.app.config.subtitles.history:
            for subtitle in found_subtitles:
                sickrage.app.log.debug('history.logSubtitle %s, %s' % (subtitle.provider_name, subtitle.language.opensubtitles))
                History.log_subtitle(series_id, series_provider_id, season, episode, episode_object.status, subtitle)

        return current_subtitles, new_subtitles

    def wanted_languages(self):
        return frozenset(sickrage.app.config.subtitles.languages.split(',')).intersection(self.subtitle_code_filter())

    def get_needed_languages(self, subtitles):
        if not sickrage.app.config.subtitles.multi:
            return set() if 'und' in subtitles else {self.from_code(language) for language in self.wanted_languages()}
        return {self.from_code(language) for language in self.wanted_languages().difference(subtitles)}

    def refresh_subtitles(self, series_id, series_provider_id, season, episode):
        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return [], None

        episode_object = show_object.get_episode(season, episode)

        video = self.get_video(episode_object.location, episode_object=episode_object)
        if not video:
            sickrage.app.log.debug("Exception caught in subliminal.scan_video, subtitles couldn't be refreshed")
            return episode_object.subtitles, None
        current_subtitles = self.get_subtitles(video)
        if episode_object.subtitles == ','.join(current_subtitles):
            sickrage.app.log.debug('No changed subtitles for {}'.format(episode_object.pretty_name()))
            return episode_object.subtitles, None
        else:
            return current_subtitles, True

    def get_video(self, video_path, subtitles_path=None, subtitles=True, embedded_subtitles=None, episode_object=None):
        if not subtitles_path:
            subtitles_path = self.get_subtitles_path(video_path)

        try:
            video = subliminal.scan_video(video_path)
        except Exception as error:
            sickrage.app.log.debug('Exception: {}'.format(error))
        else:
            if video.size > 10485760:
                video.hashes['itasa'] = hash_itasa(video_path)

            # external subtitles
            if subtitles:
                video.subtitle_languages |= set(subliminal.core.search_external_subtitles(video_path, directory=subtitles_path).values())

            if embedded_subtitles is None:
                embedded_subtitles = bool(
                    not sickrage.app.config.subtitles.enable_embedded and video_path.endswith('.mkv'))

            subliminal.refine(video,
                              episode_refiners=self.episode_refiners,
                              embedded_subtitles=embedded_subtitles,
                              release_name=episode_object.name,
                              tv_episode=episode_object)

            video.alternative_series = [x.split('|')[0] for x in episode_object.show.scene_exceptions]

            # remove format metadata
            video.format = ""

            return video

    def get_subtitles_path(self, video_path):
        if pathlib.Path(sickrage.app.config.subtitles.dir).is_absolute() and pathlib.Path(sickrage.app.config.subtitles.dir).exists():
            new_subtitles_path = sickrage.app.config.subtitles.dir
        elif sickrage.app.config.subtitles.dir:
            new_subtitles_path = str(pathlib.Path(os.path.dirname(video_path)).joinpath(sickrage.app.config.subtitles.dir.strip('/')))
            dir_exists = make_dir(new_subtitles_path)
            if not dir_exists:
                sickrage.app.log.warning('Unable to create subtitles folder {}'.format(new_subtitles_path))
            else:
                chmod_as_parent(new_subtitles_path)
        else:
            new_subtitles_path = str(pathlib.Path(video_path).parent)

        return new_subtitles_path

    def get_subtitles(self, video):
        """Return a sorted list of detected subtitles for the given video file."""
        result_list = []

        if not video.subtitle_languages:
            return result_list

        for language in video.subtitle_languages:
            if hasattr(language, 'opensubtitles') and language.opensubtitles:
                result_list.append(language.opensubtitles)

        return sorted(result_list)

    def scan_subtitle_languages(self, path):
        language_extensions = tuple('.' + c for c in language_converters['opensubtitles'].codes)
        dirpath, filename = os.path.split(path)
        subtitles = set()
        for p in os.listdir(dirpath):
            if not isinstance(p, bytes) and p.startswith(os.path.splitext(filename)[0]) and p.endswith(
                    subliminal.SUBTITLE_EXTENSIONS):
                if os.path.splitext(p)[0].endswith(language_extensions) and len(
                        os.path.splitext(p)[0].rsplit('.', 1)[1]) == 2:
                    subtitles.add(Language.fromopensubtitles(os.path.splitext(p)[0][-2:]))
                elif os.path.splitext(p)[0].endswith(language_extensions) and len(
                        os.path.splitext(p)[0].rsplit('.', 1)[1]) == 3:
                    subtitles.add(Language.fromopensubtitles(os.path.splitext(p)[0][-3:]))
                elif os.path.splitext(p)[0].endswith('pt-BR') and len(
                        os.path.splitext(p)[0].rsplit('.', 1)[1]) == 5:
                    subtitles.add(Language.fromopensubtitles('pob'))
                else:
                    subtitles.add(Language('und'))

        return subtitles

    def subtitle_code_filter(self):
        return {code for code in language_converters['opensubtitles'].codes if len(code) == 3}

    def from_code(self, language):
        language = language.strip()
        if language and language in language_converters['opensubtitles'].codes:
            return Language.fromopensubtitles(language)

        return Language('und')

    def name_from_code(self, code):
        return self.from_code(code).name

    def code_from_code(self, code):
        return self.from_code(code).opensubtitles

    def run_subs_extra_scripts(self, episode_object, found_subtitles, video, single=False):
        for curScriptName in sickrage.app.config.subtitles.extra_scripts.split('|'):
            script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", curScriptName) if piece.strip()]
            script_cmd[0] = os.path.abspath(script_cmd[0])
            sickrage.app.log.debug("Absolute path to script: " + script_cmd[0])

            for subtitle in found_subtitles:
                subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

                inner_cmd = script_cmd + [video.name, subtitle_path, subtitle.language.opensubtitles, episode_object.show.name,
                                          str(episode_object.season), str(episode_object.episode), episode_object.name, str(episode_object.show.series_id)]

                # use subprocess to run the command and capture output
                sickrage.app.log.info("Executing command: %s" % inner_cmd)
                try:
                    p = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, cwd=sickrage.PROG_DIR)
                    out, __ = p.communicate()
                    sickrage.app.log.debug("Script result: %s" % out)

                except Exception as e:
                    sickrage.app.log.info("Unable to run subs_extra_script: {}".format(e))
