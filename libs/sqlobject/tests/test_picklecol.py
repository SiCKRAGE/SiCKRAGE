from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Pickle columns
########################################

class PickleData:
    pi = 3.14156
    def __init__(self):
        self.question = 'The Ulimate Question of Life, the Universe and Everything'
        self.answer = 42

class PickleContainer(SQLObject):
    pickledata = PickleCol(default=None, length=65535)

def test_pickleCol():
    if not supports('blobData'):
        return
    setupClass([PickleContainer], force=True)
    mypickledata = PickleData()

    ctnr = PickleContainer(pickledata=mypickledata)
    iid = ctnr.id

    PickleContainer._connection.cache.clear()

    ctnr2 = PickleContainer.get(iid)
    s2 = ctnr2.pickledata

    assert isinstance(s2, PickleData)
    assert isinstance(s2.pi, float)
    assert isinstance(s2.question, str)
    assert isinstance(s2.answer, int)
    assert s2.pi == mypickledata.pi
    assert s2.question == mypickledata.question
    assert s2.answer == mypickledata.answer
