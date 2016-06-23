+++++++++++++
SQLObject FAQ
+++++++++++++

.. contents::

SQLExpression
-------------

In `SomeTable.select(SomeTable.q.Foo > 30)` why doesn't the inner parameter,
`SomeTable.q.Foo > 30`, get evaluated to some boolean value?

`q` is an object that returns special attributes of type
`sqlbuilder.SQLExpression`. SQLExpression is a special class that overrides
almost all Python magic methods and upon any operation instead of
evaluating it constructs another instance of SQLExpression that remembers
what operation it has to do. Similar to a symbolic algebra. Example:

   SQLExpression("foo") > 30

produces SQLExpression("foo", ">", 30) (well, it really produces
SQLExpression(SQLExpression("foo")...))

How does the select(...) method know what to do?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In short, select() recursively evaluates the top-most SQLExpression to a
string:

   SQLExpression("foo", ">", 30) => "foo > 30"

and passes the result as a string to the SQL backend.

The longer but more detailed and correct explanation is that select()
produces an instance of SelectResults_ class that upon being iterated over
produces an instance of Iteration class that upon calling its next()
method (it is iterator!) construct the SQL query string, passes it to the
backend, fetches the results, wraps every row as SQLObject instance and
passes them back to the user.

.. _SelectResults: SelectResults.html

For the details of the implementation see sqlobject/main.py for SQLObject,
sqlobject/sqlbuilder.py for SQLExpression, sqlobject/dbconnection.py for
DBConnection class (that constructs the query strings) and Iteration class,
and different subdirectories of sqlobject for concrete implementations of
connection classes - different backends require different query strings.

Why there is no __len__?
------------------------

There are reasons why there is no __len__ method, though many people think
having those make them feel more integrated into Python.

One is that len(foo) is expected to be fast, but issuing a COUNT query can
be slow.  Worse, often this causes the database to do essentially redundant
work when the actual query is performed (generally taking the len of a
sequence is followed by accessing items from that sequence).

