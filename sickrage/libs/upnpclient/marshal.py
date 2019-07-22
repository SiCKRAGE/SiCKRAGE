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



import datetime
from decimal import Decimal
from uuid import UUID

from dateutil.parser import parse as parse_date
from requests.compat import urlparse

TRUTHY_VALS = {'true', 'yes', '1'}

DT_RET = {'char', 'string', 'bin.base64', 'bin.hex'}
DT_INT = {'ui1', 'ui2', 'ui4', 'i1', 'i2', 'i4'}
DT_DECIMAL = {'r4', 'r8', 'number', 'float', 'fixed.14.4'}
DT_DATE = {'date'}
DT_DATETIME = {'dateTime', 'dateTime.tz'}
DT_TIME = {'time', 'time.tz'}
DT_BOOL = {'boolean'}
DT_URI = {'uri'}
DT_UUID = {'uuid'}


def parse_time(val):
    """
    Parse a time to a `datetime.time` value.
    Can't just use `dateutil.parse.parser(val).time()` because that doesn't preserve tzinfo.
    """
    dt = parse_date(val)
    if dt.tzinfo is None:
        return dt.time()
    return datetime.time(dt.hour, dt.minute, dt.second, dt.microsecond, dt.tzinfo)


MARSHAL_FUNCTIONS = (
    (DT_RET, lambda x: x),
    (DT_INT, int),
    (DT_DECIMAL, Decimal),
    (DT_DATE, lambda x: parse_date(x).date()),
    (DT_DATETIME, parse_date),
    (DT_TIME, parse_time),
    (DT_BOOL, lambda x: x.lower() in TRUTHY_VALS),
    (DT_URI, urlparse),
    (DT_UUID, UUID)
)


def marshal_value(datatype, value):
    """
    Marshal a given string into a relevant Python type given the uPnP datatype.
    Assumes that the value has been pre-validated, so performs no checks.
    Returns a tuple pair of a boolean to say whether the value was marshalled and the (un)marshalled
    value.
    """
    for types, func in MARSHAL_FUNCTIONS:
        if datatype in types:
            return True, func(value)
    return False, value
