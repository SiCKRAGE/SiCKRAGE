:Author: David Turner, The Open Planning Project

Versioning
-----------

Why
~~~

You have a table where rows can be altered, such as a table of wiki
pages.  You want to retain a history of changes for auditing, backup,
or tracking purposes.  

You could write a decorator that stores old versions and manage all
access to this object through it.  Or you could take advantage of the
event system in SQLObject 0.8+ and just catch row accesses to the
object.  SQLObject's versioning module does this for you.  And it even
works with inheritance!

How
~~~

Here's how to set it up::

    class MyClass(SQLObject):
        name = StringCol()
        versions = Versioning()

To use it, just create an instance as usual::

    mc = MyClass(name='fleem')

Then make some changes and check out the results::

    mc.set(name='morx')
    assert mc.versions[0].name == 'fleem'

You can also restore to a previous version::

    mc.versions[0].restore()
    assert mc.name == "fleem"

Inheritance
~~~~~~~~~~~

There are three ways versioning can be used with inheritance_:

.. _inheritance: Inheritance.html

1. Parent versioned, children unversioned::

     class Base(InheritableSQLObject):
         name = StringCol()
         versions = Versioning()

     class Child(Base):
         toy = StringCol()

In this case, when changes are made to an instance of Base, new
versions are created.  But when changes are made to an instance of
Child, no new versions are created.  

2. Children versioned, parents unversioned.

In this case, when changes are made to an instance of Child, new
versions are created.  But when changes are made to an instance of
Base, no new versions are created.  The version data for Child
contains all of the columns from child and from base, so that a full
restore is possible.

3. Both children and parents versioned.  

In this case, changes to either Child or Base instances create new
versions, but in different tables.  Child versions still contain all
Base data, and a change to a Child only creates a new Child version, not 
a new Base version.

Version Tables
~~~~~~~~~~~~~~

Versions are stored in a special table which is created when the table
for a versioned class is created.  Version tables are not altered when
the main table is altered, so if you add a column to your main class,
you will need to manually add the column to your version table. 

.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=74338&type=10
   :target: http://sourceforge.net/projects/sqlobject
   :class: noborder
   :align: center
   :height: 15
   :width: 80
   :alt: Get SQLObject at SourceForge.net. Fast, secure and Free Open Source software downloads
