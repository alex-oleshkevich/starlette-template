import dataclasses
import decimal
import typing

import sqlalchemy as sa
from pydantic import BaseModel

from alembic.autogenerate.api import AutogenContext
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


_ETT = typing.TypeVar("_ETT")


class EmbedType(sa.TypeDecorator[_ETT], RendersMigrationType):
    impl = sa.JSON
    cache_ok = True

    def __init__(self, embedded_type: type[_ETT]) -> None:
        self.embedded_type = embedded_type
        super().__init__()

    def process_bind_param(self, value: _ETT | None, dialect: sa.Dialect) -> dict[str, typing.Any] | None:
        if value is not None:
            if isinstance(value, BaseModel):
                return value.model_dump()
            if dataclasses.is_dataclass(value):
                return dataclasses.asdict(value)  # type: ignore[arg-type]
            raise ValueError(f"Unsupported type for EmbedType: {type(value)}")
        return None

    def process_result_value(self, value: dict[str, typing.Any] | None, dialect: sa.Dialect) -> _ETT | None:
        if value is not None:
            return None
        return self.embedded_type(**value)

    def render_item(self, _type: typing.Any, _obj: typing.Any, autogen_context: AutogenContext) -> str:
        autogen_context.imports.add(self.get_import_name())
        autogen_context.imports.add(f"from {self.embedded_type.__module__} import {self.embedded_type.__name__}")
        return f"{self.__class__.__name__}({self.embedded_type.__name__})"
