from sqlobject.dbconnection import registerConnection

def builder():
    import sybaseconnection
    return sybaseconnection.SybaseConnection

registerConnection(['sybase'], builder)
