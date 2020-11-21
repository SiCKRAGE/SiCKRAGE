# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://sickrage.ca/
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import sickrage
from sickrage.core.databases.main import MainDB


class BlackAndWhiteList(object):
    blacklist = []
    whitelist = []

    def __init__(self, series_id, series_provider_id):
        if not series_id:
            raise BlackWhitelistNoShowIDException()
        self.series_id = series_id
        self.series_provider_id = series_provider_id
        self.load()

    def load(self):
        """
        Builds black and whitelist
        """

        session = sickrage.app.main_db.session()

        sickrage.app.log.debug('Building black and white list for ' + str(self.series_id))

        self.blacklist = self._load_list(session.query(MainDB.Blacklist).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id))
        sickrage.app.log.debug('BWL: {} loaded keywords from {}: {}'.format(self.series_id, MainDB.Blacklist.__tablename__, self.blacklist))

        self.whitelist = self._load_list(session.query(MainDB.Whitelist).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id))
        sickrage.app.log.debug('BWL: {} loaded keywords from {}: {}'.format(self.series_id, MainDB.Whitelist.__tablename__, self.whitelist))

    def _add_keywords(self, table, values):
        """
        DB: Adds keywords into database for current show

        :param table: database table to add keywords to
        :param values: Values to be inserted in table
        """

        session = sickrage.app.main_db.session()

        for value in values:
            session.add(table(**{
                'series_id': self.series_id,
                'series_provider_id': self.series_provider_id,
                'keyword': value
            }))
            session.commit()

    def set_black_keywords(self, values):
        """
        Sets blacklist to new value

        :param values: Complete list of keywords to be set as blacklist
        :param session: Database session
        """

        session = sickrage.app.main_db.session()
        session.query(MainDB.Blacklist).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).delete()
        session.commit()

        self._add_keywords(MainDB.Blacklist, values)
        self.blacklist = values

        sickrage.app.log.debug('Blacklist set to: %s' % self.blacklist)

    def set_white_keywords(self, values):
        """
        Sets whitelist to new value

        :param values: Complete list of keywords to be set as whitelist
        :param session: Database session
        """
        session = sickrage.app.main_db.session()
        session.query(MainDB.Whitelist).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).delete()
        session.commit()

        self._add_keywords(MainDB.Whitelist, values)
        self.whitelist = values

        sickrage.app.log.debug('Whitelist set to: %s' % self.whitelist)

    def _load_list(self, keyword_list):
        """
        DB: Fetch keywords for current show

        :return: keywords in list
        """
        try:
            groups = [x.keyword for x in keyword_list]
        except KeyError:
            groups = []

        return groups

    def is_valid(self, result):
        """
        Check if result is valid according to white/blacklist for current show

        :param result: Result to analyse
        :return: False if result is not allowed in white/blacklist, True if it is
        """

        if self.whitelist or self.blacklist:
            if not result.release_group:
                sickrage.app.log.debug('Failed to detect release group')
                return False

            if result.release_group.lower() in [x.lower() for x in self.whitelist]:
                white_result = True
            elif not self.whitelist:
                white_result = True
            else:
                white_result = False
            if result.release_group.lower() in [x.lower() for x in self.blacklist]:
                black_result = False
            else:
                black_result = True

            sickrage.app.log.debug(
                'Whitelist check passed: %s. Blacklist check passed: %s' % (white_result, black_result))

            if white_result and black_result:
                return True
            else:
                return False
        else:
            sickrage.app.log.debug('No Whitelist and  Blacklist defined')
            return True


class BlackWhitelistNoShowIDException(Exception):
    """No series_id was given"""
