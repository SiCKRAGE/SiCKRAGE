# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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

from CodernityDB.database import RecordNotFound
from dateutil import tz

import sickrage
from sickrage.core.helpers import try_int

network_dict = {}
time_regex = re.compile(r'(?P<hour>\d{1,2})(?:[:.]?(?P<minute>\d{2})?)? ?(?P<meridiem>[PA]\.? ?M?)?\b', re.I)


# update the network timezone table
def update_network_dict():
    """Update timezone information from SR repositories"""

    url = 'https://cdn.sickrage.ca/network_timezones/'

    try:
        url_data = sickrage.app.wsession.get(url).text
    except Exception:
        sickrage.app.log.warning(
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

    queries = []
    for network, timezone in d.items():
        existing = network in network_dict
        if not existing:
            try:
                sickrage.app.cache_db.db.get('network_timezones', network)
            except RecordNotFound:
                sickrage.app.cache_db.db.insert({
                    '_t': 'network_timezones',
                    'network_name': network,
                    'timezone': timezone
                })
        elif network_dict[network] is not timezone:
            try:
                dbData = sickrage.app.cache_db.db.get('network_timezones', network, with_doc=True)['doc']
                dbData['timezone'] = timezone
                sickrage.app.cache_db.db.update(dbData)
            except RecordNotFound:
                continue

        if existing:
            del network_dict[network]

    for x in network_dict:
        try:
            sickrage.app.cache_db.db.delete(
                sickrage.app.cache_db.db.get('network_timezones', x, with_doc=True)['doc'])
        except RecordNotFound:
            continue

    load_network_dict()


# load network timezones from db into dict
def load_network_dict():
    """
    Return network timezones from db
    """

    global network_dict
    network_dict = dict([(x['doc']['network_name'], x['doc']['timezone']) for x in
                         sickrage.app.cache_db.db.all('network_timezones', with_doc=True)])


# get timezone of a network or return default timezone
def get_network_timezone(network):
    """
    Get a timezone of a network from a given network dict

    :param network: network to look up (needle)
    :return:
    """
    if network is None:
        return sickrage.app.tz

    try:
        return tz.gettz(network_dict[network]) or sickrage.app.tz
    except Exception:
        return sickrage.app.tz


# parse date and time string into local time
def parse_date_time(d, t, network):
    """
    Parse date and time string into local time
    :param d: date string
    :param t: time string
    :param network: network to use as base
    :return: datetime object containing local time
    """

    if not network_dict:
        load_network_dict()

    parsed_time = time_regex.search(t)
    network_tz = get_network_timezone(network)

    hr = 0
    m = 0

    if parsed_time:
        hr = try_int(parsed_time.group('hour'))
        m = try_int(parsed_time.group('minute'))

        ap = parsed_time.group('meridiem')
        ap = ap[0].lower() if ap else ''

        if ap == 'a' and hr == 12:
            hr -= 12
        elif ap == 'p' and hr != 12:
            hr += 12

        hr = hr if 0 <= hr <= 23 else 0
        m = m if 0 <= m <= 59 else 0

    result = datetime.fromordinal(max(try_int(d), 1))

    return result.replace(hour=hr, minute=m, tzinfo=network_tz)


def test_timeformat(t):
    return time_regex.search(t) is not None
