from sqlobject import *
from sqlobject.sqlbuilder import Select, func
from sqlobject.tests.dbtest import *

########################################
## groupBy
########################################

class GroupbyTest(SQLObject):
    name = StringCol()
    value = IntCol()

def test_groupBy():
    setupClass(GroupbyTest)
    GroupbyTest(name='a', value=1)
    GroupbyTest(name='a', value=2)
    GroupbyTest(name='b', value=1)

    connection = getConnection()
    select = Select([GroupbyTest.q.name, func.COUNT(GroupbyTest.q.value)],
        groupBy=GroupbyTest.q.name,
        orderBy=GroupbyTest.q.name)
    sql = connection.sqlrepr(select)
    rows = connection.queryAll(sql)
    assert list(rows) == [('a', 2), ('b', 1)]

def test_groupBy_list():
    setupClass(GroupbyTest)
    GroupbyTest(name='a', value=1)
    GroupbyTest(name='a', value=2)
    GroupbyTest(name='b', value=1)

    connection = getConnection()
    select = Select([GroupbyTest.q.name, GroupbyTest.q.value],
        groupBy=[GroupbyTest.q.name, GroupbyTest.q.value],
        orderBy=[GroupbyTest.q.name, GroupbyTest.q.value])
    sql = connection.sqlrepr(select)
    rows = connection.queryAll(sql)
    assert list(rows) == [('a', 1), ('a', 2), ('b', 1)]
