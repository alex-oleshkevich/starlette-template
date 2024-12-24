from fastapi import APIRouter, BackgroundTasks
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from app.config.crypto import make_password, verify_password
from app.contexts.auth.mails import send_password_changed_mail
from app.http.api.dependencies import CurrentUser, DbSession
from app.http.api.profile import schemas
from app.http.exceptions import ValidationError

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("")
async def my_profile_view(request: Request, user: CurrentUser) -> schemas.ProfileSerializer:
    return schemas.ProfileSerializer.model_validate(user)


@router.patch("")
async def update_profile_view(
    request: Request, dbsession: DbSession, user: CurrentUser, body: schemas.ProfileUpdateValidator
) -> schemas.ProfileUpdateSerializer:
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)

    await dbsession.commit()
    return schemas.ProfileUpdateSerializer.model_validate(user)


@router.post("/change-password")
async def change_password_view(
    request: Request,
    dbsession: DbSession,
    user: CurrentUser,
    body: schemas.ChangePasswordValidator,
    background_tasks: BackgroundTasks,
) -> schemas.ChangePasswordSerializer:
    if not verify_password(user.password, body.current_password):
        raise ValidationError(_("Current password is incorrect."))

    if body.password != body.password_confirm:
        raise ValidationError(_("Passwords do not match."))

    user.password = make_password(body.password)
    await dbsession.commit()

    background_tasks.add_task(send_password_changed_mail, user)

    return schemas.ChangePasswordSerializer()
