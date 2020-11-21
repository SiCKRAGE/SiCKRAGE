# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


from base64 import standard_b64encode
from datetime import date, timedelta
from http import client
from xmlrpc.client import ServerProxy, ProtocolError

import sickrage
from sickrage.core.common import Qualities
from sickrage.core.helpers import try_int
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.websession import WebSession
from sickrage.search_providers import SearchProviderType


class NZBGet(object):
    @staticmethod
    def sendNZB(nzb, proper=False):
        """
        Sends NZB to NZBGet client

        :param nzb: nzb object
        :param proper: True if this is a Proper download, False if not. Defaults to False
        """

        if sickrage.app.config.nzbget.host is None:
            sickrage.app.log.warning("No NZBGet host found in configuration. Please configure it.")
            return False

        dupe_key = ""
        dupe_score = 0
        addToTop = False
        nzbgetprio = 0

        category = sickrage.app.config.nzbget.category

        show_object = find_show(nzb.series_id, nzb.series_provider_id)
        if not show_object:
            return False

        if show_object.is_anime:
            category = sickrage.app.config.nzbget.category_anime

        url = "%(protocol)s://%(username)s:%(password)s@%(host)s/xmlrpc" % {
            "protocol": 'https' if sickrage.app.config.nzbget.use_https else 'http',
            "host": sickrage.app.config.nzbget.host,
            "username": sickrage.app.config.nzbget.username,
            "password": sickrage.app.config.nzbget.password
        }

        nzbget_rpc_client = ServerProxy(url)

        try:
            if nzbget_rpc_client.writelog("INFO", "SiCKRAGE connected to drop of %s any moment now." % (nzb.name + ".nzb")):
                sickrage.app.log.debug("Successful connected to NZBGet")
            else:
                sickrage.app.log.warning("Successful connected to NZBGet, but unable to send a message")
        except client.socket.error:
            sickrage.app.log.warning("Please check your NZBGet host and port (if it is running). NZBGet is not responding to this combination")
            return False
        except ProtocolError as e:
            if e.errmsg == "Unauthorized":
                sickrage.app.log.warning("NZBGet username or password is incorrect.")
            else:
                sickrage.app.log.warning("NZBGet Protocol Error: " + e.errmsg)
            return False

        show_object = find_show(nzb.series_id, nzb.series_provider_id)
        if not show_object:
            return False

        # if it aired recently make it high priority and generate DupeKey/Score
        for episode_number in nzb.episodes:
            episode_object = show_object.get_episode(nzb.season, episode_number)

            if dupe_key == "":
                dupe_key = f"SiCKRAGE-{episode_object.show.series_provider_id.name}-{episode_object.show.series_id}"

            dupe_key += "-" + str(episode_object.season) + "." + str(episode_object.episode)
            if date.today() - episode_object.airdate <= timedelta(days=7):
                addToTop = True
                nzbgetprio = sickrage.app.config.nzbget.priority
            else:
                category = sickrage.app.config.nzbget.category_backlog
                if show_object.is_anime:
                    category = sickrage.app.config.nzbget.category_anime_backlog

        if nzb.quality != Qualities.UNKNOWN:
            dupe_score = nzb.quality * 100
        if proper:
            dupe_score += 10

        nzbcontent64 = None
        if nzb.provider_type == SearchProviderType.NZBDATA:
            data = nzb.extraInfo[0]
            nzbcontent64 = standard_b64encode(data)

        sickrage.app.log.info("Sending NZB to NZBGet")
        sickrage.app.log.debug("URL: " + url)

        try:
            # Find out if nzbget supports priority (Version 9.0+), old versions beginning with a 0.x will use the old
            # command
            nzbget_version_str = nzbget_rpc_client.version()
            nzbget_version = try_int(nzbget_version_str[:nzbget_version_str.find(".")])
            if nzbget_version == 0:
                if nzbcontent64 is not None:
                    nzbget_result = nzbget_rpc_client.append(nzb.name + ".nzb", category, addToTop, nzbcontent64)
                else:
                    if nzb.provider_type == SearchProviderType.NZB:
                        try:
                            nzbcontent64 = standard_b64encode(WebSession().get(nzb.url).text)
                        except Exception:
                            return False
                    nzbget_result = nzbget_rpc_client.append(nzb.name + ".nzb", category, addToTop, nzbcontent64)
            elif nzbget_version == 12:
                if nzbcontent64 is not None:
                    nzbget_result = nzbget_rpc_client.append(nzb.name + ".nzb", category, nzbgetprio, False,
                                                             nzbcontent64, False, dupe_key, dupe_score, "score")
                else:
                    nzbget_result = nzbget_rpc_client.appendurl(nzb.name + ".nzb", category, nzbgetprio, False,
                                                                nzb.url, False, dupe_key, dupe_score, "score")
            # v13+ has a new combined append method that accepts both (url and content)
            # also the return value has changed from boolean to integer
            # (Positive number representing NZBID of the queue item. 0 and negative numbers represent error codes.)
            elif nzbget_version >= 13:
                nzbget_result = True if nzbget_rpc_client.append(nzb.name + ".nzb",
                                                                 nzbcontent64 if nzbcontent64 is not None else nzb.url,
                                                                 category, nzbgetprio, False, False, dupe_key, dupe_score,
                                                                 "score") > 0 else False
            else:
                if nzbcontent64 is not None:
                    nzbget_result = nzbget_rpc_client.append(nzb.name + ".nzb", category, nzbgetprio, False,
                                                             nzbcontent64)
                else:
                    nzbget_result = nzbget_rpc_client.appendurl(nzb.name + ".nzb", category, nzbgetprio, False,
                                                                nzb.url)

            if nzbget_result:
                sickrage.app.log.debug("NZB sent to NZBGet successfully")
                return True
            else:
                sickrage.app.log.warning("NZBGet could not add %s to the queue" % (nzb.name + ".nzb"))
                return False
        except Exception:
            sickrage.app.log.warning("Connect Error to NZBGet: could not add %s to the queue" % (nzb.name + ".nzb"))
            return False
