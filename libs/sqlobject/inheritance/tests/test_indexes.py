from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject.inheritance import InheritableSQLObject


class InheritedPersonIndexGet(InheritableSQLObject):
    first_name  = StringCol(notNone=True, length=100)
    last_name   = StringCol(notNone=True, length=100)
    age         = IntCol()
    pk          = DatabaseIndex(first_name, last_name, unique=True)

class InheritedEmployeeIndexGet(InheritedPersonIndexGet):
    security_number = IntCol()
    experience      = IntCol()
    sec_index       = DatabaseIndex(security_number, unique=True)

class InheritedSalesManIndexGet(InheritedEmployeeIndexGet):
    _inheritable = False
    skill        = IntCol()


def test_index_get_1():
    setupClass([InheritedPersonIndexGet, InheritedEmployeeIndexGet, InheritedSalesManIndexGet])

    InheritedSalesManIndexGet(first_name='Michael', last_name='Pallin', age=65, security_number=2304,
        experience=2, skill=10)
    InheritedEmployeeIndexGet(first_name='Eric', last_name='Idle', age=63, security_number=3402,
        experience=9)
    InheritedPersonIndexGet(first_name='Terry', last_name='Guilliam', age=64)

    InheritedPersonIndexGet.pk.get('Michael', 'Pallin')
    InheritedEmployeeIndexGet.pk.get('Michael', 'Pallin')
    InheritedSalesManIndexGet.pk.get('Michael', 'Pallin')
    InheritedPersonIndexGet.pk.get('Eric', 'Idle')
    InheritedEmployeeIndexGet.pk.get('Eric', 'Idle')
    InheritedPersonIndexGet.pk.get(first_name='Terry', last_name='Guilliam')
    InheritedEmployeeIndexGet.sec_index.get(2304)
    InheritedEmployeeIndexGet.sec_index.get(3402)
    InheritedSalesManIndexGet.sec_index.get(2304)
    InheritedSalesManIndexGet.sec_index.get(3402)
