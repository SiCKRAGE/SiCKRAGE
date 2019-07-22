#!/usr/bin/env python3
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

import os.path
import sys
from configparser import RawConfigParser, NoOptionError

import requests


def processEpisode(dir_to_process, org_nzb_name=None, status=None):
    # Default values
    host = "localhost"
    port = "8081"
    api_key = ""
    ssl = 0
    web_root = "/"

    default_url = host + ":" + port + web_root
    if ssl:
        default_url = "https://" + default_url
    else:
        default_url = "http://" + default_url

    # Get values from config_file
    config = RawConfigParser()
    config_filename = os.path.join(os.path.dirname(sys.argv[0]), "autoProcessTV.cfg")

    if not os.path.isfile(config_filename):
        print("ERROR: " + config_filename + " doesn\'t exist")
        print("copy /rename " + config_filename + ".sample and edit\n")
        print("Trying default url: " + default_url + "\n")
    else:
        try:
            print("Loading config from " + config_filename + "\n")

            with open(config_filename, "r") as fp:
                config.readfp(fp)

            # Replace default values with config_file values
            host = config.get("sickrage", "host")
            port = config.get("sickrage", "port")
            api_key = config.get("sickrage", "api_key")

            try:
                ssl = int(config.get("sickrage", "ssl"))
            except (NoOptionError, ValueError):
                pass

            try:
                web_root = config.get("sickrage", "web_root")
                if not web_root.startswith("/"):
                    web_root = "/" + web_root

                if not web_root.endswith("/"):
                    web_root += "/"
            except NoOptionError:
                pass
        except EnvironmentError as e:
            print("Could not read configuration file: " + str(e))
            sys.exit(1)

    params = {
        'cmd': 'postprocess',
        'return_data': 0,
        'path': dir_to_process
    }

    # if org_nzb_name is not None:
    #    params['nzbName'] = org_nzb_name

    if status is not None:
        params['failed'] = status

    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"

    url = "{}{}:{}{}api/{}/".format(protocol, host, port, web_root, api_key)

    print("Opening URL: " + url)

    try:
        r = requests.get(url, params=params, verify=False, allow_redirects=False, stream=True)
        for line in r.iter_lines():
            if not line:
                continue
            print(line.strip())
    except IOError as e:
        print("Unable to open URL: " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    print("This module is supposed to be used as import in other scripts and not run standalone.")
    print("Use sabToSiCKRAGE instead.")
    sys.exit(1)
