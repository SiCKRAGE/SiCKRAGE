from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## sqlmeta.asDict()
########################################

class TestAsDict(SQLObject):
    name = StringCol(length=10)
    name2 = StringCol(length=10)

def test_asDict():
    setupClass(TestAsDict, force=True)
    t1 = TestAsDict(name='one', name2='1')
    assert t1.sqlmeta.asDict() == dict(name='one', name2='1', id=1)
