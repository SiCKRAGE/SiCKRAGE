from sqlobject import *
from sqlobject.tests.dbtest import *

class TestSOListMySQL(SQLObject):
    pass

def test_list_databases():
    connection = getConnection()
    if connection.dbName != "mysql":
        return
    assert connection.db in connection.listDatabases()

def test_list_tables():
    connection = getConnection()
    if connection.dbName != "mysql":
        return
    setupClass(TestSOListMySQL)
    assert TestSOListMySQL.sqlmeta.table in connection.listTables()
