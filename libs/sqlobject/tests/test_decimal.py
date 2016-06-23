# -*- coding: koi8-r -*-

from decimal import Decimal
from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Decimal columns
########################################

class DecimalTable(SQLObject):
    name = UnicodeCol(length=255)
    col1 = DecimalCol(size=6, precision=4)
    col2 = DecimalStringCol(size=6, precision=4)
    col3 = DecimalStringCol(size=6, precision=4, quantize=True)

if supports('decimalColumn'):
    def test_1_decimal():
        setupClass(DecimalTable)
        d = DecimalTable(name='test', col1=21.12, col2='10.01', col3='10.01')
        # psycopg2 returns float as Decimal
        if isinstance(d.col1, Decimal):
            assert d.col1 == Decimal("21.12")
        else:
            assert d.col1 == 21.12
        assert d.col2 == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col2'].to_python('10.01',
            d._SO_validatorState) == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col2'].from_python('10.01',
            d._SO_validatorState) == "10.01"
        assert d.col3 == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col3'].to_python('10.01',
            d._SO_validatorState) == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col3'].from_python('10.01',
            d._SO_validatorState) == "10.0100"

    def test_2_decimal():
        setupClass(DecimalTable)
        d = DecimalTable(name='test', col1=Decimal("21.12"),
            col2=Decimal('10.01'), col3=Decimal('10.01'))
        assert d.col1 == Decimal("21.12")
        assert d.col2 == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col2'].to_python(Decimal('10.01'),
            d._SO_validatorState) == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col2'].from_python(Decimal('10.01'),
            d._SO_validatorState) == "10.01"
        assert d.col3 == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col3'].to_python(Decimal('10.01'),
            d._SO_validatorState) == Decimal("10.01")
        assert DecimalTable.sqlmeta.columns['col3'].from_python(Decimal('10.01'),
            d._SO_validatorState) == "10.0100"
