from sqlobject.dbconnection import registerConnection

def builder():
    import mssqlconnection
    return mssqlconnection.MSSQLConnection

registerConnection(['mssql'], builder)
