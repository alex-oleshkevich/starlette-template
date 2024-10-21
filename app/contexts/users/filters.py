import sqlalchemy as sa
from starlette_sqlalchemy import RepoFilter

from app.contexts.users.models import User


class ByEmail(RepoFilter[User]):
    def __init__(self, email: str) -> None:
        self.value = email

    def apply(self, stmt: sa.Select[tuple[User]]) -> sa.Select[tuple[User]]:
        return stmt.where(sa.func.lower(User.email) == self.value.lower())


class IsActive(RepoFilter[User]):
    def apply(self, stmt: sa.Select[tuple[User]]) -> sa.Select[tuple[User]]:
        return stmt.where(User.disabled_at.is_(None))


class NotDeleted(RepoFilter[User]):
    def apply(self, stmt: sa.Select[tuple[User]]) -> sa.Select[tuple[User]]:
        return stmt.where(User.deleted_at.is_(None))


class ById(RepoFilter[User]):
    def __init__(self, model_id: int | str) -> None:
        self.value = model_id

    def apply(self, stmt: sa.Select[tuple[User]]) -> sa.Select[tuple[User]]:
        return stmt.where(User.id == int(self.value))
