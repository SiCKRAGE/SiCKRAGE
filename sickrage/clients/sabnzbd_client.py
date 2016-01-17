# Author: echel0n <sickrage.tv@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage
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

import cookielib
import datetime
import httplib
import json
import urllib
import urllib2

import MultipartPostHandler

import sickrage


class SabNZBd(object):
    @staticmethod
    def sendNZB(nzb):
        """
        Sends an NZB to SABnzbd via the API.

        :param nzb: The NZBSearchResult object to send to SAB
        """

        # set up a dict with the URL params in it
        params = {}
        if sickrage.SAB_USERNAME is not None:
            params[b'ma_username'] = sickrage.SAB_USERNAME
        if sickrage.SAB_PASSWORD is not None:
            params[b'ma_password'] = sickrage.SAB_PASSWORD
        if sickrage.SAB_APIKEY is not None:
            params[b'apikey'] = sickrage.SAB_APIKEY
        category = sickrage.SAB_CATEGORY
        if nzb.show.is_anime:
            category = sickrage.SAB_CATEGORY_ANIME

        # if it aired more than 7 days ago, override with the backlog category IDs
        for curEp in nzb.episodes:
            if datetime.date.today() - curEp.airdate > datetime.timedelta(days=7):
                category = sickrage.SAB_CATEGORY_BACKLOG
                if nzb.show.is_anime:
                    category = sickrage.SAB_CATEGORY_ANIME_BACKLOG

        if category is not None:
            params[b'cat'] = category

        # use high priority if specified (recently aired episode)
        if nzb.priority == 1:
            if sickrage.SAB_FORCED == 1:
                params[b'priority'] = 2
            else:
                params[b'priority'] = 1

        try:
            f = None

            # if it's a normal result we just pass SAB the URL
            if nzb.resultType == "nzb":
                # for newzbin results send the ID to sab specifically
                if nzb.provider.id == 'newzbin':
                    id = nzb.provider.getIDFromURL(nzb.url)
                    if not id:
                        sickrage.LOGGER.error("Unable to send NZB to sab, can't find ID in URL " + str(nzb.url))
                        return False
                    params[b'mode'] = 'addid'
                    params[b'name'] = id
                else:
                    params[b'mode'] = 'addurl'
                    params[b'name'] = nzb.url

                url = sickrage.SAB_HOST + "api?" + urllib.urlencode(params)
                sickrage.LOGGER.info("Sending NZB to SABnzbd")
                sickrage.LOGGER.debug("URL: " + url)

                # if we have the URL to an NZB then we've built up the SAB API URL already so just call it
                if nzb.resultType == "nzb":
                    f = urllib.urlopen(url)

            elif nzb.resultType == "nzbdata":
                params[b'mode'] = 'addfile'
                multiPartParams = {"nzbfile": (nzb.name + ".nzb", nzb.extraInfo[0])}

                url = sickrage.SAB_HOST + "api?" + urllib.urlencode(params)
                sickrage.LOGGER.info("Sending NZB to SABnzbd")
                sickrage.LOGGER.debug("URL: " + url)

                cookies = cookielib.CookieJar()
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                              MultipartPostHandler.MultipartPostHandler)
                req = urllib2.Request(url, multiPartParams, headers={'User-Agent': sickrage.USER_AGENT})
                f = opener.open(req)

        except (EOFError, IOError) as e:
            sickrage.LOGGER.error("Unable to connect to SAB: {}".format(e))
            return False
        except httplib.InvalidURL as e:
            sickrage.LOGGER.error("Invalid SAB host, check your config: {}".format(e))
            return False

        # this means we couldn't open the connection or something just as bad
        if f is None:
            sickrage.LOGGER.error("No data returned from SABnzbd, NZB not sent")
            return False

        # if we opened the URL connection then read the result from SAB
        try:
            result = f.readlines()
        except Exception as e:
            sickrage.LOGGER.error("Error trying to get result from SAB, NZB not sent: {}".format(e))
            return False

        # SAB shouldn't return a blank result, this most likely (but not always) means that it timed out and didn't recieve the NZB
        if len(result) == 0:
            sickrage.LOGGER.error("No data returned from SABnzbd, NZB not sent")
            return False

        # massage the result a little bit
        sabText = result[0].strip()

        sickrage.LOGGER.debug("Result text from SAB: " + sabText)

        # do some crude parsing of the result text to determine what SAB said
        if sabText == "ok":
            sickrage.LOGGER.debug("NZB sent to SAB successfully")
            return True
        elif sabText == "Missing authentication":
            sickrage.LOGGER.error("Incorrect username/password sent to SAB, NZB not sent")
            return False
        else:
            sickrage.LOGGER.error("Unknown failure sending NZB to sab. Return text is: " + sabText)
            return False

    @staticmethod
    def _checkSabResponse(f):
        """
        Check response from SAB

        :param f: Response from SAV
        :return: a list of (Boolean, string) which is True if SAB is not reporting an error
        """
        try:
            result = f.readlines()
        except Exception as e:
            sickrage.LOGGER.error("Error trying to get result from SAB{}".format(e))
            return False, "Error from SAB"

        if len(result) == 0:
            sickrage.LOGGER.error("No data returned from SABnzbd, NZB not sent")
            return False, "No data from SAB"

        sabText = result[0].strip()
        sabJson = {}
        try:
            sabJson = json.loads(sabText)
        except ValueError as e:
            pass

        if sabText == "Missing authentication":
            sickrage.LOGGER.error("Incorrect username/password sent to SAB")
            return False, "Incorrect username/password sent to SAB"
        elif 'error' in sabJson:
            sickrage.LOGGER.error(sabJson[b'error'])
            return False, sabJson[b'error']
        else:
            return True, sabText

    @staticmethod
    def _sabURLOpenSimple(url):
        """
        Open a connection to SAB

        :param url: URL where SAB is at
        :return: (boolean, string) list, True if connection can be made
        """
        try:
            f = urllib.urlopen(url)
        except (EOFError, IOError) as e:
            sickrage.LOGGER.error("Unable to connect to SAB: {}".format(e))
            return False, "Unable to connect"
        except httplib.InvalidURL as e:
            sickrage.LOGGER.error("Invalid SAB host, check your config: {}".format(e))
            return False, "Invalid SAB host"
        if f is None:
            sickrage.LOGGER.error("No data returned from SABnzbd")
            return False, "No data returned from SABnzbd"
        else:
            return True, f

    @staticmethod
    def getSabAccesMethod(host=None, username=None, password=None, apikey=None):
        """
        Find out how we should connect to SAB

        :param host: hostname where SAB lives
        :param username: username to use
        :param password: password to use
        :param apikey: apikey to use
        :return: (boolean, string) with True if method was successful
        """
        url = host + "api?mode=auth"

        result, f = SabNZBd._sabURLOpenSimple(url)
        if not result:
            return False, f

        result, sabText = SabNZBd._checkSabResponse(f)
        if not result:
            return False, sabText

        return True, sabText

    @staticmethod
    def testAuthentication(host=None, username=None, password=None, apikey=None):
        """
        Sends a simple API request to SAB to determine if the given connection information is connect

        :param host: The host where SAB is running (incl port)
        :param username: The username to use for the HTTP request
        :param password: The password to use for the HTTP request
        :param apikey: The API key to provide to SAB
        :return: A tuple containing the success boolean and a message
        """

        # build up the URL parameters
        params = {}
        params[b'mode'] = 'queue'
        params[b'output'] = 'json'
        params[b'ma_username'] = username
        params[b'ma_password'] = password
        params[b'apikey'] = apikey
        url = host + "api?" + urllib.urlencode(params)

        # send the test request
        sickrage.LOGGER.debug("SABnzbd test URL: " + url)
        result, f = SabNZBd._sabURLOpenSimple(url)
        if not result:
            return False, f

        # check the result and determine if it's good or not
        result, sabText = SabNZBd._checkSabResponse(f)
        if not result:
            return False, sabText

        return True, "Success"
