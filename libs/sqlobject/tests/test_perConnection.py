from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Per-instance connection
########################################

class TestPerConnection(SQLObject):
    test = StringCol()

def test_perConnection():
    connection = getConnection()
    TestPerConnection.dropTable(connection=connection, ifExists=True)
    TestPerConnection.createTable(connection=connection)
    TestPerConnection(test='test', connection=connection)
    assert len(list(TestPerConnection.select(TestPerConnection.q.test=='test', connection=connection))) == 1
