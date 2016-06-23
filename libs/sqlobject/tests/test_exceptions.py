from sqlobject import *
from sqlobject.dberrors import *
from sqlobject.tests.dbtest import *

########################################
## Table aliases and self-joins
########################################

class TestException(SQLObject):
    name = StringCol(unique=True, length=100)

class TestExceptionWithNonexistingTable(SQLObject):
    pass

def test_exceptions():
    if not supports("exceptions"):
        return
    setupClass(TestException)
    TestException(name="test")
    raises(DuplicateEntryError, TestException, name="test")

    connection = getConnection()
    if connection.module.__name__ != 'psycopg2':
        return
    TestExceptionWithNonexistingTable.setConnection(connection)
    try:
        list(TestExceptionWithNonexistingTable.select())
    except ProgrammingError, e:
        assert e.args[0].code == '42P01'
    else:
        assert False, "DID NOT RAISE"
