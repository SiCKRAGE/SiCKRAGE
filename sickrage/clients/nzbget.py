# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
import xmlrpclib
from base64 import standard_b64encode
from datetime import date, timedelta

import sickrage
from sickrage.core.common import Quality
from sickrage.core.helpers import tryInt


class NZBGet(object):
    @staticmethod
    def sendNZB(nzb, proper=False):
        """
        Sends NZB to NZBGet client

        :param nzb: nzb object
        :param proper: True if this is a Proper download, False if not. Defaults to False
        """

        if sickrage.srCore.srConfig.NZBGET_HOST is None:
            sickrage.srCore.srLogger.error("No NZBget host found in configuration. Please configure it.")
            return False

        dupe_key = ""
        dupe_score = 0
        addToTop = False
        nzbgetprio = 0

        category = sickrage.srCore.srConfig.NZBGET_CATEGORY
        if nzb.show.is_anime:
            category = sickrage.srCore.srConfig.NZBGET_CATEGORY_ANIME

        url = "%(protocol)s://%(username)s:%(password)s@%(host)s/xmlrpc" % {
            "protocol": 'https' if sickrage.srCore.srConfig.NZBGET_USE_HTTPS else 'http',
            "host": sickrage.srCore.srConfig.NZBGET_HOST,
            "username": sickrage.srCore.srConfig.NZBGET_USERNAME,
            "password": sickrage.srCore.srConfig.NZBGET_PASSWORD
        }

        nzbGetRPC = xmlrpclib.ServerProxy(url)

        try:
            if nzbGetRPC.writelog("INFO", "SiCKRAGE connected to drop of %s any moment now." % (nzb.name + ".nzb")):
                sickrage.srCore.srLogger.debug("Successful connected to NZBget")
            else:
                sickrage.srCore.srLogger.error("Successful connected to NZBget, but unable to send a message")

        except httplib.socket.error:
            sickrage.srCore.srLogger.error(
                "Please check your NZBget host and port (if it is running). NZBget is not responding to this combination")
            return False

        except xmlrpclib.ProtocolError as e:
            if e.errmsg == "Unauthorized":
                sickrage.srCore.srLogger.error("NZBget username or password is incorrect.")
            else:
                sickrage.srCore.srLogger.error("Protocol Error: " + e.errmsg)
            return False

        # if it aired recently make it high priority and generate DupeKey/Score
        for curEp in nzb.episodes:
            if dupe_key == "":
                if curEp.show.indexer == 1:
                    dupe_key = "SiCKRAGE-" + str(curEp.show.indexerid)
                elif curEp.show.indexer == 2:
                    dupe_key = "SiCKRAGE-tvr" + str(curEp.show.indexerid)
            dupe_key += "-" + str(curEp.season) + "." + str(curEp.episode)
            if date.today() - curEp.airdate <= timedelta(days=7):
                addToTop = True
                nzbgetprio = sickrage.srCore.srConfig.NZBGET_PRIORITY
            else:
                category = sickrage.srCore.srConfig.NZBGET_CATEGORY_BACKLOG
                if nzb.show.is_anime:
                    category = sickrage.srCore.srConfig.NZBGET_CATEGORY_ANIME_BACKLOG

        if nzb.quality != Quality.UNKNOWN:
            dupe_score = nzb.quality * 100
        if proper:
            dupe_score += 10

        nzbcontent64 = None
        if nzb.resultType == "nzbdata":
            data = nzb.extraInfo[0]
            nzbcontent64 = standard_b64encode(data)

        sickrage.srCore.srLogger.info("Sending NZB to NZBget")
        sickrage.srCore.srLogger.debug("URL: " + url)

        try:
            # Find out if nzbget supports priority (Version 9.0+), old versions beginning with a 0.x will use the old command
            nzbget_version_str = nzbGetRPC.version()
            nzbget_version = tryInt(nzbget_version_str[:nzbget_version_str.find(".")])
            if nzbget_version == 0:
                if nzbcontent64 is not None:
                    nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, addToTop, nzbcontent64)
                else:
                    if nzb.resultType == "nzb":
                        try:
                            nzbcontent64 = standard_b64encode(sickrage.srCore.srWebSession.get(nzb.url).text)
                        except Exception:
                            return False
                    nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, addToTop, nzbcontent64)
            elif nzbget_version == 12:
                if nzbcontent64 is not None:
                    nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, nzbgetprio, False,
                                                     nzbcontent64, False, dupe_key, dupe_score, "score")
                else:
                    nzbget_result = nzbGetRPC.appendurl(nzb.name + ".nzb", category, nzbgetprio, False,
                                                        nzb.url, False, dupe_key, dupe_score, "score")
            # v13+ has a new combined append method that accepts both (url and content)
            # also the return value has changed from boolean to integer
            # (Positive number representing NZBID of the queue item. 0 and negative numbers represent error codes.)
            elif nzbget_version >= 13:
                nzbget_result = True if nzbGetRPC.append(nzb.name + ".nzb",
                                                         nzbcontent64 if nzbcontent64 is not None else nzb.url,
                                                         category, nzbgetprio, False, False, dupe_key, dupe_score,
                                                         "score") > 0 else False
            else:
                if nzbcontent64 is not None:
                    nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, nzbgetprio, False,
                                                     nzbcontent64)
                else:
                    nzbget_result = nzbGetRPC.appendurl(nzb.name + ".nzb", category, nzbgetprio, False,
                                                        nzb.url)

            if nzbget_result:
                sickrage.srCore.srLogger.debug("NZB sent to NZBget successfully")
                return True
            else:
                sickrage.srCore.srLogger.error("NZBget could not add %s to the queue" % (nzb.name + ".nzb"))
                return False
        except Exception:
            sickrage.srCore.srLogger.error(
                "Connect Error to NZBget: could not add %s to the queue" % (nzb.name + ".nzb"))
            return False
