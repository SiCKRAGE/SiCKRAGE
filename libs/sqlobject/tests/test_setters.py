from sqlobject import *
from sqlobject.tests.dbtest import *

class TestPlainAndNonPlainSetter(SQLObject):
    firstName = StringCol(length=50, dbName='fname_col', default=None)
    lastName = StringCol(length=50, dbName='lname_col', default=None)
    
    def _set_name(self, v):
        firstName, lastName = v.split()
        self.firstName = firstName
        self.lastName = lastName
    
    def _get_name(self):
        return "%s %s" % (self.firstName, self.lastName)

def test_create():
    setupClass(TestPlainAndNonPlainSetter)
    t = TestPlainAndNonPlainSetter(name='John Doe')
    assert t.firstName == 'John'
    assert t.lastName == 'Doe'
    assert t.name == 'John Doe'