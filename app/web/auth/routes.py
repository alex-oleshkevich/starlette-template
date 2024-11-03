import datetime
import time

import itsdangerous
import limits
import structlog
from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import StarletteOAuth2App
from authlib.oauth2.rfc6749 import OAuth2Token
from starlette import status
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_auth import login, logout
from starlette_babel import gettext_lazy as _
from starlette_dispatch import FromPath, RouteGroup
from starlette_flash import flash

from app.config import crypto, rate_limit, settings
from app.config.crypto import make_password
from app.config.dependencies import DbSession
from app.config.templating import templates
from app.contexts.auth.authentication import (
    authenticate_by_email,
    is_active_guard,
)
from app.contexts.auth.exceptions import AuthenticationError, UserNotRegisteredError
from app.contexts.auth.mails import send_password_changed_mail, send_reset_password_link_mail
from app.contexts.auth.passwords import CHANGE_PASSWORD_TTL, make_password_reset_link
from app.contexts.auth.social import oauth
from app.contexts.users.repo import UserRepo
from app.contrib import forms
from app.contrib.urls import resolve_redirect_url, safe_referer
from app.contrib.utils import get_client_ip
from app.exceptions import RateLimitedError
from app.web.auth.forms import ChangePasswordForm, ForgotPasswordForm, LoginForm

routes = RouteGroup()
login_rate_limit = limits.parse("3/minute")
forgot_password_rate_limit = limits.parse("1/minute")
login_guards = [
    is_active_guard,
]


logger = structlog.get_logger(__name__)


@routes.get_or_post("/login", name="login")
async def login_view(request: Request, dbsession: DbSession) -> Response:
    """Login the user."""
    if request.user.is_authenticated:
        return RedirectResponse(request.url_for("dashboard"), status_code=status.HTTP_302_FOUND)

    form = await forms.create_form(request, LoginForm)
    status_code = status.HTTP_200_OK
    headers = {}
    limiter = rate_limit.RateLimiter(login_rate_limit, "login")
    match await forms.validate_on_submit(request, form):
        case True:
            try:
                await limiter.hit_or_raise(get_client_ip(request))
                email = form.email.data
                password = form.password.data
                assert email and password
                user = await authenticate_by_email(dbsession, email, password)
                assert user
                for guard in login_guards:
                    await guard(user)

                user.last_sign_in = datetime.datetime.now(datetime.UTC)
                await dbsession.commit()
                await login(request, user, settings.secret_key)
                await limiter.clear(get_client_ip(request))
                flash(request).success(_("You have been logged in."))

                redirect_to = resolve_redirect_url(request, request.url_for("dashboard"))
                return RedirectResponse(redirect_to, status_code=status.HTTP_302_FOUND)
            except AuthenticationError as exc:
                await logger.awarning("login error", exc_info=True, email=form.email.data, ip=get_client_ip(request))
                status_code = status.HTTP_400_BAD_REQUEST
                flash(request).error(exc.message or _("Cannot complete authentication."))
            except RateLimitedError as ex:
                await logger.awarning("login rate limited", exc_info=True, ip=get_client_ip(request))
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                flash(request).error(_("Too many login attempts. Please try again later."))
                headers["Retry-After"] = str(int(time.time()) - ex.stats.reset_time)
                headers["X-RateLimit-Remaining"] = str(ex.stats.remaining)
        case False:
            await logger.awarning("login error", exc_info=True, email=form.email.data, ip=get_client_ip(request))
            status_code = status.HTTP_400_BAD_REQUEST

    return templates.TemplateResponse(
        request,
        "web/auth/login.html",
        {"form": form, "page_title": _("Sign in into {app_name}").format(app_name=settings.app_name)},
        status_code=status_code,
        headers=headers,
    )


@routes.post("/logout", name="logout")
async def logout_view(request: Request) -> Response:
    """Logout the user."""
    await logout(request)
    flash(request).success(_("You have been logged out."))
    return RedirectResponse(request.url_for("login"), status_code=status.HTTP_302_FOUND)


