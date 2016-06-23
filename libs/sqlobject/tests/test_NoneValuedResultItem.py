'''Test that selectResults handle NULL values
from, for example, outer joins.'''
from sqlobject import *
from sqlobject.tests.dbtest import *

class TestComposer(SQLObject):
    name = StringCol()

class TestWork(SQLObject):
    class sqlmeta:
        idName = "work_id"

    composer = ForeignKey('TestComposer')
    title = StringCol()

def test1():
    setupClass([TestComposer,
                TestWork])

    c = TestComposer(name='Mahler, Gustav')
    w = TestWork(composer=c, title='Symphony No. 9')
    c2 = TestComposer(name='Bruckner, Anton')
    # but don't add any works for Bruckner

    # do a left join, a common use case that often involves NULL results
    s = TestWork.select(join=sqlbuilder.LEFTJOINOn(TestComposer, TestWork,
                        TestComposer.q.id==TestWork.q.composerID))
    assert tuple(s)==(w, None)
