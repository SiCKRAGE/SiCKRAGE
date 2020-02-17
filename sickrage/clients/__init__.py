# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


_clients = {
    'utorrent': 'uTorrentAPI',
    'transmission': 'TransmissionAPI',
    'deluge': 'DelugeAPI',
    'deluged': 'DelugeDAPI',
    'download_station': 'DownloadStationAPI',
    'rtorrent': 'rTorrentAPI',
    'qbittorrent': 'QBittorrentAPI',
    'mlnet': 'mlnetAPI',
    'putio': 'PutioAPI',
}


def get_client_module(name, client_type):
    return __import__("{}.{}.{}".format(__name__, client_type, name.lower()), fromlist=list(_clients.keys()))


def get_client_instance(name, client_type):
    return getattr(get_client_module(name, client_type), _clients[name])
