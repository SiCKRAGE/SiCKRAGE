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


import hashlib
from pathlib import Path

main_dir = Path(__file__).parent
prog_dir = main_dir.joinpath('sickrage')
checksum_file = prog_dir.joinpath('checksums.md5')


def md5(filename):
    blocksize = 8192
    hasher = hashlib.md5()
    with open(filename, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
    return hasher.hexdigest()


with open(checksum_file, "rb") as fp:
    failed = False

    for line in fp.readlines():
        file, checksum = line.decode().strip().split(' = ')
        full_filename = main_dir.joinpath(file)
        if full_filename != checksum_file:
            if not full_filename.exists() or md5(full_filename) != checksum:
                print('SiCKRAGE file {} checksum invalid'.format(full_filename))
                failed = True

    if not failed:
        print('SiCKRAGE file checksums are all valid')