Another is that list(foo) implicitly tries to do a len first, as an
optimization (because len is expected to be cheap -- see previous point).
Worse, it swallows *all* exceptions that occur during that call to __len__,
so if it fails (e.g. there's a typo somewhere in the query), the original
cause is silently discarded, and instead you're left with mysterious errors
like "current transaction is aborted, commands ignored until end of
transaction block" for no apparent reason.

How can I do a LEFT JOIN?
-------------------------

The short: you can't.  You don't need to.  That's a relational way of
thinking, not an object way of thinking.  But it's okay!  It's not
hard to do the same thing, even if it's not with the same query.

For these examples, imagine you have a bunch of customers, with
contacts.  Not all customers have a contact, some have several.  The
left join would look like::

    SELECT customer.id, customer.first_name, customer.last_name,
           contact.id, contact.address
    FROM customer
    LEFT JOIN contact ON contact.customer_id = customer.id

Simple
~~~~~~

::

    for customer in Customer.select():
        print customer.firstName, customer.lastName
        for contact in customer.contacts:
            print '   ', contact.phoneNumber

The effect is the same as the left join -- you get all the customers,
and you get all their contacts.  The problem, however, is that you
will be executing more queries -- a query for each customer to fetch
the contacts -- where with the left join you'd only do one query.  The
actual amount of information returned from the database will be the
same.  There's a good chance that this won't be significantly slower.
I'd advise doing it this way unless you hit an actual performance
problem.

Efficient
~~~~~~~~~

Lets say you really don't want to do all those queries.  Okay, fine::

    custContacts = {}
    for contact in Contact.select():
        custContacts.setdefault(contact.customerID, []).append(contact)
    for customer in Customer.select():
        print customer.firstName, customer.lastName
        for contact in custContacts.get(customer.id, []):
            print '   ', contact.phoneNumber

This way there will only be at most two queries.  It's a little more
crude, but this is an optimization, and optimizations often look less
than pretty.

But, say you don't want to get everyone, just some group of people
(presumably a large enough group that you still need this
optimization)::

    query = Customer.q.firstName.startswith('J')
    custContacts = {}
    for contact in Contact.select(AND(Contact.q.customerID == Customer.q.id,
                                      query)):
        custContacts.setdefault(contact.customerID, []).append(contact)
    for customer in Customer.select(query):
        print customer.firstName, customer.lastName
        for contact in custContacts.get(customer.id, []):
            print '   ', contact.phoneNumber

SQL-wise
~~~~~~~~

Use LEFTJOIN() from SQLBuilder_.


How can I join a table with itself?
-----------------------------------

Use Alias from SQLBuilder_. See example_.

.. _SQLBuilder: SQLBuilder.html
.. _example: SQLObject.html#how-can-i-join-a-table-with-itself


How can I define my own intermediate table in my Many-to-Many relationship?
---------------------------------------------------------------------------

.. note::
  In User and Role, SQLRelatedJoin is used with createRelatedTable=False
  so the intermediate table is not created automatically. We also set the
  intermediate table name with intermediateTable='user_roles'.
  UserRoles is the definition of our intermediate table.
  UserRoles creates a unique index to make sure we don't have duplicate
  data in the database.
  We also added an extra field called active which has a boolean value.
  The active column might be used to activate/deactivate a given role for
  a user in this example.
  Another common field to add in this an intermediate table might be a sort
  field.
  If you want to get a list of rows from the intermediate table directly
  add a MultipleJoin to User or Role class.

We'll expand on the User and Role example and define our own UserRoles class which
will be the intermediate table for the User and Role Many-to-Many relationship.

Example::

    >>> class User(SQLObject):
    ...     class sqlmeta:
    ...         table = "user_table"
    ...     username = StringCol(alternateID=True, length=20)
    ...     roles = SQLRelatedJoin('Role',
    ...         intermediateTable='user_roles',
    ...         createRelatedTable=False)

    >>> class Role(SQLObject):
    ...     name = StringCol(alternateID=True, length=20)
    ...     users = SQLRelatedJoin('User',
    ...         intermediateTable='user_roles',
    ...         createRelatedTable=False)

    >>> class UserRoles(SQLObject):
    ...     class sqlmeta:
    ...         table = "user_roles"
    ...     user = ForeignKey('User', notNull=True, cascade=True)
    ...     role = ForeignKey('Role', notNull=True, cascade=True)
    ...     active = BoolCol(notNull=True, default=False)
    ...     unique = index.DatabaseIndex(user, role, unique=True)


How Does Inheritance Work?
--------------------------

SQLObject is not intended to represent every Python inheritance
structure in an RDBMS -- rather it is intended to represent RDBMS
structures as Python objects.  So lots of things you can do in Python
you can't do with SQLObject classes.  However, some form of
inheritance is possible.

One way of using this is to create local conventions.  Perhaps::

  class SiteSQLObject(SQLObject):
      _connection = DBConnection.MySQLConnection(user='test', db='test')
      _style = MixedCaseStyle()

      # And maybe you want a list of the columns, to autogenerate
      # forms from:
      def columns(self):
          return [col.name for col in self._columns]

Since SQLObject doesn't have a firm introspection mechanism (at least
not yet) the example shows the beginnings of a bit of ad hoc
introspection (in this case exposing the ``_columns`` attribute in a
more pleasing/public interface).

However, this doesn't relate to *database* inheritance at all, since
we didn't define any columns.  What if we do? ::

  class Person(SQLObject):
      firstName = StringCol()
      lastName = StringCol()

  class Employee(Person):
      position = StringCol()

Unfortunately, the resultant schema probably doesn't look like what
you might have wanted::

  CREATE TABLE person (
      id INT PRIMARY KEY,
      first_name TEXT,
      last_name TEXT
  );

  CREATE TABLE employee (
      id INT PRIMARY KEY
      first_name TEXT,
      last_name TEXT,
      position TEXT
  )


All the columns from ``person`` are just repeated in the ``employee``
table.  What's more, an ID for a Person is distinct from an ID for an
employee, so for instance you must choose ``ForeignKey("Person")`` or
``ForeignKey("Employee")``, you can't have a foreign key that
sometimes refers to one, and sometimes refers to the other.

Altogether, not very useful.  You probably want a ``person`` table,
and then an ``employee`` table with a one-to-one relation between the
two.  Of course, you can have that, just create the appropriate
classes/tables -- but it will appear as two distinct classes, and
you'd have to do something like ``Person(1).employee.position``.  Of
course, you can always create the necessary shortcuts, like::

  class Person(SQLObject):
      firstName = StringCol()
      lastName = StringCol()

      def _get_employee(self):
          value = Employee.selectBy(person=self)
          if value:
              return value[0]
          else:
              raise AttributeError, '%r is not an employee' % self
      def _get_isEmployee(self):
          value = Employee.selectBy(person=self)
          # turn into a bool:
          return not not value
      def _set_isEmployee(self, value):
          if value:
              # Make sure we are an employee...
              if not self.isEmployee:
                  Empoyee.new(person=self, position=None)
          else:
              if self.isEmployee:
                  self.employee.destroySelf()
      def _get_position(self):
          return self.employee.position
      def _set_position(self, value):
          self.employee.position = value

  class Employee(SQLObject):
      person = ForeignKey('Person')
      position = StringCol()

