from sqlobject import *
from sqlobject.inheritance import *
from sqlobject.tests.dbtest import *

class TestAggregate1(InheritableSQLObject):
    value1 = IntCol()

class TestAggregate2(TestAggregate1):
    value2 = IntCol()

def test_aggregates():
    setupClass([TestAggregate1, TestAggregate2])

    TestAggregate1(value1=1)
    TestAggregate2(value1=2, value2=12)

    assert TestAggregate1.select().max("value1") == 2
    assert TestAggregate2.select().max("value1") == 2
    raises(Exception, TestAggregate2.select().max, "value2")
    assert TestAggregate2.select().max(TestAggregate2.q.value2) == 12
