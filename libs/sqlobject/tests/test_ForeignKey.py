from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject.tests.dbtest import InstalledTestDatabase

class TestComposerKey(SQLObject):
    name = StringCol()
    id2 = IntCol(default=None, unique=True)

class TestWorkKey(SQLObject):
    class sqlmeta:
        idName = "work_id"

    composer = ForeignKey('TestComposerKey', cascade=True)
    title = StringCol()

class TestWorkKey2(SQLObject):
    title = StringCol()

class TestOtherColumn(SQLObject):
    key1 = ForeignKey('TestComposerKey', default=None)
    key2 = ForeignKey('TestComposerKey', refColumn='id2', default=None)

def test1():
    setupClass([TestComposerKey, TestWorkKey])

    c = TestComposerKey(name='Mahler, Gustav')
    w1 = TestWorkKey(composer=c, title='Symphony No. 9')
    w2 = TestWorkKey(composer=None, title=None)

    # Select by usual way
    s = TestWorkKey.selectBy(composerID=c.id, title='Symphony No. 9')
    assert s.count() == 1
    assert s[0]==w1
    # selectBy object.id
    s = TestWorkKey.selectBy(composer=c.id, title='Symphony No. 9')
    assert s.count() == 1
    assert s[0]==w1
    # selectBy object
    s = TestWorkKey.selectBy(composer=c, title='Symphony No. 9')
    assert s.count() == 1
    assert s[0]==w1
    # selectBy id
    s = TestWorkKey.selectBy(id=w1.id)
    assert s.count() == 1
    assert s[0]==w1
    # is None handled correctly?
    s = TestWorkKey.selectBy(composer=None, title=None)
    assert s.count() == 1
    assert s[0]==w2

    s = TestWorkKey.selectBy()
    assert s.count() == 2

    # select with objects
    s = TestWorkKey.select(TestWorkKey.q.composerID==c.id)
    assert s.count() == 1
    assert s[0]==w1
    s = TestWorkKey.select(TestWorkKey.q.composer==c.id)
    assert s.count() == 1
    assert s[0]==w1
    s = TestWorkKey.select(TestWorkKey.q.composerID==c)
    assert s.count() == 1
    assert s[0]==w1
    s = TestWorkKey.select(TestWorkKey.q.composer==c)
    assert s.count() == 1
    assert s[0]==w1
    s = TestWorkKey.select((TestWorkKey.q.composer==c) & \
        (TestWorkKey.q.title=='Symphony No. 9'))
    assert s.count() == 1
    assert s[0]==w1

def test2():
    TestWorkKey._connection = getConnection()
    InstalledTestDatabase.drop(TestWorkKey)
    setupClass([TestComposerKey, TestWorkKey2], force=True)
    TestWorkKey2.sqlmeta.addColumn(ForeignKey('TestComposerKey'), changeSchema=True)

def test_otherColumn():
    setupClass([TestComposerKey, TestOtherColumn])
    test_composer1 = TestComposerKey(name='Test1')
    test_composer2 = TestComposerKey(name='Test2', id2=2)
    test_fkey = TestOtherColumn(key1=test_composer1)
    test_other = TestOtherColumn(key2=test_composer2.id2)
    getConnection().cache.clear()
    assert test_fkey.key1 == test_composer1
    assert test_other.key2 == test_composer2
