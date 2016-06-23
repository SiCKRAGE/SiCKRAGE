# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import functools
import locale
from datetime import datetime

import sickrage
from sickrage.core.updaters.tz_updater import sr_timezone


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


# helper class
class static_or_instance(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return functools.partial(self.func, instance)


# subclass datetime to add function to display custom date and time formats
class srDateTime(datetime):
    has_locale = True
    en_US_norm = locale.normalize('en_US.utf-8')

    @static_or_instance
    def convert_to_setting(self, dt=None):
        try:
            if sickrage.srCore.srConfig.TIMEZONE_DISPLAY == 'local':
                return dt.astimezone(sr_timezone) if self is None else self.astimezone(sr_timezone)
            else:
                return dt if self is None else self
        except Exception:
            return dt if self is None else self

    # display Time in SickRage Format
    @static_or_instance
    def srftime(self, dt=None, show_seconds=False, t_preset=None):
        """
        Display time in SR format
        TODO: Rename this to srftime

        :param dt: datetime object
        :param show_seconds: Boolean, show seconds
        :param t_preset: Preset time format
        :return: time string
        """

        try:
            locale.setlocale(locale.LC_TIME, '')
        except Exception:
            pass

        try:
            if srDateTime.has_locale:
                locale.setlocale(locale.LC_TIME, 'en_US')
        except Exception:
            try:
                if srDateTime.has_locale:
                    locale.setlocale(locale.LC_TIME, srDateTime.en_US_norm)
            except Exception:
                srDateTime.has_locale = False

        strt = ''
        try:
            if self is None:
                if dt is not None:
                    if t_preset is not None:
                        strt = dt.strftime(t_preset)
                    elif show_seconds:
                        strt = dt.strftime(sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS)
                    else:
                        strt = dt.strftime(sickrage.srCore.srConfig.TIME_PRESET)
            else:
                if t_preset is not None:
                    strt = self.strftime(t_preset)
                elif show_seconds:
                    strt = self.strftime(sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS)
                else:
                    strt = self.strftime(sickrage.srCore.srConfig.TIME_PRESET)
        finally:
            try:
                if srDateTime.has_locale:
                    locale.setlocale(locale.LC_TIME, '')
            except Exception:
                srDateTime.has_locale = False

        return strt

    # display Date in SickRage Format
    @static_or_instance
    def srfdate(self, dt=None, d_preset=None):
        """
        Display date in SR format
        TODO: Rename this to srfdate

        :param dt: datetime object
        :param d_preset: Preset date format
        :return: date string
        """

        try:
            locale.setlocale(locale.LC_TIME, '')
        except Exception:
            pass

        strd = ''
        try:
            if self is None:
                if dt is not None:
                    if d_preset is not None:
                        strd = dt.strftime(d_preset)
                    else:
                        strd = dt.strftime(sickrage.srCore.srConfig.DATE_PRESET)
            else:
                if d_preset is not None:
                    strd = self.strftime(d_preset)
                else:
                    strd = self.strftime(sickrage.srCore.srConfig.DATE_PRESET)
        finally:

            try:
                locale.setlocale(locale.LC_TIME, '')
            except Exception:
                pass

        return strd

    # display Datetime in SickRage Format
    @static_or_instance
    def srfdatetime(self, dt=None, show_seconds=False, d_preset=None, t_preset=None):
        """
        Show datetime in SR format
        TODO: Rename this to srfdatetime

        :param dt: datetime object
        :param show_seconds: Boolean, show seconds as well
        :param d_preset: Preset date format
        :param t_preset: Preset time format
        :return: datetime string
        """

        try:
            locale.setlocale(locale.LC_TIME, '')
        except Exception:
            pass

        strd = ''
        try:
            if self is None:
                if dt is not None:
                    if d_preset is not None:
                        strd = dt.strftime(d_preset)
                    else:
                        strd = dt.strftime(sickrage.srCore.srConfig.DATE_PRESET)
                    try:
                        if srDateTime.has_locale:
                            locale.setlocale(locale.LC_TIME, 'en_US')
                    except Exception:
                        try:
                            if srDateTime.has_locale:
                                locale.setlocale(locale.LC_TIME, srDateTime.en_US_norm)
                        except Exception:
                            srDateTime.has_locale = False
                    if t_preset is not None:
                        strd += ', {}'.format(dt.strftime(t_preset))
                    elif show_seconds:
                        strd += ', {}'.format(dt.strftime(sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS))
                    else:
                        strd += ', {}'.format(dt.strftime(sickrage.srCore.srConfig.TIME_PRESET))
            else:
                if d_preset is not None:
                    strd = self.strftime(d_preset)
                else:
                    strd = self.strftime(sickrage.srCore.srConfig.DATE_PRESET)

                try:
                    if srDateTime.has_locale:
                        locale.setlocale(locale.LC_TIME, 'en_US')
                except Exception:
                    try:
                        if srDateTime.has_locale:
                            locale.setlocale(locale.LC_TIME, srDateTime.en_US_norm)
                    except Exception:
                        srDateTime.has_locale = False
                if t_preset is not None:
                    strd += ', {}'.format(dt.strftime(t_preset))
                elif show_seconds:
                    strd += ', {}'.format(dt.strftime(sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS))
                else:
                    strd += ', {}'.format(dt.strftime(sickrage.srCore.srConfig.TIME_PRESET))
        finally:
            try:
                if srDateTime.has_locale:
                    locale.setlocale(locale.LC_TIME, '')
            except Exception:
                srDateTime.has_locale = False

        return strd
