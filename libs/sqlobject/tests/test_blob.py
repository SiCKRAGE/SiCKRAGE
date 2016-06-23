from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## BLOB columns
########################################

class ImageData(SQLObject):
    image = BLOBCol(default='emptydata', length=65535)

def test_BLOBCol():
    if not supports('blobData'):
        return
    setupClass(ImageData)
    data = ''.join([chr(x) for x in range(256)])

    prof = ImageData()
    prof.image = data
    iid = prof.id

    ImageData._connection.cache.clear()

    prof2 = ImageData.get(iid)
    assert prof2.image == data
