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

from __future__ import unicode_literals

import os
import sys
import site

if __name__ == '__main__':
    # add sickrage libs path to python system path
    LIBS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'libs'))
    if not (LIBS_DIR in sys.path):
        sys.path, remainder = sys.path[:1], sys.path[1:]
        site.addsitedir(LIBS_DIR)
        sys.path.extend(remainder)

    from sickrage import main

    main()
