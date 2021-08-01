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
import base64
import datetime
import json
import os
from functools import cmp_to_key

from tornado.httputil import url_concat
from tornado.web import authenticated

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import HomeLayout, HistoryLayout, PosterSortBy, PosterSortDirection
from sickrage.core.helpers import remove_article
from sickrage.core.media.util import series_image, SeriesImageType
from sickrage.core.tv.show.coming_episodes import ComingEpisodes, ComingEpsLayout, ComingEpsSortBy
from sickrage.core.tv.show.helpers import get_show_list, find_show
from sickrage.core.webserver.handlers.api.v1 import ApiV1Handler
from sickrage.core.webserver.handlers.base import BaseHandler


class RobotsDotTxtHandler(BaseHandler):
    def initialize(self):
        self.set_header('Content-Type', 'text/plain')

    def get(self, *args, **kwargs):
        """ Keep web crawlers out """
        return "User-agent: *\nDisallow: /"


class MessagesDotPoHandler(BaseHandler):
    def initialize(self):
        self.set_header('Content-Type', 'text/plain')

    @authenticated
    def get(self, *args, **kwargs):
        """ Get /sickrage/locale/{lang_code}/LC_MESSAGES/messages.po """
        if sickrage.app.config.gui.gui_lang:
            locale_file = os.path.join(sickrage.LOCALE_DIR, sickrage.app.config.gui.gui_lang, 'LC_MESSAGES/messages.po')
            if os.path.isfile(locale_file):
                with open(locale_file, 'r', encoding='utf8') as f:
                    return f.read()

class APIBulderHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        def titler(x):
            return (remove_article(x), x)[not x or sickrage.app.config.general.sort_article]

        episodes = {}

        for show_object in get_show_list():
            if show_object.series_id not in episodes:
                episodes[show_object.series_id] = {}

            for episode_object in show_object.episodes:
                if episode_object.season not in episodes[show_object.series_id]:
                    episodes[show_object.series_id][episode_object.season] = []

                episodes[show_object.series_id][episode_object.season].append(episode_object.episode)

        if len(sickrage.app.config.general.api_v1_key) == 32:
            apikey = sickrage.app.config.general.api_v1_key
        else:
            apikey = _('API Key not generated')

        api_commands = {}
        for command, api_call in ApiV1Handler(self.application, self.request).api_calls.items():
            api_commands[command] = api_call(self.application, self.request, **{'help': 1}).run()

        return self.render('api_builder.mako',
                           title=_('API Builder'),
                           header=_('API Builder'),
                           shows=sorted(get_show_list(), key=cmp_to_key(lambda x, y: titler(x.name) < titler(y.name))),
                           episodes=base64.b64encode(json.dumps(episodes).encode()).decode(),
                           apikey=apikey,
                           api_commands=api_commands,
                           controller='root',
                           action='api_builder')


class SetHomeLayoutHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        layout = self.get_argument('layout', 'POSTER')

        if layout not in ('POSTER', 'SMALL', 'BANNER', 'SIMPLE', 'DETAILED'):
            layout = 'POSTER'

        sickrage.app.config.gui.home_layout = HomeLayout[layout]
        sickrage.app.config.save()

        # Don't redirect to default page so user can see new layout
        return self.redirect("/home/")


class SetPosterSortByHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        sort = self.get_argument('sort', 'NAME')

        if sort not in ('NAME', 'DATE', 'NETWORK', 'PROGRESS'):
            sort = 'NAME'

        sickrage.app.config.gui.poster_sort_by = PosterSortBy[sort]
        sickrage.app.config.save()


class SetPosterSortDirHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        direction = self.get_argument('direction', 'ASCENDING')

        sickrage.app.config.gui.poster_sort_dir = PosterSortDirection[direction]
        sickrage.app.config.save()


class SetHistoryLayoutHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        layout = self.get_argument('layout', 'DETAILED')

        if layout not in ('COMPACT', 'DETAILED'):
            layout = 'DETAILED'

        sickrage.app.config.gui.history_layout = HistoryLayout[layout]

        return self.redirect("/history/")


class ToggleDisplayShowSpecialsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        sickrage.app.config.gui.display_show_specials = not sickrage.app.config.gui.display_show_specials
        return self.redirect(url_concat("/home/displayShow", {'show': show}))


class SetScheduleLayoutHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        layout = self.get_argument('layout', 'BANNER')

        if layout not in ('POSTER', 'BANNER', 'LIST', 'CALENDAR'):
            layout = 'BANNER'

        if layout == 'CALENDAR':
            sickrage.app.config.gui.coming_eps_sort = ComingEpsSortBy.DATE

        sickrage.app.config.gui.coming_eps_layout = ComingEpsLayout[layout]

        return self.redirect("/schedule/")


class ToggleScheduleDisplayPausedHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        sickrage.app.config.gui.coming_eps_display_paused = not sickrage.app.config.gui.coming_eps_display_paused
        self.redirect("/schedule/")


class SetScheduleSortHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        sort = self.get_argument('sort', 'DATE')

        if sort not in ('DATE', 'NETWORK', 'SHOW'):
            sort = 'DATE'

        if sickrage.app.config.gui.coming_eps_layout == ComingEpsLayout.CALENDAR:
            sort = 'DATE'

        sickrage.app.config.gui.coming_eps_sort = ComingEpsSortBy[sort]

        return self.redirect("/schedule/")


class ScheduleHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        layout = self.get_argument('layout', None)

        next_week = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=7),
                                              datetime.datetime.now().time().replace(tzinfo=sickrage.app.tz))

        today = datetime.datetime.now().replace(tzinfo=sickrage.app.tz)

        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, sickrage.app.config.gui.coming_eps_sort, False)

        return self.render('schedule.mako',
                           next_week=next_week,
                           today=today,
                           results=results,
                           layout=ComingEpsLayout[layout] if layout else sickrage.app.config.gui.coming_eps_layout,
                           title=_('Schedule'),
                           header=_('Schedule'),
                           topmenu='schedule',
                           controller='root',
                           action='schedule')


class QuicksearchDotJsonHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        term = self.get_argument('term')

        shows = []
        episodes = []

        session = sickrage.app.main_db.session()

        for result in session.query(MainDB.TVShow).filter(MainDB.TVShow.name.like('%{}%'.format(term))).all():
            shows.append({
                'category': 'shows',
                'series_id': result.series_id,
                'series_provider_id': result.series_provider_id.name,
                'seasons': len(set([s.season for s in result.episodes])),
                'name': result.name,
                'img': sickrage.app.config.general.web_root + series_image(result.series_id, result.series_provider_id, SeriesImageType.POSTER_THUMB).url
            })

        for result in session.query(MainDB.TVEpisode).filter(MainDB.TVEpisode.name.like('%{}%'.format(term))).all():
            show_object = find_show(result.series_id, result.series_provider_id)
            if not show_object:
                continue

            episodes.append({
                'category': 'episodes',
                'series_id': result.series_id,
                'series_provider_id': result.series_provider_id.name,
                'episode_id': result.episode_id,
                'season': result.season,
                'episode': result.episode,
                'name': result.name,
                'show_name': show_object.name,
                'img': sickrage.app.config.general.web_root + series_image(result.series_id, result.series_provider_id, SeriesImageType.POSTER_THUMB).url
            })

        if not len(shows):
            shows = [{
                'category': 'shows',
                'series_id': '',
                'series_provider_id': '',
                'name': term,
                'img': '/images/poster-thumb.png',
                'seasons': 0,
            }]

        return json.dumps(shows + episodes)


class ForceSchedulerJobHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        name = self.get_argument('name')

        service = getattr(sickrage.app, name, None)
        if service:
            job = sickrage.app.scheduler.get_job(service.name)
            if job:
                job.modify(next_run_time=datetime.datetime.utcnow(), kwargs={'force': True})
