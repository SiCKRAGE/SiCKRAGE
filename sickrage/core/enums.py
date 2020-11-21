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
import enum


class SeriesProviderID(enum.Enum):
    THETVDB = 'thetvdb'

    @property
    def _strings(self):
        return {
            self.THETVDB.name: 'TheTVDB'
        }

    @property
    def _slug_strings(self):
        return {
            self.THETVDB.name: 'thetvdb'
        }

    @property
    def display_name(self):
        return self._strings[self.name]

    @property
    def slug(self):
        return self._slug_strings[self.name]

    @classmethod
    def by_slug(cls, value):
        for item in cls:
            if item.slug == value:
                return item


class DefaultHomePage(enum.Enum):
    HOME = 'home'
    SCHEDULE = 'schedule'
    HISTORY = 'history'

    @property
    def _strings(self):
        return {
            self.HOME.name: 'Home',
            self.SCHEDULE.name: 'Schedule',
            self.HISTORY.name: 'History',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class MultiEpNaming(enum.Enum):
    REPEAT = 1
    EXTEND = 2
    DUPLICATE = 4
    LIMITED_EXTEND = 8
    SEPARATED_REPEAT = 16
    LIMITED_EXTEND_E_PREFIXED = 32

    @property
    def _strings(self):
        return {
            self.REPEAT.name: 'Repeat',
            self.SEPARATED_REPEAT.name: 'Repeat (Separated)',
            self.DUPLICATE.name: 'Duplicate',
            self.EXTEND.name: 'Extend',
            self.LIMITED_EXTEND.name: 'Extend (Limited)',
            self.LIMITED_EXTEND_E_PREFIXED.name: 'Extend (Limited, E-prefixed)'
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class CpuPreset(enum.Enum):
    LOW = 0.01
    NORMAL = 0.02
    HIGH = 0.05

    @property
    def _strings(self):
        return {
            self.LOW.name: 'Low',
            self.NORMAL.name: 'Normal',
            self.HIGH.name: 'High',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class CheckPropersInterval(enum.Enum):
    DAILY = 24 * 60
    FOUR_HOURS = 4 * 60
    NINETY_MINUTES = 90
    FORTY_FIVE_MINUTES = 45
    FIFTEEN_MINUTES = 15

    @property
    def _strings(self):
        return {
            self.DAILY.name: '24 hours',
            self.FOUR_HOURS.name: '4 hours',
            self.NINETY_MINUTES.name: '90 mins',
            self.FORTY_FIVE_MINUTES.name: '45 mins',
            self.FIFTEEN_MINUTES.name: '15 mins',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class FileTimestampTimezone(enum.Enum):
    NETWORK = 0
    LOCAL = 1

    @property
    def _strings(self):
        return {
            self.NETWORK.name: 'Network',
            self.LOCAL.name: 'Local',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class ProcessMethod(enum.Enum):
    COPY = 'copy'
    MOVE = 'move'
    HARDLINK = 'hardlink'
    SYMLINK = 'symlink'
    SYMLINK_REVERSED = 'symlink_reversed'

    @property
    def _strings(self):
        return {
            self.COPY.name: 'Copy',
            self.MOVE.name: 'Move',
            self.HARDLINK.name: 'Hard Link',
            self.SYMLINK.name: 'Symbolic Link',
            self.SYMLINK_REVERSED.name: 'Symbolic Link Reversed',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class NzbMethod(enum.Enum):
    BLACKHOLE = 'blackhole'
    SABNZBD = 'sabnzbd'
    NZBGET = 'nzbget'
    DOWNLOAD_STATION = 'download_station'

    @property
    def _strings(self):
        return {
            self.BLACKHOLE.name: 'Blackhole',
            self.SABNZBD.name: 'SABnzbd',
            self.NZBGET.name: 'NZBget',
            self.DOWNLOAD_STATION.name: 'Synology DS',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class TorrentMethod(enum.Enum):
    BLACKHOLE = 'blackhole'
    UTORRENT = 'utorrent'
    TRANSMISSION = 'transmission'
    DELUGE = 'deluge'
    DELUGED = 'deluged'
    DOWNLOAD_STATION = 'download_station'
    RTORRENT = 'rtorrent'
    QBITTORRENT = 'qbittorrent'
    MLNET = 'mlnet'
    PUTIO = 'putio'

    @property
    def _strings(self):
        return {
            self.BLACKHOLE.name: 'Blackhole',
            self.UTORRENT.name: 'uTorrent',
            self.TRANSMISSION.name: 'Transmission',
            self.DELUGE.name: 'Deluge (via WebUI)',
            self.DELUGED.name: 'Deluge (via Daemon)',
            self.DOWNLOAD_STATION.name: 'Synology DS',
            self.RTORRENT.name: 'rTorrent',
            self.QBITTORRENT.name: 'qBitTorrent',
            self.MLNET.name: 'MLDonkey',
            self.PUTIO.name: 'Putio',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class SearchFormat(enum.Enum):
    STANDARD = 1
    AIR_BY_DATE = 2
    ANIME = 3
    SPORTS = 4
    COLLECTION = 6

    @property
    def _strings(self):
        return {
            self.STANDARD.name: 'Standard (Show.S01E01)',
            self.AIR_BY_DATE.name: 'Air By Date (Show.2010.03.02)',
            self.ANIME.name: 'Anime (Show.265)',
            self.SPORTS.name: 'Sports (Show.2010.03.02)',
            self.COLLECTION.name: 'Collection (Show.Series.1.1of10) or (Show.Series.1.Part.1)'
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class UserPermission(enum.Enum):
    SUPERUSER = 0
    GUEST = 1

    @property
    def _strings(self):
        return {
            self.SUPERUSER.name: 'Superuser',
            self.GUEST.name: 'Guest',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class PosterSortDirection(enum.Enum):
    ASCENDING = 0
    DESCENDING = 1

    @property
    def _strings(self):
        return {
            self.ASCENDING.name: 'Ascending',
            self.DESCENDING.name: 'Descending',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class HomeLayout(enum.Enum):
    POSTER = 'poster'
    SMALL = 'small'
    BANNER = 'banner'
    DETAILED = 'detailed'
    SIMPLE = 'simple'

    @property
    def _strings(self):
        return {
            self.POSTER.name: 'Poster',
            self.SMALL.name: 'Small Poster',
            self.BANNER.name: 'Banner',
            self.DETAILED.name: 'Detailed',
            self.SIMPLE.name: 'Simple',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class PosterSortBy(enum.Enum):
    NAME = 0
    DATE = 1
    NETWORK = 2
    PROGRESS = 3

    @property
    def _strings(self):
        return {
            self.NAME.name: 'Sort By Name',
            self.DATE.name: 'Sort By Date',
            self.NETWORK.name: 'Sort By Network',
            self.PROGRESS.name: 'Sort By Progress',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class HistoryLayout(enum.Enum):
    DETAILED = 'detailed'
    COMPACT = 'compact'

    @property
    def _strings(self):
        return {
            self.DETAILED.name: 'Detailed',
            self.COMPACT.name: 'Compact',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class TimezoneDisplay(enum.Enum):
    LOCAL = 0
    NETWORK = 1

    @property
    def _strings(self):
        return {
            self.LOCAL.name: 'Local',
            self.NETWORK.name: 'Network',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class UITheme(enum.Enum):
    DARK = 'dark'
    LIGHT = 'light'

    @property
    def _strings(self):
        return {
            self.DARK.name: 'Dark',
            self.LIGHT.name: 'Light',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class TraktAddMethod(enum.Enum):
    SKIP_ALL = 0
    DOWNLOAD_PILOT_ONLY = 1
    WHOLE_SHOW = 2

    @property
    def _strings(self):
        return {
            self.SKIP_ALL.name: 'Skip All',
            self.DOWNLOAD_PILOT_ONLY.name: 'Download Pilot Only',
            self.WHOLE_SHOW.name: 'Get Whole Show',
        }

    @property
    def display_name(self):
        return self._strings[self.name]
