from sqlobject import *
from sqlobject.tests.dbtest import *

class TestCreateDrop(SQLObject):
    class sqlmeta(sqlmeta):
        idName = 'test_id_here'
        table = 'test_create_drop_table'
    name = StringCol()
    number = IntCol()
    time = DateTimeCol()
    short = StringCol(length=10)
    blobcol = BLOBCol()

def test_create_drop():
    conn = getConnection()
    TestCreateDrop.setConnection(conn)
    TestCreateDrop.dropTable(ifExists=True)
    assert not conn.tableExists(TestCreateDrop.sqlmeta.table)
    TestCreateDrop.createTable(ifNotExists=True)
    assert conn.tableExists(TestCreateDrop.sqlmeta.table)
    TestCreateDrop.createTable(ifNotExists=True)
    assert conn.tableExists(TestCreateDrop.sqlmeta.table)
    TestCreateDrop.dropTable(ifExists=True)
    assert not conn.tableExists(TestCreateDrop.sqlmeta.table)
    TestCreateDrop.dropTable(ifExists=True)
    assert not conn.tableExists(TestCreateDrop.sqlmeta.table)
