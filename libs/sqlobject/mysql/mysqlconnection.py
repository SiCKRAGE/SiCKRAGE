from sqlobject import col
from sqlobject.dbconnection import DBAPI
from sqlobject.dberrors import *

class ErrorMessage(str):
    def __new__(cls, e, append_msg=''):
        obj = str.__new__(cls, e[1] + append_msg)
        obj.code = int(e[0])
        obj.module = e.__module__
        obj.exception = e.__class__.__name__
        return obj

class MySQLConnection(DBAPI):

    supportTransactions = False
    dbName = 'mysql'
    schemes = [dbName]

    def __init__(self, db, user, password='', host='localhost', port=0, **kw):
        import MySQLdb, MySQLdb.constants.CR, MySQLdb.constants.ER
        self.module = MySQLdb
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password
        self.kw = {}
        for key in ("unix_socket", "init_command",
                "read_default_file", "read_default_group", "conv"):
            if key in kw:
                self.kw[key] = kw.pop(key)
        for key in ("connect_timeout", "compress", "named_pipe", "use_unicode",
                "client_flag", "local_infile"):
            if key in kw:
                self.kw[key] = int(kw.pop(key))
        for key in ("ssl_key", "ssl_cert", "ssl_ca", "ssl_capath"):
            if key in kw:
                if "ssl" not in self.kw:
                    self.kw["ssl"] = {}
                self.kw["ssl"][key[4:]] = kw.pop(key)
        if "charset" in kw:
            self.dbEncoding = self.kw["charset"] = kw.pop("charset")
        else:
            self.dbEncoding = None

        # MySQLdb < 1.2.1: only ascii
        # MySQLdb = 1.2.1: only unicode
        # MySQLdb > 1.2.1: both ascii and unicode
        self.need_unicode = (self.module.version_info[:3] >= (1, 2, 1)) and (self.module.version_info[:3] < (1, 2, 2))

        self._server_version = None
        self._can_use_microseconds = None
        DBAPI.__init__(self, **kw)

    @classmethod
    def _connectionFromParams(cls, user, password, host, port, path, args):
        return cls(db=path.strip('/'), user=user or '', password=password or '',
                   host=host or 'localhost', port=port or 0, **args)

    def makeConnection(self):
        dbEncoding = self.dbEncoding
        if dbEncoding:
            from MySQLdb.connections import Connection
            if not hasattr(Connection, 'set_character_set'):
                # monkeypatch pre MySQLdb 1.2.1
                def character_set_name(self):
                    return dbEncoding + '_' + dbEncoding
                Connection.character_set_name = character_set_name
        try:
            conn = self.module.connect(host=self.host, port=self.port,
                db=self.db, user=self.user, passwd=self.password, **self.kw)
            if self.module.version_info[:3] >= (1, 2, 2):
                conn.ping(True) # Attempt to reconnect. This setting is persistent.
        except self.module.OperationalError, e:
            conninfo = "; used connection string: host=%(host)s, port=%(port)s, db=%(db)s, user=%(user)s" % self.__dict__
            raise OperationalError(ErrorMessage(e, conninfo))

        if hasattr(conn, 'autocommit'):
            conn.autocommit(bool(self.autoCommit))

        if dbEncoding:
            if hasattr(conn, 'set_character_set'): # MySQLdb 1.2.1 and later
                conn.set_character_set(dbEncoding)
            else: # pre MySQLdb 1.2.1
                # works along with monkeypatching code above
                conn.query("SET NAMES %s" % dbEncoding)

        return conn

    def _setAutoCommit(self, conn, auto):
        if hasattr(conn, 'autocommit'):
            conn.autocommit(auto)

    def _executeRetry(self, conn, cursor, query):
        if self.need_unicode and not isinstance(query, unicode):
            try:
                query = unicode(query, self.dbEncoding)
            except UnicodeError:
                pass

        # When a server connection is lost and a query is attempted, most of
        # the time the query will raise a SERVER_LOST exception, then at the
        # second attempt to execute it, the mysql lib will reconnect and
        # succeed. However is a few cases, the first attempt raises the
        # SERVER_GONE exception, the second attempt the SERVER_LOST exception
        # and only the third succeeds. Thus the 3 in the loop count.
        # If it doesn't reconnect even after 3 attempts, while the database is
        # up and running, it is because a 5.0.3 (or newer) server is used
        # which no longer permits autoreconnects by default. In that case a
        # reconnect flag must be set when making the connection to indicate
        # that autoreconnecting is desired. In MySQLdb 1.2.2 or newer this is
        # done by calling ping(True) on the connection.
        for count in range(3):
            try:
                return cursor.execute(query)
            except self.module.OperationalError, e:
                if e.args[0] in (self.module.constants.CR.SERVER_GONE_ERROR, self.module.constants.CR.SERVER_LOST):
                    if count == 2:
                        raise OperationalError(ErrorMessage(e))
                    if self.debug:
                        self.printDebug(conn, str(e), 'ERROR')
                else:
                    raise OperationalError(ErrorMessage(e))
            except self.module.IntegrityError, e:
                msg = ErrorMessage(e)
                if e.args[0] == self.module.constants.ER.DUP_ENTRY:
                    raise DuplicateEntryError(msg)
                else:
                    raise IntegrityError(msg)
            except self.module.InternalError, e:
                raise InternalError(ErrorMessage(e))
            except self.module.ProgrammingError, e:
                raise ProgrammingError(ErrorMessage(e))
            except self.module.DataError, e:
                raise DataError(ErrorMessage(e))
            except self.module.NotSupportedError, e:
                raise NotSupportedError(ErrorMessage(e))
            except self.module.DatabaseError, e:
                raise DatabaseError(ErrorMessage(e))
            except self.module.InterfaceError, e:
                raise InterfaceError(ErrorMessage(e))
            except self.module.Warning, e:
                raise Warning(ErrorMessage(e))
            except self.module.Error, e:
                raise Error(ErrorMessage(e))

    def _queryInsertID(self, conn, soInstance, id, names, values):
        table = soInstance.sqlmeta.table
        idName = soInstance.sqlmeta.idName
        c = conn.cursor()
        if id is not None:
            names = [idName] + names
            values = [id] + values
        q = self._insertSQL(table, names, values)
        if self.debug:
            self.printDebug(conn, q, 'QueryIns')
        self._executeRetry(conn, c, q)
        if id is None:
            try:
                id = c.lastrowid
            except AttributeError:
                id = c.insert_id()
        if self.debugOutput:
            self.printDebug(conn, id, 'QueryIns', 'result')
        return id

    @classmethod
    def _queryAddLimitOffset(cls, query, start, end):
        if not start:
            return "%s LIMIT %i" % (query, end)
        if not end:
            return "%s LIMIT %i, -1" % (query, start)
        return "%s LIMIT %i, %i" % (query, start, end-start)

    def createReferenceConstraint(self, soClass, col):
        return col.mysqlCreateReferenceConstraint()

    def createColumn(self, soClass, col):
        return col.mysqlCreateSQL(self)

    def createIndexSQL(self, soClass, index):
        return index.mysqlCreateIndexSQL(soClass)

    def createIDColumn(self, soClass):
        if soClass.sqlmeta.idType == str:
            return '%s TEXT PRIMARY KEY' % soClass.sqlmeta.idName
        return '%s INT PRIMARY KEY AUTO_INCREMENT' % soClass.sqlmeta.idName

    def joinSQLType(self, join):
        return 'INT NOT NULL'

    def tableExists(self, tableName):
        try:
            # Use DESCRIBE instead of SHOW TABLES because SHOW TABLES
            # assumes there is a default database selected
            # which is not always True (for an embedded application, e.g.)
            self.query('DESCRIBE %s' % (tableName))
            return True
        except ProgrammingError, e:
            if e[0].code == 1146: # ER_NO_SUCH_TABLE
                return False
            raise

    def addColumn(self, tableName, column):
        self.query('ALTER TABLE %s ADD COLUMN %s' %
                   (tableName,
                    column.mysqlCreateSQL(self)))

    def delColumn(self, sqlmeta, column):
        self.query('ALTER TABLE %s DROP COLUMN %s' % (sqlmeta.table, column.dbName))

    def columnsFromSchema(self, tableName, soClass):
        colData = self.queryAll("SHOW COLUMNS FROM %s"
                                % tableName)
        results = []
        for field, t, nullAllowed, key, default, extra in colData:
            if field == soClass.sqlmeta.idName:
                continue
            colClass, kw = self.guessClass(t)
            if self.kw.get('use_unicode') and colClass is col.StringCol:
                colClass = col.UnicodeCol
                if self.dbEncoding: kw['dbEncoding'] = self.dbEncoding
            kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
            kw['dbName'] = field

            # Since MySQL 5.0, 'NO' is returned in the NULL column (SQLObject expected '')
            kw['notNone'] = (nullAllowed.upper() != 'YES' and True or False)

            if default and t.startswith('int'):
                kw['default'] = int(default)
            elif default and t.startswith('float'):
                kw['default'] = float(default)
            elif default == 'CURRENT_TIMESTAMP' and t == 'timestamp':
                kw['default'] = None
            elif default and colClass is col.BoolCol:
                kw['default'] = int(default) and True or False
            else:
                kw['default'] = default
            # @@ skip key...
            # @@ skip extra...
            results.append(colClass(**kw))
        return results

    def guessClass(self, t):
        if t.startswith('int'):
            return col.IntCol, {}
        elif t.startswith('enum'):
            values = []
            for i in t[5:-1].split(','): # take the enum() off and split
                values.append(i[1:-1]) # remove the surrounding \'
            return col.EnumCol, {'enumValues': values}
        elif t.startswith('double'):
            return col.FloatCol, {}
        elif t.startswith('varchar'):
            colType = col.StringCol
            if self.kw.get('use_unicode', False):
                colType = col.UnicodeCol
            if t.endswith('binary'):
                return colType, {'length': int(t[8:-8]),
                                       'char_binary': True}
            else:
                return colType, {'length': int(t[8:-1])}
        elif t.startswith('char'):
            if t.endswith('binary'):
                return col.StringCol, {'length': int(t[5:-8]),
                                       'varchar': False,
                                       'char_binary': True}
            else:
                return col.StringCol, {'length': int(t[5:-1]),
                                       'varchar': False}
        elif t.startswith('datetime'):
            return col.DateTimeCol, {}
        elif t.startswith('date'):
            return col.DateCol, {}
        elif t.startswith('time'):
            return col.TimeCol, {}
        elif t.startswith('timestamp'):
            return col.TimestampCol, {}
        elif t.startswith('bool'):
            return col.BoolCol, {}
        elif t.startswith('tinyblob'):
            return col.BLOBCol, {"length": 2**8-1}
        elif t.startswith('tinytext'):
            return col.StringCol, {"length": 2**8-1, "varchar": True}
        elif t.startswith('blob'):
            return col.BLOBCol, {"length": 2**16-1}
        elif t.startswith('text'):
            return col.StringCol, {"length": 2**16-1, "varchar": True}
        elif t.startswith('mediumblob'):
            return col.BLOBCol, {"length": 2**24-1}
        elif t.startswith('mediumtext'):
            return col.StringCol, {"length": 2**24-1, "varchar": True}
        elif t.startswith('longblob'):
            return col.BLOBCol, {"length": 2**32}
        elif t.startswith('longtext'):
            return col.StringCol, {"length": 2**32, "varchar": True}
        else:
            return col.Col, {}

    def listTables(self):
        return [v[0] for v in self.queryAll("SHOW TABLES")]

    def listDatabases(self):
        return [v[0] for v in self.queryAll("SHOW DATABASES")]

    def _createOrDropDatabase(self, op="CREATE"):
        self.query('%s DATABASE %s' % (op, self.db))

    def createEmptyDatabase(self):
        self._createOrDropDatabase()

    def dropDatabase(self):
        self._createOrDropDatabase(op="DROP")

    def server_version(self):
        if self._server_version is not None:
            return self._server_version
        try:
            server_version = self.queryOne("SELECT VERSION()")[0]
            server_version = server_version.split('-', 1)
            db_tag = "MySQL"
            if len(server_version) == 2:
                if "MariaDB" in server_version[1]:
                    db_tag = "MariaDB"
                server_version = server_version[0]
            server_version = tuple(int(v) for v in server_version.split('.'))
            server_version = (server_version, db_tag)
        except:
            server_version = None # unknown
        self._server_version = server_version
        return server_version

    def can_use_microseconds(self):
        if self._can_use_microseconds is not None:
            return self._can_use_microseconds
        server_version = self.server_version()
        if server_version is None:
            return None
        server_version, db_tag = server_version
        if db_tag == "MariaDB":
            can_use_microseconds = (server_version >= (5, 3, 0))
        else: # MySQL
            can_use_microseconds = (server_version >= (5, 6, 4))
        self._can_use_microseconds = can_use_microseconds
        return can_use_microseconds