There is also another kind of inheritance. See Inheritance.html_

.. _Inheritance.html: Inheritance.html


Composite/Compound Attributes
-----------------------------

A composite attribute is an attribute formed from two columns.  For
example::

  CREATE TABLE invoice_item (
      id INT PRIMARY KEY,
      amount NUMERIC(10, 2),
      currency CHAR(3)
  );

Now, you'll probably want to deal with one amount/currency value,
instead of two columns.  SQLObject doesn't directly support this, but
it's easy (and encouraged) to do it on your own::

  class InvoiceItem(SQLObject):
      amount = Currency()
      currency = StringChar(length=3)

      def _get_price(self):
          return Price(self.amount, self.currency)
      def _set_price(self, price):
          self.amount = price.amount
          self.currency = price.currency

  class Price(object):
      def __init__(self, amount, currency):
          self._amount = amount
          self._currency = currency

      def _get_amount(self):
          return self._amount
      amount = property(_get_amount)

      def _get_currency(self):
          return self._currency
      currency = property(_get_currency)

      def __repr__(self):
          return '<Price: %s %s>' % (self.amount, self.currency)

You'll note we go to some trouble to make sure that ``Price`` is an
immutable object.  This is important, because if ``Price`` wasn't and
someone changed an attribute, the containing ``InvoiceItem`` instance
wouldn't detect the change and update the database.  (Also, since
``Price`` doesn't subclass ``SQLObject``, we have to be explicit about
creating properties)  Some people refer to this sort of class as a
*Value Object*, that can be used similar to how an integer or string
is used.

You could also use a mutable composite class::

  class Address(SQLObject):
      street = StringCol()
      city = StringCol()
      state = StringCol(length=2)

      latitude = FloatCol()
      longitude = FloatCol()

      def _init(self, id):
          SQLObject._init(self, id)
          self._coords = SOCoords(self)

      def _get_coords(self):
          return self._coords

  class SOCoords(object):
      def __init__(self, so):
          self._so = so

      def _get_latitude(self):
          return self._so.latitude
      def _set_latitude(self, value):
          self._so.latitude = value
      latitude = property(_get_latitude, set_latitude)

      def _get_longitude(self):
          return self._so.longitude
      def _set_longitude(self, value):
          self._so.longitude = value
      longitude = property(_get_longitude, set_longitude)


Pretty much a proxy, really, but ``SOCoords`` could contain other
logic, could interact with non-SQLObject-based latitude/longitude
values, or could be used among several objects that have
latitude/longitude columns.


Non-Integer IDs
---------------

Yes, you can use non-integer IDs.

If you use non-integer IDs, you will not be able to use automatic ``CREATE
TABLE`` generation (i.e., ``createTable``); SQLObject can create tables
with int or str IDs.  You also will have to give your own ID values when
creating an object, like::

    color = Something(id="blue", r=0, b=100, g=0)

IDs are, and always will in future versions, be considered immutable.
Right now that is not enforced; you can assign to the ``id``
attribute.  But if you do you'll just mess everything up.  This will
probably be taken away sometime to avoid possibly confusing bugs
(actually, assigning to ``id`` is almost certain to cause confusing
bugs).

If you are concerned about enforcing the type of IDs (which can be a
problem even with integer IDs) you may want to do this::

    def Color(SQLObject):
        def _init(self, id, connection=None):
            id = str(id)
            SQLObject._init(self, id, connection)

Instead of ``str()`` you may use ``int()`` or whatever else you want.
This will be resolved in a future version when ID column types can be
declared like other columns.

Additionally you can set idType=str in you SQLObject class.


Binary Values
-------------

Binary values can be difficult to store in databases, as SQL doesn't
have a widely-implemented way to express binaries as literals, and
there's differing support in database.

The module sqlobject.col defines validators and column classes that
to some extent support binary values. There is BLOBCol that extends
StringCol and allow to store binary values; currently it works only
with PostgreSQL and MySQL. PickleCol extends BLOBCol and allows to store
any object in the column; the column, naturally, pickles the object upon
assignment and unpickles it upon retrieving the data from the DB.

Another possible way to keep binary data in a database is by using
encoding.  Base 64 is a good encoding, reasonably compact but also
safe.  As an example, imagine you want to store images in the
database::

  class Image(SQLObject):

      data = StringCol()
      height = IntCol()
      width = IntCol()

      def _set_data(self, value):
          self._SO_set_data(value.encode('base64'))

      def _get_data(self, value):
          return self._SO_get_data().decode('base64')


