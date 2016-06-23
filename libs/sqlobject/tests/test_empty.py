from sqlobject import *
from sqlobject.tests.dbtest import *

class EmptyClass(SQLObject):

    pass

def test_empty():
    if not supports('emptyTable'):
        return
    setupClass(EmptyClass)
    e1 = EmptyClass()
    e2 = EmptyClass()
    assert e1 != e2
    assert e1.id != e2.id
    assert e1 in list(EmptyClass.select())
    assert e2 in list(EmptyClass.select())
    e1.destroySelf()
    assert list(EmptyClass.select()) == [e2]
