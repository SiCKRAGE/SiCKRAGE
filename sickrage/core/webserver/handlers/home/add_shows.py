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
import re
from urllib.parse import unquote_plus, urlencode

from tornado.escape import json_encode
from tornado.httputil import url_concat
from tornado.web import authenticated

import sickrage
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.enums import SearchFormat, SeriesProviderID
from sickrage.core.helpers import sanitize_file_name, make_dir, chmod_as_parent, checkbox_to_value
from sickrage.core.helpers.anidb import short_group_names
from sickrage.core.imdb_popular import imdbPopular
from sickrage.core.traktapi import TraktAPI
from sickrage.core.tv.show import TVShow
from sickrage.core.tv.show.helpers import find_show, get_show_list, find_show_by_location
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.series_providers.helpers import search_series_provider_for_series_id


def split_extra_show(extra_show):
    if not extra_show:
        return None, None, None, None

    split_vals = extra_show.split('|')

    if len(split_vals) < 4:
        series_provider_id = split_vals[0]
        show_dir = split_vals[1]
        return series_provider_id, show_dir, None, None

    series_provider_id = split_vals[0]
    show_dir = split_vals[1]
    series_id = split_vals[2]
    show_name = '|'.join(split_vals[3:])

    return series_provider_id, show_dir, series_id, show_name


class HomeAddShowsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('home/add_shows.mako',
                           title=_('Add Shows'),
                           header=_('Add Shows'),
                           topmenu='home',
                           controller='home',
                           action='add_shows')


class SearchSeriesProviderForShowNameHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        search_term = self.get_argument('search_term')
        series_provider_id = self.get_argument('series_provider_id', None)
        lang = self.get_argument('lang', None)

        results = []

        series_provider = sickrage.app.series_providers[SeriesProviderID[series_provider_id]]
        series_provider_language = lang if not lang or lang == 'null' else sickrage.app.config.general.series_provider_default_language

        sickrage.app.log.debug(f"Searching for Show with term: {search_term} on series provider: {series_provider.name}")

        # search via series name
        series_results = series_provider.search(search_term, language=series_provider_language)
        if series_results:
            for series in series_results:
                if not series.get('seriesname', None):
                    continue

                if not series.get('firstaired', None):
                    continue

                results.append((
                    series_provider.name,
                    series_provider_id,
                    series_provider.show_url,
                    int(series['id']),
                    series['seriesname'],
                    series['firstaired'],
                    ('', 'disabled')[isinstance(find_show(int(series['id']), SeriesProviderID[series_provider_id]), TVShow)]
                ))

        return json_encode({'results': results, 'langid': lang})


class MassAddTableHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        root_dir = self.get_arguments('rootDir')

        root_dirs = [unquote_plus(x) for x in root_dir]

        if sickrage.app.config.general.root_dirs:
            default_index = int(sickrage.app.config.general.root_dirs.split('|')[0])
        else:
            default_index = 0

        if len(root_dirs) > default_index:
            tmp = root_dirs[default_index]
            if tmp in root_dirs:
                root_dirs.remove(tmp)
                root_dirs = [tmp] + root_dirs

        dir_list = []

        for root_dir in root_dirs:
            try:
                file_list = os.listdir(root_dir)
            except Exception:
                continue

            for cur_file in file_list:
                try:
                    cur_path = os.path.normpath(os.path.join(root_dir, cur_file))
                    if not os.path.isdir(cur_path):
                        continue

                    # ignore Synology folders
                    if cur_file.lower() in ['#recycle', '@eadir']:
                        continue

                    cur_dir = {'dir': cur_path, 'display_dir': '<b>{}{}</b>{}'.format(os.path.dirname(cur_path), os.sep, os.path.basename(cur_path))}

                    # see if the folder is in database already
                    cur_dir['added_already'] = False
                    if find_show_by_location(cur_path):
                        cur_dir['added_already'] = True

                    dir_list.append(cur_dir)

                    series_id = show_name = series_provider_id = None
                    for cur_provider in sickrage.app.metadata_providers.values():
                        if all([series_id, show_name, series_provider_id]):
                            continue

                        (series_id, show_name, series_provider_id) = cur_provider.retrieve_show_metadata(cur_path)
                        if show_name:
                            if not series_provider_id and series_id:
                                for series_provider_id in SeriesProviderID:
                                    result = search_series_provider_for_series_id(series_provider_id, show_name)
                                    if result == series_id:
                                        break
                            elif not series_id and series_provider_id:
                                series_id = search_series_provider_for_series_id(series_provider_id, show_name)

                    cur_dir['existing_info'] = (series_id, show_name, series_provider_id)
                    if series_id and find_show(series_id, series_provider_id):
                        cur_dir['added_already'] = True
                except Exception:
                    pass

        return self.render('home/mass_add_table.mako',
                           dirList=dir_list,
                           controller='home',
                           action="mass_add_table")


class NewShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """

        show_to_add = self.get_argument('show_to_add', None)
        other_shows = self.get_arguments('other_shows')
        search_string = self.get_argument('search_string', None)

        series_provider_id, show_dir, series_id, show_name = split_extra_show(show_to_add)

        use_provided_info = False
        if series_id and series_provider_id and show_name:
            use_provided_info = True

        # use the given show_dir for the series provider search if available
        default_show_name = show_name or ''
        if not show_dir and search_string:
            default_show_name = search_string
        elif not show_name and show_dir:
            default_show_name = re.sub(r' \(\d{4}\)', '', os.path.basename(os.path.normpath(show_dir)).replace('.', ' '))

        provided_series_id = int(series_id or 0)
        provided_series_name = show_name or ''
        provided_series_provider_id = SeriesProviderID[series_provider_id] if series_provider_id else sickrage.app.config.general.series_provider_default

        return self.render('home/new_show.mako',
                           enable_anime_options=True,
                           use_provided_info=use_provided_info,
                           default_show_name=default_show_name,
                           other_shows=other_shows,
                           provided_show_dir=show_dir,
                           provided_series_id=provided_series_id,
                           provided_series_name=provided_series_name,
                           provided_series_provider_id=provided_series_provider_id,
                           series_providers=SeriesProviderID,
                           quality=sickrage.app.config.general.quality_default,
                           whitelist=[],
                           blacklist=[],
                           groups=[],
                           title=_('New Show'),
                           header=_('New Show'),
                           topmenu='home',
                           controller='home',
                           action="new_show")


class TraktShowsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """

        show_list = self.get_argument('list', 'trending')
        limit = self.get_argument('limit', None) or 10

        trakt_shows = []

        shows, black_list = getattr(TraktAPI()['shows'], show_list)(extended="full", limit=int(limit) + len(get_show_list())), False

        while len(trakt_shows) < int(limit):
            trakt_shows += [x for x in shows if 'tvdb' in x.ids and not find_show(int(x.ids['tvdb']))]

        return self.render('home/trakt_shows.mako',
                           title="Trakt {} Shows".format(show_list.capitalize()),
                           header="Trakt {} Shows".format(show_list.capitalize()),
                           enable_anime_options=False,
                           black_list=black_list,
                           trakt_shows=trakt_shows[:int(limit)],
                           trakt_list=show_list,
                           limit=limit,
                           controller='home',
                           action="trakt_shows")


class PopularShowsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        imdb_exception = None

        try:
            popular_shows = imdbPopular().fetch_popular_shows()
        except Exception as e:
            popular_shows = None
            imdb_exception = e

        return self.render('home/imdb_shows.mako',
                           title="IMDB Popular Shows",
                           header="IMDB Popular Shows",
                           popular_shows=popular_shows,
                           imdb_exception=imdb_exception,
                           topmenu="home",
                           controller='home',
                           action="popular_shows")


class AddShowToBlacklistHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        series_id = self.get_argument('series_id')

        data = {'shows': [{'ids': {'tvdb': series_id}}]}
        TraktAPI()["users/me/lists/{list}".format(list=sickrage.app.config.trakt.blacklist_name)].add(data)
        return self.redirect('/home/addShows/trendingShows/')


class ExistingShowsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        """
        Prints out the page to add existing shows from a root dir
        """
        return self.render('home/add_existing_shows.mako',
                           enable_anime_options=False,
                           quality=sickrage.app.config.general.quality_default,
                           title=_('Existing Show'),
                           header=_('Existing Show'),
                           topmenu="home",
                           controller='home',
                           action="add_existing_shows")


class AddShowByIDHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        series_id = self.get_argument('series_id')
        show_name = self.get_argument('showName')

        if re.search(r'tt\d+', series_id):
            result = sickrage.app.series_providers[SeriesProviderID.THETVDB].search(series_id)
            if result and 'id' in result:
                series_id = int(result['id'])

        if find_show(int(series_id), SeriesProviderID.THETVDB):
            sickrage.app.log.debug(f"{series_id} already exists in your show library, skipping!")
            return

        location = None
        if sickrage.app.config.general.root_dirs:
            root_dirs = sickrage.app.config.general.root_dirs.split('|')
            location = root_dirs[int(root_dirs[0]) + 1]

        if not location:
            sickrage.app.log.warning("There was an error creating the show, no root directory setting found")
            return _('No root directories setup, please go back and add one.')

        show_dir = os.path.join(location, sanitize_file_name(show_name))

        return self.redirect(url_concat("/home/addShows/newShow",
                                        {'show_to_add': '{series_provider_id}|{show_dir}|{series_id}|{show_name}'.format(
                                            **{'series_provider_id': SeriesProviderID.THETVDB.name,
                                               'show_dir': show_dir,
                                               'series_id': series_id,
                                               'show_name': show_name})}))


class AddNewShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.redirect("/home/")

    @authenticated
    def post(self, *args, **kwargs):
        """
        Receive tvdb id, dir, and other options and create a show from them. If extra show dirs are
        provided then it forwards back to newShow, if not it goes to /home.
        """

        whichSeries = self.get_argument('whichSeries', None)
        rootDir = self.get_argument('rootDir', None)
        fullShowPath = self.get_argument('fullShowPath', None)
        provided_series_name = self.get_argument('providedSeriesName', None)
        series_provider_language = self.get_argument('seriesProviderLanguage', None)
        defaultStatus = self.get_argument('defaultStatus', None)
        quality_preset = self.get_argument('quality_preset', None)
        anyQualities = self.get_arguments('anyQualities')
        bestQualities = self.get_arguments('bestQualities')
        flatten_folders = self.get_argument('flatten_folders', None)
        subtitles = self.get_argument('subtitles', None)
        sub_use_sr_metadata = self.get_argument('sub_use_sr_metadata', None)
        other_shows = self.get_arguments('other_shows')
        skipShow = self.get_argument('skipShow', None)
        provided_series_provider_id = self.get_argument('providedSeriesProviderID', None)
        anime = self.get_argument('anime', None)
        search_format = self.get_argument('search_format', None)
        dvd_order = self.get_argument('dvd_order', None)
        blacklist = self.get_argument('blacklist', None)
        whitelist = self.get_argument('whitelist', None)
        defaultStatusAfter = self.get_argument('defaultStatusAfter', None)
        scene = self.get_argument('scene', None)
        skip_downloaded = self.get_argument('skip_downloaded', None)
        add_show_year = self.get_argument('add_show_year', None)

        # if we're skipping then behave accordingly
        if skipShow:
            return self.finish_add_show(other_shows)

        if not whichSeries:
            return self.redirect("/home/")

        # figure out what show we're adding and where
        series_pieces = whichSeries.split('|')
        if (whichSeries and rootDir or whichSeries and fullShowPath) and len(series_pieces) > 1:
            if len(series_pieces) < 6:
                sickrage.app.log.error('Unable to add show due to show selection. Not anough arguments: %s' % (repr(series_pieces)))
                sickrage.app.alerts.error(_('Unknown error. Unable to add show due to problem with show selection.'))
                return self.redirect('/home/addShows/existingShows/')

            series_provider_id = series_pieces[1]
            series_id = int(series_pieces[3])
            show_name = series_pieces[4]
        else:
            series_provider_id = provided_series_provider_id or sickrage.app.config.general.series_provider_default
            series_id = int(whichSeries)
            if fullShowPath:
                show_name = os.path.basename(os.path.normpath(fullShowPath))
            else:
                show_name = provided_series_name

        # use the whole path if it's given, or else append the show name to the root dir to get the full show path
        if fullShowPath:
            show_dir = os.path.normpath(fullShowPath)
        else:
            show_dir = os.path.join(rootDir, sanitize_file_name(show_name))
            if add_show_year and not re.match(r'.*\(\d+\)$', show_dir) and re.search(r'\d{4}', series_pieces[5]):
                show_dir = "{} ({})".format(show_dir, re.search(r'\d{4}', series_pieces[5]).group(0))

        # blanket policy - if the dir exists you should have used "add existing show" numbnuts
        if os.path.isdir(show_dir) and not fullShowPath:
            sickrage.app.alerts.error(_("Unable to add show"),
                                      _("Folder ") + show_dir + _(" exists already"))
            return self.redirect('/home/addShows/existingShows/')

        # don't create show dir if config says not to
        if sickrage.app.config.general.add_shows_wo_dir:
            sickrage.app.log.info("Skipping initial creation of " + show_dir + " due to SiCKRAGE configuation setting")
        else:
            dir_exists = make_dir(show_dir)
            if not dir_exists:
                sickrage.app.log.warning("Unable to create the folder " + show_dir + ", can't add the show")
                sickrage.app.alerts.error(_("Unable to add show"),
                                          _("Unable to create the folder " +
                                            show_dir + ", can't add the show"))

                # Don't redirect to default page because user wants to see the new show
                return self.redirect("/home/")
            else:
                chmod_as_parent(show_dir)

        if whitelist:
            whitelist = short_group_names(whitelist)
        if blacklist:
            blacklist = short_group_names(blacklist)

        try:
            new_quality = Qualities[quality_preset.upper()]
        except (AttributeError, KeyError):
            new_quality = Quality.combine_qualities([Qualities[x.upper()] for x in anyQualities], [Qualities[x.upper()] for x in bestQualities])

        # add the show
        sickrage.app.show_queue.add_show(series_provider_id=SeriesProviderID[series_provider_id],
                                         series_id=series_id,
                                         showDir=show_dir,
                                         default_status=EpisodeStatus[defaultStatus],
                                         default_status_after=EpisodeStatus[defaultStatusAfter],
                                         quality=new_quality,
                                         flatten_folders=checkbox_to_value(flatten_folders),
                                         lang=series_provider_language or sickrage.app.config.general.series_provider_default_language,
                                         subtitles=checkbox_to_value(subtitles),
                                         sub_use_sr_metadata=checkbox_to_value(sub_use_sr_metadata),
                                         anime=checkbox_to_value(anime),
                                         dvd_order=checkbox_to_value(dvd_order),
                                         search_format=SearchFormat[search_format],
                                         paused=False,
                                         blacklist=blacklist,
                                         whitelist=whitelist,
                                         scene=checkbox_to_value(scene),
                                         skip_downloaded=checkbox_to_value(skip_downloaded))

        sickrage.app.alerts.message(_('Adding Show'), _('Adding the specified show into ') + show_dir)

        return self.finish_add_show(other_shows)

    def finish_add_show(self, other_shows):
        # if there are no extra shows then go home
        if not other_shows:
            return self.redirect('/home/')

        # peel off the next one
        next_show_dir = other_shows[0]
        rest_of_show_dirs = other_shows[1:]

        # go to add the next show
        return self.redirect("/home/addShows/newShow?" + urlencode({'show_to_add': next_show_dir, 'other_shows': rest_of_show_dirs}, True))


class AddExistingShowsHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        """
        Receives a dir list and add them. Adds the ones with given TVDB IDs first, then forwards
        along to the newShow page.
        """
        shows_to_add = self.get_arguments('shows_to_add')
        prompt_for_settings = self.get_argument('promptForSettings')

        # grab a list of other shows to add, if provided
        shows_to_add = [unquote_plus(x) for x in shows_to_add]

        prompt_for_settings = checkbox_to_value(prompt_for_settings)

        series_id_given = []
        dirs_only = []
        # separate all the ones with series id
        for cur_dir in shows_to_add:
            split_vals = cur_dir.split('|')
            if split_vals:
                if len(split_vals) > 2:
                    series_provider_id, show_dir, series_id, show_name = split_extra_show(cur_dir)
                    if all([show_dir, series_id, show_name]):
                        series_id_given.append((series_provider_id, show_dir, int(series_id), show_name))
                else:
                    dirs_only.append(cur_dir)
            else:
                dirs_only.append(cur_dir)

        # if they want me to prompt for settings then I will just carry on to the newShow page
        if prompt_for_settings and shows_to_add:
            return self.redirect("/home/addShows/newShow?" + urlencode({'show_to_add': shows_to_add[0], 'other_shows': shows_to_add[1:]}, True))

        # if they don't want me to prompt for settings then I can just add all the nfo shows now
        num_added = 0
        for cur_show in series_id_given:
            series_provider_id, show_dir, series_id, show_name = cur_show

            if series_provider_id is not None and series_id is not None:
                # add the show
                sickrage.app.show_queue.add_show(SeriesProviderID[series_provider_id],
                                                 series_id,
                                                 show_dir,
                                                 default_status=sickrage.app.config.general.status_default,
                                                 quality=sickrage.app.config.general.quality_default,
                                                 flatten_folders=sickrage.app.config.general.flatten_folders_default,
                                                 subtitles=sickrage.app.config.subtitles.default,
                                                 anime=sickrage.app.config.general.anime_default,
                                                 search_format=sickrage.app.config.general.search_format_default,
                                                 default_status_after=sickrage.app.config.general.status_default_after,
                                                 scene=sickrage.app.config.general.scene_default,
                                                 skip_downloaded=sickrage.app.config.general.skip_downloaded_default)
                num_added += 1

        if num_added:
            sickrage.app.alerts.message(_("Shows Added"),
                                        _("Automatically added ") + str(num_added) + _(" from their existing metadata files"))

        # if we're done then go home
        if not dirs_only:
            return self.redirect('/home/')

        # for the remaining shows we need to prompt for each one, so forward this on to the newShow page
        return self.redirect("/home/addShows/newShow?" + urlencode({'show_to_add': dirs_only[0], 'other_shows': dirs_only[1:]}, True))
