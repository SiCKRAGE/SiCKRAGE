# Author: echel0n <echel0n@sickrage.ca>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import sickrage


class srNotifiers(object):
    def __init__(self):
        self.session = None

    @staticmethod
    def notify_download(ep_name):
        for n in sickrage.srCore.notifiersDict.values():
            try:
                n._notify_download(ep_name)
            except:
                continue

    @staticmethod
    def notify_subtitle_download(ep_name, lang):
        for n in sickrage.srCore.notifiersDict.values():
            try:
                n._notify_subtitle_download(ep_name, lang)
            except:
                continue

    @staticmethod
    def notify_snatch(ep_name):
        for n in sickrage.srCore.notifiersDict.values():
            try:
                n._notify_snatch(ep_name)
            except:
                continue

    @staticmethod
    def notify_version_update(new_version=""):
        for n in sickrage.srCore.notifiersDict.values():
            try:
                n._notify_version_update(new_version)
            except:
                continue
