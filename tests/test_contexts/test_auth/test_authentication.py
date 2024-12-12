import datetime
from unittest import mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.contexts.auth import authentication
from app.contexts.auth.exceptions import InvalidCredentialsError
from app.contexts.auth.tokens import TokenIssuer
from app.contexts.users.models import User
from tests.factories import RequestFactory, RequestScopeFactory, UserFactory


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


class TestJWTBackend:
    async def test_authenticate(self, user: User, token_manager: TokenIssuer, dbsession: AsyncSession) -> None:
        refresh_token, _ = await token_manager.issue_refresh_token(
            dbsession,
            subject=user.id,
            subject_name=user.display_name,
            extra_claims={authentication.JWTClaim.EMAIL: user.email},
        )
        access_token, _ = token_manager.issue_access_token(refresh_token)

        request = RequestFactory(
            scope=RequestScopeFactory(
                user=user,
                headers=[
                    (b"authorization", f"Bearer {access_token}".encode("utf-8")),
                ],
                state={
                    "dbsession": dbsession,
                },
            )
        )

        backend = authentication.JWTBackend(
            user_finder=authentication.db_user_loader,
            token_type="bearer",
        )
        auth_credentials = await backend.authenticate(request)
        assert auth_credentials
        credentials, auth_user = auth_credentials
        assert user.identity == auth_user.identity

    async def test_invalid_token_type(self, user: User, token_manager: TokenIssuer, dbsession: AsyncSession) -> None:
        refresh_token, _ = await token_manager.issue_refresh_token(
            dbsession,
            subject=user.id,
            subject_name=user.display_name,
            extra_claims={authentication.JWTClaim.EMAIL: user.email},
        )
        access_token, _ = token_manager.issue_access_token(refresh_token)

        request = RequestFactory(
            scope=RequestScopeFactory(
                user=user,
                headers=[
                    (b"authorization", f"Auth {access_token}".encode("utf-8")),
                ],
                state={
                    "dbsession": dbsession,
                },
            )
        )

        backend = authentication.JWTBackend(
            user_finder=authentication.db_user_loader,
            token_type="bearer",
        )
        assert not await backend.authenticate(request)

    async def test_invalid_jwt(self, user: User, token_manager: TokenIssuer, dbsession: AsyncSession) -> None:
        refresh_token, _ = await token_manager.issue_refresh_token(
            dbsession,
            subject=user.id,
            subject_name=user.display_name,
            extra_claims={authentication.JWTClaim.EMAIL: user.email},
        )
        access_token, _ = token_manager.issue_access_token(refresh_token)

        request = RequestFactory(
            scope=RequestScopeFactory(
                user=user,
                headers=[
                    (b"authorization", b"Bearer blah"),
                ],
                state={
                    "dbsession": dbsession,
                },
            )
        )

        backend = authentication.JWTBackend(
            user_finder=authentication.db_user_loader,
            token_type="bearer",
        )
        assert not await backend.authenticate(request)

    async def test_no_user(self, user: User, token_manager: TokenIssuer, dbsession: AsyncSession) -> None:
        refresh_token, _ = await token_manager.issue_refresh_token(
            dbsession,
            subject=user.id,
            subject_name=user.display_name,
            extra_claims={authentication.JWTClaim.EMAIL: user.email},
        )
        access_token, _ = token_manager.issue_access_token(refresh_token)

        request = RequestFactory(
            scope=RequestScopeFactory(
                user=user,
                headers=[
                    (b"authorization", f"Bearer {access_token}".encode()),
                ],
                state={
                    "dbsession": dbsession,
                },
            )
        )

        backend = authentication.JWTBackend(
            user_finder=mock.AsyncMock(return_value=None),
            token_type="bearer",
        )
        assert not await backend.authenticate(request)

    async def test_revoked_token(self, user: User, token_manager: TokenIssuer, dbsession: AsyncSession) -> None:
        refresh_token, _ = await token_manager.issue_refresh_token(
            dbsession,
            subject=user.id,
            subject_name=user.display_name,
            extra_claims={authentication.JWTClaim.EMAIL: user.email},
        )
        access_token, _ = token_manager.issue_access_token(refresh_token)
        await token_manager.revoke_refresh_token(dbsession, refresh_token)

        request = RequestFactory(
            scope=RequestScopeFactory(
                user=user,
                headers=[
                    (b"authorization", f"Bearer {access_token}".encode()),
                ],
                state={
                    "dbsession": dbsession,
                },
            )
        )

        backend = authentication.JWTBackend(
            user_finder=authentication.db_user_loader,
            token_type="bearer",
        )
        assert not await backend.authenticate(request)
