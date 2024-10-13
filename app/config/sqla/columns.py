import datetime
import typing

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column

IntPk = typing.Annotated[int, mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)]
DateTimeTz = typing.Annotated[datetime.datetime, mapped_column(sa.DateTime(timezone=True))]
AutoCreatedAt = typing.Annotated[
    datetime.datetime,
    mapped_column(
        sa.DateTime(timezone=True),
        default=datetime.datetime.now,
        server_default=sa.func.now(),
        nullable=False,
    ),
]
AutoUpdatedAt = typing.Annotated[
    datetime.datetime,
    mapped_column(
        sa.DateTime(timezone=True),
        default=datetime.datetime.now,
        server_default=sa.func.now(),
        nullable=False,
        onupdate=datetime.datetime.now,
        server_onupdate=sa.func.now(),
    ),
]
