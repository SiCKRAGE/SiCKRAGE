:Author: Daniel Savard, XSOLI Inc.

Inheritance
-----------

Why
~~~

Imagine you have a list of persons, and every person plays a certain role.
Some persons are students, some are professors, some are employees. Every
role has different attributes. Students are known by their department and
year. Professors have a department (some attributes are common for all or some
roles), timetable and other attributes.

How does one implement this in SQLObject? Well, the obvious approach is to
create a table Person with a column that describes or name the role, and a
table for an every role. Then one must write code that interprets and
dereferences the role column.

Well, the inheritance machinery described below does exactly this! Only it
does it automagically and mostly transparent to the user.

First, you create a table Person. Nothing magical here::

    class Person(SQLObject):
        name = StringCol()
        age = FloatCol()

Now you need a hierarchy of roles::

    class Role(InheritableSQLObject):
        department = StringCol()

The magic starts here! You inherit the class from the special root class
``InheritableSQLObject`` and provide a set of attributes common for all
roles. Other roles must be inherited from Role::

    class Student(Role):
        year = IntCol()

    class Professor(Role):
        timetable = StringCol()

Now you want a column in Person that can be interpreted as the role. Easy::

    class Person(SQLObject):
        name = StringCol()
        age = FloatCol()
        role = ForeignKey("Role")

That's all, really! When asked for its role, Person returns the value of
its .role attribute dereferenced and interpreted. Instead of returning an
instance of class Role it returns an instance of the corresponding subclass
- a Student or a Professor.

This is a brief explanation based on a task people meet most often, but of
course it can be used far beyond the person/role task. I also omitted all
details in the explanation. Now look at the real working program::

    from sqlobject import *
    from sqlobject.inheritance import InheritableSQLObject

    __connection__ = "sqlite:/:memory:"

    class Role(InheritableSQLObject):
       department = StringCol()

    class Student(Role):
       year = IntCol()

    class Professor(Role):
       timetable = StringCol(default=None)

    class Person(SQLObject):
       name = StringCol()
       age = FloatCol()
       role = ForeignKey("Role", default=None)

    Role.createTable()
    Student.createTable()
    Professor.createTable()
    Person.createTable()

    first_year = Student(department="CS", year=1)
    lecturer = Professor(department="Mathematics")

    student = Person(name="A student", age=21, role=first_year)
    professor = Person(name="A professor", age=42, role=lecturer)

    print student.role
    print professor.role

It prints::

    <Student 1 year=1 department='CS'>
    <Professor 2 timetable=None department='Mathematics'>

You can get the list of all available roles::

    print list(Role.select())

It prints::

    [<Student 1 year=1 department='CS'>, <Professor 2 timetable=None department='Mathematics'>]

Look - you have gotten a list of Role's subclasses!

If you add a MultipleJoin column to Role, you can list all persons for a
given role::

    class Role(InheritableSQLObject):
        department = StringCol()
        persons = MultipleJoin("Person")

    for role in Role.select():
        print role.persons

It prints::

    [<Person 1 name='A student' age=21.0 roleID=1>]
    [<Person 2 name='A professor' age=42.0 roleID=2>]

If you you want your persons to have many roles, use RelatedJoin::

    class Role(InheritableSQLObject):
        department = StringCol()
        persons = RelatedJoin("Person")

    class Student(Role):
        year = IntCol()

    class Professor(Role):
        timetable = StringCol(default=None)

    class Person(SQLObject):
        name = StringCol()
        age = FloatCol()
        roles = RelatedJoin("Role")

    Role.createTable()
    Student.createTable()
    Professor.createTable()
    Person.createTable()

    first_year = Student(department="CS", year=1)
    lecturer = Professor(department="Mathematics")

    student = Person(name="A student", age=21)
    student.addRole(first_year)
    professor = Person(name="A professor", age=42)
    professor.addRole(lecturer)

    print student.roles
    print professor.roles

    for role in Role.select():
        print role.persons

It prints::

   [<Student 1 year=1 department='CS'>]
   [<Professor 2 timetable=None department='Mathematics'>]
   [<Person 1 name='A student' age=21.0>]
   [<Person 2 name='A professor' age=42.0>]


Who, What and How
~~~~~~~~~~~~~~~~~

Daniel Savard has implemented inheritance for SQLObject. According to
ObjectMatter_ this is a kind of vertical inheritance. The only difference
is that objects reference their leaves, not parents. Links to parents are
reconstructed at run-time using the hierarchy of Python classes.

.. _ObjectMatter: http://www.objectmatter.com/vbsf/docs/maptool/ormapping.html

* As suggested by Ian Bicking, each child class now has the same
  ID as the parent class.  No more need for childID column and
  parent foreignKey (and a small speed boost).
* No more need to call getSubClass, as the 'latest' child will always
  be returned when an instance of a class is created.
* This version now seems to work correctly with addColumn, delColumn,
  addJoin and delJoin.

