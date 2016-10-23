# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

import os
from urllib import urlencode
from urllib2 import HTTPError, Request, urlopen

import sickrage
from sickrage.notifiers import srNotifiers


class pyTivoNotifier(srNotifiers):
    def _notify_snatch(self, ep_name):
        pass

    def _notify_download(self, ep_name):
        pass

    def _notify_subtitle_download(self, ep_name, lang):
        pass

    def _notify_version_update(self, new_version):
        pass

    def update_library(self, ep_obj):

        # Values from config

        if not sickrage.srCore.srConfig.USE_PYTIVO:
            return False

        host = sickrage.srCore.srConfig.PYTIVO_HOST
        shareName = sickrage.srCore.srConfig.PYTIVO_SHARE_NAME
        tsn = sickrage.srCore.srConfig.PYTIVO_TIVO_NAME

        # There are two more values required, the container and file.
        #
        # container: The share name, show name and season
        #
        # file: The file name
        #
        # Some slicing and dicing of variables is required to get at these values.
        #
        # There might be better ways to arrive at the values, but this is the best I have been able to
        # come up with.
        #


        # Calculated values

        showPath = ep_obj.show.location
        showName = ep_obj.show.name
        rootShowAndSeason = os.path.dirname(ep_obj.location)
        absPath = ep_obj.location

        # Some show names have colons in them which are illegal in a path location, so strip them out.
        # (Are there other characters?)
        showName = showName.replace(":", "")

        root = showPath.replace(showName, "")
        showAndSeason = rootShowAndSeason.replace(root, "")

        container = shareName + "/" + showAndSeason
        file = "/" + absPath.replace(root, "")

        # Finally create the url and make request
        requestUrl = "http://" + host + "/TiVoConnect?" + urlencode(
                {'Command': 'Push', 'Container': container, 'File': file, 'tsn': tsn})

        sickrage.srCore.srLogger.debug("pyTivo notification: Requesting " + requestUrl)

        request = Request(requestUrl)

        try:
            response = urlopen(request)  # @UnusedVariable
        except HTTPError  as e:
            if hasattr(e, 'reason'):
                sickrage.srCore.srLogger.error("pyTivo notification: Error, failed to reach a server - " + e.reason)
                return False
            elif hasattr(e, 'code'):
                sickrage.srCore.srLogger.error("pyTivo notification: Error, the server couldn't fulfill the request - " + e.code)
            return False
        except Exception as e:
            sickrage.srCore.srLogger.error("PYTIVO: Unknown exception: {}".format(e.message))
            return False
        else:
            sickrage.srCore.srLogger.info("pyTivo notification: Successfully requested transfer of file")
            return True
