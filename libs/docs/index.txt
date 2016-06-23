+++++++++
SQLObject
+++++++++

SQLObject is a popular *Object Relational Manager* for providing an
object interface to your database, with tables as classes, rows as
instances, and columns as attributes.

SQLObject includes a Python-object-based query language that makes SQL
more abstract, and provides substantial database independence for
applications.

* `Download <download.html>`_
* `Mailing list, bugs, etc. <community.html>`_
* `Related projects and articles <links.html>`_

Documentation
=============

* `News and updates <News.html>`_
* `Main SQLObject documentation <SQLObject.html>`_
* `Frequently Asked Questions <FAQ.html>`_
* `sqlbuilder documentation <SQLBuilder.html>`_
* `select() and SelectResults <SelectResults.html>`_
* `sqlobject-admin documentation <sqlobject-admin.html>`_
* `Inheritance <Inheritance.html>`_
* `Versioning <Versioning.html>`_
* `Views <Views.html>`_
* `Developer Guide <DeveloperGuide.html>`_
* `Contributors <Authors.html>`_

Example
=======

Examples are good.  Examples give a feel for the aesthetic of the API,
which matters to me a great deal.  This is just a snippet that creates
a simple class that wraps a table::

  >>> from sqlobject import *
  >>>
  >>> sqlhub.processConnection = connectionForURI('sqlite:/:memory:')
  >>>
  >>> class Person(SQLObject):
  ...     fname = StringCol()
  ...     mi = StringCol(length=1, default=None)
  ...     lname = StringCol()
  ...
  >>> Person.createTable()

SQLObject supports most database schemas that you already have, and
can also issue the ``CREATE`` statement for you (seen in
``Person.createTable()``).

Here's how you'd use the object::

  >>> p = Person(fname="John", lname="Doe")
  >>> p
  <Person 1 fname='John' mi=None lname='Doe'>
  >>> p.fname
  'John'
  >>> p.mi = 'Q'
  >>> p2 = Person.get(1)
  >>> p2
  <Person 1 fname='John' mi='Q' lname='Doe'>
  >>> p is p2
  True

.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=74338&type=10
   :target: http://sourceforge.net/projects/sqlobject
   :class: noborder
   :align: center
   :height: 15
   :width: 80
   :alt: Get SQLObject at SourceForge.net. Fast, secure and Free Open Source software downloads
