``````````
SQLBuilder
``````````

.. contents::

A number of variables from SQLBuilder are included with ``from
sqlobject import *`` -- see the `relevant SQLObject documentation`_
for more.  Its functionality is also available through the special
``q`` attribute of `SQLObject` classes.

.. _`relevant SQLObject documentation`: SQLObject.html#exported-symbols

SQLExpression
=============

SQLExpression uses clever overriding of operators to make Python
expressions build SQL expressions -- so long as you start with a Magic
Object that knows how to fake it.

With SQLObject, you get a Magic Object by accessing the ``q`` attribute
of a table class -- this gives you an object that represents the
field. All of this is probably easier to grasp in an example::

    >>> from sqlobject.sqlbuilder import *
    >>> person = table.person
    # person is now equivalent to the Person.q object from the SQLObject
    # documentation
    >>> person
    person
    >>> person.first_name
    person.first_name
    >>> person.first_name == 'John'
    person.first_name = 'John'
    >>> name = 'John'
    >>> person.first_name != name
    person.first_name <> 'John'
    >>> AND(person.first_name == 'John', person.last_name == 'Doe')
    (person.first_name = 'John' AND person.last_name = 'Doe')

Most of the operators work properly: <, >, <=, >=, !=, ==, +, -, /,
\*, \*\*, %.  However, ``and``, ``or``, and ``not`` **do not work**.
You can use &, \|, and ~ instead -- but be aware that these have
the same precedence as multiplication.  So::

    # This isn't what you want:
    >> person.first_name == 'John' & person.last_name == 'Doe'
    (person.first_name = ('John' AND person.last_name)) = 'Doe')
    # This is:
    >> (person.first_name == 'John') & (person.last_name == 'Doe')
    ((person.first_name = 'John') AND (person.last_name == 'Doe'))

SQLBuilder also contains the functions ``AND``, ``OR``, and ``NOT`` which
also work -- I find these easier to work with.  ``AND`` and ``OR`` can
take any number of arguments.

You can also use ``.startswith()`` and ``.endswith()`` on an SQL
expression -- these will translate to appropriate ``LIKE`` statements
and all ``%`` quoting is handled for you, so you can ignore that
implementation detail.  There is also a ``LIKE`` function, where you
can pass your string, with ``%`` for the wildcard, as usual.

If you want to access an SQL function, use the ``func`` variable,
like::

    >> person.created < func.NOW()

To pass a constant, use the ``const`` variable which is actually an
alias for func.

SQL statements
==============

SQLBuilder implements objects that execute SQL statements. SQLObject
uses them internally in its `higher-level API`_, but users can use this
mid-level API to execute SQL queries that are not supported by the
high-level API. To use these objects first construct an instance of a
statement object, then ask the connection to convert the instance to an
SQL query and finally ask the connection to execute the query and return
the results. For example, for ``Select`` class::

    >>> from sqlobject.sqlbuilder import *
    >> select = Select(['name', 'AVG(salary)'], staticTables=['employees'],
    >>     groupBy='name') # create an instance
    >> query = connection.sqlrepr(select) # Convert to SQL string:
    >>     # SELECT name, AVG(salary) FROM employees GROUP BY name
    >> rows = connection.queryAll(query) # Execute the query
    >>     # and get back the results as a list of rows
    >>     # where every row is a sequence of length 2 (name and average salary)

.. _`higher-level API`: SQLObject.html

Select
~~~~~~

A class to build ``SELECT`` queries. Accepts a number of parameters, all
parameters except `items` are optional. Use ``connection.queryAll(query)``
to execute the query and get back the results as a list of rows.

`items`:
   A string, an SQLExpression or a sequence of strings or
   SQLExpression's, represents the list of columns. If there are
   q-values SQLExpression's ``Select`` derives a list of tables for
   SELECT query.

`where`:
   A string or an SQLExpression, represents the ``WHERE`` clause.

`groupBy`:
   A string or an SQLExpression, represents the ``GROUP BY`` clause.

`having`:
   A string or an SQLExpression, represents the ``HAVING`` part of the
   ``GROUP BY`` clause.

`orderBy`:
   A string or an SQLExpression, represents the ``ORDER BY`` clause.

`join`:
   A (list of) JOINs (``LEFT JOIN``, etc.)

`distinct`:
   A bool flag to turn on ``DISTINCT`` query.

`start`, `end`:
   Integers. The way to calculate ``OFFSET`` and ``LIMIT``.

`limit`:
   An integer. `limit`, if passed, overrides `end`.

