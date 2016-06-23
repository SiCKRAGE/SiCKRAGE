#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

from __future__ import print_function, unicode_literals

import ConfigParser
import io
import logging
import os
import sys
import time

import sickrage


sickragePath = os.path.split(os.path.split(sys.argv[0])[0])[0]
sys.path.append(sickragePath)
configFilename = os.path.join(sickragePath, "config.ini")

config = ConfigParser.ConfigParser()

try:
    with io.open(configFilename, "r") as fp:
        sickrage.srCore.srConfig.readfp(fp)
except IOError as e:
    print ("Could not find/read SiCKRAGE config.ini: " + str(e))
    print (
    'Possibly wrong mediaToSiCKRAGE.py location. Ensure the file is in the autoProcessTV subdir of your SiCKRAGE installation')
    time.sleep(3)
    sys.exit(1)

scriptlogger = logging.getLogger('mediaToSiCKRAGE')
formatter = logging.Formatter('%(asctime)s %(levelname)-8s MEDIATOSICKRAGE :: %(message)s', '%b-%d %H:%M:%S')

# Get the log dir setting from SB config
logdirsetting = sickrage.srCore.srConfig.get("General", "log_dir") if sickrage.srCore.srConfig.get("General", "log_dir") else 'Logs'
# put the log dir inside the SiCKRAGE dir, unless an absolute path
logdir = os.path.normpath(os.path.join(sickragePath, logdirsetting))
logfile = os.path.join(logdir, 'SiCKRAGE.log')

try:
    handler = logging.FileHandler(logfile)
except:
    print ('Unable to open/create the log file at ' + logfile)
    time.sleep(3)
    sys.exit()

handler.setFormatter(formatter)
scriptlogger.addHandler(handler)
scriptlogger.setLevel(logging.DEBUG)


def utorrent():
    #    print 'Calling utorrent'
    if len(sys.argv) < 2:
        scriptlogger.error('No folder supplied - is this being called from uTorrent?')
        print ("No folder supplied - is this being called from uTorrent?")
        time.sleep(3)
        sys.exit()

    dirName = sys.argv[1]
    nzbName = sys.argv[2]

    return (dirName, nzbName)


def transmission():
    dirName = os.getenv('TR_TORRENT_DIR')
    nzbName = os.getenv('TR_TORRENT_NAME')

    return (dirName, nzbName)


def deluge():
    if len(sys.argv) < 4:
        scriptlogger.error('No folder supplied - is this being called from Deluge?')
        print ("No folder supplied - is this being called from Deluge?")
        time.sleep(3)
        sys.exit()

    dirName = sys.argv[3]
    nzbName = sys.argv[2]

    return (dirName, nzbName)


def blackhole():
    if None != os.getenv('TR_TORRENT_DIR'):
        scriptlogger.debug('Processing script triggered by Transmission')
        print ("Processing script triggered by Transmission")
        scriptlogger.debug('TR_TORRENT_DIR: ' + os.getenv('TR_TORRENT_DIR'))
        scriptlogger.debug('TR_TORRENT_NAME: ' + os.getenv('TR_TORRENT_NAME'))
        dirName = os.getenv('TR_TORRENT_DIR')
        nzbName = os.getenv('TR_TORRENT_NAME')
    else:
        if len(sys.argv) < 2:
            scriptlogger.error('No folder supplied - Your client should invoke the script with a Dir and a Relese Name')
            print ("No folder supplied - Your client should invoke the script with a Dir and a Relese Name")
            time.sleep(3)
            sys.exit()

        dirName = sys.argv[1]
        nzbName = sys.argv[2]

    return (dirName, nzbName)


