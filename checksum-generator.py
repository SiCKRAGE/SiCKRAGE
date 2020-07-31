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
import os
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


with open(checksum_file, "wb") as fp:
    for root, dirs, files in os.walk(prog_dir):
        for file in files:
            full_filename = Path(str(root).replace(str(prog_dir), 'sickrage')).joinpath(file)
            if full_filename != checksum_file:
                fp.write('{} = {}\n'.format(full_filename, md5(full_filename)).encode())

    print('Finished generating {}'.format(checksum_file))
