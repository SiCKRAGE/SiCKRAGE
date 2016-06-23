from sqlobject import *
from sqlobject.tests.dbtest import *

class myid_sqlmeta(sqlmeta):
    idName = "my_id"

class TestSqlmeta1(SQLObject):
    class sqlmeta(myid_sqlmeta):
        pass

class TestSqlmeta2(SQLObject):
    class sqlmeta(sqlmeta):
        style = MixedCaseStyle(longID=True)

class TestSqlmeta3(SQLObject):
    class sqlmeta(myid_sqlmeta):
        style = MixedCaseStyle(longID=True)

class TestSqlmeta4(SQLObject):
    class sqlmeta(myid_sqlmeta):
        idName = None
        style = MixedCaseStyle(longID=True)

class longid_sqlmeta(sqlmeta):
    idName = "my_id"
    style = MixedCaseStyle(longID=True)

class TestSqlmeta5(SQLObject):
    class sqlmeta(longid_sqlmeta):
        pass

class TestSqlmeta6(SQLObject):
    class sqlmeta(longid_sqlmeta):
        idName = None

def test_sqlmeta_inherited_idName():
    setupClass([TestSqlmeta1, TestSqlmeta2])
    assert TestSqlmeta1.sqlmeta.idName == "my_id"
    assert TestSqlmeta2.sqlmeta.idName == "TestSqlmeta2ID"
    assert TestSqlmeta3.sqlmeta.idName == "my_id"
    assert TestSqlmeta4.sqlmeta.idName == "TestSqlmeta4ID"
    assert TestSqlmeta5.sqlmeta.idName == "my_id"
    assert TestSqlmeta6.sqlmeta.idName == "TestSqlmeta6ID"
