import datetime
import time

import itsdangerous
from starlette import status
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_auth import forget_me, login, logout, remember_me
from starlette_babel import gettext_lazy as _
from starlette_dispatch import FromPath, RouteGroup
from starlette_flash import flash

from app.config import crypt, rate_limit, settings
from app.config.crypt import make_password
from app.config.dependencies import DbSession
from app.config.templating import templates
from app.contexts.auth.authentication import (
    authenticate_by_email,
    forgot_password_limiter,
    is_active_guard,
    login_limiter,
)
from app.contexts.auth.exceptions import AuthenticationError
from app.contexts.auth.passwords import CHANGE_PASSWORD_TTL, make_password_reset_link
from app.contexts.users.repo import UserRepo
from app.contrib import forms
from app.contrib.urls import safe_referer
from app.contrib.utils import get_client_ip
from app.exceptions import RateLimitedError
from app.web.login.forms import ChangePasswordForm, ForgotPasswordForm, LoginForm
from app.web.login.mails import send_password_changed_mail, send_reset_password_link_mail

routes = RouteGroup()

login_guards = [
    is_active_guard,
]


@routes.get_or_post("/login", name="login")
async def login_view(request: Request, dbsession: DbSession) -> Response:
    """Login the user."""
    redirect_to = safe_referer(request, request.query_params.get("next", request.url_for("dashboard")))
    if request.user.is_authenticated:
        return RedirectResponse(redirect_to, status_code=status.HTTP_302_FOUND)

    form = await forms.create_form(request, LoginForm)
    status_code = status.HTTP_200_OK
    headers = {}
    limiter = rate_limit.RateLimiter(login_limiter, "login")
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
                await login(request, user)
                await limiter.clear(get_client_ip(request))
                flash(request).success(_("You have been logged in."))
                response = RedirectResponse(redirect_to, status_code=status.HTTP_302_FOUND)
                if form.remember_me.data:
                    response = remember_me(
                        response,
                        settings.secret_key,
                        user,
                        datetime.timedelta(days=60),
                        cookie_secure=True,
                    )
            except AuthenticationError as exc:
                status_code = status.HTTP_400_BAD_REQUEST
                flash(request).error(exc.message or _("Cannot complete authentication."))
            except RateLimitedError as ex:
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                flash(request).error(_("Too many login attempts. Please try again later."))
                headers["Retry-After"] = str(int(time.time()) - ex.stats.reset_time)
                headers["X-RateLimit-Remaining"] = str(ex.stats.remaining)
            else:
                return response
        case False:
            status_code = status.HTTP_400_BAD_REQUEST

    return templates.TemplateResponse(
        request,
        "web/auth/login.html",
        {"form": form},
        status_code=status_code,
        headers=headers,
    )


@routes.post("/logout", name="logout")
async def logout_view(request: Request) -> Response:
    """Logout the user."""
    await logout(request)
    flash(request).success(_("You have been logged out."))
    response = RedirectResponse(request.url_for("login"), status_code=status.HTTP_302_FOUND)
    return forget_me(response)


@routes.get_or_post("/forgot-password", name="forgot_password")
async def forgot_password_view(request: Request, dbsession: DbSession) -> Response:
    """Send reset password link to the user."""
    form = await forms.create_form(request, ForgotPasswordForm)
    limiter = rate_limit.RateLimiter(forgot_password_limiter, "forgot_password")
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
        {"form": form},
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
        email = crypt.verify_signed_value(email).decode()
        user = await user_repo.find_by_email(email)
        if not user:
            raise AuthenticationError(_("User not found."))

        # if this fails then the signature is invalid because the user's password has changed
        crypt.verify_signed_value(signature, max_age=CHANGE_PASSWORD_TTL, secret_key=user.password)
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
