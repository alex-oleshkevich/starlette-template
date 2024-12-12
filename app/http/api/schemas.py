from __future__ import annotations

import typing

from pydantic import BaseModel
from starlette_sqlalchemy import Page

M = typing.TypeVar("M")
T = typing.TypeVar("T", bound=BaseModel)


class Paginated(BaseModel, typing.Generic[T]):
    page: int
    page_size: int
    total: int
    items: list[T]

    @classmethod
    def from_page(cls, page: Page[M], serializer: type[T]) -> Paginated[T]:
        return Paginated(
            page=page.page,
            page_size=page.page_size,
            total=page.total,
            items=[serializer.model_validate(obj) for obj in page],
        )
