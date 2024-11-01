import decimal

import sqlalchemy as sa

from app.config.sqla.types import MoneyType


class TestMoneyType:
    def test_process_bind_param(self) -> None:
        instance = MoneyType()
        assert instance.process_bind_param(decimal.Decimal("1.23"), sa.Dialect()) == decimal.Decimal("123")
        assert instance.process_bind_param(None, sa.Dialect()) is None

    def test_process_result_value(self) -> None:
        instance = MoneyType()
        assert instance.process_result_value(123, sa.Dialect()) == decimal.Decimal("1.23")
        assert instance.process_result_value(None, sa.Dialect()) is None
