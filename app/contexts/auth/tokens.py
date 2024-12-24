import datetime
import enum
import secrets
import time
import typing

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.exceptions import TokenError
from app.contexts.auth.repos import RefreshTokenRepo

type AccessTokenType = str
type RefreshTokenType = str
type ClaimValue = str | int | float | bool
type TokenPayload = typing.Mapping[str | JWTClaim, ClaimValue]

JWT_ALGORITHM = "HS256"


class JWTClaim(enum.StrEnum):
    EXPIRES = "exp"
    NOT_BEFORE = "nbf"
    ISSUER = "iss"
    AUDIENCE = "aud"
    ISSUED_AT = "iat"
    SUBJECT = "sub"
    JIT = "jit"
    NAME = "name"
    EMAIL = "email"
    REFRESH_ID = "refresh_id"


class TokenIssuer:
    def __init__(
        self,
        secret_key: str,
        issuer: str,
        audience: str,
        access_token_ttl: datetime.timedelta,
        refresh_token_ttl: datetime.timedelta,
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self.secret_key = secret_key
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl

    def issue_access_token(self, refresh_token: str) -> tuple[AccessTokenType, str]:
        jit = "at_{token}".format(token=secrets.token_hex(32))
        decoded = self.parse_token(refresh_token)
        expires_at = datetime.datetime.now(datetime.UTC) + self.access_token_ttl

        # copy claims from refresh token, access token should not have a different scope
        claims = dict(decoded)
        claims.update(
            {
                JWTClaim.JIT: jit,
                JWTClaim.ISSUED_AT: time.time(),
                JWTClaim.NOT_BEFORE: time.time(),
                JWTClaim.EXPIRES: expires_at.timestamp(),
                JWTClaim.REFRESH_ID: decoded[JWTClaim.JIT],
            }
        )

        return self.create_jwt_token(claims), jit

    async def issue_refresh_token(
        self,
        dbsession: AsyncSession,
        subject: str | int,
        subject_name: str,
        *,
        extra_claims: typing.Mapping[str | JWTClaim, ClaimValue] | None = None,
    ) -> tuple[RefreshTokenType, str]:
        jit = "rt_{token}".format(token=secrets.token_hex(32))

        expires_at = datetime.datetime.now(tz=datetime.UTC) + self.refresh_token_ttl
        claims = dict(extra_claims or {})
        claims.update(
            {
                JWTClaim.JIT: jit,
                JWTClaim.SUBJECT: str(subject),
                JWTClaim.NAME: subject_name,
                JWTClaim.ISSUED_AT: time.time(),
                JWTClaim.ISSUER: self.issuer,
                JWTClaim.AUDIENCE: self.audience,
                JWTClaim.NOT_BEFORE: time.time(),
                JWTClaim.EXPIRES: expires_at.timestamp(),
            }
        )

        repo = RefreshTokenRepo(dbsession)
        instance = await repo.create(jit, int(subject), expires_at)
        return self.create_jwt_token(claims), instance.jit

    async def refresh_access_token(
        self, dbsession: AsyncSession, refresh_token: str, *, rolling: bool = False
    ) -> tuple[AccessTokenType, RefreshTokenType]:
        """Refresh the access token using the refresh token.
        If rolling is True, a new refresh token will be issued."""
        if not rolling:
            access_token, _ = self.issue_access_token(refresh_token)
            return access_token, refresh_token

        decoded = self.parse_token(refresh_token)
        repo = RefreshTokenRepo(dbsession)
        await repo.revoke(str(decoded[JWTClaim.JIT]))
        refresh_token, _ = await self.issue_refresh_token(
            dbsession,
            str(decoded[JWTClaim.SUBJECT]),
            str(decoded[JWTClaim.NAME]),
            extra_claims=decoded,
        )
        access_token, _ = self.issue_access_token(refresh_token)
        return access_token, refresh_token

    async def revoke_refresh_token(self, dbsession: AsyncSession, refresh_token: str) -> None:
        decoded = self.parse_token(refresh_token)
        jit = decoded[JWTClaim.JIT]
        repo = RefreshTokenRepo(dbsession)
        await repo.revoke(str(jit))

    async def validate_access_token(self, dbsession: AsyncSession, access_token: str) -> bool:
        """Access token is valid if the refresh token is valid."""
        repo = RefreshTokenRepo(dbsession)
        token = self.parse_token(access_token)
        return await repo.find_by_jit(str(token[JWTClaim.REFRESH_ID])) is not None

    async def validate_refresh_token(self, dbsession: AsyncSession, refresh_token: str) -> bool:
        repo = RefreshTokenRepo(dbsession)
        token = self.parse_token(refresh_token)
        fetched_token = await repo.find_by_jit(str(token[JWTClaim.JIT]))
        return fetched_token is not None

    def create_jwt_token(self, claims: dict[str, ClaimValue], headers: dict[str, str] | None = None) -> str:
        return str(jwt.encode(payload=claims, key=self.secret_key, headers=headers, algorithm=JWT_ALGORITHM))

    def parse_token(self, token: str) -> TokenPayload:
        try:
            decoded = jwt.decode(
                token.encode(),
                verify=True,
                issuer=self.issuer,
                key=self.secret_key,
                audience=self.audience,
                algorithms=[JWT_ALGORITHM],
            )
            return typing.cast(TokenPayload, decoded)
        except Exception as ex:
            raise TokenError(str(ex)) from ex
