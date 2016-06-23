from sqlobject import *
from sqlobject.tests.dbtest import *

class TestComparison(SQLObject):
    pass

def test_eq():
    setupClass(TestComparison, force=True)
    t1 = TestComparison()
    t2 = TestComparison()

    TestComparison._connection.cache.clear()
    t3 = TestComparison.get(1)
    t4 = TestComparison.get(2)

    assert t1.id == t3.id
    assert t2.id == t4.id
    assert t1 is not t3
    assert t2 is not t4
    assert t1 == t3
    assert t2 == t4
    assert t1 <> t2