@routes.get_or_post("/forgot-password", name="forgot_password")
async def forgot_password_view(request: Request, dbsession: DbSession) -> Response:
    """Send reset password link to the user."""
    form = await forms.create_form(request, ForgotPasswordForm)
    limiter = rate_limit.RateLimiter(forgot_password_rate_limit, "forgot_password")
    status_code = status.HTTP_200_OK
    headers = {}
    match await forms.validate_on_submit(request, form):
        case True:
            try:
                await limiter.hit_or_raise(get_client_ip(request))

                user_repo = UserRepo(dbsession)
                assert form.email.data
                user = await user_repo.find_by_email(form.email.data)
                background_tasks: BackgroundTasks | None = None
                if user:
                    link = make_password_reset_link(request, user)
                    background_tasks = BackgroundTasks([BackgroundTask(send_reset_password_link_mail, user, link)])
                return RedirectResponse(
                    request.url_for("forgot_password_sent"),
                    status_code=status.HTTP_302_FOUND,
                    background=background_tasks,
                )
            except AuthenticationError as exc:
                flash(request).error(exc.message or _("Cannot complete password reset."))
            except RateLimitedError as ex:
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                flash(request).error(_("Too many requests. Please try again later."))
                headers["Retry-After"] = str(int(time.time()) - ex.stats.reset_time)
                headers["X-RateLimit-Remaining"] = str(ex.stats.remaining)

        case False:
            status_code = status.HTTP_400_BAD_REQUEST

    return templates.TemplateResponse(
        request,
        "web/auth/forgot_password.html",
        {"form": form, "page_title": _("Reset password")},
        status_code=status_code,
        headers=headers,
    )


@routes.get("/forgot-password/sent", name="forgot_password_sent")
async def forgot_password_success_view(request: Request) -> Response:
    """Show message that the reset password link has been sent."""
    return templates.TemplateResponse(request, "web/auth/forgot_password_sent.html")


@routes.get_or_post("/change-password/{email}/{signature}", name="change_password")
async def change_password_view(
    request: Request,
    dbsession: DbSession,
    email: FromPath[str],
    signature: FromPath[str],
) -> Response:
    """Change user password."""
    try:
        user_repo = UserRepo(dbsession)
        email = crypto.get_signed_value(email).decode()
        user = await user_repo.find_by_email(email)
        if not user:
            raise AuthenticationError(_("User not found."))

        # if this fails then the signature is invalid because the user's password has changed
        crypto.get_signed_value(signature, max_age=CHANGE_PASSWORD_TTL, secret_key=user.password)
    except (itsdangerous.BadData, AuthenticationError):
        return templates.TemplateResponse(
            request,
            "web/auth/change_password_invalid_token.html",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    form = await forms.create_form(request, ChangePasswordForm)
    if await forms.validate_on_submit(request, form):
        assert form.password.data
        user.password = make_password(form.password.data)
        await dbsession.commit()
        flash(request).success(_("Your password has been changed."))
        return RedirectResponse(
            request.url_for("login"),
            status_code=status.HTTP_302_FOUND,
            background=BackgroundTask(send_password_changed_mail, user),
        )

    return templates.TemplateResponse(request, "web/auth/change_password.html", {"form": form})


@routes.get("/social/google", name="auth.social.google")
async def google_auth_view(request: Request) -> Response:
    google: StarletteOAuth2App = oauth.create_client("google")
    redirect_uri = request.url_for("auth.social.google_callback")
    request.session["next"] = str(request.query_params.get("next", request.url_for("dashboard")))
    return await google.authorize_redirect(request, redirect_uri)  # type: ignore[no-any-return]


@routes.get("/social/google/callback", name="auth.social.google_callback")
async def google_auth_callback_view(request: Request, dbsession: DbSession) -> Response:
    try:
        google: StarletteOAuth2App = oauth.create_client("google")
        token: OAuth2Token = await google.authorize_access_token(request)
        repo = UserRepo(dbsession)
        user = await repo.find_by_email(token["userinfo"]["email"])
        if not user:
            raise UserNotRegisteredError()

        await login(request, user, secret_key=settings.secret_key)
        next_url = request.session.get("next", request.url_for("dashboard"))
        redirect_to = safe_referer(request, next_url)
        return RedirectResponse(redirect_to, status_code=status.HTTP_302_FOUND)
    except (OAuthError, UserNotRegisteredError, KeyError):
        await logger.awarning("social login error", exc_info=True, provider="google")
        flash(request).error(_("Cannot authenticated with Google, try logging in with email or create an account."))
        return RedirectResponse(request.url_for("login"), status_code=status.HTTP_302_FOUND)
