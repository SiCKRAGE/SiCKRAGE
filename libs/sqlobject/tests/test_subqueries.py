from sqlobject import *
from sqlobject.sqlbuilder import *
from sqlobject.tests.dbtest import *

########################################
## Subqueries (subselects)
########################################

class TestIn1(SQLObject):
    col1 = StringCol()

class TestIn2(SQLObject):
    col2 = StringCol()

class TestOuter(SQLObject):
    fk = ForeignKey('TestIn1')

def setup():
    setupClass(TestIn1)
    setupClass(TestIn2)

def insert():
    setup()
    TestIn1(col1=None)
    TestIn1(col1='')
    TestIn1(col1="test")
    TestIn2(col2=None)
    TestIn2(col2='')
    TestIn2(col2="test")

def test_1syntax_in():
    setup()
    select = TestIn1.select(IN(TestIn1.q.col1, Select(TestIn2.q.col2)))
    assert str(select) == \
        "SELECT test_in1.id, test_in1.col1 FROM test_in1 WHERE test_in1.col1 IN (SELECT test_in2.col2 FROM test_in2)"

    select = TestIn1.select(IN(TestIn1.q.col1, TestIn2.select()))
    assert str(select) == \
        "SELECT test_in1.id, test_in1.col1 FROM test_in1 WHERE test_in1.col1 IN (SELECT test_in2.id FROM test_in2 WHERE 1 = 1)"

def test_2perform_in():
    insert()
    select = TestIn1.select(IN(TestIn1.q.col1, Select(TestIn2.q.col2)))
    assert select.count() == 2

def test_3syntax_exists():
    setup()
    select = TestIn1.select(NOTEXISTS(Select(TestIn2.q.col2, where=(Outer(TestIn1).q.col1 == TestIn2.q.col2))))
    assert str(select) == \
        "SELECT test_in1.id, test_in1.col1 FROM test_in1 WHERE NOT EXISTS (SELECT test_in2.col2 FROM test_in2 WHERE ((test_in1.col1) = (test_in2.col2)))"

    setupClass(TestOuter)
    select = TestOuter.select(NOTEXISTS(Select(TestIn1.q.col1, where=(Outer(TestOuter).q.fk == TestIn1.q.id))))
    assert str(select) == \
        "SELECT test_outer.id, test_outer.fk_id FROM test_outer WHERE NOT EXISTS (SELECT test_in1.col1 FROM test_in1 WHERE ((test_outer.fk_id) = (test_in1.id)))"

def test_4perform_exists():
    insert()
    select = TestIn1.select(EXISTS(Select(TestIn2.q.col2, where=(Outer(TestIn1).q.col1 == TestIn2.q.col2))))
    assert len(list(select)) == 2

    setupClass(TestOuter)
    select = TestOuter.select(NOTEXISTS(Select(TestIn1.q.col1, where=(Outer(TestOuter).q.fkID == TestIn1.q.id))))
    assert len(list(select)) == 0

def test_4syntax_direct():
    setup()
    select = TestIn1.select(TestIn1.q.col1 == Select(TestIn2.q.col2, where=(TestIn2.q.col2 == "test")))
    assert str(select) == \
        "SELECT test_in1.id, test_in1.col1 FROM test_in1 WHERE ((test_in1.col1) = (SELECT test_in2.col2 FROM test_in2 WHERE ((test_in2.col2) = ('test'))))"

def test_4perform_direct():
    insert()
    select = TestIn1.select(TestIn1.q.col1 == Select(TestIn2.q.col2, where=(TestIn2.q.col2 == "test")))
    assert select.count() == 1

def test_5perform_direct():
     insert()
     select = TestIn1.select(TestIn1.q.col1 == Select(TestIn2.q.col2, where=(TestIn2.q.col2 == "test")))
     assert select.count() == 1

def test_6syntax_join():
     insert()
     j = LEFTOUTERJOINOn(TestIn2, TestIn1, TestIn1.q.col1==TestIn2.q.col2)
     select = TestIn1.select(TestIn1.q.col1 == Select(TestIn2.q.col2, where=(TestIn2.q.col2 == "test"), join=j))
     assert str(select) == \
        "SELECT test_in1.id, test_in1.col1 FROM test_in1 WHERE ((test_in1.col1) = (SELECT test_in2.col2 FROM test_in2 LEFT OUTER JOIN test_in1 ON ((test_in1.col1) = (test_in2.col2)) WHERE ((test_in2.col2) = ('test'))))"

def test_6perform_join():
     insert()
     j = LEFTOUTERJOINOn(TestIn2, TestIn1, TestIn1.q.col1==TestIn2.q.col2)
     select = TestIn1.select(TestIn1.q.col1 == Select(TestIn2.q.col2, where=(TestIn2.q.col2 == "test"), join=j))
     assert select.count() == 1
