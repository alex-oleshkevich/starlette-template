import sqlalchemy as sa
from starlette_sqlalchemy import Repo

from app.contexts.users import filters
from app.contexts.users.models import User


class UserRepo(Repo[User]):
    model_class = User
    base_query = sa.select(User).where(User.deleted_at.is_(None))

    async def find_by_email(self, email: str) -> User | None:
        return await self.one_or_none(filters.ByEmail(email))
