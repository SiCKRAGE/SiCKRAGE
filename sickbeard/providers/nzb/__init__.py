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

import logging

import sickbeard
from providers import GenericProvider, sortedProviderList
from providers.nzb import newznab


class NZBProvider(GenericProvider):
    def __init__(self, name):
        super(NZBProvider, self).__init__(name)
        self.providerType = GenericProvider.NZB

    def isActive(self):
        return sickbeard.USE_NZBS and self.isEnabled()

    def _get_size(self, item):
        try:
            size = item.get('links')[1].get('length', -1)
        except IndexError:
            size = -1

        if not size:
            logging.debug("Size was not found in your provider response")

        return int(size)


def getNZBProviderList():
    return [curProvider for curProvider in sortedProviderList() if issubclass(NZBProvider, curProvider)]


def getNewznabProviderList(data):
    defaultList = [makeNewznabProvider(x) for x in getDefaultNewznabProviders().split('!!!')]
    providerList = filter(lambda x: x, [makeNewznabProvider(x) for x in data.split('!!!')])

    seen_values = set()
    providerListDeduped = []
    for d in providerList:
        value = d.name
        if value not in seen_values:
            providerListDeduped.append(d)
            seen_values.add(value)

    providerList = providerListDeduped
    providerDict = dict(zip([x.name for x in providerList], providerList))

    for curDefault in defaultList:
        if not curDefault:
            continue

        if curDefault.name not in providerDict:
            curDefault.default = True
            providerList.append(curDefault)
        else:
            providerDict[curDefault.name].default = True
            providerDict[curDefault.name].name = curDefault.name
            providerDict[curDefault.name].url = curDefault.url
            providerDict[curDefault.name].needs_auth = curDefault.needs_auth
            providerDict[curDefault.name].search_mode = curDefault.search_mode
            providerDict[curDefault.name].search_fallback = curDefault.search_fallback
            providerDict[curDefault.name].enable_daily = curDefault.enable_daily
            providerDict[curDefault.name].enable_backlog = curDefault.enable_backlog

    return filter(lambda x: x, providerList)


def makeNewznabProvider(configString):
    if not configString:
        return None

    search_mode = 'eponly'
    search_fallback = 0
    enable_daily = 0
    enable_backlog = 0

    try:
        values = configString.split('|')
        if len(values) == 9:
            name, url, key, catIDs, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
        else:
            name = values[0]
            url = values[1]
            key = values[2]
            catIDs = values[3]
            enabled = values[4]
    except ValueError:
        logging.error("Skipping Newznab provider string: '" + configString + "', incorrect format")
        return None

    newProvider = newznab.NewznabProvider(name, url, key=key, catIDs=catIDs, search_mode=search_mode,
                                          search_fallback=search_fallback, enable_daily=enable_daily,
                                          enable_backlog=enable_backlog)
    newProvider.enabled = enabled == '1'

    return newProvider


def getDefaultNewznabProviders():
    # name|url|key|catIDs|enabled|search_mode|search_fallback|enable_daily|enable_backlog
    return 'NZB.Cat|https://nzb.cat/||5030,5040,5010|0|eponly|1|1|1!!!' + \
           'NZBGeek|https://api.nzbgeek.info/||5030,5040|0|eponly|0|0|0!!!' + \
           'NZBs.org|https://nzbs.org/||5030,5040|0|eponly|0|0|0!!!' + \
           'Usenet-Crawler|https://www.usenet-crawler.com/||5030,5040|0|eponly|0|0|0'
