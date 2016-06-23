from sqlobject.dbconnection import registerConnection

def builder():
    import sqliteconnection
    return sqliteconnection.SQLiteConnection

registerConnection(['sqlite'], builder)
