# Author: echel0n <sickrage.tv@gmail.com>
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


def notify_download(ep_name):
    for n in sickrage.NOTIFIERS.values():
        try:n.notify_download(ep_name)
        except:continue

def notify_subtitle_download(ep_name, lang):
    for n in sickrage.NOTIFIERS.values():
        try:n.notify_subtitle_download(ep_name, lang)
        except:continue

def notify_snatch(ep_name):
    for n in sickrage.NOTIFIERS.values():
        try:n.notify_snatch(ep_name)
        except:continue


def notify_version_update(new_version=""):
    for n in sickrage.NOTIFIERS.values():
        try:n.notify_version_update(new_version)
        except:continue
