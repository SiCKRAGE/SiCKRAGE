# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://sickrage.ca/
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
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
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import sickrage
from CodernityDB.database import RecordNotFound
from sickrage.indexers.adba.aniDBerrors import AniDBCommandTimeoutError


class BlackAndWhiteList(object):
    blacklist = []
    whitelist = []

    def __init__(self, show_id):
        if not show_id:
            raise BlackWhitelistNoShowIDException()
        self.show_id = show_id
        self.load()

    def load(self):
        """
        Builds black and whitelist
        """
        sickrage.srCore.srLogger.debug('Building black and white list for ' + str(self.show_id))
        self.blacklist = self._load_list('blacklist')
        self.whitelist = self._load_list('whitelist')

    def _add_keywords(self, table, values):
        """
        DB: Adds keywords into database for current show

        :param table: database table to add keywords to
        :param values: Values to be inserted in table
        """
        for value in values:
            sickrage.srCore.mainDB.db.insert({
                '_t': table,
                'show_id': self.show_id,
                'keywork': value
            })

    def set_black_keywords(self, values):
        """
        Sets blacklist to new value

        :param values: Complete list of keywords to be set as blacklist
        """
        self._del_all_keywords('blacklist')
        self._add_keywords('blacklist', values)
        self.blacklist = values
        sickrage.srCore.srLogger.debug('Blacklist set to: %s' % self.blacklist)

    def set_white_keywords(self, values):
        """
        Sets whitelist to new value

        :param values: Complete list of keywords to be set as whitelist
        """
        self._del_all_keywords('whitelist')
        self._add_keywords('whitelist', values)
        self.whitelist = values
        sickrage.srCore.srLogger.debug('Whitelist set to: %s' % self.whitelist)

    def _del_all_keywords(self, table):
        """
        DB: Remove all keywords for current show

        :param table: database table remove keywords from
        """
        try:
            sickrage.srCore.mainDB.db.delete(sickrage.srCore.mainDB.db.get(table, self.show_id, with_doc=True)['doc'])
        except RecordNotFound:
            pass

    def _load_list(self, table):
        """
        DB: Fetch keywords for current show

        :param table: Table to fetch list of keywords from

        :return: keywords in list
        """
        groups = []
        for result in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many(table, self.show_id, with_doc=True)]:
            groups.append(result['keyword'])

        sickrage.srCore.srLogger.debug(
            'BWL: ' + str(self.show_id) + ' loaded keywords from ' + table + ': ' + str(groups))

        return groups

    def is_valid(self, result):
        """
        Check if result is valid according to white/blacklist for current show

        :param result: Result to analyse
        :return: False if result is not allowed in white/blacklist, True if it is
        """

        if self.whitelist or self.blacklist:
            if not result.release_group:
                sickrage.srCore.srLogger.debug('Failed to detect release group')
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

            sickrage.srCore.srLogger.debug(
                'Whitelist check passed: %s. Blacklist check passed: %s' % (white_result, black_result))

            if white_result and black_result:
                return True
            else:
                return False
        else:
            sickrage.srCore.srLogger.debug('No Whitelist and  Blacklist defined')
            return True


class BlackWhitelistNoShowIDException(Exception):
    """No show_id was given"""


def short_group_names(groups):
    """
    Find AniDB short group names for release groups

    :param groups: list of groups to find short group names for
    :return: list of shortened group names
    """
    groups = groups.split(",")
    shortGroupList = []
    if sickrage.srCore.ADBA_CONNECTION:
        for groupName in groups:
            try:
                group = sickrage.srCore.ADBA_CONNECTION.group(gname=groupName)
            except AniDBCommandTimeoutError:
                sickrage.srCore.srLogger.debug("Timeout while loading group from AniDB. Trying next group")
            except Exception:
                sickrage.srCore.srLogger.debug("Failed while loading group from AniDB. Trying next group")
            else:
                for line in group.datalines:
                    if line["shortname"]:
                        shortGroupList.append(line["shortname"])
                    else:
                        if groupName not in shortGroupList:
                            shortGroupList.append(groupName)
    else:
        shortGroupList = groups
    return shortGroupList
