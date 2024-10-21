from starlette.datastructures import URL
from starlette.requests import Request

from app.config import crypt, settings
from app.contexts.users.models import User

CHANGE_PASSWORD_TTL = 3600


def make_password_reset_link(request: Request, user: User) -> URL:
    """Create a password reset link for the user.
    The link is signed with the user's password hash.
    If the user changes their password, the link becomes invalid.
    """
    email = crypt.sign_value(user.email, secret_key=settings.secret_key)
    signature = crypt.sign_value(user.email, secret_key=user.password)
    return request.url_for("change_password", email=email.decode(), signature=signature.decode())
