import datetime

import sqlalchemy as sa
from starlette_sqlalchemy import Repo

from app.contexts.auth.models import RefreshToken


class RefreshTokenRepo(Repo[RefreshToken]):
    model_class = RefreshToken
    base_query = sa.select(RefreshToken)

    async def find_by_jit(self, jit: str) -> RefreshToken | None:
        stmt = self.base_query.where(RefreshToken.jit == jit)
        return await self.query.one_or_none(stmt)  # type: ignore

    async def revoke(self, jit: str) -> None:
        stmt = sa.delete(RefreshToken).where(RefreshToken.jit == jit)
        await self.dbsession.execute(stmt)
        await self.dbsession.flush()

    async def create(self, jit: str, user_id: int, expires_at: datetime.datetime) -> RefreshToken:
        instance = RefreshToken(jit=jit, user_id=user_id, expires_at=expires_at)
        self.dbsession.add(instance)
        await self.dbsession.flush()
        return instance
