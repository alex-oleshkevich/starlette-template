import contextlib
import datetime

import itsdangerous

from app.config import crypto, settings
from app.contexts.users.models import User


def make_verification_token(user: User) -> str:
    return crypto.sign_value(user.email, secret_key=settings.secret_key).decode()


def get_verified_email(token: str) -> str | None:
    with contextlib.suppress(itsdangerous.BadData):
        return crypto.get_signed_value(token, max_age=3600, secret_key=settings.secret_key).decode()
    return None


def confirm_user_email(user: User) -> None:
    user.email_confirmed_at = datetime.datetime.now(datetime.UTC)
