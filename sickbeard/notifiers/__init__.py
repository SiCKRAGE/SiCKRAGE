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

from boxcar import BoxcarNotifier
from boxcar2 import Boxcar2Notifier
from emailnotify import EmailNotifier
from emby import EMBYNotifier
from freemobile import FreeMobileNotifier
from growl import GrowlNotifier
from kodi import KODINotifier
from libnotify import LibnotifyNotifier
from nma import NMA_Notifier
from nmj import NMJNotifier
from nmjv2 import NMJv2Notifier
from plex import PLEXNotifier
from prowl import ProwlNotifier
from pushalot import PushalotNotifier
from pushbullet import PushbulletNotifier
from pushover import PushoverNotifier
from pytivo import pyTivoNotifier
from synoindex import synoIndexNotifier
from synologynotifier import synologyNotifier
from trakt import TraktNotifier
from tweet import TwitterNotifier

# home theater / nas
kodi_notifier = KODINotifier()
plex_notifier = PLEXNotifier()
emby_notifier = EMBYNotifier()
nmj_notifier = NMJNotifier()
nmjv2_notifier = NMJv2Notifier()
synoindex_notifier = synoIndexNotifier()
synology_notifier = synologyNotifier()
pytivo_notifier = pyTivoNotifier()
# devices
growl_notifier = GrowlNotifier()
prowl_notifier = ProwlNotifier()
libnotify_notifier = LibnotifyNotifier()
pushover_notifier = PushoverNotifier()
boxcar_notifier = BoxcarNotifier()
boxcar2_notifier = Boxcar2Notifier()
nma_notifier = NMA_Notifier()
pushalot_notifier = PushalotNotifier()
pushbullet_notifier = PushbulletNotifier()
freemobile_notifier = FreeMobileNotifier()
# social
twitter_notifier = TwitterNotifier()
trakt_notifier = TraktNotifier()
email_notifier = EmailNotifier()

notifiers = [
    libnotify_notifier,  # Libnotify notifier goes first because it doesn't involve blocking on network activity.
    kodi_notifier,
    plex_notifier,
    nmj_notifier,
    nmjv2_notifier,
    synoindex_notifier,
    synology_notifier,
    pytivo_notifier,
    growl_notifier,
    freemobile_notifier,
    prowl_notifier,
    pushover_notifier,
    boxcar_notifier,
    boxcar2_notifier,
    nma_notifier,
    pushalot_notifier,
    pushbullet_notifier,
    twitter_notifier,
    trakt_notifier,
    email_notifier,
]


def notify_download(ep_name):
    for n in notifiers:
        n.notify_download(ep_name)


def notify_subtitle_download(ep_name, lang):
    for n in notifiers:
        n.notify_subtitle_download(ep_name, lang)


def notify_snatch(ep_name):
    for n in notifiers:
        n.notify_snatch(ep_name)


def notify_git_update(new_version=""):
    for n in notifiers:
        n.notify_git_update(new_version)
