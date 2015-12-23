#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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

import datetime
import logging
import os

import classes
import db
import helpers
import show_name_helpers
import sickbeard
from common import Quality
from providers import GenericProvider, sortedProviderList


class TorrentProvider(GenericProvider):
    def __init__(self, name):
        super(TorrentProvider, self).__init__(name)

        self.providerType = GenericProvider.TORRENT

    def isActive(self):
        return sickbeard.USE_TORRENTS and self.isEnabled()

    def _get_title_and_url(self, item):
        title = None
        download_url = None

        from feedparser.util import FeedParserDict
        if isinstance(item, (dict, FeedParserDict)):
            title = item.get('title', '')
            download_url = item.get('url', '')
            if not download_url:
                download_url = item.get('link', '')
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            title = item[0]
            download_url = item[1]

        # Temp global block `DIAMOND` releases
        if title and title.endswith('DIAMOND'):
            logging.info('Skipping DIAMOND release for mass fake releases.')
            title = download_url = 'FAKERELEASE'
        elif title:
            title = self._clean_title_from_provider(title)
        if download_url:
            download_url = download_url.replace('&amp;', '&')

        return title, download_url

    def _get_size(self, item):

        size = -1
        if isinstance(item, dict):
            size = item.get('size', -1)
        elif isinstance(item, (list, tuple)) and len(item) > 2:
            size = item[2]

        # Make sure we didn't select seeds/leechers by accident
        if not size or size < 1024 * 1024:
            size = -1

        return size

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  # 1) showName.SXX

            search_string[b'Season'].append(ep_string.encode('utf-8').strip())

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        for show_name in set(show_name_helpers.allPossibleShowNames(ep_obj.show)):
            ep_string = show_name + ' '
            if ep_obj.show.air_by_date:
                ep_string += str(ep_obj.airdate).replace('-', ' ')
            elif ep_obj.show.sports:
                ep_string += str(ep_obj.airdate).replace('-', ' ') + ('|', ' ')[
                    len(self.proper_strings) > 1] + ep_obj.airdate.strftime('%b')
            elif ep_obj.show.anime:
                ep_string += "%02d" % int(ep_obj.scene_absolute_number)
            else:
                ep_string += sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                   'episodenumber': ep_obj.scene_episode}
            if add_string:
                ep_string = ep_string + ' %s' % add_string

            search_string[b'Episode'].append(ep_string.strip())

        return [search_string]

    @staticmethod
    def _clean_title_from_provider(title):
        return (title or '').replace(' ', '.')

    def findPropers(self, search_date=datetime.datetime.today()):

        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
                'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
                ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
                ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
                ' AND e.status IN (' + ','.join(
                        [str(x) for x in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST]) + ')'
        )

        for sqlshow in sqlResults or []:
            show = helpers.findCertainShow(sickbeard.showList, int(sqlshow[b"showid"]))
            if show:
                curEp = show.getEpisode(int(sqlshow[b"season"]), int(sqlshow[b"episode"]))
                for term in self.proper_strings:
                    searchString = self._get_episode_search_strings(curEp, add_string=term)

                    for item in self._doSearch(searchString[0]):
                        title, url = self._get_title_and_url(item)
                        results.append(classes.Proper(title, url, datetime.datetime.today(), show))

        return results


def getTorrentProviderList():
    return [curProvider for curProvider in sortedProviderList() if issubclass(TorrentProvider, curProvider)]


def getTorrentRssProviderList(data):
    providerList = filter(lambda x: x, [makeTorrentRssProvider(x) for x in data.split('!!!')])

    seen_values = set()
    providerListDeduped = []
    for d in providerList:
        value = d.name
        if value not in seen_values:
            providerListDeduped.append(d)
            seen_values.add(value)

    return filter(lambda l: l, providerList)


def makeTorrentRssProvider(configString):
    if not configString:
        return None

    cookies = None
    titleTAG = 'title'
    search_mode = 'eponly'
    search_fallback = 0
    enable_daily = 0
    enable_backlog = 0

    try:
        values = configString.split('|')
        if len(values) == 9:
            name, url, cookies, titleTAG, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
        elif len(values) == 8:
            name, url, cookies, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
        else:
            name = values[0]
            url = values[1]
            enabled = values[4]
    except ValueError:
        logging.error("Skipping RSS Torrent provider string: '" + configString + "', incorrect format")
        return None

    try:
        torrentRss = os.sys.modules['sickbeard.providers.rsstorrent']
    except Exception:
        return

    newProvider = torrentRss.TorrentRssProvider(name, url, cookies, titleTAG, search_mode, search_fallback,
                                                enable_daily,
                                                enable_backlog)
    newProvider.enabled = enabled == '1'

    return newProvider
