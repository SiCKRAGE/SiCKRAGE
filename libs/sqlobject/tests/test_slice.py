from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Slicing tests
########################################

class Counter(SQLObject):

    number = IntCol(notNull=True)

class TestSlice:

    def setup_method(self, meth):
        setupClass(Counter)
        for i in range(100):
            Counter(number=i)

    def counterEqual(self, counters, value):
        if not supports('limitSelect'):
            return
        assert [c.number for c in counters] == value

    def test_slice(self):
        self.counterEqual(
            Counter.select(None, orderBy='number'), range(100))

        self.counterEqual(
            Counter.select(None, orderBy='number')[10:20],
            range(10, 20))

        self.counterEqual(
            Counter.select(None, orderBy='number')[20:30][:5],
            range(20, 25))

        self.counterEqual(
            Counter.select(None, orderBy='number')[20:30][1:5],
            range(21, 25))

        self.counterEqual(
            Counter.select(None, orderBy='number')[:-10],
            range(0, 90))

        self.counterEqual(
            Counter.select(None, orderBy='number', reversed=True),
            range(99, -1, -1))

        self.counterEqual(
            Counter.select(None, orderBy='-number'),
            range(99, -1, -1))
