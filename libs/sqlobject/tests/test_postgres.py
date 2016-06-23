from sqlobject import *
from sqlobject.tests.dbtest import *

class TestSOList(SQLObject):
    pass

def test_list_databases():
    connection = getConnection()
    if connection.dbName != "postgres":
        return
    assert connection.db in connection.listDatabases()

def test_list_tables():
    connection = getConnection()
    if connection.dbName != "postgres":
        return
    setupClass(TestSOList)
    assert TestSOList.sqlmeta.table in connection.listTables()
