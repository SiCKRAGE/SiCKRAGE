from sqlobject import *
from sqlobject.col import validators
from sqlobject.tests.dbtest import *

########################################
## Validation/conversion
########################################

class SOTestValidator(validators.Validator):
    def to_python(self, value, state):
        if value:
            self.save_value.append(value)
            return 1
        return value

    def from_python(self, value, state):
        if value:
            self.save_value.append(value)
            return 2
        return value

validator1 = SOTestValidator(save_value=[])
validator2 = SOTestValidator(save_value=[])


class SOValidation(SQLObject):

    name = StringCol(validator=validators.PlainText(),
        default='x', dbName='name_col')
    name2 = StringCol(validator=validators.ConfirmType(type=str), default='y')
    name3 = IntCol(validator=validators.Wrapper(fromPython=int), default=100)
    name4 = FloatCol(default=2.718)
    name5 = PickleCol(default=None)
    name6 = BoolCol(default=None)
    name7 = UnicodeCol(default=None)
    name8 = IntCol(default=None)
    name9 = IntCol(validator=validator1, validator2=validator2, default=0)

class SOValidationTest(object):
    def __init__(self, value):
        self.value = value

class SOValidationTestUnicode(SOValidationTest):
    def __unicode__(self):
        return self.value

class SOValidationTestInt(SOValidationTest):
    def __int__(self):
        return self.value

class SOValidationTestBool(SOValidationTest):
    def __nonzero__(self):
        return self.value

class SOValidationTestFloat(SOValidationTest):
    def __float__(self):
        return self.value

class TestValidation:

    def setup_method(self, meth):
        setupClass(SOValidation)

    def test_validate(self):
        t = SOValidation(name='hey')
        raises(validators.Invalid, setattr, t, 'name', '!!!')
        t.name = 'you'
        assert t.name == 'you'

    def test_confirmType(self):
        t = SOValidation(name2='hey')
        raises(validators.Invalid, setattr, t, 'name2', 1)
        raises(validators.Invalid, setattr, t, 'name3', '1')
        raises(validators.Invalid, setattr, t, 'name4', '1')
        raises(validators.Invalid, setattr, t, 'name6', '1')
        raises(validators.Invalid, setattr, t, 'name7', 1)
        t.name2 = 'you'
        assert t.name2 == 'you'

        for name, cls, value in (
                ('name4', SOValidationTestFloat, 1.1),
                ('name6', SOValidationTestBool, True),
                ('name7', SOValidationTestUnicode, u'test'),
                ('name8', SOValidationTestInt, 1)):
            setattr(t, name, cls(value))
            assert getattr(t, name) == value

    def test_wrapType(self):
        t = SOValidation(name3=1)
        raises(validators.Invalid, setattr, t, 'name3', 'x')
        t.name3 = 1L
        assert t.name3 == 1
        t.name3 = 0
        assert t.name3 == 0

    def test_emptyValue(self):
        t = SOValidation(name5={})
        assert t.name5 == {}

    def test_validator2(self):
        t = SOValidation(name9=1)
        t = SOValidation(name9=2)
        assert validator1.save_value == [2, 2, 2, 2, 2, 2]
        assert validator2.save_value == [1, 1, 1, 2, 1, 1]