# def sabnzb():
#    if len(sys.argv) < 2:
#        scriptlogger.error('No folder supplied - is this being called from SABnzbd?')
#        print "No folder supplied - is this being called from SABnzbd?"
#        sys.exit()
#    elif len(sys.argv) >= 3:
#        dirName = sys.argv[1]
#        nzbName = sys.argv[2]
#    else:
#        dirName = sys.argv[1]
#        
#    return (dirName, nzbName)    
#
# def hella():
#    if len(sys.argv) < 4:
#        scriptlogger.error('No folder supplied - is this being called from HellaVCR?')
#        print "No folder supplied - is this being called from HellaVCR?"
#        sys.exit()
#    else:
#        dirName = sys.argv[3]
#        nzbName = sys.argv[2]
#        
#    return (dirName, nzbName)    

def main():
    scriptlogger.info('Starting external PostProcess script ' + __file__)

    host = sickrage.srCore.srConfig.get("General", "web_host")
    port = sickrage.srCore.srConfig.get("General", "web_port")
    username = sickrage.srCore.srConfig.get("General", "web_username")
    password = sickrage.srCore.srConfig.get("General", "web_password")
    try:
        ssl = int(sickrage.srCore.srConfig.get("General", "enable_https"))
    except (ConfigParser.NoOptionError, ValueError):
        ssl = 0

    try:
        web_root = sickrage.srCore.srConfig.get("General", "web_root")
    except ConfigParser.NoOptionError:
        web_root = ""

    tv_dir = sickrage.srCore.srConfig.get("General", "tv_download_dir")
    use_torrents = int(sickrage.srCore.srConfig.get("General", "use_torrents"))
    torrent_method = sickrage.srCore.srConfig.get("General", "torrent_method")

    if not use_torrents:
        scriptlogger.error('Enable Use Torrent on SiCKRAGE to use this Script. Aborting!')
        print ('Enable Use Torrent on SiCKRAGE to use this Script. Aborting!')
        time.sleep(3)
        sys.exit()

    if not torrent_method in ['utorrent', 'transmission', 'deluge', 'blackhole']:
        scriptlogger.error('Unknown Torrent Method. Aborting!')
        print ('Unknown Torrent Method. Aborting!')
        time.sleep(3)
        sys.exit()

    dirName, nzbName = eval(locals()['torrent_method'])()

    if dirName is None:
        scriptlogger.error('MediaToSiCKRAGE script need a dir to be run. Aborting!')
        print ('MediaToSiCKRAGE script need a dir to be run. Aborting!')
        time.sleep(3)
        sys.exit()

    if not os.path.isdir(dirName):
        scriptlogger.error('Folder ' + dirName + ' does not exist. Aborting AutoPostProcess.')
        print ('Folder ' + dirName + ' does not exist. Aborting AutoPostProcess.')
        time.sleep(3)
        sys.exit()

    if nzbName and os.path.isdir(os.path.join(dirName, nzbName)):
        dirName = os.path.join(dirName, nzbName)

    params = {}

    params['quiet'] = 1

    params['dir'] = dirName
    if nzbName != None:
        params['nzbName'] = nzbName

    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"

    if host == '0.0.0.0':
        host = 'localhost'

    url = protocol + host + ":" + port + web_root + "/home/postprocess/processEpisode"

    scriptlogger.debug("Opening URL: " + url + ' with params=' + str(params))
    print ("Opening URL: " + url + ' with params=' + str(params))

    try:
        response = sickrage.srCore.srWebSession.get(url, auth=(username, password), params=params, verify=False)
    except Exception as e:
        scriptlogger.error(': Unknown exception raised when opening url: ' + str(e))
        sys.exit('Unknown exception raised when opening url: ' + str(e))

    if response.status_code == 401:
        scriptlogger.error('Invalid SiCKRAGE Username or Password, check your config')
        sys.exit('Invalid SiCKRAGE Username or Password, check your config')

    if response.status_code == 200:
        scriptlogger.info('Script ' + __file__ + ' Succesfull')
        print('Script ' + __file__ + ' Succesfull')
        sys.exit()


if __name__ == '__main__':
    main()
