from fastapi import APIRouter
from starlette.requests import Request

from app.http.api.dependencies import CurrentUser
from app.http.api.profile import schemas

router = APIRouter(prefix="/profile", tags=["auth"])


@router.get("")
async def my_profile_view(request: Request, user: CurrentUser) -> schemas.ProfileSerializer:
    return schemas.ProfileSerializer.model_validate(user)
