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


import os
from urllib.parse import urlencode

import requests
from requests import HTTPError

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class pyTivoNotification(NotificationProvider):
    def __init__(self):
        super(pyTivoNotification, self).__init__()
        self.name = 'pytivo'

    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_version_update(self, new_version):
        pass

    def update_library(self, ep_obj):

        # Values from config

        if not sickrage.app.config.pytivo.enable:
            return False

        host = sickrage.app.config.pytivo.host
        share_name = sickrage.app.config.pytivo.share_name
        tsn = sickrage.app.config.pytivo.tivo_name

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

        show_path = ep_obj.show.location
        show_name = ep_obj.show.name
        root_show_and_season = os.path.dirname(ep_obj.location)
        abs_path = ep_obj.location

        # Some show names have colons in them which are illegal in a path location, so strip them out.
        # (Are there other characters?)
        show_name = show_name.replace(":", "")

        root = show_path.replace(show_name, "")
        show_and_season = root_show_and_season.replace(root, "")

        container = share_name + "/" + show_and_season
        file = "/" + abs_path.replace(root, "")

        # Finally create the url and make request
        request_url = "http://{}/TiVoConnect?{}".format(host, urlencode({'Command': 'Push', 'Container': container, 'File': file, 'tsn': tsn}))

        sickrage.app.log.debug("pyTivo notification: Requesting " + request_url)

        try:
            WebSession().get(request_url)
        except requests.exceptions.HTTPError as e:
            sickrage.app.log.error("pyTivo notification: Error, the server couldn't fulfill the request - " + e.response.text)
            return False
        except Exception as e:
            sickrage.app.log.error("PYTIVO: Unknown exception: {}".format(e))
            return False

        sickrage.app.log.info("pyTivo notification: Successfully requested transfer of file")
        return True
