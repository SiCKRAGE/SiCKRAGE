from sqlobject import *
from sqlobject.tests.dbtest import *

# Test MIN, AVG, MAX, COUNT, SUM


class IntAccumulator(SQLObject):
    value = IntCol()


class FloatAccumulator(SQLObject):
    value = FloatCol()


def test_integer():
    setupClass(IntAccumulator)
    IntAccumulator(value=1)
    IntAccumulator(value=2)
    IntAccumulator(value=3)

    assert IntAccumulator.select().min(IntAccumulator.q.value) == 1
    assert IntAccumulator.select().avg(IntAccumulator.q.value) == 2
    assert IntAccumulator.select().max(IntAccumulator.q.value) == 3
    assert IntAccumulator.select().sum(IntAccumulator.q.value) == 6

    assert IntAccumulator.select(IntAccumulator.q.value > 1).max(IntAccumulator.q.value) == 3
    assert IntAccumulator.select(IntAccumulator.q.value > 1).sum(IntAccumulator.q.value) == 5


def floatcmp(f1, f2):
    if abs(f1-f2) < 0.1:
        return 0
    if f1 < f2:
        return 1
    return -1

def test_float():
    setupClass(FloatAccumulator)
    FloatAccumulator(value=1.2)
    FloatAccumulator(value=2.4)
    FloatAccumulator(value=3.8)

    assert floatcmp(FloatAccumulator.select().min(FloatAccumulator.q.value), 1.2) == 0
    assert floatcmp(FloatAccumulator.select().avg(FloatAccumulator.q.value), 2.5) == 0
    assert floatcmp(FloatAccumulator.select().max(FloatAccumulator.q.value), 3.8) == 0
    assert floatcmp(FloatAccumulator.select().sum(FloatAccumulator.q.value), 7.4) == 0


def test_many():
    setupClass(IntAccumulator)
    IntAccumulator(value=1)
    IntAccumulator(value=1)
    IntAccumulator(value=2)
    IntAccumulator(value=2)
    IntAccumulator(value=3)
    IntAccumulator(value=3)

    attribute = IntAccumulator.q.value
    assert IntAccumulator.select().accumulateMany(
        ("MIN", attribute), ("AVG", attribute), ("MAX", attribute),
        ("COUNT", attribute), ("SUM", attribute)
    ) == (1, 2, 3, 6, 12)

    assert IntAccumulator.select(distinct=True).accumulateMany(
        ("MIN", attribute), ("AVG", attribute), ("MAX", attribute),
        ("COUNT", attribute), ("SUM", attribute)
    ) == (1, 2, 3, 3, 6)
