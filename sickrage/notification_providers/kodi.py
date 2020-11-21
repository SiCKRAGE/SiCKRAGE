# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import base64
import json
import socket
import time
import uuid
from urllib import parse
from urllib.parse import unquote_plus, urlencode, unquote
from xml.etree import ElementTree

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class KODINotification(NotificationProvider):
    sr_logo_url = 'https://www.sickrage.ca/favicon.ico'

    def __init__(self):
        super(KODINotification, self).__init__()
        self.name = 'kodi'

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

        checkCommand = {"jsonrpc": "2.0", "method": "JSONRPC.Version", "id": uuid.uuid4().hex}
        result = self._send_to_kodi_json(checkCommand, host, username, password)

        # revert back to default socket timeout
        socket.setdefaulttimeout(sickrage.app.config.general.socket_timeout)

        if not result or result is False or 'error' in result:
            # fallback to legacy HTTPAPI method
            testCommand = {'command': 'Help'}
            request = self._send_to_kodi(testCommand, host, username, password)
            if request:
                # return a fake version number, so it uses the legacy method
                return 1
            else:
                return False

        return result["result"]["version"]["major"]

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
            host = sickrage.app.config.kodi.host
        if not username:
            username = sickrage.app.config.kodi.username
        if not password:
            password = sickrage.app.config.kodi.password

        # suppress notifications if the notifier is disabled but the notify options are checked
        if not sickrage.app.config.kodi.enable and not force:
            sickrage.app.log.debug("Notification for KODI not enabled, skipping this notification")
            return False

        result = ''
        for curHost in [x.strip() for x in host.split(",")]:
            sickrage.app.log.debug("Sending KODI notification to '" + curHost + "' - " + message)

            kodiapi = self._get_kodi_version(curHost, username, password)
            if kodiapi:
                if kodiapi <= 4:
                    sickrage.app.log.debug("Detected KODI version <= 11, using KODI HTTP API")
                    command = {'command': 'ExecBuiltIn',
                               'parameter': 'Notification({},{})'.format(title.encode("utf-8"), message.encode("utf-8"))}
                    notifyResult = self._send_to_kodi(command, curHost, username, password)
                    if notifyResult:
                        result += curHost + ':' + str(notifyResult)
                else:
                    sickrage.app.log.debug("Detected KODI version >= 12, using KODI JSON API")

                    command = {"jsonrpc": "2.0",
                               "method": "GUI.ShowNotification",
                               "params": {"title": title, "message": message, "image": self.sr_logo_url},
                               "id": uuid.uuid4().hex}

                    notifyResult = self._send_to_kodi_json(command, curHost, username, password)
                    if notifyResult and notifyResult.get('result'):
                        result += curHost + ':' + notifyResult["result"]
            else:
                if sickrage.app.config.kodi.always_on or force:
                    sickrage.app.log.warning("Failed to detect KODI version for '" + curHost + "', check configuration and try again.")
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

        sickrage.app.log.debug("Sending request to update library for KODI host: '" + host + "'")

        kodiapi = self._get_kodi_version(host, sickrage.app.config.kodi.username,
                                         sickrage.app.config.kodi.password)
        if kodiapi:
            if kodiapi <= 4:
                # try to update for just the show, if it fails, do full update if enabled
                if not self._update_library(host, showName) and sickrage.app.config.kodi.update_full:
                    sickrage.app.log.debug("Single show update failed, falling back to full update")
                    return self._update_library(host)
                else:
                    return True
            else:
                # try to update for just the show, if it fails, do full update if enabled
                if not self._update_library_json(host, showName) and sickrage.app.config.kodi.update_full:
                    sickrage.app.log.debug("Single show update failed, falling back to full update")
                    return self._update_library_json(host)
                else:
                    return True
        elif sickrage.app.config.kodi.always_on:
            sickrage.app.log.warning(
                "Failed to detect KODI version for '" + host + "', check configuration and try again.")

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
            username = sickrage.app.config.kodi.username
        if not password:
            password = sickrage.app.config.kodi.password

        if not host:
            sickrage.app.log.warning('No KODI host passed, aborting update')
            return False

        enc_command = urlencode(command)
        sickrage.app.log.debug("KODI encoded API command: " + enc_command)

        url = 'http://%s/kodiCmds/kodiHttp/?%s' % (host, enc_command)

        headers = {}

        # if we have a password, use authentication
        if password:
            authheader = "Basic {}".format(base64.b64encode(bytes('{}:{}'.format(username, password).replace('\n', ''), 'utf-8')).decode('ascii'))
            headers["Authorization"] = authheader
            sickrage.app.log.debug("Contacting KODI (with auth header) via url: " + url)
        else:
            sickrage.app.log.debug("Contacting KODI via url: " + url)

        try:
            result = WebSession().get(url, headers=headers).text
        except Exception as e:
            sickrage.app.log.debug("Couldn't contact KODI HTTP at %r : %r" % (url, e))
            return False

        sickrage.app.log.debug("KODI HTTP response: " + result.replace('\n', ''))
        return result

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
            sickrage.app.log.warning('No KODI host passed, aborting update')
            return False

        sickrage.app.log.debug("Updating KODI library via HTTP method for host: " + host)

        # if we're doing per-show
        if showName:
            sickrage.app.log.debug("Updating library in KODI via HTTP method for show " + showName)

            pathSql = 'select path.strPath from path, tvshow, tvshowlinkpath where ' \
                      'tvshow.c00 = "{0:s}" and tvshowlinkpath.idShow = tvshow.idShow ' \
                      'and tvshowlinkpath.idPath = path.idPath'.format(showName)

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
                sickrage.app.log.debug("Invalid response for " + showName + " on " + host)
                return False

            encSqlXML = parse.quote(sqlXML, ':\\/<>')
            try:
                et = ElementTree.fromstring(encSqlXML)
            except SyntaxError as e:
                sickrage.app.log.error("Unable to parse XML returned from KODI: {}".format(e))
                return False

            paths = et.findall('.//field')

            if not paths:
                sickrage.app.log.debug("No valid paths found for " + showName + " on " + host)
                return False

            for path in paths:
                # we do not need it double-encoded, gawd this is dumb
                unEncPath = unquote(path.text)
                sickrage.app.log.debug("KODI Updating " + showName + " on " + host + " at " + unEncPath)
                updateCommand = {'command': 'ExecBuiltIn', 'parameter': 'KODI.updatelibrary(video, %s)' % (unEncPath)}
                request = self._send_to_kodi(updateCommand, host)
                if not request:
                    sickrage.app.log.warning(
                        "Update of show directory failed on " + showName + " on " + host + " at " + unEncPath)
                    return False
                # sleep for a few seconds just to be sure kodi has a chance to finish each directory
                if len(paths) > 1:
                    time.sleep(5)
        # do a full update if requested
        else:
            sickrage.app.log.debug("Doing Full Library KODI update on host: " + host)
            updateCommand = {'command': 'ExecBuiltIn', 'parameter': 'KODI.updatelibrary(video)'}
            request = self._send_to_kodi(updateCommand, host)

            if not request:
                sickrage.app.log.warning("KODI Full Library update failed on: " + host)
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
            username = sickrage.app.config.kodi.username
        if not password:
            password = sickrage.app.config.kodi.password

        if not host:
            sickrage.app.log.warning('No KODI host passed, aborting update')
            return False

        sickrage.app.log.debug("KODI JSON command: {!r}".format(command))

        url = 'http://%s/jsonrpc' % host

        headers = {"Content-type": "application/json"}

        # if we have a password, use authentication
        if password:
            authheader = "Basic {}".format(base64.b64encode(bytes('{}:{}'.format(username, password).replace('\n', ''), 'utf-8')).decode('ascii'))
            headers["Authorization"] = authheader
            sickrage.app.log.debug("Contacting KODI (with auth header) via url: " + url)
        else:
            sickrage.app.log.debug("Contacting KODI via url: " + url)

        try:
            result = WebSession().post(url, json=command, headers=headers).json()
            sickrage.app.log.debug("KODI JSON response: " + str(result))
            return result
        except Exception as e:
            if sickrage.app.config.kodi.always_on:
                sickrage.app.log.warning("Warning: Couldn't contact KODI JSON API at " + url + " {}".format(e))

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
            sickrage.app.log.warning('No KODI host passed, aborting update')
            return False

        sickrage.app.log.debug("Updating KODI library via JSON method for host: " + host)

        # if we're doing per-show
        if showName:
            showName = unquote_plus(showName)
            tvshowid = -1
            path = ''

            sickrage.app.log.debug("Updating library in KODI via JSON method for show " + showName)

            # let's try letting kodi filter the shows
            showsCommand = {"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows",
                            "params": {"filter": {"field": "title", "operator": "is", "value": showName}, "properties": ["title"]},
                            "id": uuid.uuid4().hex}

            # get tvshowid by showName
            showsResponse = self._send_to_kodi_json(showsCommand, host)

            if showsResponse and "result" in showsResponse and "tvshows" in showsResponse["result"]:
                shows = showsResponse["result"]["tvshows"]
            else:
                # fall back to retrieving the entire show list
                showsCommand = {"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "id": uuid.uuid4().hex}
                showsResponse = self._send_to_kodi_json(showsCommand, host)

                if showsResponse and "result" in showsResponse and "tvshows" in showsResponse["result"]:
                    shows = showsResponse["result"]["tvshows"]
                else:
                    sickrage.app.log.debug("KODI: No tvshows in KODI TV show list")
                    return False

            for show in shows:
                if ("label" in show and show["label"] == showName) or ("title" in show and show["title"] == showName):
                    tvshowid = show["tvshowid"]
                    # set the path is we have it already
                    if "file" in show:
                        path = show["file"]

                    break

            # this can be big, so free some memory
            del shows

            # we didn't find the show (exact match), thus revert to just doing a full update if enabled
            if tvshowid == -1:
                sickrage.app.log.debug('Exact show name not matched in KODI TV show list')
                return False

            # lookup tv-show path if we don't already know it
            if not len(path):
                pathCommand = {"jsonrpc": "2.0",
                               "method": "VideoLibrary.GetTVShowDetails",
                               "params": {"tvshowid": tvshowid, "properties": ["file"]},
                               "id": uuid.uuid4().hex}

                pathResponse = self._send_to_kodi_json(pathCommand, host)

                path = pathResponse["result"]["tvshowdetails"]["file"]

            sickrage.app.log.debug(
                "Received Show: " + showName + " with ID: " + str(tvshowid) + " Path: " + path)

            if not len(path):
                sickrage.app.log.warning("No valid path found for " + showName + " with ID: " + str(tvshowid) + " on " + host)
                return False

            sickrage.app.log.debug("KODI Updating " + showName + " on " + host + " at " + path)
            updateCommand = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "params": {"directory": path}, "id": uuid.uuid4().hex}
            request = self._send_to_kodi_json(updateCommand, host)
            if request is False:
                sickrage.app.log.warning("Update of show directory failed on " + showName + " on " + host + " at " + path)
                return False

            # catch if there was an error in the returned request
            for r in request:
                if 'error' in r:
                    sickrage.app.log.warning("Error while attempting to update show directory for " + showName + " on " + host + " at " + path)
                    return False

        # do a full update if requested
        else:
            sickrage.app.log.debug("Doing Full Library KODI update on host: " + host)
            updateCommand = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "id": uuid.uuid4().hex}
            request = self._send_to_kodi_json(updateCommand, host)

            if not request:
                sickrage.app.log.warning("KODI Full Library update failed on: " + host)
                return False

        return True

    ##############################################################################
    # Public functions which will call the JSON or Legacy HTTP API methods
    ##############################################################################

    def notify_snatch(self, ep_name):
        if sickrage.app.config.kodi.notify_on_snatch:
            self._notify_kodi(ep_name, self.notifyStrings[self.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickrage.app.config.kodi.notify_on_download:
            self._notify_kodi(ep_name, self.notifyStrings[self.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.kodi.notify_on_subtitle_download:
            self._notify_kodi(ep_name + ": " + lang, self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.kodi.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notify_kodi(update_text + new_version, title)

    def test_notify(self, host, username, password):
        return self._notify_kodi("Testing KODI notifications from SiCKRAGE", "Test Notification", host, username, password, force=True)

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

        if sickrage.app.config.kodi.enable and sickrage.app.config.kodi.update_library:
            if not sickrage.app.config.kodi.host:
                sickrage.app.log.debug("No KODI hosts specified, check your settings")
                return False

            # either update each host, or only attempt to update until one successful result
            result = 0
            for host in [x.strip() for x in sickrage.app.config.kodi.host.split(",")]:
                if self._send_update_library(host, showName):
                    if sickrage.app.config.kodi.update_only_first:
                        sickrage.app.log.debug("Successfully updated '" + host + "', stopped sending update library commands.")
                        return True
                else:
                    if sickrage.app.config.kodi.always_on:
                        sickrage.app.log.warning("Failed to detect KODI version for '" + host + "', check configuration and try again.")
                    result += 1

            # needed for the 'update kodi' submenu command
            # as it only cares of the final result vs the individual ones
            if result == 0:
                return True
            else:
                return False
