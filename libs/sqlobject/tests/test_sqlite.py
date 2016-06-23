import threading
from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject.tests.dbtest import setSQLiteConnectionFactory
from test_basic import TestSO1

class SQLiteFactoryTest(SQLObject):
    name = StringCol()

def test_sqlite_factory():
    setupClass(SQLiteFactoryTest)

    if SQLiteFactoryTest._connection.dbName == "sqlite":
        if not SQLiteFactoryTest._connection.using_sqlite2:
            return

        factory = [None]
        def SQLiteConnectionFactory(sqlite):
            class MyConnection(sqlite.Connection):
                pass
            factory[0] = MyConnection
            return MyConnection

        setSQLiteConnectionFactory(SQLiteFactoryTest, SQLiteConnectionFactory)

        conn = SQLiteFactoryTest._connection.makeConnection()
        assert factory[0]
        assert isinstance(conn, factory[0])

def test_sqlite_factory_str():
    setupClass(SQLiteFactoryTest)

    if SQLiteFactoryTest._connection.dbName == "sqlite":
        if not SQLiteFactoryTest._connection.using_sqlite2:
            return

        factory = [None]
        def SQLiteConnectionFactory(sqlite):
            class MyConnection(sqlite.Connection):
                pass
            factory[0] = MyConnection
            return MyConnection
        from sqlobject.sqlite import sqliteconnection
        sqliteconnection.SQLiteConnectionFactory = SQLiteConnectionFactory

        setSQLiteConnectionFactory(SQLiteFactoryTest, "SQLiteConnectionFactory")

        conn = SQLiteFactoryTest._connection.makeConnection()
        assert factory[0]
        assert isinstance(conn, factory[0])
        del sqliteconnection.SQLiteConnectionFactory

def test_sqlite_aggregate():
    setupClass(SQLiteFactoryTest)

    if SQLiteFactoryTest._connection.dbName == "sqlite":
        if not SQLiteFactoryTest._connection.using_sqlite2:
            return

        def SQLiteConnectionFactory(sqlite):
            class MyConnection(sqlite.Connection):
                def __init__(self, *args, **kwargs):
                    super(MyConnection, self).__init__(*args, **kwargs)
                    self.create_aggregate("group_concat", 1, self.group_concat)

                class group_concat:
                    def __init__(self):
                        self.acc = []
                    def step(self, value):
                        if isinstance(value, basestring):
                            self.acc.append(value)
                        else:
                            self.acc.append(str(value))
                    def finalize(self):
                        self.acc.sort()
                        return ", ".join(self.acc)

            return MyConnection

        setSQLiteConnectionFactory(SQLiteFactoryTest, SQLiteConnectionFactory)

        SQLiteFactoryTest(name='sqlobject')
        SQLiteFactoryTest(name='sqlbuilder')
        assert SQLiteFactoryTest.select(orderBy="name").accumulateOne("group_concat", "name") == \
            "sqlbuilder, sqlobject"


def do_select():
    list(TestSO1.select())

def test_sqlite_threaded():
    setupClass(TestSO1)
    t = threading.Thread(target=do_select)
    t.start()
    t.join()
    # This should reuse the same connection as the connection
    # made above (at least will with most database drivers, but
    # this will cause an error in SQLite):
    do_select()


def test_empty_string():
    setupClass(TestSO1)
    test = TestSO1(name=None, passwd='')
    assert test.name is None
    assert test.passwd == ''

def test_memorydb():
    if not supports("memorydb"):
        return
    connection = getConnection()
    if connection.dbName != "sqlite":
        return
    if not connection._memory:
        return
    setupClass(TestSO1)
    connection.close() # create a new connection to an in-memory database
    TestSO1.setConnection(connection)
    TestSO1.createTable()

def test_list_databases():
    connection = getConnection()
    if connection.dbName != "sqlite":
        return
    assert connection.listDatabases() == ['main']

def test_list_tables():
    connection = getConnection()
    if connection.dbName != "sqlite":
        return
    setupClass(TestSO1)
    assert TestSO1.sqlmeta.table in connection.listTables()
