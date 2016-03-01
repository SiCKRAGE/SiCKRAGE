#!/usr/bin/env python2

# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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

import io
import os.path
import sys

# Try importing Python 2 modules using new names
import sickrage

try:
    import ConfigParser as configparser
    import urllib2
    from urllib import urlencode
except ImportError:
    import configparser
    # noinspection PyUnresolvedReferences
    import urllib.request as urllib2
    # noinspection PyUnresolvedReferences,PyUnresolvedReferences
    from urllib.parse import urlencode

# workaround for broken urllib2 in python 2.6.5: wrong credentials lead to an infinite recursion
if sys.version_info >= (2, 6, 5) and sys.version_info < (2, 6, 6):
    class HTTPBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
        def retry_http_basic_auth(self, host, req, realm):
            # don't retry if auth failed
            if req.get_header(self.auth_header, None) is not None:
                return None

            return urllib2.HTTPBasicAuthHandler.retry_http_basic_auth(self, host, req, realm)

else:
    HTTPBasicAuthHandler = urllib2.HTTPBasicAuthHandler


def processEpisode(dir_to_process, org_NZB_name=None, status=None):
    # Default values
    host = "localhost"
    port = "8081"
    username = ""
    password = ""
    ssl = 0
    web_root = "/"

    default_url = host + ":" + port + web_root
    if ssl:
        default_url = "https://" + default_url
    else:
        default_url = "http://" + default_url

    # Get values from config_file
    config = configparser.RawConfigParser()
    config_filename = os.path.join(os.path.dirname(sys.argv[0]), "autoProcessTV.cfg")

    if not os.path.isfile(config_filename):
        print ("ERROR: " + config_filename + " doesn\'t exist")
        print ("copy /rename " + config_filename + ".sample and edit\n")
        print ("Trying default url: " + default_url + "\n")

    else:
        try:
            print ("Loading config from " + config_filename + "\n")

            with io.open(config_filename, "r") as fp:
                sickrage.srConfig.readfp(fp)

            # Replace default values with config_file values
            host = sickrage.srConfig.get("sickrage", "host")
            port = sickrage.srConfig.get("sickrage", "port")
            username = sickrage.srConfig.get("sickrage", "username")
            password = sickrage.srConfig.get("sickrage", "password")

            try:
                ssl = int(sickrage.srConfig.get("sickrage", "ssl"))

            except (configparser.NoOptionError, ValueError):
                pass

            try:
                web_root = sickrage.srConfig.get("sickrage", "web_root")
                if not web_root.startswith("/"):
                    web_root = "/" + web_root

                if not web_root.endswith("/"):
                    web_root = web_root + "/"

            except configparser.NoOptionError:
                pass

        except EnvironmentError:
            e = sys.exc_info()[1]
            print ("Could not read configuration file: " + str(e))
            # There was a config_file, don't use default values but exit
            sys.exit(1)

    params = {}

    params['quiet'] = 1

    params['dir'] = dir_to_process
    if org_NZB_name != None:
        params['nzbName'] = org_NZB_name

    if status != None:
        params['failed'] = status

    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"

    url = protocol + host + ":" + port + web_root + "home/postprocess/processEpisode?" + urlencode(params)

    print ("Opening URL: " + url)

    try:
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        handler = HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

        result = opener.open(url).readlines()

        for line in result:
            if line:
                print (line.strip())

    except IOError:
        e = sys.exc_info()[1]
        print ("Unable to open URL: " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    print ("This module is supposed to be used as import in other scripts and not run standalone.")
    print ("Use sabToSiCKRAGE instead.")
    sys.exit(1)