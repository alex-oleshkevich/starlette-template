import typing

import limits
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection

from app.config.crypt import verify_password
from app.contexts.auth.exceptions import InvalidCredentialsError, UserDisabledError
from app.contexts.users import filters as user_filters
from app.contexts.users.models import User
from app.contexts.users.repo import UserRepo

GuardType = typing.Callable[[User], typing.Awaitable[None]]

login_limiter = limits.parse("3/minute")
forgot_password_limiter = limits.parse("1/minute")


async def authenticate_by_email(dbsession: AsyncSession, email: str, password: str) -> User | None:
    repo = UserRepo(dbsession)
    user = await repo.find_by_email(email)
    if not user:
        exc = InvalidCredentialsError()
        exc.add_note("User not found.")
        raise exc

    if not verify_password(user.password, password):
        exc = InvalidCredentialsError()
        exc.add_note("Invalid password.")
        raise exc

    return user


async def is_active_guard(user: User) -> None:
    if not user.is_active:
        raise UserDisabledError


async def db_user_loader(conn: HTTPConnection, user_id: str) -> User | None:
    return await UserRepo(conn.state.dbsession).one_or_none(
        user_filters.IsActive() & user_filters.NotDeleted() & user_filters.ById(user_id)
    )
