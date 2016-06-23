from sqlobject.dbconnection import registerConnection

def builder():
    import rdbhostconnection
    return rdbhostconnection.RdbhostConnection

registerConnection(['rdbhost'], builder)
