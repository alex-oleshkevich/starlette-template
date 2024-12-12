import functools
import typing

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser
from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse, Response
from starlette_auth.authentication import ByIdUserFinder, get_scopes
from starlette_dispatch.route_group import AsyncViewCallable

from app import settings
from app.config.crypto import verify_password
from app.contexts.auth.exceptions import InvalidCredentialsError, TokenError, UserDisabledError
from app.contexts.auth.tokens import JWTClaim, TokenIssuer
from app.contexts.users import filters as user_filters
from app.contexts.users.models import User
from app.contexts.users.repo import UserRepo

GuardType = typing.Callable[[User], typing.Awaitable[None]]
token_manager = TokenIssuer(
    secret_key=settings.secret_key,
    issuer=settings.app_name,
    audience=settings.app_url,
    access_token_ttl=settings.access_token_ttl,
    refresh_token_ttl=settings.refresh_token_ttl,
)


async def authenticate_by_email(dbsession: AsyncSession, email: str, password: str) -> User:
    """Authenticate a user by email and password.

    If the user is not found or the password is invalid, raise an InvalidCredentialsError.
    """
    repo = UserRepo(dbsession)
    user = await repo.find_by_email(email)
    if not user:
        raise InvalidCredentialsError("User not found.")

    if not verify_password(user.password, password):
        raise InvalidCredentialsError("Invalid password.")

    return user


async def is_active_guard(user: User) -> None:
    if not user.is_active:
        raise UserDisabledError()


async def db_user_loader(conn: HTTPConnection, user_id: str) -> User | None:
    return await UserRepo(conn.state.dbsession).one_or_none(
        user_filters.IsActive() & user_filters.NotDeleted() & user_filters.ById(user_id)
    )


def login_required(
    redirect_to: str = "login", status_code: int = status.HTTP_302_FOUND
) -> typing.Callable[[AsyncViewCallable], AsyncViewCallable]:
    def decorator(fn: AsyncViewCallable) -> AsyncViewCallable:
        @functools.wraps(fn)
        async def view(request: Request, **kwargs: typing.Any) -> Response:
            if not request.user.is_authenticated:
                if redirect_to.startswith("/"):
                    return RedirectResponse(redirect_to, status_code=status_code)
                return RedirectResponse(request.url_for(redirect_to), status_code=status_code)
            return await fn(request, **kwargs)

        return view

    return decorator


class JWTBackend(AuthenticationBackend):
    def __init__(self, user_finder: ByIdUserFinder, token_type: str = "Bearer") -> None:
        self.token_type = token_type
        self.user_finder = user_finder

    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
        header = conn.headers.get("authorization", "")

        try:
            token_type, token = header.split(" ", 1)
            if token_type.lower() != self.token_type.lower():
                return None

            decoded = token_manager.parse_token(token)
            if not await token_manager.validate_access_token(conn.state.dbsession, token):
                return None
            user_id = str(decoded.get(JWTClaim.SUBJECT))
        except (TypeError, ValueError, TokenError):
            return None

        user = await self.user_finder(conn, user_id)
        if not user:
            return None

        return AuthCredentials(scopes=get_scopes(user)), user
