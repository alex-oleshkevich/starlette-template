import decimal
import typing

import sqlalchemy as sa

from app.config.sqla.migrations import RendersMigrationType


class MoneyType(sa.TypeDecorator[decimal.Decimal], RendersMigrationType):
    impl = sa.Numeric(precision=12, scale=2)

    def process_bind_param(self, value: decimal.Decimal | None, dialect: sa.Dialect) -> typing.Any:
        if value is not None:
            return value * 100
        return None

    def process_result_value(self, value: typing.Any | None, dialect: sa.Dialect) -> decimal.Decimal | None:
        if value is not None:
            return decimal.Decimal(value) / 100
        return None
