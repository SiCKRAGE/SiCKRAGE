# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

__all__ = ['ENCODING', 'str_to_unicode', 'unicode_to_str']

import locale

# find the correct encoding
try:
    ENCODING = locale.getdefaultlocale()[1]
    ''.encode(ENCODING)
except (UnicodeError, TypeError):
    ENCODING = 'latin-1'


def str_to_unicode(s, encoding=None):
    """
    Attempts to convert a string of unknown character set to a unicode
    string.  First it tries to decode the string based on the locale's
    preferred encoding, and if that fails, fall back to UTF-8 and then
    latin-1.  If all fails, it will force encoding to the preferred
    charset, replacing unknown characters. If the given object is no
    string, this function will return the given object.
    """
    if not type(s) == str:
        return s

    if not encoding:
        encoding = ENCODING

    for c in [encoding, "utf-8", "latin-1"]:
        try:
            return s.decode(c)
        except UnicodeDecodeError:
            pass

    return s.decode(encoding, "replace")


def unicode_to_str(s, encoding=None):
    """
    Attempts to convert a unicode string of unknown character set to a
    string.  First it tries to encode the string based on the locale's
    preferred encoding, and if that fails, fall back to UTF-8 and then
    latin-1.  If all fails, it will force encoding to the preferred
    charset, replacing unknown characters. If the given object is no
    unicode string, this function will return the given object.
    """
    if not type(s) == unicode:
        return s

    if not encoding:
        encoding = ENCODING

    for c in [encoding, "utf-8", "latin-1"]:
        try:
            return s.encode(c)
        except UnicodeDecodeError:
            pass

    return s.encode(encoding, "replace")
