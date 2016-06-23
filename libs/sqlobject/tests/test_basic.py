from sqlobject import *
from sqlobject.tests.dbtest import *

class TestSO1(SQLObject):

    name = StringCol(length=50, dbName='name_col')
    name.title = 'Your Name'
    name.foobar = 1
    passwd = StringCol(length=10)

    class sqlmeta:
        cacheValues = False

    def _set_passwd(self, passwd):
        self._SO_set_passwd(passwd.encode('rot13'))

def setupGetters(cls):
    setupClass(cls)
    inserts(cls, [('bob', 'god'), ('sally', 'sordid'),
                  ('dave', 'dremel'), ('fred', 'forgo')],
            'name passwd')

def test_case1():
    setupGetters(TestSO1)
    bob = TestSO1.selectBy(name='bob')[0]
    assert bob.name == 'bob'
    assert bob.passwd == 'god'.encode('rot13')
    bobs = TestSO1.selectBy(name='bob')[:10]
    assert len(list(bobs)) == 1

def test_newline():
    setupGetters(TestSO1)
    bob = TestSO1.selectBy(name='bob')[0]
    testString = 'hey\nyou\\can\'t you see me?\t'
    bob.name = testString
    bob.expire()
    assert bob.name == testString

def test_count():
    setupGetters(TestSO1)
    assert TestSO1.selectBy(name=None).count() == 0
    assert TestSO1.selectBy(name='bob').count() == 1
    assert TestSO1.select(TestSO1.q.name == 'bob').count() == 1
    assert TestSO1.select().count() == len(list(TestSO1.select()))

def test_getset():
    setupGetters(TestSO1)
    bob = TestSO1.selectBy(name='bob')[0]
    assert bob.name == 'bob'
    bob.name = 'joe'
    assert bob.name == 'joe'
    bob.set(name='joebob', passwd='testtest')
    assert bob.name == 'joebob'

def test_extra_vars():
    setupGetters(TestSO1)
    col = TestSO1.sqlmeta.columns['name']
    assert col.title == 'Your Name'
    assert col.foobar == 1
    assert getattr(TestSO1.sqlmeta.columns['passwd'], 'title', None) is None

class TestSO2(SQLObject):
    name = StringCol(length=50, dbName='name_col')
    passwd = StringCol(length=10)

    def _set_passwd(self, passwd):
        self._SO_set_passwd(passwd.encode('rot13'))

def test_case2():
    setupGetters(TestSO2)
    bob = TestSO2.selectBy(name='bob')[0]
    assert bob.name == 'bob'
    assert bob.passwd == 'god'.encode('rot13')

class Student(SQLObject):
    is_smart = BoolCol()

def test_boolCol():
    setupClass(Student)
    student = Student(is_smart=False)
    assert student.is_smart == False
    student2 = Student(is_smart=1)
    assert student2.is_smart == True

class TestSO3(SQLObject):
    name = StringCol(length=10, dbName='name_col')
    other = ForeignKey('TestSO4', default=None)
    other2 = KeyCol(foreignKey='TestSO4', default=None)

class TestSO4(SQLObject):
    me = StringCol(length=10)

def test_foreignKey():
    setupClass([TestSO4, TestSO3])
    test3_order = [col.name for col in TestSO3.sqlmeta.columnList]
    assert test3_order == ['name', 'otherID', 'other2ID']
    tc3 = TestSO3(name='a')
    assert tc3.other is None
    assert tc3.other2 is None
    assert tc3.otherID is None
    assert tc3.other2ID is None
    tc4a = TestSO4(me='1')
    tc3.other = tc4a
    assert tc3.other == tc4a
    assert tc3.otherID == tc4a.id
    tc4b = TestSO4(me='2')
    tc3.other = tc4b.id
    assert tc3.other == tc4b
    assert tc3.otherID == tc4b.id
    tc4c = TestSO4(me='3')
    tc3.other2 = tc4c
    assert tc3.other2 == tc4c
    assert tc3.other2ID == tc4c.id
    tc4d = TestSO4(me='4')
    tc3.other2 = tc4d.id
    assert tc3.other2 == tc4d
    assert tc3.other2ID == tc4d.id
    tcc = TestSO3(name='b', other=tc4a)
    assert tcc.other == tc4a
    tcc2 = TestSO3(name='c', other=tc4a.id)
    assert tcc2.other == tc4a

def test_selectBy():
    setupClass([TestSO4, TestSO3])
    tc4 = TestSO4(me='another')
    tc3 = TestSO3(name='sel', other=tc4)
    anothertc3 = TestSO3(name='not joined')
    assert tc3.other == tc4
    assert list(TestSO3.selectBy(other=tc4)) == [tc3]
    assert list(TestSO3.selectBy(otherID=tc4.id)) == [tc3]
    assert TestSO3.selectBy(otherID=tc4.id)[0] == tc3
    assert list(TestSO3.selectBy(otherID=tc4.id)[:10]) == [tc3]
    assert list(TestSO3.selectBy(other=tc4)[:10]) == [tc3]

class TestSO5(SQLObject):
    name = StringCol(length=10, dbName='name_col')
    other = ForeignKey('TestSO6', default=None, cascade=True)
    another = ForeignKey('TestSO7', default=None, cascade=True)

class TestSO6(SQLObject):
    name = StringCol(length=10, dbName='name_col')
    other = ForeignKey('TestSO7', default=None, cascade=True)

class TestSO7(SQLObject):
    name = StringCol(length=10, dbName='name_col')

