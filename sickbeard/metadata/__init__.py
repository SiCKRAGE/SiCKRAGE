# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ['generic', 'helpers', 'xbmc', 'xbmc_12plus', 'mediabrowser', 'ps3', 'wdtv', 'tivo', 'mede8er']

import sys

import xbmc
import xbmc_12plus
import mediabrowser
import ps3
import wdtv
import tivo
import mede8er


def available_generators():
    return filter(lambda x: x not in ('generic', 'helpers'), __all__)


def _getMetadataModule(name):
    name = name.lower()
    prefix = "sickbeard.metadata."
    if name in __all__ and prefix + name in sys.modules:
        return sys.modules[prefix + name]
    else:
        return None


def _getMetadataClass(name):
    module = _getMetadataModule(name)

    if not module:
        return None

    return module.metadata_class()


def get_metadata_generator_dict():
    result = {}
    for cur_generator_id in available_generators():
        cur_generator = _getMetadataClass(cur_generator_id)
        if not cur_generator:
            continue
        result[cur_generator.name] = cur_generator

    return result
