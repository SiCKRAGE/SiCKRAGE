from sqlobject.dbconnection import registerConnection
#import mysqltypes

def builder():
    import mysqlconnection
    return mysqlconnection.MySQLConnection

registerConnection(['mysql'], builder)
