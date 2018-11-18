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
import threading
from datetime import datetime

from dateutil import tz

import sickrage
from sickrage.core.helpers import try_int
from sickrage.core.helpers.encoding import ss
from sickrage.core.websession import WebSession


class TimeZoneUpdater(object):
    def __init__(self):
        self.name = "TZUPDATER"
        self.time_regex = re.compile(r'(?P<hour>\d{1,2})(?:[:.]?(?P<minute>\d{2})?)? ?(?P<meridiem>[PA]\.? ?M?)?\b',
                                     re.I)

    def run(self):
        # set thread name
        threading.currentThread().setName(self.name)

        self.update_network_timezones()

    # update the network timezone table
    def update_network_timezones(self):
        """Update timezone information from SR repositories"""

        network_timezones = {}

        try:
            url_data = WebSession().get('https://cdn.sickrage.ca/network_timezones/').text
        except Exception:
            sickrage.app.log.warning('Updating network timezones failed.')
            return

        try:
            for line in url_data.splitlines():
                (key, val) = line.strip().rsplit(':', 1)
                if all([key, val]):
                    network_timezones[key] = val
        except (IOError, OSError):
            pass

        for x in sickrage.app.cache_db.all('network_timezones'):
            if x['network_name'] not in network_timezones:
                sickrage.app.cache_db.delete(x)

        for network, timezone in network_timezones.items():
            dbData = sickrage.app.cache_db.get('network_timezones', network)
            if not dbData:
                sickrage.app.cache_db.insert({
                    '_t': 'network_timezones',
                    'network_name': ss(network),
                    'timezone': timezone
                })
            elif dbData['timezone'] != timezone:
                dbData['timezone'] = timezone
                sickrage.app.cache_db.update(dbData)

        # cleanup
        del network_timezones

    # get timezone of a network or return default timezone
    def get_network_timezone(self, network):
        """
        Get a timezone of a network from a given network dict

        :param network: network to look up (needle)
        :return:
        """
        if network is None:
            return sickrage.app.tz

        try:
            return tz.gettz(sickrage.app.cache_db.get('network_timezones', network)['timezone'])
        except Exception:
            return sickrage.app.tz

    # parse date and time string into local time
    def parse_date_time(self, d, t, network):
        """
        Parse date and time string into local time
        :param d: date string
        :param t: time string
        :param network: network to use as base
        :return: datetime object containing local time
        """

        parsed_time = self.time_regex.search(t)
        network_tz = self.get_network_timezone(network)

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

    def test_timeformat(self, t):
        return self.time_regex.search(t) is not None
