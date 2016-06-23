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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import cgi
import os

import sickrage
from sickrage.core.common import NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, NOTIFY_GIT_UPDATE_TEXT, \
    NOTIFY_GIT_UPDATE
from sickrage.core.common import notifyStrings
from sickrage.notifiers import srNotifiers


def diagnose():
    '''
    Check the environment for reasons libnotify isn't working.  Return a
    user-readable message indicating possible issues.
    '''
    try:
        # noinspection PyUnresolvedReferences
        from gi.repository import Notify  # @UnusedImport
    except ImportError:
        return ("<p>Error: gir-notify isn't installed. On Ubuntu/Debian, install the "
                "<a href=\"apt:gir1.2-notify-0.7\">gir1.2-notify-0.7</a> or "
                "<a href=\"apt:gir1.0-notify-0.4\">gir1.0-notify-0.4</a> package.")
    if 'DISPLAY' not in os.environ and 'DBUS_SESSION_BUS_ADDRESS' not in os.environ:
        return ("<p>Error: Environment variables DISPLAY and DBUS_SESSION_BUS_ADDRESS "
                "aren't set.  libnotify will only work when you run SiCKRAGE "
                "from a desktop login.")
    try:
        # noinspection PyUnresolvedReferences
        import dbus
    except ImportError:
        pass
    else:
        try:
            bus = dbus.SessionBus()
        except dbus.DBusException as e:
            return ("<p>Error: unable to connect to D-Bus session bus: <code>%s</code>."
                    "<p>Are you running SiCKRAGE in a desktop session?") % (cgi.escape(e),)
        try:
            bus.get_object('org.freedesktop.Notifications',
                           '/org/freedesktop/Notifications')
        except dbus.DBusException as e:
            return ("<p>Error: there doesn't seem to be a notification daemon available: <code>%s</code> "
                    "<p>Try installing notification-daemon or notify-osd.") % (cgi.escape(e),)
    return "<p>Error: Unable to send notification."


class LibnotifyNotifier(srNotifiers):
    def __init__(self):
        self.Notify = None
        self.gobject = None

    def init_notify(self):
        if self.Notify is not None:
            return True
        try:
            # noinspection PyUnresolvedReferences
            from gi.repository import Notify
        except ImportError:
            sickrage.srCore.srLogger.error("Unable to import Notify from gi.repository. libnotify notifications won't work.")
            return False
        try:
            # noinspection PyUnresolvedReferences
            from gi.repository import GObject
        except ImportError:
            sickrage.srCore.srLogger.error("Unable to import GObject from gi.repository. We can't catch a GError in display.")
            return False
        if not Notify.init('SiCKRAGE'):
            sickrage.srCore.srLogger.error("Initialization of Notify failed. libnotify notifications won't work.")
            return False
        self.Notify = Notify
        self.gobject = GObject
        return True

    def _notify_snatch(self, ep_name):
        if sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONSNATCH:
            self._notify(notifyStrings[NOTIFY_SNATCH], ep_name)

    def _notify_download(self, ep_name):
        if sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONDOWNLOAD:
            self._notify(notifyStrings[NOTIFY_DOWNLOAD], ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify(notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD], ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.srCore.srConfig.USE_LIBNOTIFY:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notify(title, update_text + new_version)

    def test_notify(self):
        return self._notify('Test notification', "This is a test notification from SiCKRAGE", force=True)

    def _notify(self, title, message, force=False):
        if not sickrage.srCore.srConfig.USE_LIBNOTIFY and not force:
            return False
        if not self.init_notify():
            return False

        # Can't make this a global constant because PROG_DIR isn't available
        # when the module is imported.
        icon_path = os.path.join(sickrage.srCore.srConfig.GUI_DIR, 'images', 'ico', 'favicon-120.png')

        # If the session bus can't be acquired here a bunch of warning messages
        # will be printed but the call to show() will still return True.
        # pynotify doesn't seem too keen on error handling.
        n = self.Notify.Notification.new(title, message, icon_path)
        try:
            return n.show()
        except self.gobject.GError:
            return False