The following code::

    from sqlobject.inheritance import InheritableSQLObject
    class Person(InheritableSQLObject):
        firstName = StringCol()
        lastName = StringCol()

    class Employee(Person):
        _inheritable = False
        position = StringCol()

will generate the following tables::

    CREATE TABLE person (
        id INT PRIMARY KEY,
        child_name TEXT,
        first_name TEXT,
        last_name TEXT
    );

    CREATE TABLE employee (
        id INT PRIMARY KEY,
        position TEXT
    )

A new class attribute ``_inheritable`` is added.  When this new
attribute is set to 1, the class is marked 'inheritable' and a new
columns will automatically be added: childName (TEXT).

Each class that inherits from a parent class will get the same ID as
the parent class.  So, there is no need to keep track of parent ID and
child ID, as they are the same.

The column childName will contain the name of the child class (for
example 'Employee').  This will permit a class to always return its
child class if available (a person that is also an employee will always
return an instance of the employee class).

For example, the following code::

    p = Person(firstName='John', lastName='Doe')
    e = Employee(firstName='Jane', lastName='Doe', position='Chief')
    p2 = Person.get(1)

Will create the following data in the database::

    *Person*
    id
        child_name
        first_name
        last_name
    0
        Null
        John
        Doe
    1
        Employee
        Jane
        Doe


    *Employee*
    id
        position
    1
        Chief

You will still be able to ask for the attribute normally:
e.firstName will return Jane and setting it will write the new value in
the person table.

If you use p2, as p2 is a person object, you will get an employee
object.
person(0) will return a Person instance and will have the following
attributes: firstName and lastName.
person(1) or employee(1) will both return the same Employee instance and
will have the following attributes: firstName, lastName and position.

Also, deleting a person or an employee that is linked will destroy
both entries as one would expect.

The SQLObject q magic also works.  Using these selects is valid::

    Employee.select(AND(Employee.q.firstName == 'Jane', Employee.q.position == 'Chief')) will return Jane Doe
    Employee.select(AND(Person.q.firstName == 'Jane', Employee.q.position == 'Chief')) will return Jane Doe
    Employee.select(Employee.q.lastName == 'Doe') will only return Jane Doe (as Joe isn't an employee)
    Person.select(Person.q.lastName == 'Doe') will return both entries.

The SQL 'where' clause will contain additional clauses when used with
'inherited' classes.  These clauses are the link between the id and the
parent id.  This will look like the following request::

    SELECT employee.id, person.first_name, person.last_name
    FROM person, employee WHERE person.first_name = 'Jane'
    AND employee.position = 'Chief' AND person.id = employee.id


Limitations and notes
~~~~~~~~~~~~~~~~~~~~~

* Only single inheritance will work.  It is not possible to inherit
  from multiple SQLObject classes.
* It is possible to inherit from an inherited class and this will
  work well.  In the above example, you can have a Chief class that
  inherits from Employee and all parents attributes will be
  available through the Chief class.
* You may not redefine columns in an inherited class (this
  will raise an exception).
* If you don't want 'childName' columns in your last class (one that
  will never be inherited), you must set '_inheritable' to False in this
  class.
* The inheritance implementation is incompatible with lazy updates. Do not
  set lazyUpdate to True. If you need this, you have to patch SQLObject
  and override many methods - _SO_setValue(), sync(), syncUpdate() at
  least. Patches will be gladly accepted.
* You'd better restrain yourself to simple use cases. The inheritance
  implementation is easily choked on more complex cases.
* A join between tables inherited from the same parent produces incorrect
  result due to joins to the same parent table (they must use different
  aliases).
* Inheritance works in two stages - first it draws the IDs from the parent
  table and then it draws the rows from the children tables. The first
  stage could fail if you try to do complex things. For example,
  Children.select(orderBy=Children.q.column, distinct=True)
  could fail because at the first stage inheritance generates a SELECT
  query for the parent table with ORDER BY the column from the children
  table.
* I made it because I needed to be able to have automatic
  inheritance with linked tables.
* This version works for me; it may not work for you.  I tried to do
  my best but it is possible that I broke some things... So, there
  is no warranty that this version will work.
* Thanks to Ian Bicking for SQLObject; this is a wonderful python
  module.
* Although all the attributes are inherited, the same does not apply
  to sqlmeta data. Don't try to get a parent column via the sqlmeta.columns
  dictionary of an inherited InheritableSQLObject: it will raise a KeyError.
  The same applies to joins: the sqlmeta.joins list will be empty in an 
  inherited InheritableSQLObject if a join has been defined in the parent
  class, even though the join method will work correctly.
* If you have suggestion, bugs, or patch to this patch, you can
  contact the SQLObject team: <sqlobject-discuss at lists.sourceforge.net>

.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=74338&type=10
   :target: http://sourceforge.net/projects/sqlobject
   :class: noborder
   :align: center
   :height: 15
   :width: 80
   :alt: Get SQLObject at SourceForge.net. Fast, secure and Free Open Source software downloads
