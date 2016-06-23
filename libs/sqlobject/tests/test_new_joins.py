from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Joins
########################################

class PersonJoinerNew(SQLObject):

    name = StringCol(length=40, alternateID=True)
    addressJoiners = ManyToMany('AddressJoinerNew')

class AddressJoinerNew(SQLObject):

    zip = StringCol(length=5, alternateID=True)
    personJoiners = ManyToMany('PersonJoinerNew')

class ImplicitJoiningSONew(SQLObject):
    foo = ManyToMany('Bar')

class ExplicitJoiningSONew(SQLObject):
    foo = OneToMany('Bar')

class TestJoin:

    def setup_method(self, meth):
        setupClass(PersonJoinerNew)
        setupClass(AddressJoinerNew)
        for n in ['bob', 'tim', 'jane', 'joe', 'fred', 'barb']:
            PersonJoinerNew(name=n)
        for z in ['11111', '22222', '33333', '44444']:
            AddressJoinerNew(zip=z)

    def test_join(self):
        b = PersonJoinerNew.byName('bob')
        assert list(b.addressJoiners) == []
        z = AddressJoinerNew.byZip('11111')
        b.addressJoiners.add(z)
        self.assertZipsEqual(b.addressJoiners, ['11111'])
        print str(z.personJoiners), repr(z.personJoiners)
        self.assertNamesEqual(z.personJoiners, ['bob'])
        z2 = AddressJoinerNew.byZip('22222')
        b.addressJoiners.add(z2)
        print str(b.addressJoiners)
        self.assertZipsEqual(b.addressJoiners, ['11111', '22222'])
        self.assertNamesEqual(z2.personJoiners, ['bob'])
        b.addressJoiners.remove(z)
        self.assertZipsEqual(b.addressJoiners, ['22222'])
        self.assertNamesEqual(z.personJoiners, [])

    def assertZipsEqual(self, zips, dest):
        assert [a.zip for a in zips] == dest

    def assertNamesEqual(self, people, dest):
        assert [p.name for p in people] == dest

    def test_joinAttributeWithUnderscores(self):
        # Make sure that the implicit setting of joinMethodName works
        assert hasattr(ImplicitJoiningSONew, 'foo')
        assert not hasattr(ImplicitJoiningSONew, 'bars')

        # And make sure explicit setting also works
        assert hasattr(ExplicitJoiningSONew, 'foo')
        assert not hasattr(ExplicitJoiningSONew, 'bars')


class PersonJoinerNew2(SQLObject):

    name = StringCol('name', length=40, alternateID=True)
    addressJoiner2s = OneToMany('AddressJoinerNew2')

class AddressJoinerNew2(SQLObject):

    class sqlmeta:
        defaultOrder = ['-zip', 'plus4']

    zip = StringCol(length=5)
    plus4 = StringCol(length=4, default=None)
    personJoinerNew2 = ForeignKey('PersonJoinerNew2')

class TestJoin2:

    def setup_method(self, meth):
        setupClass([PersonJoinerNew2, AddressJoinerNew2])
        p1 = PersonJoinerNew2(name='bob')
        p2 = PersonJoinerNew2(name='sally')
        for z in ['11111', '22222', '33333']:
            a = AddressJoinerNew2(zip=z, personJoinerNew2=p1)
            #p1.addAddressJoinerNew2(a)
        AddressJoinerNew2(zip='00000', personJoinerNew2=p2)

    def test_basic(self):
        bob = PersonJoinerNew2.byName('bob')
        sally = PersonJoinerNew2.byName('sally')
        print bob.addressJoiner2s
        print bob
        assert len(list(bob.addressJoiner2s)) == 3
        assert len(list(sally.addressJoiner2s)) == 1
        bob.addressJoiner2s[0].destroySelf()
        assert len(list(bob.addressJoiner2s)) == 2
        z = bob.addressJoiner2s[0]
        z.zip = 'xxxxx'
        id = z.id
        del z
        z = AddressJoinerNew2.get(id)
        assert z.zip == 'xxxxx'

    def test_defaultOrder(self):
        p1 = PersonJoinerNew2.byName('bob')
        assert ([i.zip for i in p1.addressJoiner2s]
                == ['33333', '22222', '11111'])


_personJoiner3_getters = []
_personJoiner3_setters = []

class PersonJoinerNew3(SQLObject):

    name = StringCol('name', length=40, alternateID=True)
    addressJoinerNew3s = OneToMany('AddressJoinerNew3')

class AddressJoinerNew3(SQLObject):

    zip = StringCol(length=5)
    personJoinerNew3 = ForeignKey('PersonJoinerNew3')

    def _get_personJoinerNew3(self):
        value = self._SO_get_personJoinerNew3()
        _personJoiner3_getters.append((self, value))
        return value

    def _set_personJoinerNew3(self, value):
        self._SO_set_personJoinerNew3(value)
        _personJoiner3_setters.append((self, value))

class TestJoin3:

    def setup_method(self, meth):
        setupClass([PersonJoinerNew3, AddressJoinerNew3])
        p1 = PersonJoinerNew3(name='bob')
        p2 = PersonJoinerNew3(name='sally')
        for z in ['11111', '22222', '33333']:
            a = AddressJoinerNew3(zip=z, personJoinerNew3=p1)
        AddressJoinerNew3(zip='00000', personJoinerNew3=p2)

    def test_accessors(self):
        assert len(list(_personJoiner3_getters)) == 0
        assert len(list(_personJoiner3_setters)) == 4
        bob = PersonJoinerNew3.byName('bob')
        for addressJoiner3 in bob.addressJoinerNew3s:
            addressJoiner3.personJoinerNew3
        assert len(list(_personJoiner3_getters)) == 3
        assert len(list(_personJoiner3_setters)) == 4
