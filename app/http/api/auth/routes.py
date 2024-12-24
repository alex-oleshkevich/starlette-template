import datetime
import logging

import limits
from fastapi import APIRouter, BackgroundTasks, Request

from app import error_codes, settings
from app.config import rate_limit
from app.config.events import events
from app.contexts.auth.authentication import authenticate_by_email, is_active_guard, token_manager
from app.contexts.auth.events import UserAuthenticated
from app.contexts.auth.exceptions import AuthenticationError, TokenError
from app.contexts.auth.mails import send_reset_password_link_mail
from app.contexts.auth.passwords import make_password_reset_link
from app.contexts.auth.tokens import JWTClaim
from app.contexts.users.repo import UserRepo
from app.contrib.utils import get_client_ip
from app.http.api.auth import schemas
from app.http.api.dependencies import DbSession
from app.http.exceptions import BadRequestError

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)
login_rate_limit = limits.parse("3/minute")
forgot_password_rate_limit = limits.parse("1/minute")

login_guards = [
    is_active_guard,
]


@router.post("/login")
async def login_view(request: Request, dbsession: DbSession, body: schemas.LoginValidator) -> schemas.LoginSerializer:
    try:
        limiter = rate_limit.RateLimiter(login_rate_limit, "api_login")
        await limiter.hit_or_raise(get_client_ip(request))

        user = await authenticate_by_email(dbsession, body.email, body.password)
        for guard in login_guards:
            await guard(user)

        user.last_sign_in = datetime.datetime.now(datetime.UTC)
        refresh_token, _ = await token_manager.issue_refresh_token(
            dbsession,
            subject=user.id,
            subject_name=user.display_name,
            extra_claims={JWTClaim.EMAIL: user.email},
        )
        access_token, _ = token_manager.issue_access_token(refresh_token)
    except AuthenticationError as ex:
        logger.warning("login error", exc_info=True, extra={"email": body.email, "ip": get_client_ip(request)})
        raise BadRequestError(error_code=ex.error_code) from ex
    else:
        await dbsession.commit()
        await limiter.clear(get_client_ip(request))
        await events.emit(UserAuthenticated(user_id=user.id))
        return schemas.LoginSerializer(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout_view(
    request: Request, dbsession: DbSession, body: schemas.LogoutValidator
) -> schemas.LogoutSerializer:
    try:
        await token_manager.revoke_refresh_token(dbsession, body.refresh_token)
    except TokenError as ex:
        raise BadRequestError(error_code=error_codes.AUTH_INVALID_REFRESH_TOKEN) from ex
    else:
        await dbsession.commit()
        return schemas.LogoutSerializer()


@router.post("/refresh")
async def refresh_token_view(
    request: Request, dbsession: DbSession, body: schemas.RefreshTokenValidator
) -> schemas.RefreshTokenSerializer:
    try:
        if not await token_manager.validate_refresh_token(dbsession, body.refresh_token):
            raise BadRequestError(error_code=error_codes.AUTH_INVALID_REFRESH_TOKEN)

        access_token, refresh_token = await token_manager.refresh_access_token(
            dbsession, body.refresh_token, rolling=settings.session_rolling
        )
    except TokenError as ex:
        raise BadRequestError(error_code=error_codes.AUTH_INVALID_REFRESH_TOKEN) from ex
    else:
        await dbsession.commit()
        return schemas.RefreshTokenSerializer(
            access_token=access_token,
            refresh_token=refresh_token,
        )


@router.post("/reset-password")
async def reset_password_view(
    request: Request, dbsession: DbSession, body: schemas.ResetPasswordValidator, background_tasks: BackgroundTasks
) -> schemas.ResetPasswordSerializer:
    limiter = rate_limit.RateLimiter(forgot_password_rate_limit, "forgot_password")
    await limiter.hit_or_raise(get_client_ip(request))

    user_repo = UserRepo(dbsession)
    user = await user_repo.find_by_email(body.email)
    if user:
        link = make_password_reset_link(request, user)
        background_tasks.add_task(send_reset_password_link_mail, user, link)
    return schemas.ResetPasswordSerializer()
