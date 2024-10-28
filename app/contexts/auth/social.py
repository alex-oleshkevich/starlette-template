# social auth
import typing

from authlib.integrations.starlette_client import OAuth

from app.config import settings


class GoogleOAuthUser(typing.TypedDict):
    iss: str
    azp: str
    aud: str
    sub: str
    email: str
    email_verified: bool
    at_hash: str
    nonce: str
    name: str
    given_name: str
    family_name: str
    iat: str
    exp: str
    picture: str
    locale: str


class GoogleOAuth2Token(typing.TypedDict):
    access_token: str
    expires_in: int
    refresh_token: str
    scope: str
    token_type: str
    id_token: str
    expires_at: int
    user_info: GoogleOAuthUser


oauth = OAuth()
oauth.register(
    "google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",  # force to select account
    },
)
