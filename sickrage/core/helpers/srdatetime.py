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


import locale

import sickrage
from sickrage.core.enums import TimezoneDisplay

date_presets = (
    '%Y-%m-%d',
    '%a, %Y-%m-%d',
    '%A, %Y-%m-%d',
    '%y-%m-%d',
    '%a, %y-%m-%d',
    '%A, %y-%m-%d',
    '%m/%d/%Y',
    '%a, %m/%d/%Y',
    '%A, %m/%d/%Y',
    '%m/%d/%y',
    '%a, %m/%d/%y',
    '%A, %m/%d/%y',
    '%m-%d-%Y',
    '%a, %m-%d-%Y',
    '%A, %m-%d-%Y',
    '%m-%d-%y',
    '%a, %m-%d-%y',
    '%A, %m-%d-%y',
    '%m.%d.%Y',
    '%a, %m.%d.%Y',
    '%A, %m.%d.%Y',
    '%m.%d.%y',
    '%a, %m.%d.%y',
    '%A, %m.%d.%y',
    '%d-%m-%Y',
    '%a, %d-%m-%Y',
    '%A, %d-%m-%Y',
    '%d-%m-%y',
    '%a, %d-%m-%y',
    '%A, %d-%m-%y',
    '%d/%m/%Y',
    '%a, %d/%m/%Y',
    '%A, %d/%m/%Y',
    '%d/%m/%y',
    '%a, %d/%m/%y',
    '%A, %d/%m/%y',
    '%d.%m.%Y',
    '%a, %d.%m.%Y',
    '%A, %d.%m.%Y',
    '%d.%m.%y',
    '%a, %d.%m.%y',
    '%A, %d.%m.%y',
    '%d. %b %Y',
    '%a, %d. %b %Y',
    '%A, %d. %b %Y',
    '%d. %b %y',
    '%a, %d. %b %y',
    '%A, %d. %b %y',
    '%d. %B %Y',
    '%a, %d. %B %Y',
    '%A, %d. %B %Y',
    '%d. %B %y',
    '%a, %d. %B %y',
    '%A, %d. %B %y',
    '%b %d, %Y',
    '%a, %b %d, %Y',
    '%A, %b %d, %Y',
    '%B %d, %Y',
    '%a, %B %d, %Y',
    '%A, %B %d, %Y'
)

time_presets = ('%I:%M:%S %p', '%H:%M:%S')


class SRDateTime(object):
    def __init__(self, dt, convert=False):
        self.dt = dt
        if convert and sickrage.app.config.gui.timezone_display == TimezoneDisplay.LOCAL:
            try:
                self.dt = dt.astimezone(sickrage.app.tz)
            except Exception as e:
                pass

        self.has_locale = True
        self.en_US_norm = locale.normalize('en_US.utf-8')

    # display Time in SickRage Format
    def srftime(self, show_seconds=False, t_preset=None):
        """
        Display time in SR format

        :param show_seconds: Boolean, show seconds
        :param t_preset: Preset time format
        :return: time string
        """

        strt = ''

        try:
            locale.setlocale(locale.LC_TIME, '')
        except Exception:
            pass

        try:
            if self.has_locale:
                locale.setlocale(locale.LC_TIME, locale.normalize(sickrage.app.config.gui.gui_lang))
        except Exception:
            try:
                if self.has_locale:
                    locale.setlocale(locale.LC_TIME, self.en_US_norm)
            except Exception:
                self.has_locale = False

        try:
            if t_preset is not None:
                strt = self.dt.strftime(t_preset)
            elif show_seconds:
                strt = self.dt.strftime(sickrage.app.config.gui.time_preset_w_seconds)
            else:
                strt = self.dt.strftime(sickrage.app.config.gui.time_preset)
        finally:
            try:
                if self.has_locale:
                    locale.setlocale(locale.LC_TIME, '')
            except Exception:
                self.has_locale = False

        return strt

    # display Date in SickRage Format
    def srfdate(self, d_preset=None):
        """
        Display date in SR format

        :param d_preset: Preset date format
        :return: date string
        """

        strd = ''

        try:
            locale.setlocale(locale.LC_TIME, '')
        except Exception:
            pass

        try:
            if self.has_locale:
                locale.setlocale(locale.LC_TIME, locale.normalize(sickrage.app.config.gui.gui_lang))
        except Exception:
            try:
                if self.has_locale:
                    locale.setlocale(locale.LC_TIME, self.en_US_norm)
            except Exception:
                self.has_locale = False

        try:
            if d_preset is not None:
                strd = self.dt.strftime(d_preset)
            else:
                strd = self.dt.strftime(sickrage.app.config.gui.date_preset)
        finally:
            try:
                locale.setlocale(locale.LC_TIME, '')
            except Exception:
                pass

        return strd

    # display Datetime in SickRage Format
    def srfdatetime(self, show_seconds=False, d_preset=None, t_preset=None):
        """
        Show datetime in SR format

        :param show_seconds: Boolean, show seconds as well
        :param d_preset: Preset date format
        :param t_preset: Preset time format
        :return: datetime string
        """

        strd = ''

        try:
            locale.setlocale(locale.LC_TIME, '')
        except Exception:
            pass

        try:
            if d_preset is not None:
                strd = self.dt.strftime(d_preset)
            else:
                strd = self.dt.strftime(sickrage.app.config.gui.date_preset)

            try:
                if self.has_locale:
                    locale.setlocale(locale.LC_TIME, locale.normalize(sickrage.app.config.gui.gui_lang))
            except Exception:
                try:
                    if self.has_locale:
                        locale.setlocale(locale.LC_TIME, self.en_US_norm)
                except Exception:
                    self.has_locale = False

            if t_preset is not None:
                strd += ', {}'.format(self.dt.strftime(t_preset))
            elif show_seconds:
                strd += ', {}'.format(self.dt.strftime(sickrage.app.config.gui.time_preset_w_seconds))
            else:
                strd += ', {}'.format(self.dt.strftime(sickrage.app.config.gui.time_preset))
        finally:
            try:
                if self.has_locale:
                    locale.setlocale(locale.LC_TIME, '')
            except Exception:
                self.has_locale = False

        return strd
