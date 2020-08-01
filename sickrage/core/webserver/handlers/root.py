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
from abc import ABC
from functools import cmp_to_key

from tornado.httputil import url_concat
from tornado.web import authenticated

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.core.helpers import remove_article
from sickrage.core.media.util import showImage
from sickrage.core.tv.show.coming_episodes import ComingEpisodes
from sickrage.core.tv.show.helpers import get_show_list, find_show
from sickrage.core.webserver import ApiHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class RobotsDotTxtHandler(BaseHandler, ABC):
    def initialize(self):
        self.set_header('Content-Type', 'text/plain')

    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        """ Keep web crawlers out """
        return self.write("User-agent: *\nDisallow: /")


class MessagesDotPoHandler(BaseHandler, ABC):
    def initialize(self):
        self.set_header('Content-Type', 'text/plain')

    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        """ Get /sickrage/locale/{lang_code}/LC_MESSAGES/messages.po """
        if sickrage.app.config.gui_lang:
            locale_file = os.path.join(sickrage.LOCALE_DIR, sickrage.app.config.gui_lang, 'LC_MESSAGES/messages.po')
            if os.path.isfile(locale_file):
                with open(locale_file, 'r', encoding='utf8') as f:
                    return self.write(f.read())


class APIBulderHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        def titler(x):
            return (remove_article(x), x)[not x or sickrage.app.config.sort_article]

        episodes = {}

        for show_object in get_show_list():
            if show_object.indexer_id not in episodes:
                episodes[show_object.indexer_id] = {}

            for episode_object in show_object.episodes:
                if episode_object.season not in episodes[show_object.indexer_id]:
                    episodes[show_object.indexer_id][episode_object.season] = []

                episodes[show_object.indexer_id][episode_object.season].append(episode_object.episode)

        if len(sickrage.app.config.api_key) == 32:
            apikey = sickrage.app.config.api_key
        else:
            apikey = _('API Key not generated')

        api_commands = {}
        for command, api_call in ApiHandler(self.application, self.request).api_calls.items():
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


class SetHomeLayoutHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        layout = self.get_argument('layout', 'poster')

        if layout not in ('poster', 'small', 'banner', 'simple', 'detailed'):
            layout = 'poster'

        sickrage.app.config.home_layout = layout

        # Don't redirect to default page so user can see new layout
        return self.redirect("/home/")


class SetPosterSortByHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        sort = self.get_argument('sort')

        if sort not in ('name', 'date', 'network', 'progress'):
            sort = 'name'

        sickrage.app.config.poster_sortby = sort
        sickrage.app.config.save()


class SetPosterSortDirHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        direction = self.get_argument('direction')

        sickrage.app.config.poster_sortdir = int(direction)
        sickrage.app.config.save()


class SetHistoryLayoutHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        layout = self.get_argument('layout', 'detailed')

        if layout not in ('compact', 'detailed'):
            layout = 'detailed'

        sickrage.app.config.history_layout = layout

        return self.redirect("/history/")


class ToggleDisplayShowSpecialsHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        show = self.get_argument('show')

        sickrage.app.config.display_show_specials = not sickrage.app.config.display_show_specials
        return self.redirect(url_concat("/home/displayShow", {'show': show}))


class SetScheduleLayoutHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        layout = self.get_argument('layout', 'banner')

        if layout not in ('poster', 'banner', 'list', 'calendar'):
            layout = 'banner'

        if layout == 'calendar':
            sickrage.app.config.coming_eps_sort = 'date'

        sickrage.app.config.coming_eps_layout = layout

        return self.redirect("/schedule/")


class ToggleScheduleDisplayPausedHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        sickrage.app.config.coming_eps_display_paused = not sickrage.app.config.coming_eps_display_paused
        self.redirect("/schedule/")


class SetScheduleSortHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        sort = self.get_argument('sort', 'date')

        if sort not in ('date', 'network', 'show'):
            sort = 'date'

        if sickrage.app.config.coming_eps_layout == 'calendar':
            sort = 'date'

        sickrage.app.config.coming_eps_sort = sort

        return self.redirect("/schedule/")


class ScheduleHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        layout = self.get_argument('layout', sickrage.app.config.coming_eps_layout)

        next_week = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=7),
                                              datetime.datetime.now().time().replace(tzinfo=sickrage.app.tz))

        today = datetime.datetime.now().replace(tzinfo=sickrage.app.tz)

        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, sickrage.app.config.coming_eps_sort, False)

        return self.render('schedule.mako',
                           next_week=next_week,
                           today=today,
                           results=results,
                           layout=layout,
                           title=_('Schedule'),
                           header=_('Schedule'),
                           topmenu='schedule',
                           controller='root',
                           action='schedule')


class QuicksearchDotJsonHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        term = self.get_argument('term')

        shows = []
        episodes = []

        session = sickrage.app.main_db.session()

        for result in session.query(MainDB.TVShow).filter(MainDB.TVShow.name.like('%{}%'.format(term))).all():
            shows.append({
                'category': 'shows',
                'showid': result.indexer_id,
                'seasons': len(set([s.season for s in result.episodes])),
                'name': result.name,
                'img': sickrage.app.config.web_root + showImage(result.indexer_id, 'poster_thumb').url
            })

        for result in session.query(MainDB.TVEpisode).filter(MainDB.TVEpisode.name.like('%{}%'.format(term))).all():
            show_object = find_show(result.showid)
            if not show_object:
                continue

            episodes.append({
                'category': 'episodes',
                'showid': result.showid,
                'episodeid': result.indexer_id,
                'season': result.season,
                'episode': result.episode,
                'name': result.name,
                'showname': show_object.name,
                'img': sickrage.app.config.web_root + showImage(result.showid, 'poster_thumb').url
            })

        if not len(shows):
            shows = [{
                'category': 'shows',
                'showid': '',
                'name': term,
                'img': '/images/poster-thumb.png',
                'seasons': 0,
            }]

        return self.write(json.dumps(shows + episodes))


class ForceSchedulerJobHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        name = self.get_argument('name')

        service = getattr(sickrage.app, name, None)
        if service:
            job = sickrage.app.scheduler.get_job(service.name)
            if job:
                job.modify(next_run_time=datetime.datetime.utcnow(), kwargs={'force': True})
                sickrage.app.wserver.io_loop.add_timeout(datetime.timedelta(seconds=10), job.modify, kwargs={})
