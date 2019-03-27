#!/usr/bin/env python3
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.

import os

if __name__ == '__main__':
    # removes stale .pyc files
    for root, dirs, files in os.walk(os.path.dirname(__file__)):
        pyc_files = list(filter(lambda filename: filename.endswith(".pyc"), files))
        py_files = set(filter(lambda filename: filename.endswith(".py"), files))
        excess_pyc_files = list(filter(lambda pyc_filename: pyc_filename[:-1] not in py_files, pyc_files))
        for excess_pyc_file in excess_pyc_files:
            full_path = os.path.join(root, excess_pyc_file)
            os.remove(full_path)

    from sickrage import main

    main()
