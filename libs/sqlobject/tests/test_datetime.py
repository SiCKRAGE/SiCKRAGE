import py.test
from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Date/time columns
########################################

from sqlobject import col
col.default_datetime_implementation = DATETIME_IMPLEMENTATION
from datetime import datetime, date, time

class DateTime1(SQLObject):
    col1 = DateTimeCol()
    col2 = DateCol()
    col3 = TimeCol()

def test_dateTime():
    setupClass(DateTime1)
    _now = datetime.now()
    dt1 = DateTime1(col1=_now, col2=_now, col3=_now.time())

    assert isinstance(dt1.col1, datetime)
    assert dt1.col1.year == _now.year
    assert dt1.col1.month == _now.month
    assert dt1.col1.day == _now.day
    assert dt1.col1.hour == _now.hour
    assert dt1.col1.minute == _now.minute
    assert dt1.col1.second == _now.second

    assert isinstance(dt1.col2, date)
    assert not isinstance(dt1.col2, datetime)
    assert dt1.col2.year == _now.year
    assert dt1.col2.month == _now.month
    assert dt1.col2.day == _now.day

    assert isinstance(dt1.col3, time)
    assert dt1.col3.hour == _now.hour
    assert dt1.col3.minute == _now.minute
    assert dt1.col3.second == _now.second

def test_microseconds():
    connection = getConnection()
    if hasattr(connection, 'can_use_microseconds') and \
            not connection.can_use_microseconds():
        py.test.skip("The database doesn't support microseconds; microseconds are supported by MariaDB since version 5.3.0 and by MySQL since version 5.6.4.")

    setupClass(DateTime1)
    _now = datetime.now()
    dt1 = DateTime1(col1=_now, col2=_now, col3=_now.time())

    assert dt1.col1.microsecond == _now.microsecond
    assert dt1.col3.microsecond == _now.microsecond

if mxdatetime_available:
    col.default_datetime_implementation = MXDATETIME_IMPLEMENTATION
    from mx.DateTime import now, Time

    dateFormat = None # use default
    connection = getConnection()
    if connection.dbName == "sqlite":
        if connection.using_sqlite2:
            # mxDateTime sends and PySQLite2 returns full date/time for dates
            dateFormat = "%Y-%m-%d %H:%M:%S.%f"

    class DateTime2(SQLObject):
        col1 = DateTimeCol()
        col2 = DateCol(dateFormat=dateFormat)
        col3 = TimeCol()

    def test_mxDateTime():
        setupClass(DateTime2)
        _now = now()
        dt2 = DateTime2(col1=_now, col2=_now, col3=Time(_now.hour, _now.minute, _now.second))

        assert isinstance(dt2.col1, col.DateTimeType)
        assert dt2.col1.year == _now.year
        assert dt2.col1.month == _now.month
        assert dt2.col1.day == _now.day
        assert dt2.col1.hour == _now.hour
        assert dt2.col1.minute == _now.minute
        assert dt2.col1.second == int(_now.second)

        assert isinstance(dt2.col2, col.DateTimeType)
        assert dt2.col2.year == _now.year
        assert dt2.col2.month == _now.month
        assert dt2.col2.day == _now.day
        if getConnection().dbName == "sqlite":
            assert dt2.col2.hour == _now.hour
            assert dt2.col2.minute == _now.minute
            assert dt2.col2.second == int(_now.second)
        else:
            assert dt2.col2.hour == 0
            assert dt2.col2.minute == 0
            assert dt2.col2.second == 0

        assert isinstance(dt2.col3, (col.DateTimeType, col.TimeType))
        assert dt2.col3.hour == _now.hour
        assert dt2.col3.minute == _now.minute
        assert dt2.col3.second == int(_now.second)
