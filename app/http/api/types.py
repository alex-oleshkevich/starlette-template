import decimal
import typing

from pydantic import PlainSerializer, StringConstraints

PriceType = typing.Annotated[decimal.Decimal, PlainSerializer(lambda x: int(x), return_type=int, when_used="json")]
PasswordType = typing.Annotated[str, StringConstraints(min_length=6)]
