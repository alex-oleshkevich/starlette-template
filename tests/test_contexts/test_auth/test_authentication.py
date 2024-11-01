import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.contexts.auth import authentication
from app.contexts.auth.exceptions import InvalidCredentialsError
from tests.factories import UserFactory


async def test_authenticate_by_email(dbsession: AsyncSession) -> None:
    user = UserFactory()
    assert await authentication.authenticate_by_email(dbsession, user.email, "password") == user


async def test_authenticate_by_email_no_user(dbsession: AsyncSession) -> None:
    with pytest.raises(InvalidCredentialsError, match="User not found."):
        await authentication.authenticate_by_email(dbsession, "missing@user.tld", "password")


async def test_authenticate_by_email_invalid_password(dbsession: AsyncSession) -> None:
    user = UserFactory()
    with pytest.raises(InvalidCredentialsError, match="Invalid password."):
        await authentication.authenticate_by_email(dbsession, user.email, "invalidpassword")


class TestDbUserLoader:
    async def test_load_user(self, http_request: Request) -> None:
        user = UserFactory()
        assert await authentication.db_user_loader(http_request, str(user.id)) == user

    async def test_ignores_inactive(self, http_request: Request) -> None:
        user = UserFactory(disabled_at=datetime.datetime.now(datetime.UTC))
        assert await authentication.db_user_loader(http_request, str(user.id)) is None

    async def test_ignores_deleted(self, http_request: Request) -> None:
        user = UserFactory(deleted_at=datetime.datetime.now(datetime.UTC))
        assert await authentication.db_user_loader(http_request, str(user.id)) is None
