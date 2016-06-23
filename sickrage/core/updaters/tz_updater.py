# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import re
from datetime import datetime

from dateutil import tz

import sickrage
from sickrage.core.databases import cache_db
from sickrage.core.helpers import tryInt


time_regex = re.compile(r'(?P<hour>\d{1,2})(?:[:.]?(?P<minute>\d{2})?)? ?(?P<meridiem>[PA]\.? ?M?)?\b', re.I)
sr_timezone = tz.tzwinlocal() if tz.tzwinlocal else tz.tzlocal()


# update the network timezone table
def update_network_dict():
    """Update timezone information from SR repositories"""

    url = 'http://sickragetv.github.io/network_timezones/network_timezones.txt'

    try:
        url_data = sickrage.srCore.srWebSession.get(url).text
    except Exception:
        sickrage.srCore.srLogger.warning(
            'Updating network timezones failed, this can happen from time to time. URL: %s' % url)
        return

    d = {}
    try:
        for line in url_data.splitlines():
            (key, val) = line.strip().rsplit(':', 1)
            if key is None or val is None:
                continue
            d[key] = val
    except (IOError, OSError):
        pass

    network_timezones = load_network_dict()

    queries = []
    for network, timezone in d.items():
        existing = network in network_timezones
        if not existing:
            queries.append(['INSERT OR IGNORE INTO network_timezones VALUES (?,?);', [network, timezone]])
        elif network_timezones[network] is not timezone:
            queries.append(['UPDATE OR IGNORE network_timezones SET timezone = ? WHERE network_name = ?;',
                            [timezone, network]])

        if existing:
            del network_timezones[network]

    if network_timezones:
        purged = [x for x in network_timezones]
        queries.append(
            ['DELETE FROM network_timezones WHERE network_name IN (%s);' % ','.join(['?'] * len(purged)), purged])

    if len(queries) > 0:
        cache_db.CacheDB().mass_action(queries)
        del queries  # cleanup


# load network timezones from db into dict
def load_network_dict():
    """
    Return network timezones from db
    """
    try:
        cur_network_list = cache_db.CacheDB().select('SELECT * FROM network_timezones;')
        if cur_network_list:
            return dict(cur_network_list)
    except Exception:
        pass

    return {}

# get timezone of a network or return default timezone
def get_network_timezone(network, _network_dict):
    """
    Get a timezone of a network from a given network dict

    :param network: network to look up (needle)
    :param _network_dict: dict to look up in (haystack)
    :return:
    """
    if network is None:
        return sr_timezone

    try:
        return tz.gettz(_network_dict[network]) or sr_timezone
    except Exception:
        return sr_timezone


# parse date and time string into local time
def parse_date_time(d, t, network, dateOnly=False):
    """
    Parse date and time string into local time
    :param d: date string
    :param t: time string
    :param network: network to use as base
    :return: datetime object containing local time
    """

    parsed_time = time_regex.search(t)
    network_tz = get_network_timezone(network, load_network_dict())

    hr = 0
    m = 0

    if parsed_time:
        hr = tryInt(parsed_time.group('hour'))
        m = tryInt(parsed_time.group('minute'))

        ap = parsed_time.group('meridiem')
        ap = ap[0].lower() if ap else ''

        if ap == 'a' and hr == 12:
            hr -= 12
        elif ap == 'p' and hr != 12:
            hr += 12

        hr = hr if 0 <= hr <= 23 else 0
        m = m if 0 <= m <= 59 else 0

    result = datetime.fromordinal(max(tryInt(d), 1))

    return result.replace(hour=hr, minute=m, tzinfo=network_tz) if not dateOnly else result.replace(tzinfo=network_tz)


def test_timeformat(t):
    return time_regex.search(t) is not None
