"""dberrors: database exception classes for SQLObject.

   These classes are dictated by the DB API v2.0:
   
   http://www.python.org/topics/database/DatabaseAPI-2.0.html
"""

class Error(StandardError): pass
class Warning(StandardError): pass

class InterfaceError(Error): pass
class DatabaseError(Error): pass

class InternalError(DatabaseError): pass
class OperationalError(DatabaseError): pass
class ProgrammingError(DatabaseError): pass
class IntegrityError(DatabaseError): pass
class DataError(DatabaseError): pass
class NotSupportedError(DatabaseError): pass

class DuplicateEntryError(IntegrityError): pass
