from sqlobject import *
from sqlobject.inheritance import *
from sqlobject.tests.dbtest import *

class TestCascade1(InheritableSQLObject):
    dummy = IntCol()

class TestCascade2(TestCascade1):
    c = ForeignKey('TestCascade3', cascade='null')

class TestCascade3(SQLObject):
    dummy = IntCol()


def test_destroySelf():
    setupClass([TestCascade1, TestCascade3, TestCascade2])

    c = TestCascade3(dummy=1)
    b = TestCascade2(cID=c.id, dummy=1)
    c.destroySelf()
