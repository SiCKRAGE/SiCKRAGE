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

import httplib
import urllib
import urllib2
import socket
import base64
import time

import sickbeard
import logging
from sickbeard import common
from sickrage.helper.exceptions import ex
from sickrage.helper.encoding import ss

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

try:
    import json
except ImportError:
    import simplejson as json


class KODINotifier:
    sr_logo_url = 'https://raw.githubusercontent.com/SiCKRAGETV/SiCKRAGE/master/gui/slick/images/sickrage-shark-mascot.png'

    def _get_kodi_version(self, host, username, password):
        """Returns KODI JSON-RPC API version (odd # = dev, even # = stable)

        Sends a request to the KODI host using the JSON-RPC to determine if
        the legacy API or if the JSON-RPC API functions should be used.

        Fallback to testing legacy HTTPAPI before assuming it is just a badly configured host.

        Args:
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password

        Returns:
            Returns API number or False

            List of possible known values:
                API | KODI Version
               -----+---------------
                 2  | v10 (Dharma)
                 3  | (pre Eden)
                 4  | v11 (Eden)
                 5  | (pre Frodo)
                 6  | v12 (Frodo) / v13 (Gotham)

        """

        # since we need to maintain python 2.5 compatability we can not pass a timeout delay to urllib2 directly (python 2.6+)
        # override socket timeout to reduce delay for this call alone
        socket.setdefaulttimeout(10)

        checkCommand = '{"jsonrpc":"2.0","method":"JSONRPC.Version","id":1}'
        result = self._send_to_kodi_json(checkCommand, host, username, password)

        # revert back to default socket timeout
        socket.setdefaulttimeout(sickbeard.SOCKET_TIMEOUT)

        if result:
            return result[b"result"][b"version"]
        else:
            # fallback to legacy HTTPAPI method
            testCommand = {'command': 'Help'}
            request = self._send_to_kodi(testCommand, host, username, password)
            if request:
                # return a fake version number, so it uses the legacy method
                return 1
            else:
                return False

    def _notify_kodi(self, message, title="SiCKRAGE", host=None, username=None, password=None, force=False):
        """Internal wrapper for the notify_snatch and notify_download functions

        Detects JSON-RPC version then branches the logic for either the JSON-RPC or legacy HTTP API methods.

        Args:
            message: Message body of the notice to send
            title: Title of the notice to send
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password
            force: Used for the Test method to override config saftey checks

        Returns:
            Returns a list results in the format of host:ip:result
            The result will either be 'OK' or False, this is used to be parsed by the calling function.

        """

        # fill in omitted parameters
        if not host:
            host = sickbeard.KODI_HOST
        if not username:
            username = sickbeard.KODI_USERNAME
        if not password:
            password = sickbeard.KODI_PASSWORD

        # suppress notifications if the notifier is disabled but the notify options are checked
        if not sickbeard.USE_KODI and not force:
            logging.debug("Notification for KODI not enabled, skipping this notification")
            return False

        result = ''
        for curHost in [x.strip() for x in host.split(",")]:
            logging.debug("Sending KODI notification to '" + curHost + "' - " + message)

            kodiapi = self._get_kodi_version(curHost, username, password)
            if kodiapi:
                if kodiapi <= 4:
                    logging.debug("Detected KODI version <= 11, using KODI HTTP API")
                    command = {'command': 'ExecBuiltIn',
                               'parameter': 'Notification(' + title.encode("utf-8") + ',' + message.encode(
                                       "utf-8") + ')'}
                    notifyResult = self._send_to_kodi(command, curHost, username, password)
                    if notifyResult:
                        result += curHost + ':' + str(notifyResult)
                else:
                    logging.debug("Detected KODI version >= 12, using KODI JSON API")
                    command = '{"jsonrpc":"2.0","method":"GUI.ShowNotification","params":{"title":"%s","message":"%s", "image": "%s"},"id":1}' % (
                        title.encode("utf-8"), message.encode("utf-8"), self.sr_logo_url)
                    notifyResult = self._send_to_kodi_json(command, curHost, username, password)
                    if notifyResult and notifyResult.get('result'):
                        result += curHost + ':' + notifyResult[b"result"].decode(sickbeard.SYS_ENCODING)
            else:
                if sickbeard.KODI_ALWAYS_ON or force:
                    logging.warning(
                        "Failed to detect KODI version for '" + curHost + "', check configuration and try again.")
                result += curHost + ':False'

        return result

    def _send_update_library(self, host, showName=None):
        """Internal wrapper for the update library function to branch the logic for JSON-RPC or legacy HTTP API

        Checks the KODI API version to branch the logic to call either the legacy HTTP API or the newer JSON-RPC over HTTP methods.

        Args:
            host: KODI webserver host:port
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False, if the update was successful

        """

        logging.debug("Sending request to update library for KODI host: '" + host + "'")

        kodiapi = self._get_kodi_version(host, sickbeard.KODI_USERNAME, sickbeard.KODI_PASSWORD)
        if kodiapi:
            if kodiapi <= 4:
                # try to update for just the show, if it fails, do full update if enabled
                if not self._update_library(host, showName) and sickbeard.KODI_UPDATE_FULL:
                    logging.debug("Single show update failed, falling back to full update")
                    return self._update_library(host)
                else:
                    return True
            else:
                # try to update for just the show, if it fails, do full update if enabled
                if not self._update_library_json(host, showName) and sickbeard.KODI_UPDATE_FULL:
                    logging.debug("Single show update failed, falling back to full update")
                    return self._update_library_json(host)
                else:
                    return True
        elif sickbeard.KODI_ALWAYS_ON:
            logging.warning("Failed to detect KODI version for '" + host + "', check configuration and try again.")

        return False

    # #############################################################################
    # Legacy HTTP API (pre KODI 12) methods
    ##############################################################################

    def _send_to_kodi(self, command, host=None, username=None, password=None):
        """Handles communication to KODI servers via HTTP API

        Args:
            command: Dictionary of field/data pairs, encoded via urllib and passed to the KODI API via HTTP
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password

        Returns:
            Returns response.result for successful commands or False if there was an error

        """

        # fill in omitted parameters
        if not username:
            username = sickbeard.KODI_USERNAME
        if not password:
            password = sickbeard.KODI_PASSWORD

        if not host:
            logging.warning('No KODI host passed, aborting update')
            return False

        for key in command:
            if isinstance(command[key], unicode):
                command[key] = command[key].encode('utf-8')

        enc_command = urllib.urlencode(command)
        logging.debug("KODI encoded API command: " + enc_command)

        url = 'http://%s/kodiCmds/kodiHttp/?%s' % (host, enc_command)
        try:
            req = urllib2.Request(url)
            # if we have a password, use authentication
            if password:
                base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
                authheader = "Basic %s" % base64string
                req.add_header("Authorization", authheader)
                logging.debug("Contacting KODI (with auth header) via url: " + ss(url))
            else:
                logging.debug("Contacting KODI via url: " + ss(url))

            try:
                response = urllib2.urlopen(req)
            except (httplib.BadStatusLine, urllib2.URLError) as e:
                logging.debug("Couldn't contact KODI HTTP at %r : %r" % (url, ex(e)))
                return False

            result = response.read().decode(sickbeard.SYS_ENCODING)
            response.close()

            logging.debug("KODI HTTP response: " + result.replace('\n', ''))
            return result

        except Exception as e:
            logging.debug("Couldn't contact KODI HTTP at %r : %r" % (url, ex(e)))
            return False

    def _update_library(self, host=None, showName=None):
        """Handles updating KODI host via HTTP API

        Attempts to update the KODI video library for a specific tv show if passed,
        otherwise update the whole library if enabled.

        Args:
            host: KODI webserver host:port
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False

        """

        if not host:
            logging.warning('No KODI host passed, aborting update')
            return False

        logging.debug("Updating KODI library via HTTP method for host: " + host)

        # if we're doing per-show
        if showName:
            logging.debug("Updating library in KODI via HTTP method for show " + showName)

            pathSql = 'select path.strPath from path, tvshow, tvshowlinkpath where ' \
                      'tvshow.c00 = "%s" and tvshowlinkpath.idShow = tvshow.idShow ' \
                      'and tvshowlinkpath.idPath = path.idPath' % (showName)

            # use this to get xml back for the path lookups
            xmlCommand = {
                'command': 'SetResponseFormat(webheader;false;webfooter;false;header;<xml>;footer;</xml>;opentag;<tag>;closetag;</tag>;closefinaltag;false)'}
            # sql used to grab path(s)
            sqlCommand = {'command': 'QueryVideoDatabase(%s)' % (pathSql)}
            # set output back to default
            resetCommand = {'command': 'SetResponseFormat()'}

            # set xml response format, if this fails then don't bother with the rest
            request = self._send_to_kodi(xmlCommand, host)
            if not request:
                return False

            sqlXML = self._send_to_kodi(sqlCommand, host)
            request = self._send_to_kodi(resetCommand, host)

            if not sqlXML:
                logging.debug("Invalid response for " + showName + " on " + host)
                return False

            encSqlXML = urllib.quote(sqlXML, ':\\/<>')
            try:
                et = etree.fromstring(encSqlXML)
            except SyntaxError as e:
                logging.error("Unable to parse XML returned from KODI: {}".format(ex(e)))
                return False

            paths = et.findall('.//field')

            if not paths:
                logging.debug("No valid paths found for " + showName + " on " + host)
                return False

            for path in paths:
                # we do not need it double-encoded, gawd this is dumb
                unEncPath = urllib.unquote(path.text).decode(sickbeard.SYS_ENCODING)
                logging.debug("KODI Updating " + showName + " on " + host + " at " + unEncPath)
                updateCommand = {'command': 'ExecBuiltIn', 'parameter': 'KODI.updatelibrary(video, %s)' % (unEncPath)}
                request = self._send_to_kodi(updateCommand, host)
                if not request:
                    logging.warning("Update of show directory failed on " + showName + " on " + host + " at " + unEncPath)
                    return False
                # sleep for a few seconds just to be sure kodi has a chance to finish each directory
                if len(paths) > 1:
                    time.sleep(5)
        # do a full update if requested
        else:
            logging.debug("Doing Full Library KODI update on host: " + host)
            updateCommand = {'command': 'ExecBuiltIn', 'parameter': 'KODI.updatelibrary(video)'}
            request = self._send_to_kodi(updateCommand, host)

            if not request:
                logging.warning("KODI Full Library update failed on: " + host)
                return False

        return True

    ##############################################################################
    # JSON-RPC API (KODI 12+) methods
    ##############################################################################

    def _send_to_kodi_json(self, command, host=None, username=None, password=None):
        """Handles communication to KODI servers via JSONRPC

        Args:
            command: Dictionary of field/data pairs, encoded via urllib and passed to the KODI JSON-RPC via HTTP
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password

        Returns:
            Returns response.result for successful commands or False if there was an error

        """

        # fill in omitted parameters
        if not username:
            username = sickbeard.KODI_USERNAME
        if not password:
            password = sickbeard.KODI_PASSWORD

        if not host:
            logging.warning('No KODI host passed, aborting update')
            return False

        command = command.encode('utf-8')
        logging.debug("KODI JSON command: " + command)

        url = 'http://%s/jsonrpc' % (host)
        try:
            req = urllib2.Request(url, command)
            req.add_header("Content-type", "application/json")
            # if we have a password, use authentication
            if password:
                base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
                authheader = "Basic %s" % base64string
                req.add_header("Authorization", authheader)
                logging.debug("Contacting KODI (with auth header) via url: " + ss(url))
            else:
                logging.debug("Contacting KODI via url: " + ss(url))

            try:
                response = urllib2.urlopen(req)
            except (httplib.BadStatusLine, urllib2.URLError) as e:
                if sickbeard.KODI_ALWAYS_ON:
                    logging.warning("Error while trying to retrieve KODI API version for " + host + ": {}".format(ex(e)))
                return False

            # parse the json result
            try:
                result = json.load(response)
                response.close()
                logging.debug("KODI JSON response: " + str(result))
                return result  # need to return response for parsing
            except ValueError as e:
                logging.warning("Unable to decode JSON: " + str(response.read()))
                return False

        except IOError as e:
            if sickbeard.KODI_ALWAYS_ON:
                logging.warning("Warning: Couldn't contact KODI JSON API at " + ss(url) + " {}".format(ex(e)))
            return False

    def _update_library_json(self, host=None, showName=None):
        """Handles updating KODI host via HTTP JSON-RPC

        Attempts to update the KODI video library for a specific tv show if passed,
        otherwise update the whole library if enabled.

        Args:
            host: KODI webserver host:port
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False

        """

        if not host:
            logging.warning('No KODI host passed, aborting update')
            return False

        logging.debug("Updating KODI library via JSON method for host: " + host)

        # if we're doing per-show
        if showName:
            showName = urllib.unquote_plus(showName)
            tvshowid = -1
            path = ''

            logging.debug("Updating library in KODI via JSON method for show " + showName)

            # let's try letting kodi filter the shows
            showsCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShows","params":{"filter":{"field":"title","operator":"is","value":"%s"},"properties":["title",]},"id":"SiCKRAGE"}'

            # get tvshowid by showName
            showsResponse = self._send_to_kodi_json(showsCommand % showName, host)

            if showsResponse and "result" in showsResponse and "tvshows" in showsResponse[b"result"]:
                shows = showsResponse[b"result"][b"tvshows"]
            else:
                # fall back to retrieving the entire show list
                showsCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShows","id":1}'
                showsResponse = self._send_to_kodi_json(showsCommand, host)

                if showsResponse and "result" in showsResponse and "tvshows" in showsResponse[b"result"]:
                    shows = showsResponse[b"result"][b"tvshows"]
                else:
                    logging.debug("KODI: No tvshows in KODI TV show list")
                    return False

            for show in shows:
                if ("label" in show and show[b"label"] == showName) or ("title" in show and show[b"title"] == showName):
                    tvshowid = show[b"tvshowid"]
                    # set the path is we have it already
                    if "file" in show:
                        path = show[b"file"]

                    break

            # this can be big, so free some memory
            del shows

            # we didn't find the show (exact match), thus revert to just doing a full update if enabled
            if tvshowid == -1:
                logging.debug('Exact show name not matched in KODI TV show list')
                return False

            # lookup tv-show path if we don't already know it
            if not len(path):
                pathCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShowDetails","params":{"tvshowid":%d, "properties": ["file"]},"id":1}' % (
                tvshowid)
                pathResponse = self._send_to_kodi_json(pathCommand, host)

                path = pathResponse[b"result"][b"tvshowdetails"][b"file"]

            logging.debug("Received Show: " + showName + " with ID: " + str(tvshowid) + " Path: " + path)

            if not len(path):
                logging.warning("No valid path found for " + showName + " with ID: " + str(tvshowid) + " on " + host)
                return False

            logging.debug("KODI Updating " + showName + " on " + host + " at " + path)
            updateCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan","params":{"directory":%s},"id":1}' % (
            json.dumps(path))
            request = self._send_to_kodi_json(updateCommand, host)
            if not request:
                logging.warning("Update of show directory failed on " + showName + " on " + host + " at " + path)
                return False

            # catch if there was an error in the returned request
            for r in request:
                if 'error' in r:
                    logging.warning(
                        "Error while attempting to update show directory for " + showName + " on " + host + " at " + path)
                    return False

        # do a full update if requested
        else:
            logging.debug("Doing Full Library KODI update on host: " + host)
            updateCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan","id":1}'
            request = self._send_to_kodi_json(updateCommand, host)

            if not request:
                logging.warning("KODI Full Library update failed on: " + host)
                return False

        return True

    ##############################################################################
    # Public functions which will call the JSON or Legacy HTTP API methods
    ##############################################################################

    def notify_snatch(self, ep_name):
        if sickbeard.KODI_NOTIFY_ONSNATCH:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickbeard.KODI_NOTIFY_ONDOWNLOAD:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_kodi(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_KODI:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_kodi(update_text + new_version, title)

    def test_notify(self, host, username, password):
        return self._notify_kodi("Testing KODI notifications from SiCKRAGE", "Test Notification", host, username,
                                 password, force=True)

    def update_library(self, showName=None):
        """Public wrapper for the update library functions to branch the logic for JSON-RPC or legacy HTTP API

        Checks the KODI API version to branch the logic to call either the legacy HTTP API or the newer JSON-RPC over HTTP methods.
        Do the ability of accepting a list of hosts deliminated by comma, only one host is updated, the first to respond with success.
        This is a workaround for SQL backend users as updating multiple clients causes duplicate entries.
        Future plan is to revist how we store the host/ip/username/pw/options so that it may be more flexible.

        Args:
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False

        """

        if sickbeard.USE_KODI and sickbeard.KODI_UPDATE_LIBRARY:
            if not sickbeard.KODI_HOST:
                logging.debug("No KODI hosts specified, check your settings")
                return False

            # either update each host, or only attempt to update until one successful result
            result = 0
            for host in [x.strip() for x in sickbeard.KODI_HOST.split(",")]:
                if self._send_update_library(host, showName):
                    if sickbeard.KODI_UPDATE_ONLYFIRST:
                        logging.debug("Successfully updated '" + host + "', stopped sending update library commands.")
                        return True
                else:
                    if sickbeard.KODI_ALWAYS_ON:
                        logging.warning(
                            "Failed to detect KODI version for '" + host + "', check configuration and try again.")
                    result = result + 1

            # needed for the 'update kodi' submenu command
            # as it only cares of the final result vs the individual ones
            if result == 0:
                return True
            else:
                return False


notifier = KODINotifier
