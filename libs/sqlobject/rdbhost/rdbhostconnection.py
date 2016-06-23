"""
This module written by David Keeney, 2009, 2010

Released under the LGPL for use with the SQLObject ORM library.
"""

import re
from sqlobject import col
from sqlobject import sqlbuilder
from sqlobject.converters import registerConverter
from sqlobject.dbconnection import DBAPI
from sqlobject.postgres.pgconnection import PostgresConnection

class RdbhostConnection(PostgresConnection):

    supportTransactions = False
    dbName = 'rdbhost'
    schemes = [dbName]

    def __init__(self, dsn=None, host=None, port=None, db=None,
                 user=None, password=None, unicodeCols=False, driver='rdbhost',
                 **kw):
        drivers = driver
        for driver in drivers.split(','):
            driver = driver.strip()
            if not driver:
                continue
            try:
                if driver == 'rdbhost':
                    from rdbhdb import rdbhdb as rdb
                    # monkey patch % escaping into Cursor._execute
                    old_execute = getattr(rdb.Cursor, '_execute')
                    setattr(rdb.Cursor, '_old_execute', old_execute)
                    def _execute(self, query, *args):
                        assert not any([a for a in args])
                        query = query.replace('%', '%%')
                        self._old_execute(query, (), (), ())
                    setattr(rdb.Cursor, '_execute', _execute)
                    self.module = rdb
                else:
                    raise ValueError('Unknown Rdbhost driver %s' % driver)
            except ImportError:
                pass
            else:
                break
        else:
            raise ImportError('Cannot find the Rdbhost driver')
        self.user = user
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.dsn_dict = dsn_dict = {}
        self.use_dsn = dsn is not None
        if host:
            dsn_dict["host"] = host
        if user:
            dsn_dict["role"] = user
        if password:
            dsn_dict["authcode"] = password
        if dsn is None:
            dsn = []
            if db:
                dsn.append('dbname=%s' % db)
            if user:
                dsn.append('user=%s' % user)
            if password:
                dsn.append('password=%s' % password)
            if host:
                dsn.append('host=%s' % host)
            if port:
                dsn.append('port=%d' % port)
            dsn = ' '.join(dsn)
        self.dsn = dsn
        self.unicodeCols = unicodeCols
        self.schema = kw.pop('schema', None)
        self.dbEncoding = 'utf-8'
        DBAPI.__init__(self, **kw)