`reversed`:
   A bool flag to do ``ORDER BY`` in the reverse direction.

`forUpdate`:
   A bool flag to turn on ``SELECT FOR UPDATE`` query.

`staticTables`:
   A sequence of strings or SQLExpression's that name tables for
   ``FROM``. This parameter must be used if `items` is a list of strings
   from which Select cannot derive the list of tables.

Insert
~~~~~~

A class to build ``INSERT`` queries. Accepts a number of parameters.
Use ``connection.query(query)`` to execute the query.

`table`:
   A string that names the table to ``INSERT`` into. Required.

`valueList`:
   A list of (key, value) sequences or {key: value} dictionaries; keys
   are column names. Either `valueList` or `values` must be passed, but
   not both. Example::

    >> insert = Insert('person', valueList=[('name', 'Test'), ('age', 42)])
           # or
    >> insert = Insert('person', valueList=[{'name': 'Test'}, {'age': 42}])
    >> query = connection.sqlrepr(insert)
           # Both generate the same query:
           # INSERT INTO person (name, age) VALUES ('Test', 42)
    >> connection.query(query)

`values`:
   A dictionary {key: value}; keys are column names. Either `valueList`
   or `values` must be passed, but not both. Example::

    >> insert = Insert('person', values={'name': 'Test', 'age': 42})
    >> query = connection.sqlrepr(insert)
           # The query is the same
           # INSERT INTO person (name, age) VALUES ('Test', 42)
    >> connection.query(query)

Instances of the class work fast and thus are suitable for
mass-insertion. If one needs to populate a database with SQLObject
running a lot of ``INSERT`` queries this class is the way to go.

Update
~~~~~~

A class to build ``UPDATE`` queries. Accepts a number of parameters.
Use ``connection.query(query)`` to execute the query.

`table`:
   A string that names the table to ``UPDATE``. Required.

`values`:
   A dictionary {key: value}; keys are column names. Required.

`where`:
   An optional string or SQLExpression, represents the ``WHERE`` clause.

Example::

    >> update = Update('person',
    >>     values={'name': 'Test', 'age': 42}, where='id=1')
    >> query = connection.sqlrepr(update)
           # UPDATE person SET name='Test', age=42 WHERE id=1
    >> connection.query(query)

Delete
~~~~~~

A class to build ``DELETE FROM`` queries. Accepts a number of parameters.
Use ``connection.query(query)`` to execute the query.

`table`:
   A string that names the table to ``UPDATE``. Required.

`where`:
   An optional string or an SQLExpression, represents the ``WHERE``
   clause. Required. If you need to delete all rows pass ``where=None``;
   this is a safety measure.

Example::

    >> update = Delete('person', where='id=1')
    >> query = connection.sqlrepr(update)
           # DELETE FROM person WHERE id=1
    >> connection.query(query)

Union
~~~~~

A class to build ``UNION`` queries. Accepts a number of parameters -
``Select`` queries. Use ``connection.queryAll(query)`` to execute the
query and get back the results.

Example::

    >> select1 = Select(['min', func.MIN(const.salary)], staticTables=['employees'])
    >> select2 = Select(['max', func.MAX(const.salary)], staticTables=['employees'])
    >> union = Union(select1, select2)
    >> query = connection.sqlrepr(union)
           # SELECT 'min', MIN(salary) FROM employees
           #    UNION
           # SELECT 'max', MAX(salary) FROM employees
    >> rows = connection.queryAll(query)

Nested SQL statements (subqueries)
==================================

There are a few special operators that receive as parameter SQL
statements. These are ``IN``, ``NOTIN``, ``EXISTS``, ``NOTEXISTS``,
``SOME``, ``ANY`` and ``ALL``. Consider the following example: You are
interested in removing records from a table using deleteMany. However,
the criterion for doing so depends on another table.

You would expect the following to work::

    >> PersonWorkplace.deleteMany(where=
       ((PersonWorkplace.q.WorkplaceID==Workplace.q.id) &
       (Workplace.q.id==SOME_ID)))

But this doesn't work! However, you can't do a join in a deleteMany
call. To work around this issue, use ``IN``::

    >> PersonWorkplace.deleteMany(where=
       IN(PersonWorkplace.q.WorkplaceID,
       Select(Workplace.q.id, Workplace.q.id==SOME_ID)))

.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=74338&type=10
   :target: http://sourceforge.net/projects/sqlobject
   :class: noborder
   :align: center
   :height: 15
   :width: 80
   :alt: Get SQLObject at SourceForge.net. Fast, secure and Free Open Source software downloads
