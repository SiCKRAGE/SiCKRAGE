from sqlobject import *
from sqlobject.tests.dbtest import *

class TestCyclicReferenceA(SQLObject):
    class sqlmeta(sqlmeta):
        idName = 'test_id_here'
        table = 'test_cyclic_reference_a_table'
    name = StringCol()
    number = IntCol()
    time = DateTimeCol()
    short = StringCol(length=10)
    blobcol = BLOBCol()
    fkeyb = ForeignKey('TestCyclicReferenceB')

class TestCyclicReferenceB(SQLObject):
    class sqlmeta(sqlmeta):
        idName = 'test_id_here'
        table = 'test_cyclic_reference_b_table'
    name = StringCol()
    number = IntCol()
    time = DateTimeCol()
    short = StringCol(length=10)
    blobcol = BLOBCol()
    fkeya = ForeignKey('TestCyclicReferenceA') 

def test_cyclic_reference():
    if not supports('dropTableCascade'):
        return
    conn = getConnection()
    TestCyclicReferenceA.setConnection(conn)
    TestCyclicReferenceB.setConnection(conn)
    TestCyclicReferenceA.dropTable(ifExists=True, cascade=True)
    assert not conn.tableExists(TestCyclicReferenceA.sqlmeta.table)
    TestCyclicReferenceB.dropTable(ifExists=True, cascade=True)
    assert not conn.tableExists(TestCyclicReferenceB.sqlmeta.table)

    constraints = TestCyclicReferenceA.createTable(ifNotExists=True,
                                                   applyConstraints=False)
    assert conn.tableExists(TestCyclicReferenceA.sqlmeta.table)
    constraints += TestCyclicReferenceB.createTable(ifNotExists=True,
                                                   applyConstraints=False)
    assert conn.tableExists(TestCyclicReferenceB.sqlmeta.table)

    for constraint in constraints:
        conn.query(constraint)

    TestCyclicReferenceA.dropTable(ifExists=True, cascade=True)
    assert not conn.tableExists(TestCyclicReferenceA.sqlmeta.table)
    TestCyclicReferenceB.dropTable(ifExists=True, cascade=True)
    assert not conn.tableExists(TestCyclicReferenceB.sqlmeta.table)