Reloading Modules
-----------------

If you've tried to reload a module that defines SQLObject subclasses,
you've probably encountered various odd errors.  The short answer: you
can't reload these modules.

The long answer: reloading modules in Python doesn't work very well.
Reloading actually means *re-running* the module.  Every ``class``
statement creates a class -- but your old classes don't disappear.
When you reload a module, new classes are created, and they take over
the names in the module.

SQLObject, however, doesn't search the names in a module to find a
class.  When you say ``ForeignKey('SomeClass')``, SQLObject looks for
any SQLObject subclass anywhere with the name ``SomeClass``.  This is
to avoid problems with circular imports and circular dependencies, as
tables have forward- and back-references, and other circular
dependencies.  SQLObject resolves these dependencies lazily.

But when you reload a module, suddenly there will be two SQLObject
classes in the process with the same name.  SQLObject doesn't know
that one of them is obsolete.  And even if it did, it doesn't know
every other place in the system that has a reference to that obsolete
class.

For this reason and several others, reloading modules is highly
error-prone and difficult to support.

Python Keywords
---------------

If you have a table column that is a Python keyword, you should know
that the Python attribute doesn't have to match the name of the
column.  See `Irregular Naming`_ in the documentation.

.. _Irregular Naming: SQLObject.html#irregular-naming

Lazy Updates and Insert
-----------------------

`Lazy updates <SQLObject.html#lazy-updates>`_ allow you to defer
sending ``UPDATES`` until you synchronize the object.  However, there
is no way to do a lazy insert; as soon as you create an instance the
``INSERT`` is executed.

The reason for this limit is that each object needs a database ID, and
in many databases you cannot attain an ID until you create a row.

Mutually referencing tables
---------------------------

How can I create mutually referencing tables? For the code::

    class Person(SQLObject):
        role = ForeignKey("Role")

    class Role(SQLObject):
        person = ForeignKey("Person")

    Person.createTable()
    Role.createTable()

Postgres raises ProgrammingError: ERROR: relation "role" does not exist.

The correct way is to delay constraints creation until all tables are
created::

    class Person(SQLObject):
        role = ForeignKey("Role")

    class Role(SQLObject):
        person = ForeignKey("Person")

    constraints = Person.createTable(applyConstraints=False)
    constraints += Role.createTable(applyConstraints=False)

    for constraint in constraints:
        connection.query(constraint)

What about GROUP BY, UNION, etc?
--------------------------------

In short - not every query can be represented in SQLObject. SQLOBject's
objects are instances of "table" clasess::

    class MyTable(SQLObject):
        ...

    my_table_row = MyTable.get(id)

Now my_table_row is an instance of MyTable class and represents a row in
the my_table table. But for a statement with GROUP BY like this::

    SELECT my_column, COUNT(*) FROM my_table GROUP BY my_column;

there is no table, there is no corresponding "table" class, and SQLObject
cannot return a list of meaningful objects.

You can use a lower-level machinery available in SQLBuilder_.

How to do mass-insertion?
-------------------------

Mass-insertion using high-level API in SQLObject is slow. There are many
reasons for that. First, on creation SQLObject instances pass all values
through validators/converters which is convenient but takes time.
Second, after an INSERT query SQLObject executes a SELECT query to get
back autogenerated values (id and timestamps). Third, there is caching
and cache maintaining. Most of this is unnecessary for mass-insertion,
hence high-level API is unsuitable.

Less convenient (no validators) but much faster API is Insert_ from
SQLBuilder_.

.. _Insert: SQLBuilder.html#insert

How can I specify the MySQL engine to use, or tweak other SQL-engine specific features?
---------------------------------------------------------------------------------------

You can *ALTER* the table just after creation using the ``sqlmeta``
attribute ``createSQL``, for example::

    class SomeObject(SQLObject):
        class sqlmeta:
            createSQL = { 'mysql' : 'ALTER TABLE some_object ENGINE InnoDB' }
        # your columns here

Maybe you want to specify the charset too? No problem::

    class SomeObject(SQLObject):
        class sqlmeta:
            createSQL = { 'mysql' : [
                'ALTER TABLE some_object ENGINE InnoDB',
                '''ALTER TABLE some_object CHARACTER SET utf8
                    COLLATE utf8_estonian_ci''']
                }

.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=74338&type=10
   :target: http://sourceforge.net/projects/sqlobject
   :class: noborder
   :align: center
   :height: 15
   :width: 80
   :alt: Get SQLObject at SourceForge.net. Fast, secure and Free Open Source software downloads
