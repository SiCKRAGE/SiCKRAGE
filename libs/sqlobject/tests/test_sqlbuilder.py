from sqlobject import *
from sqlobject.sqlbuilder import *
from sqlobject.tests.dbtest import *

class TestSQLBuilder(SQLObject):
    name = StringCol()
    value = IntCol()

def test_Select():
    setupClass(TestSQLBuilder)

    select1 = Select([const.id, func.MAX(const.salary)], staticTables=['employees'])
    assert sqlrepr(select1) == 'SELECT id, MAX(salary) FROM employees'

    select2 = Select([TestSQLBuilder.q.name, TestSQLBuilder.q.value])
    assert sqlrepr(select2) == 'SELECT test_sql_builder.name, test_sql_builder.value FROM test_sql_builder'

    union = Union(select1, select2)
    assert sqlrepr(union) == 'SELECT id, MAX(salary) FROM employees UNION SELECT test_sql_builder.name, test_sql_builder.value FROM test_sql_builder'

    union = Union(TestSQLBuilder.select().queryForSelect())
    assert sqlrepr(union) == 'SELECT test_sql_builder.id, test_sql_builder.name, test_sql_builder.value FROM test_sql_builder WHERE 1 = 1'

def test_empty_AND():
    assert AND() == None
    assert AND(True) == True

    # sqlrepr() is needed because AND() returns an SQLExpression that overrides
    # comparison. The following
    #     AND('x', 'y') == "foo bar"
    # is True! (-: Eeek!
    assert sqlrepr(AND(1, 2)) == sqlrepr(SQLOp("AND", 1, 2)) == "((1) AND (2))"
    assert sqlrepr(AND(1, 2, '3'), "sqlite") == \
        sqlrepr(SQLOp("AND", 1, SQLOp("AND", 2, '3')), "sqlite") == \
        "((1) AND ((2) AND ('3')))"

def test_modulo():
    setupClass(TestSQLBuilder)
    assert sqlrepr(TestSQLBuilder.q.value % 2 == 0, 'mysql') == \
        "((MOD(test_sql_builder.value, 2)) = (0))"
    assert sqlrepr(TestSQLBuilder.q.value % 2 == 0, 'sqlite') == \
        "(((test_sql_builder.value) % (2)) = (0))"

def test_str_or_sqlrepr():
    select = Select(['id', 'name'], staticTables=['employees'],
        where='value>0', orderBy='id')
    assert sqlrepr(select, 'sqlite') == \
        'SELECT id, name FROM employees WHERE value>0 ORDER BY id'

    select = Select(['id', 'name'], staticTables=['employees'],
        where='value>0', orderBy='id', lazyColumns=True)
    assert sqlrepr(select, 'sqlite') == \
        'SELECT id FROM employees WHERE value>0 ORDER BY id'

    insert = Insert('employees', values={'id': 1, 'name': 'test'})
    assert sqlrepr(insert, 'sqlite') == \
        "INSERT INTO employees (id, name) VALUES (1, 'test')"

    update = Update('employees', {'name': 'test'}, where='id=1')
    assert sqlrepr(update, 'sqlite') == \
        "UPDATE employees SET name='test' WHERE id=1"

    update = Update('employees', {'name': 'test', 'age': 42}, where='id=1')
    assert sqlrepr(update, 'sqlite') == \
        "UPDATE employees SET age=42, name='test' WHERE id=1"

    delete = Delete('employees', where='id=1')
    assert sqlrepr(delete, 'sqlite') == \
        "DELETE FROM employees WHERE id=1"

    raises(TypeError, Delete, 'employees')

    delete = Delete('employees', where=None)
    assert sqlrepr(delete, 'sqlite') == \
        "DELETE FROM employees"
