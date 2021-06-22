# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import re

from dateutil import tz
from sqlalchemy import orm

import sickrage
from sickrage.core.databases.cache import CacheDB
from sickrage.core.helpers import try_int


class TimeZoneUpdater(object):
    def __init__(self):
        self.name = "TZUPDATER"
        self.running = False
        self.time_regex = re.compile(r'(?P<hour>\d{1,2})(?:[:.]?(?P<minute>\d{2})?)? ?(?P<meridiem>[PA]\.? ?M?)?\b', re.I)

    def update_network_timezone(self, network, timezone):
        session = sickrage.app.cache_db.session()

        try:
            dbData = session.query(CacheDB.NetworkTimezone).filter_by(network_name=network).one()
            if dbData.timezone != timezone:
                dbData.timezone = timezone
        except orm.exc.NoResultFound:
            session.add(CacheDB.NetworkTimezone(**{
                'network_name': network,
                'timezone': timezone
            }))
        finally:
            session.commit()

    def delete_network_timezone(self, network):
        session = sickrage.app.cache_db.session()
        session.query(CacheDB.NetworkTimezone).filter_by(network_name=network).delete()

    def update_network_timezones(self):
        """Update timezone information from SR repositories"""

        session = sickrage.app.cache_db.session()

        resp = sickrage.app.api.network_timezones()
        if not resp or 'data' not in resp:
            sickrage.app.log.warning('Updating network timezones failed.')
            return

        network_timezones = {item['network']: item['timezone'] for item in resp['data']}

        for x in session.query(CacheDB.NetworkTimezone):
            if x.network_name not in network_timezones:
                session.query(CacheDB.NetworkTimezone).filter_by(network_name=x.network_name).delete()
                session.commit()

        sql_to_add = []
        sql_to_update = []

        for network, timezone in network_timezones.items():
            try:
                dbData = session.query(CacheDB.NetworkTimezone).filter_by(network_name=network).one()
                if dbData.timezone != timezone:
                    dbData.timezone = timezone
                    sql_to_update.append(dbData.as_dict())
            except orm.exc.NoResultFound:
                sql_to_add.append({
                    'network_name': network,
                    'timezone': timezone
                })

        if len(sql_to_add):
            session.bulk_insert_mappings(CacheDB.NetworkTimezone, sql_to_add)
            session.commit()

        if len(sql_to_update):
            session.bulk_update_mappings(CacheDB.NetworkTimezone, sql_to_update)
            session.commit()

        # cleanup
        del network_timezones

    def get_network_timezone(self, network):
        """
        Get a timezone of a network from a given network dict

        :param network: network to look up (needle)
        :return:
        """
        if network is None:
            return sickrage.app.tz

        session = sickrage.app.cache_db.session()

        try:
            return tz.gettz(session.query(CacheDB.NetworkTimezone).filter_by(network_name=network).one().timezone)
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

        if isinstance(d, datetime.date):
            d = datetime.datetime.combine(d, datetime.datetime.min.time())

        return d.replace(hour=hr, minute=m, tzinfo=network_tz)

    def test_timeformat(self, t):
        return self.time_regex.search(t) is not None
