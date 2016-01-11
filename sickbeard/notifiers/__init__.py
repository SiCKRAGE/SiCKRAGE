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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from sickbeard import NOTIFIERS


def notify_download(ep_name):
    for n in NOTIFIERS:
        n.notify_download(ep_name)


def notify_subtitle_download(ep_name, lang):
    for n in NOTIFIERS:
        n.notify_subtitle_download(ep_name, lang)


def notify_snatch(ep_name):
    for n in NOTIFIERS:
        n.notify_snatch(ep_name)


def notify_git_update(new_version=""):
    for n in NOTIFIERS:
        n.notify_git_update(new_version)