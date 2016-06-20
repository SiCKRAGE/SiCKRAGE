# Author: Nico Berlee http://nico.berlee.nl/
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

import re
import telnetlib
import urllib
import urllib2
from xml.etree import ElementTree

import sickrage
from sickrage.notifiers import srNotifiers


class NMJNotifier(srNotifiers):
    def notify_settings(self, host):
        """
        Retrieves the settings from a NMJ/Popcorn hour

        host: The hostname/IP of the Popcorn Hour server

        Returns: True if the settings were retrieved successfully, False otherwise
        """

        # establish a terminal session to the PC
        terminal = False
        try:
            terminal = telnetlib.Telnet(host)
        except Exception:
            sickrage.srCore.srLogger.warning("Warning: unable to get a telnet session to %s" % (host))
            return False

        # tell the terminal to output the necessary info to the screen so we can search it later
        sickrage.srCore.srLogger.debug("Connected to %s via telnet" % (host))
        terminal.read_until("sh-3.00# ")
        terminal.write("cat /tmp/source\n")
        terminal.write("cat /tmp/netshare\n")
        terminal.write("exit\n")
        tnoutput = terminal.read_all()

        database = ""
        device = ""
        match = re.search(r"(.+\.db)\r\n?(.+)(?=sh-3.00# cat /tmp/netshare)", tnoutput)

        # if we found the database in the terminal output then save that database to the config
        if match:
            database = match.group(1)
            device = match.group(2)
            sickrage.srCore.srLogger.debug("Found NMJ database %s on device %s" % (database, device))
            sickrage.srCore.srConfig.NMJ_DATABASE = database
        else:
            sickrage.srCore.srLogger.warning("Could not get current NMJ database on %s, NMJ is probably not running!" % (host))
            return False

        # if the device is a remote host then try to parse the mounting URL and save it to the config
        if device.startswith("NETWORK_SHARE/"):
            match = re.search(".*(?=\r\n?%s)" % (re.escape(device[14:])), tnoutput)

            if match:
                mount = match.group().replace("127.0.0.1", host)
                sickrage.srCore.srLogger.debug("Found mounting url on the Popcorn Hour in configuration: %s" % (mount))
                sickrage.srCore.srConfig.NMJ_MOUNT = mount
            else:
                sickrage.srCore.srLogger.warning("Detected a network share on the Popcorn Hour, but could not get the mounting url")
                return False

        return True

    def _notify_snatch(self, ep_name):
        return False
        # Not implemented: Start the scanner when snatched does not make any sense

    def _notify_download(self, ep_name):
        if sickrage.srCore.srConfig.USE_NMJ:
            self._notifyNMJ()

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srCore.srConfig.USE_NMJ:
            self._notifyNMJ()

    def _notify_version_update(self, new_version):
        return False
        # Not implemented, no reason to start scanner.

    def test_notify(self, host, database, mount):
        return self._sendNMJ(host, database, mount)

    def _sendNMJ(self, host, database, mount=None):
        """
        Sends a NMJ update command to the specified machine

        host: The hostname/IP to send the request to (no port)
        database: The database to send the requst to
        mount: The mount URL to use (optional)

        Returns: True if the request succeeded, False otherwise
        """

        # if a mount URL is provided then attempt to open a handle to that URL
        if mount:
            try:
                req = urllib2.Request(mount)
                sickrage.srCore.srLogger.debug("Try to mount network drive via url: %s" % (mount))
                handle = urllib2.urlopen(req)
            except IOError as e:
                if hasattr(e, 'reason'):
                    sickrage.srCore.srLogger.warning("NMJ: Could not contact Popcorn Hour on host %s: %s" % (host, e.reason))
                elif hasattr(e, 'code'):
                    sickrage.srCore.srLogger.warning("NMJ: Problem with Popcorn Hour on host %s: %s" % (host, e.code))
                return False
            except Exception as e:
                sickrage.srCore.srLogger.error("NMJ: Unknown exception: {}".format(e.message))
                return False

        # build up the request URL and parameters
        UPDATE_URL = "http://%(host)s:8008/metadata_database?%(params)s"
        params = {
            "arg0": "scanner_start",
            "arg1": database,
            "arg2": "background",
            "arg3": ""
        }
        params = urllib.urlencode(params)
        updateUrl = UPDATE_URL % {"host": host, "params": params}

        # send the request to the server
        try:
            req = urllib2.Request(updateUrl)
            sickrage.srCore.srLogger.debug("Sending NMJ scan update command via url: %s" % (updateUrl))
            handle = urllib2.urlopen(req)
            response = handle.read()
        except IOError as e:
            if hasattr(e, 'reason'):
                sickrage.srCore.srLogger.warning("NMJ: Could not contact Popcorn Hour on host %s: %s" % (host, e.reason))
            elif hasattr(e, 'code'):
                sickrage.srCore.srLogger.warning("NMJ: Problem with Popcorn Hour on host %s: %s" % (host, e.code))
            return False
        except Exception as e:
            sickrage.srCore.srLogger.error("NMJ: Unknown exception: {}".format(e.message))
            return False

        # try to parse the resulting XML
        try:
            et = ElementTree.fromstring(response)
            result = et.findtext("returnValue")
        except SyntaxError as e:
            sickrage.srCore.srLogger.error("Unable to parse XML returned from the Popcorn Hour: {}".format(e.message))
            return False

        # if the result was a number then consider that an error
        if int(result) > 0:
            sickrage.srCore.srLogger.error("Popcorn Hour returned an errorcode: {}".format(result))
            return False
        else:
            sickrage.srCore.srLogger.info("NMJ started background scan")
            return True

    def _notifyNMJ(self, host=None, database=None, mount=None, force=False):
        """
        Sends a NMJ update command based on the SB config settings

        host: The host to send the command to (optional, defaults to the host in the config)
        database: The database to use (optional, defaults to the database in the config)
        mount: The mount URL (optional, defaults to the mount URL in the config)
        force: If True then the notification will be sent even if NMJ is disabled in the config
        """
        if not sickrage.srCore.srConfig.USE_NMJ and not force:
            sickrage.srCore.srLogger.debug("Notification for NMJ scan update not enabled, skipping this notification")
            return False

        # fill in omitted parameters
        if not host:
            host = sickrage.srCore.srConfig.NMJ_HOST
        if not database:
            database = sickrage.srCore.srConfig.NMJ_DATABASE
        if not mount:
            mount = sickrage.srCore.srConfig.NMJ_MOUNT

        sickrage.srCore.srLogger.debug("Sending scan command for NMJ ")

        return self._sendNMJ(host, database, mount)
