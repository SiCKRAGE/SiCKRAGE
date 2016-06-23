Views and SQLObjects
====================

In general, if your database backend supports defining views
you may define them outside of SQLObject and treat them
as a regular table when defining your SQLObject class.


ViewSQLObject
-------------

The rest of this document is experimental.

``from sqlobject.views import *``

``ViewSQLObject`` is an attempt to allow defining
views that allow you to define a SQL query that acts
like a SQLObject class. You define columns based on
other SQLObject classes .q SQLBuilder columns, have columns
that are aggregates of other columns, and join
multiple SQLObject classes into one and add restrictions
using SQLBuilder expressions.

The resulting classes are currently read only, if you find
use for this idea please bring discussion to the mailing list.

A short example from the tests will suffice for now.

Base classes::

  class PhoneNumber(SQLObject):
    number = StringCol()
    calls = SQLMultipleJoin('PhoneCall')
    incoming = SQLMultipleJoin('PhoneCall', joinColumn='toID')

  class PhoneCall(SQLObject):
    phoneNumber = ForeignKey('PhoneNumber')
    to = ForeignKey('PhoneNumber')
    minutes = IntCol()

View classes::

  class ViewPhoneCall(ViewSQLObject):
    class sqlmeta:
        idName = PhoneCall.q.id
        clause = PhoneCall.q.phoneNumberID==PhoneNumber.q.id

    minutes = IntCol(dbName=PhoneCall.q.minutes)
    number = StringCol(dbName=PhoneNumber.q.number)
    phoneNumber = ForeignKey('PhoneNumber', dbName=PhoneNumber.q.id)
    call = ForeignKey('PhoneCall', dbName=PhoneCall.q.id)

  class ViewPhone(ViewSQLObject):
    class sqlmeta:
        idName = PhoneNumber.q.id
        clause = PhoneCall.q.phoneNumberID==PhoneNumber.q.id

    minutes = IntCol(dbName=func.SUM(PhoneCall.q.minutes))
    numberOfCalls = IntCol(dbName=func.COUNT(PhoneCall.q.phoneNumberID))
    number = StringCol(dbName=PhoneNumber.q.number)
    phoneNumber = ForeignKey('PhoneNumber', dbName=PhoneNumber.q.id)
    calls = SQLMultipleJoin('PhoneCall', joinColumn='phoneNumberID')
    vCalls = SQLMultipleJoin('ViewPhoneCall', joinColumn='phoneNumberID')

.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=74338&type=10
   :target: http://sourceforge.net/projects/sqlobject
   :class: noborder
   :align: center
   :height: 15
   :width: 80
   :alt: Get SQLObject at SourceForge.net. Fast, secure and Free Open Source software downloads