def test_foreignKeyDestroySelfCascade():
    setupClass([TestSO7, TestSO6, TestSO5])

    tc5 = TestSO5(name='a')
    tc6a = TestSO6(name='1')
    tc5.other = tc6a
    tc7a = TestSO7(name='2')
    tc6a.other = tc7a
    tc5.another = tc7a
    assert tc5.other == tc6a
    assert tc5.otherID == tc6a.id
    assert tc6a.other == tc7a
    assert tc6a.otherID == tc7a.id
    assert tc5.other.other == tc7a
    assert tc5.other.otherID == tc7a.id
    assert tc5.another == tc7a
    assert tc5.anotherID == tc7a.id
    assert tc5.other.other == tc5.another
    assert TestSO5.select().count() == 1
    assert TestSO6.select().count() == 1
    assert TestSO7.select().count() == 1
    tc6b = TestSO6(name='3')
    tc6c = TestSO6(name='4')
    tc7b = TestSO7(name='5')
    tc6b.other = tc7b
    tc6c.other = tc7b
    assert TestSO5.select().count() == 1
    assert TestSO6.select().count() == 3
    assert TestSO7.select().count() == 2
    tc6b.destroySelf()
    assert TestSO5.select().count() == 1
    assert TestSO6.select().count() == 2
    assert TestSO7.select().count() == 2
    tc7b.destroySelf()
    assert TestSO5.select().count() == 1
    assert TestSO6.select().count() == 1
    assert TestSO7.select().count() == 1
    tc7a.destroySelf()
    assert TestSO5.select().count() == 0
    assert TestSO6.select().count() == 0
    assert TestSO7.select().count() == 0

def testForeignKeyDropTableCascade():
    if not supports('dropTableCascade'):
        return
    setupClass(TestSO7)
    setupClass(TestSO6)
    setupClass(TestSO5)

    tc5a = TestSO5(name='a')
    tc6a = TestSO6(name='1')
    tc5a.other = tc6a
    tc7a = TestSO7(name='2')
    tc6a.other = tc7a
    tc5a.another = tc7a
    tc5b = TestSO5(name='b')
    tc5c = TestSO5(name='c')
    tc6b = TestSO6(name='3')
    tc5c.other = tc6b
    assert TestSO5.select().count() == 3
    assert TestSO6.select().count() == 2
    assert TestSO7.select().count() == 1
    TestSO7.dropTable(cascade=True)
    assert TestSO5.select().count() == 3
    assert TestSO6.select().count() == 2
    tc6a.destroySelf()
    assert TestSO5.select().count() == 2
    assert TestSO6.select().count() == 1
    tc6b.destroySelf()
    assert TestSO5.select().count() == 1
    assert TestSO6.select().count() == 0
    assert iter(TestSO5.select()).next() == tc5b
    tc6c = TestSO6(name='3')
    tc5b.other = tc6c
    assert TestSO5.select().count() == 1
    assert TestSO6.select().count() == 1
    tc6c.destroySelf()
    assert TestSO5.select().count() == 0
    assert TestSO6.select().count() == 0

class TestSO8(SQLObject):
    name = StringCol(length=10, dbName='name_col')
    other = ForeignKey('TestSO9', default=None, cascade=False)

class TestSO9(SQLObject):
    name = StringCol(length=10, dbName='name_col')

def testForeignKeyDestroySelfRestrict():
    setupClass([TestSO9, TestSO8])

    tc8a = TestSO8(name='a')
    tc9a = TestSO9(name='1')
    tc8a.other = tc9a
    tc8b = TestSO8(name='b')
    tc9b = TestSO9(name='2')
    assert tc8a.other == tc9a
    assert tc8a.otherID == tc9a.id
    assert TestSO8.select().count() == 2
    assert TestSO9.select().count() == 2
    raises(Exception, tc9a.destroySelf)
    tc9b.destroySelf()
    assert TestSO8.select().count() == 2
    assert TestSO9.select().count() == 1
    tc8a.destroySelf()
    tc8b.destroySelf()
    tc9a.destroySelf()
    assert TestSO8.select().count() == 0
    assert TestSO9.select().count() == 0

class TestSO10(SQLObject):
    name = StringCol()

class TestSO11(SQLObject):
    name = StringCol()
    other = ForeignKey('TestSO10', default=None, cascade='null')

def testForeignKeySetNull():
    setupClass([TestSO10, TestSO11])
    obj1 = TestSO10(name='foo')
    obj2 = TestSO10(name='bar')
    dep1 = TestSO11(name='xxx', other=obj1)
    dep2 = TestSO11(name='yyy', other=obj1)
    dep3 = TestSO11(name='zzz', other=obj2)
    for name in 'xxx', 'yyy', 'zzz':
        assert len(list(TestSO11.selectBy(name=name))) == 1
    obj1.destroySelf()
    for name in 'xxx', 'yyy', 'zzz':
        assert len(list(TestSO11.selectBy(name=name))) == 1
    assert dep1.other is None
    assert dep2.other is None
    assert dep3.other is obj2

def testAsDict():
    setupGetters(TestSO1)
    bob = TestSO1.selectBy(name='bob')[0]
    assert bob.sqlmeta.asDict() == {
        'passwd': 'tbq', 'name': 'bob', 'id': bob.id}

def test_nonexisting_attr():
    setupClass(Student)
    try:
        Student.select(Student.q.nonexisting)
    except AttributeError:
        pass
    else:
        assert 0, "Expected an AttributeError"

class TestSO12(SQLObject):
    name = StringCol()
    value = IntCol(defaultSQL='1')

def test_defaultSQL():
    setupClass(TestSO12)
    test = TestSO12(name="test")
    assert test.value == 1

def test_connection_override():
    sqlhub.processConnection = connectionForURI('sqlite:///db1')
    class TestSO13(SQLObject):
        _connection = connectionForURI('sqlite:///db2')
    assert TestSO13._connection.uri() == 'sqlite:///db2'
    del sqlhub.processConnection
