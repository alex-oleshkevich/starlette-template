import limits
from fastapi import APIRouter, BackgroundTasks
from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import get_locale, get_timezone

from app import settings
from app.config import rate_limit
from app.contexts.register.mails import send_email_verification_link
from app.contexts.register.registration import register_user
from app.contexts.register.verification import make_verification_token
from app.contrib.utils import get_client_ip
from app.http.api.dependencies import DbSession
from app.http.api.register import schemas

router = APIRouter(tags=["Register"])
register_rate_limit = limits.parse("3/minute")


@router.post("/register")
async def register_view(
    request: Request,
    dbsession: DbSession,
    data: schemas.RegisterValidator,
    background_tasks: BackgroundTasks,
    response: Response,
) -> schemas.RegisterSerializer:
    limiter = rate_limit.RateLimiter(register_rate_limit, "register")
    await limiter.hit_or_raise(get_client_ip(request))

    user = await register_user(
        dbsession,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        plain_password=data.password,
        language=get_locale().language,
        timezone=str(get_timezone()),
        auto_confirm=not settings.register_require_email_confirmation,
    )
    dbsession.add(user)
    await dbsession.commit()

    if settings.register_require_email_confirmation:
        token = make_verification_token(user)
        verification_link = request.url_for("verify_email", token=token)
        background_tasks.add_task(send_email_verification_link, user=user, link=verification_link)

    response.status_code = 201
    return schemas.RegisterSerializer.model_validate(user)
