import typing

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_sqlalchemy import NoResultError

from app import error_codes
from app.contexts.auth.authentication import token_manager
from app.contexts.auth.exceptions import TokenError
from app.contexts.users.models import User
from app.contexts.users.repo import UserRepo
from app.http.exceptions import AuthenticationError


def get_dbsession(request: Request) -> AsyncSession:
    return typing.cast(AsyncSession, request.state.dbsession)


DbSession = typing.Annotated[AsyncSession, Depends(get_dbsession)]


def get_access_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    return header.replace("Bearer ", "")


AccessToken = typing.Annotated[str, Depends(get_access_token)]


async def get_current_user(dbsession: DbSession, access_token: AccessToken) -> User:
    try:
        data = token_manager.parse_token(access_token)
        repo = UserRepo(dbsession)
        user = await repo.get(int(data["sub"]))
    except NoResultError:
        raise AuthenticationError(error_code=error_codes.AUTH_UNAUTHENTICATED)
    except TokenError as ex:
        raise AuthenticationError(error_code=error_codes.AUTH_INVALID_ACCESS_TOKEN) from ex
    else:
        return user


CurrentUser = typing.Annotated[User, Depends(get_current_user)]
