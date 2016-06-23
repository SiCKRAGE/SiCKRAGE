from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Test PosgreSQL sslmode
########################################

class TestSSLMode(SQLObject):
    test = StringCol()

def test_sslmode():
    setupClass(TestSSLMode)
    connection = TestSSLMode._connection
    if (connection.dbName != 'postgres') or \
            (not connection.module.__name__.startswith('psycopg')):
        # sslmode is only implemented by psycopg[12] PostgreSQL driver
        return

    connection = getConnection(sslmode='require')
    TestSSLMode._connection = connection
    test = TestSSLMode(test='test') # Connect to the DB to test sslmode

    connection.cache.clear()
    test = TestSSLMode.select()[0]
    assert test.test == 'test'
