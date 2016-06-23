SelectResults: Using Queries
============================

.. contents:: Contents:

Overview
--------

SelectResults are returned from ``.select`` and ``.selectBy`` methods on SQLObject classes, and from ``SQLMultipleJoin``, and ``SQLRelatedJoin`` accessors on SQLObject instances.

Select results are generators, which are lazily evaluated.  The SQL
is only executed when you iterate over the select results, fetching
rows one at a time.  This way you
can iterate over large results without keeping the entire result set
in memory. You can also do things like ``.reversed()`` without
fetching and reversing the entire result -- instead, SQLObject can
change the SQL that is sent so you get equivalent results.

.. note::
   To retrieve the results all at once use the python idiom
   of calling ``list()`` on the generator to force execution
   and convert the results to a stored list.

You can also slice select results.  This modifies the SQL query, so
``peeps[:10]`` will result in ``LIMIT 10`` being added to the end of
the SQL query.  If the slice cannot be performed in the SQL (e.g.,
peeps[:-10]), then the select is executed, and the slice is performed
on the list of results.  This will generally only happen when you use
negative indexes.

In certain cases, you may get a select result with an object in it
more than once, e.g., in some joins.  If you don't want this, you can
add the keyword argument ``MyClass.select(..., distinct=True)``, which
results in a ``SELECT DISTINCT`` call.

You can get the length of the result without fetching all the results
by calling ``count`` on the result object, like
``MyClass.select().count()``.  A ``COUNT(*)`` query is used -- the
actual objects are not fetched from the database.  Together with
slicing, this makes batched queries easy to write::

    start = 20
    size = 10
    query = Table.select()
    results = query[start:start+size]
    total = query.count()
    print "Showing page %i of %i" % (start/size + 1, total/size + 1)

.. note::

   There are several factors when considering the efficiency of this
   kind of batching, and it depends very much how the batching is
   being used.  Consider a web application where you are showing an
   average of 100 results, 10 at a time, and the results are ordered
   by the date they were added to the database.  While slicing will
   keep the database from returning all the results (and so save some
   communication time), the database will still have to scan through
   the entire result set to sort the items (so it knows which the
   first ten are), and depending on your query may need to scan
   through the entire table (depending on your use of indexes).
   Indexes are probably the most important way to improve importance
   in a case like this, and you may find caching to be more effective
   than slicing.

   In this case, caching would mean retrieving the *complete* results.
   You can use ``list(MyClass.select(...))`` to do this.  You can save
   these results for some limited period of time, as the user looks
   through the results page by page.  This means the first page in a
   search result will be slightly more expensive, but all later pages
   will be very cheap.

Retrieval Methods
-----------------

Iteration
~~~~~~~~~

As mentioned in the overview, the typical way to access the results
is by treating it as a generator and iterating over it (in a loop,
by converting to a list, etc).

``getOne(default=optional)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In cases where your restrictions cause there to always be a single record
in the result set, this method will return it or raise an exception:
SQLObjectIntegrityError if more than one result is found, or 
SQLObjectNotFound if there are actually no results, unless you pass in
a default like ``.getOne(None)``.

Cloning Methods
---------------

These methods return a modified copy of the SelectResult instance 
they are called on, so successive calls can chained, eg 
``results = MyClass.selectBy(city='Boston').filter(MyClass.q.commute_distance>10).orderBy('vehicle_mileage')``
or used independently later on.


``orderBy(column)``
~~~~~~~~~~~~~~~~~~~

Takes a string column name (optionally prefixed with '-' for DESCending)
or a `SQLBuilder expression`_.

``limit(num)``
~~~~~~~~~~~~~~

Only return first num many results. Equivalent to results[:num] slicing.

``lazyColumns(v)``
~~~~~~~~~~~~~~~~~~

Only fetch the IDs for the results, the rest of the columns will be
retrieved when attributes of the returned instances are accessed.

``reversed()``
~~~~~~~~~~~~~~

Reverse-order. Alternative to calling orderBy with SQLBuilder.DESC or '-'.


``distinct()``
~~~~~~~~~~~~~~

In SQL, SELECT DISTINCT, removing duplicate rows.

``filter(expression)``
~~~~~~~~~~~~~~~~~~~~~~

Add additional expressions to restrict result set.
Takes either a string static SQL expression valid in a WHERE clause,
or a `SQLBuilder expression`_. ANDed with any previous expressions. 

.. _`SQLBuilder expression`: SQLBuilder.html


Aggregate Methods
-----------------

These return column values (strings, numbers, etc) 
not new SQLResults instances, by making the appropriate
SQL query (the actual result rows are not retrieved).
Any that take a column can also take a SQLBuilder 
column instance, e.g. ``MyClass.q.size``.


``count()``
~~~~~~~~~~~

Returns the length of the result set, by a SQL ``SELECT COUNT(...)``
query.

``sum(column)``
~~~~~~~~~~~~~~~

The sum of values for ``column`` in the result set.

``min(column)``
~~~~~~~~~~~~~~~

The minimum value for ``column`` in the result set.

``max(column)``
~~~~~~~~~~~~~~~

The maximum value for ``column`` in the result set.

``avg(column)``
~~~~~~~~~~~~~~~

The average value for the ``column`` in the result set.

Traversal to related SQLObject classes
--------------------------------------

``throughTo.join_name and throughTo.foreign_key_name``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This accessor lets you retrieve the objects related to your 
SelectResults by either a join or foreign key relationship,
in the same manner as the cloning methods above. For instance::

  Schools.select(Schools.q.student_satisfaction>90).throughTo.teachers

returns a SelectResult of Teachers of Schools with satisfied students,
assuming Schools has a SQLMultipleJoin or SQLRelatedJoin attribute
named ``teachers``. Similarily, with a self-joining foreign key named
``father``::

  Person.select(Person.q.name=='Steve').throughTo.father.throughTo.father

returns a SelectResult of Persons who are the paternal grandfather of someone
named ``Steve``.

.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=74338&type=10
   :target: http://sourceforge.net/projects/sqlobject
   :class: noborder
   :align: center
   :height: 15
   :width: 80
   :alt: Get SQLObject at SourceForge.net. Fast, secure and Free Open Source software downloads
