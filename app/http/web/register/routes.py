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

from app.config import rate_limit
from app.config.templating import templates
from app.contexts.auth.authentication import login_required
from app.contexts.register.exceptions import InvalidVerificationTokenError, RegisterError
from app.contexts.register.mails import send_email_verification_link
from app.contexts.register.registration import register_user
from app.contexts.register.verification import confirm_user_email, get_verified_email, make_verification_token
from app.contexts.users.repo import UserRepo
from app.contrib import forms
from app.contrib.forms import validate_on_submit
from app.contrib.urls import resolve_redirect_url
from app.contrib.utils import get_client_ip
from app.exceptions import RateLimitedError
from app.http.dependencies import CurrentUser, DbSession, Settings
from app.http.web.register.forms import RegisterForm

routes = RouteGroup()
register_rate_limit = limits.parse("3/minute")


@routes.get_or_post("/register", name="register")
async def register_view(request: Request, dbsession: DbSession, settings: Settings) -> Response:
    status_code = status.HTTP_200_OK
    invited_user_email = request.session.get("invited_user_email", None)
    form = await forms.create_form(request, RegisterForm, data={"email": invited_user_email})
    headers = {}
    limiter = rate_limit.RateLimiter(register_rate_limit, "register")
    match await validate_on_submit(request, form):
        case True:
            try:
                await limiter.hit_or_raise(get_client_ip(request))
                user = await register_user(
                    dbsession,
                    email=form.email.data,  # type: ignore[arg-type]
                    first_name=form.first_name.data,  # type: ignore[arg-type]
                    last_name=form.last_name.data,  # type: ignore[arg-type]
                    plain_password=form.password.data,  # type: ignore[arg-type]
                    language=get_locale().language,
                    timezone=str(get_timezone()),
                    auto_confirm=not settings.register_require_email_confirmation,
                )
                dbsession.add(user)
                await dbsession.commit()

                flash(request).success(_("Your account has been created."))
                tasks: list[BackgroundTask] = []
                if settings.register_require_email_confirmation:
                    token = make_verification_token(user)
                    verification_link = request.url_for("verify_email", token=token)
                    tasks.append(BackgroundTask(send_email_verification_link, user=user, link=verification_link))

                redirect_url = request.url_for("login")
                if settings.register_auto_login:
                    redirect_url = resolve_redirect_url(request, request.url_for("dashboard"))
                    await login(request, user, secret_key=settings.secret_key)

                return RedirectResponse(redirect_url, status.HTTP_302_FOUND, background=BackgroundTasks(tasks))
            except RegisterError as ex:
                flash(request).error(ex.message or _("An error occurred."))
                status_code = status.HTTP_400_BAD_REQUEST

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
        {"form": form, "page_title": _("Register for {app_name}").format(app_name=settings.app_name)},
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


@routes.get("/register/privacy-policy", name="register_privacy_policy")
async def privacy_policy_view(request: Request) -> Response:
    return templates.TemplateResponse(
        request,
        "web/register/privacy_policy.html",
        {
            "page_title": _("Privacy Policy"),
        },
    )


@routes.get("/register/terms-of-service", name="register_terms")
async def terms_and_conditions_view(request: Request) -> Response:
    return templates.TemplateResponse(
        request,
        "web/register/terms_and_conditions.html",
        {
            "page_title": _("Terms and Conditions"),
        },
    )
