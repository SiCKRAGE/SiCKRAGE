from sqlobject import *
from sqlobject.col import validators
from sqlobject.tests.dbtest import *

########################################
## Enum test
########################################

class Enum1(SQLObject):

    l = EnumCol(enumValues=['a', 'bcd', 'e'])

def testBad():
    setupClass(Enum1)
    for l in ['a', 'bcd', 'a', 'e']:
        Enum1(l=l)
    raises(
        (Enum1._connection.module.IntegrityError,
         Enum1._connection.module.ProgrammingError,
         validators.Invalid),
        Enum1, l='b')


class EnumWithNone(SQLObject):

    l = EnumCol(enumValues=['a', 'bcd', 'e', None])

def testNone():
    setupClass(EnumWithNone)
    for l in [None, 'a', 'bcd', 'a', 'e', None]:
        e = EnumWithNone(l=l)
        assert e.l == l


class EnumWithDefaultNone(SQLObject):

    l = EnumCol(enumValues=['a', 'bcd', 'e', None], default=None)

def testDefaultNone():
    setupClass(EnumWithDefaultNone)

    e = EnumWithDefaultNone()
    assert e.l == None


class EnumWithDefaultOther(SQLObject):

    l = EnumCol(enumValues=['a', 'bcd', 'e', None], default='a')

def testDefaultOther():
    setupClass(EnumWithDefaultOther)

    e = EnumWithDefaultOther()
    assert e.l == 'a'


class EnumUnicode(SQLObject):

    n = UnicodeCol()
    l = EnumCol(enumValues=['a', 'b'])

def testUnicode():
    setupClass(EnumUnicode)

    EnumUnicode(n=u'a', l='a')
    EnumUnicode(n=u'b', l=u'b')
    EnumUnicode(n=u'\u201c', l='a')
    EnumUnicode(n=u'\u201c', l=u'b')
