import datetime
import time

import limits
from starlette import status
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_auth import login
from starlette_babel import get_locale, get_timezone
from starlette_babel import gettext_lazy as _
from starlette_dispatch import FromPath, RouteGroup
from starlette_flash import flash

from app.config import crypto, rate_limit
from app.config.dependencies import CurrentUser, DbSession, Settings
from app.config.templating import templates
from app.contexts.auth.authentication import login_required
from app.contexts.register.exceptions import InvalidVerificationTokenError, RegisterError
from app.contexts.register.mails import send_email_verification_link
from app.contexts.register.verification import confirm_user_email, get_verified_email, make_verification_token
from app.contexts.users.models import User
from app.contexts.users.repo import UserRepo
from app.contrib import forms
from app.contrib.forms import validate_on_submit
from app.contrib.utils import get_client_ip
from app.exceptions import RateLimitedError
from app.web.register.forms import RegisterForm

routes = RouteGroup()
register_rate_limit = limits.parse("3/minute")


@routes.get_or_post("/register", name="register")
async def register_view(request: Request, dbsession: DbSession, settings: Settings) -> Response:
    redirect_url = request.url_for("dashboard")
    user = User(
        timezone=str(get_timezone()),
        language=get_locale().language,
        email_confirmed_at=(
            None if settings.register_require_email_confirmation else datetime.datetime.now(datetime.UTC)
        ),
    )
    status_code = status.HTTP_200_OK
    form = await forms.create_form(request, RegisterForm)
    headers = {}
    limiter = rate_limit.RateLimiter(register_rate_limit, "register")
    match await validate_on_submit(request, form):
        case True:
            try:
                await limiter.hit_or_raise(get_client_ip(request))
                form.populate_obj(user)
                user.password = await crypto.amake_password(form.password.data)  # type: ignore[arg-type]
                dbsession.add(user)
                await dbsession.commit()

                flash(request).success(_("Your account has been created."))
                if settings.register_auto_login:
                    await login(request, user)

                tasks: list[BackgroundTask] = []
                if settings.register_require_email_confirmation:
                    token = make_verification_token(user)
                    verification_link = request.url_for("verify_email", token=token)
                    tasks.append(BackgroundTask(send_email_verification_link, user=user, link=verification_link))

                return RedirectResponse(
                    redirect_url,
                    status_code=status.HTTP_302_FOUND,
                    background=BackgroundTasks(tasks),
                )
            except RateLimitedError as ex:
                flash(request).error(_("Too many registration attempts. Please try again later."))
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                headers["Retry-After"] = str(int(time.time()) - ex.stats.reset_time)
                headers["X-RateLimit-Remaining"] = str(ex.stats.remaining)
        case False:
            status_code = status.HTTP_400_BAD_REQUEST

    return templates.TemplateResponse(
        request,
        "web/register/register.html",
        {"form": form},
        status_code=status_code,
        headers=headers,
    )


@routes.get("/register/verify-email/{token}", name="verify_email")
async def verify_email_view(request: Request, dbsession: DbSession, token: FromPath[str]) -> Response:
    try:
        email = get_verified_email(token)
        if not email:
            raise InvalidVerificationTokenError()

        user_repo = UserRepo(dbsession)
        user = await user_repo.find_by_email(email)
        if not user:
            raise InvalidVerificationTokenError()
        if user.is_confirmed:
            raise InvalidVerificationTokenError()

    except RegisterError as ex:
        return templates.TemplateResponse(
            request,
            "web/register/email_verification.html",
            {
                "message": ex.message,
            },
        )
    else:
        confirm_user_email(user)
        await dbsession.commit()
    return templates.TemplateResponse(
        request,
        "web/register/email_verification.html",
        {"message": _("Your email has been verified.")},
    )


@routes.post("/register/verify-email/resend", name="resend_verify_email")
@login_required()
async def resend_verify_email_view(request: Request, user: CurrentUser) -> Response:
    if user.is_confirmed:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    token = make_verification_token(user)
    verification_link = request.url_for("verify_email", token=token)
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        background=BackgroundTask(send_email_verification_link, user=user, link=verification_link),
    )
