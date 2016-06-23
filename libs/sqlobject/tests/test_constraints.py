from sqlobject.constraints import *
from sqlobject.tests.dbtest import *

def test_constraints():
    obj = 'Test object'
    col = Dummy(name='col')
    isString(obj, col, 'blah')
    raises(BadValue, isString, obj, col, 1)
    # @@: Should this really be an error?
    raises(BadValue, isString, obj, col, u'test!')
    #isString(obj, col, u'test!')

    raises(BadValue, notNull, obj, col, None)
    raises(BadValue, isInt, obj, col, 1.1)
    isInt(obj, col, 1)
    isInt(obj, col, 1L)
    isFloat(obj, col, 1)
    isFloat(obj, col, 1L)
    isFloat(obj, col, 1.2)
    raises(BadValue, isFloat, obj, col, '1.0')

    # @@: Should test isBool, but I don't think isBool is right

    lst = InList(('a', 'b', 'c'))
    lst(obj, col, 'a')
    raises(BadValue, lst, obj, col, ('a', 'b', 'c'))
    raises(BadValue, lst, obj, col, 'A')

    maxlen = MaxLength(2)
    raises(BadValue, maxlen, obj, col, '123')
    maxlen(obj, col, '12')
    maxlen(obj, col, (1,))
    raises(BadValue, maxlen, obj, col, 1)
