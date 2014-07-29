# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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

__all__ = ['ezrss',
           'tvtorrents',
           'womble',
           'btn',
           'thepiratebay',
           'kat',
           'torrentleech',
           'scc',
           'hdtorrents',
           'torrentday',
           'hdbits',
           'iptorrents',
           'omgwtfnzbs',
           'nextgen',
           'speedcd',
           'nyaatorrents',
           'fanzub',
           'torrentbytes',
           'animezb',
           'freshontv',
           'bitsoup'
]

import sickbeard
import generic
from sickbeard import logger
from os import sys


def sortedProviderList():
    initialList = sickbeard.providerList + sickbeard.newznabProviderList + sickbeard.torrentRssProviderList
    providerDict = dict(zip([x.getID() for x in initialList], initialList))

    newList = []

    # add all modules in the priority list, in order
    for curModule in sickbeard.PROVIDER_ORDER:
        if curModule in providerDict:
            newList.append(providerDict[curModule])

    # add any modules that are missing from that list
    for curModule in providerDict:
        if providerDict[curModule] not in newList:
            newList.append(providerDict[curModule])

    return newList

def makeProviderList():
    return [x.provider for x in [getProviderModule(y) for y in __all__] if x]


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

    return filter(lambda x: x, providerList)


def makeNewznabProvider(configString):
    if not configString:
        return None

    search_mode = 'eponly'
    search_fallback = 0

    try:
        name, url, key, catIDs, enabled, search_mode, search_fallback = configString.split('|')
    except ValueError:
        try:
            name, url, key, catIDs, enabled = configString.split('|')
        except ValueError:
            logger.log(u"Skipping Newznab provider string: '" + configString + "', incorrect format", logger.ERROR)
            return None

    newznab = sys.modules['sickbeard.providers.newznab']

    newProvider = newznab.NewznabProvider(name, url, key=key, catIDs=catIDs, search_mode=search_mode,
                                          search_fallback=search_fallback)
    newProvider.enabled = enabled == '1'

    return newProvider


def getTorrentRssProviderList(data):
    providerList = filter(lambda x: x, [makeTorrentRssProvider(x) for x in data.split('!!!')])

    seen_values = set()
    providerListDeduped = []
    for d in providerList:
        value = d.name
        if value not in seen_values:
            providerListDeduped.append(d)
            seen_values.add(value)

    return filter(lambda x: x, providerList)


def makeTorrentRssProvider(configString):
    if not configString:
        return None

    cookies = None
    search_mode = 'eponly'
    search_fallback = 0
    backlog_only = 0

    try:
        name, url, cookies, enabled, search_mode, search_fallback, backlog_only = configString.split('|')
    except ValueError:
        try:
            name, url, enabled, search_mode, search_fallback, backlog_only = configString.split('|')
        except ValueError:
            try:
                name, url, enabled = configString.split('|')
            except ValueError:
                logger.log(u"Skipping RSS Torrent provider string: '" + configString + "', incorrect format", logger.ERROR)
                return None

    try:
        torrentRss = sys.modules['sickbeard.providers.rsstorrent']
    except:
        return

    newProvider = torrentRss.TorrentRssProvider(name, url, cookies, search_mode, search_fallback, backlog_only)
    newProvider.enabled = enabled == '1'

    return newProvider


def getDefaultNewznabProviders():
    return 'Sick Beard Index|http://lolo.sickbeard.com/|0|5030,5040|0|eponly|0!!!NZBs.org|https://nzbs.org/||5030,5040|0|eponly|0!!!Usenet-Crawler|https://www.usenet-crawler.com/||5030,5040|0|eponly|0'


def getProviderModule(name):
    name = name.lower()
    prefix = "sickbeard.providers."
    if name in __all__ and prefix + name in sys.modules:
        return sys.modules[prefix + name]
    else:
        raise Exception("Can't find " + prefix + name + " in " + "Providers")


def getProviderClass(id):
    providerMatch = [x for x in
                     sickbeard.providerList + sickbeard.newznabProviderList + sickbeard.torrentRssProviderList if
                     x.getID() == id]

    if len(providerMatch) != 1:
        return None
    else:
        return providerMatch[0]
