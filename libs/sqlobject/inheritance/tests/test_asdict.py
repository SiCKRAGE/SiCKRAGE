from sqlobject import *
from sqlobject.inheritance import *
from sqlobject.tests.dbtest import *

########################################
## sqlmeta.asDict
########################################

class InheritablePersonAD(InheritableSQLObject):
    firstName = StringCol()
    lastName = StringCol(alternateID=True, length=255)

class ManagerAD(InheritablePersonAD):
    department = StringCol()

class EmployeeAD(InheritablePersonAD):
    _inheritable = False
    position = StringCol()

def test_getColumns():
    setupClass([InheritablePersonAD, ManagerAD, EmployeeAD])

    for klass, columns in (
            (InheritablePersonAD, ['firstName', 'lastName']),
            (ManagerAD, ['department', 'firstName', 'lastName']),
            (EmployeeAD, ['firstName', 'lastName', 'position'])):
        _columns = klass.sqlmeta.getColumns().keys()
        _columns.sort()
        assert _columns == columns

def test_asDict():
    setupClass([InheritablePersonAD, ManagerAD, EmployeeAD], force=True)
    InheritablePersonAD(firstName='Oneof', lastName='Authors')
    ManagerAD(firstName='ManagerAD', lastName='The', department='Dep')
    EmployeeAD(firstName='Project', lastName='Leader', position='Project leader')

    assert InheritablePersonAD.get(1).sqlmeta.asDict() == \
        dict(firstName='Oneof', lastName='Authors', id=1)
    assert InheritablePersonAD.get(2).sqlmeta.asDict() == \
        dict(firstName='ManagerAD', lastName='The', department='Dep', id=2)
    assert InheritablePersonAD.get(3).sqlmeta.asDict() == \
        dict(firstName='Project', lastName='Leader', position='Project leader', id=3)
