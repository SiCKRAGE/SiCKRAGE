from sqlobject import *
from sqlobject.sqlbuilder import *
from sqlobject.tests.dbtest import *

''' Going to test that complex sqlbuilder constructions are never
    prematurely stringified. A straight-forward approach is to use
    Bools, since postgresql wants special formatting in queries.
    The test is whether a call to sqlrepr(x, 'postgres') includes
    the appropriate bool formatting throughout.
'''

class SBButton(SQLObject):
    activated = BoolCol()

def makeClause():
    return SBButton.q.activated==True

def makeSelect():
    return Select(SBButton.q.id, clause=makeClause())

def checkCount(q, c, msg=''):
    print "STRING:", str(q)
    print "POSTGR:", sqlrepr(q, 'postgres')
    assert sqlrepr(q, 'postgres').count("'t'") == c and sqlrepr(q, 'postgres') != str(q), msg

def testSimple():
    setupClass(SBButton)
    yield checkCount, makeClause(), 1
    yield checkCount, makeSelect(), 1

def testMiscOps():
    setupClass(SBButton)
    yield checkCount, AND(makeClause(), makeClause()), 2
    yield checkCount, AND(makeClause(), EXISTS(makeSelect())), 2
    
def testAliased():
    setupClass(SBButton)
    b = Alias(makeSelect(), 'b')
    yield checkCount, b, 1
    yield checkCount, Select(b.q.id), 1
    
    # Table1 & Table2 are treated individually in joins
    yield checkCount, JOIN(None, b), 1
    yield checkCount, JOIN(b, SBButton), 1
    yield checkCount, JOIN(SBButton, b), 1
    yield checkCount, LEFTJOINOn(None, b, SBButton.q.id==b.q.id), 1
    yield checkCount, LEFTJOINOn(b, SBButton, SBButton.q.id==b.q.id), 1
    yield checkCount, LEFTJOINOn(SBButton, b, SBButton.q.id==b.q.id), 1
    
def testTablesUsedSResults():
    setupClass(SBButton)
    
    yield checkCount, SBButton.select(makeClause()).queryForSelect(), 1
    