# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca/
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


import datetime
import sys
from collections import deque

from sickrage.core.common import dateTimeFormat


class UIError(object):
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
        self.title = sys.exc_info()[-2] or message
        self.message = message


class UIWarning(object):
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
        self.title = sys.exc_info()[-2] or message
        self.message = message


class ErrorViewer(object):
    """
    Keeps a static list of UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    def __init__(self):
        self.errors = deque(maxlen=100)

    def add(self, error, ui=False):
        self.errors += [(error, UIError(error))[ui]]

    def clear(self):
        self.errors.clear()

    def get(self, *args, **kwargs):
        return self.errors

    def count(self):
        return len(self.errors)


class WarningViewer(object):
    """
    Keeps a static list of (warning) UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    def __init__(self):
        self.warnings = deque(maxlen=100)

    def add(self, warning, ui=False):
        self.warnings += [(warning, UIWarning(warning))[ui]]

    def clear(self):
        self.warnings.clear()

    def get(self, *args, **kwargs):
        return self.warnings

    def count(self):
        return len(self.warnings)
