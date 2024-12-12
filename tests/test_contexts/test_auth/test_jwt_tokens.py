import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Config
from app.contexts.auth.exceptions import TokenError
from app.contexts.auth.tokens import JWTClaim, TokenIssuer


@pytest.fixture
def token_issuer(settings: Config) -> TokenIssuer:
    return TokenIssuer(
        secret_key=settings.secret_key,
        issuer=settings.app_name,
        audience=settings.app_url,
        access_token_ttl=settings.access_token_ttl,
        refresh_token_ttl=settings.refresh_token_ttl,
    )


class TestTokenIssuer:
    async def test_issue_tokens(self, dbsession: AsyncSession, token_issuer: TokenIssuer) -> None:
        refresh_token, refresh_jit = await token_issuer.issue_refresh_token(
            dbsession, 1, "test", extra_claims={"key": "value"}
        )
        assert refresh_token
        assert refresh_jit

        decoded = token_issuer.parse_token(refresh_token)
        assert decoded["key"] == "value"
        assert decoded["sub"] == "1"
        assert decoded["name"] == "test"

        access_token, access_jit = token_issuer.issue_access_token(refresh_token)
        assert access_token
        assert access_jit

        decoded = token_issuer.parse_token(access_token)
        assert decoded["key"] == "value"
        assert decoded["sub"] == "1"
        assert decoded["name"] == "test"
        assert decoded["refresh_id"] == refresh_jit

    async def test_issue_tokens_invalid_refresh(self, dbsession: AsyncSession, token_issuer: TokenIssuer) -> None:
        with pytest.raises(TokenError):
            token_issuer.issue_access_token("invalid_token")

    async def test_refresh_access_token_rolling(self, dbsession: AsyncSession, token_issuer: TokenIssuer) -> None:
        refresh_token, _ = await token_issuer.issue_refresh_token(dbsession, 1, "test", extra_claims={"key": "value"})
        access_token, _ = token_issuer.issue_access_token(refresh_token)
        old_access = token_issuer.parse_token(access_token)

        time.sleep(0.001)
        refreshed_access_token, refreshed_refresh_token = await token_issuer.refresh_access_token(
            dbsession, refresh_token, rolling=True
        )

        old_refresh = token_issuer.parse_token(refresh_token)
        new_access = token_issuer.parse_token(refreshed_access_token)

        assert refresh_token != refreshed_refresh_token

        assert new_access[JWTClaim.JIT] != old_access[JWTClaim.JIT]

        assert new_access["key"] == old_refresh["key"]
        assert new_access[JWTClaim.NAME] == old_refresh[JWTClaim.NAME]
        assert new_access[JWTClaim.SUBJECT] == old_refresh[JWTClaim.SUBJECT]
        assert new_access[JWTClaim.ISSUER] == old_refresh[JWTClaim.ISSUER]
        assert new_access[JWTClaim.AUDIENCE] == old_refresh[JWTClaim.AUDIENCE]
        assert new_access[JWTClaim.REFRESH_ID] != old_refresh[JWTClaim.JIT]

        assert float(new_access[JWTClaim.EXPIRES]) > float(old_access[JWTClaim.EXPIRES])
        assert float(new_access[JWTClaim.NOT_BEFORE]) > float(old_access[JWTClaim.NOT_BEFORE])
        assert float(new_access[JWTClaim.ISSUED_AT]) > float(old_access[JWTClaim.ISSUED_AT])

    async def test_refresh_access_token_not_rolling(self, dbsession: AsyncSession, token_issuer: TokenIssuer) -> None:
        refresh_token, _ = await token_issuer.issue_refresh_token(dbsession, 1, "test", extra_claims={"key": "value"})
        access_token, _ = token_issuer.issue_access_token(refresh_token)
        old_access = token_issuer.parse_token(access_token)

        refreshed_access_token, refreshed_refresh_token = await token_issuer.refresh_access_token(
            dbsession, refresh_token
        )

        old_refresh = token_issuer.parse_token(refresh_token)
        new_access = token_issuer.parse_token(refreshed_access_token)

        assert refresh_token == refreshed_refresh_token

        assert new_access[JWTClaim.JIT] != old_access[JWTClaim.JIT]

        assert new_access["key"] == old_refresh["key"]
        assert new_access[JWTClaim.NAME] == old_refresh[JWTClaim.NAME]
        assert new_access[JWTClaim.SUBJECT] == old_refresh[JWTClaim.SUBJECT]
        assert new_access[JWTClaim.ISSUER] == old_refresh[JWTClaim.ISSUER]
        assert new_access[JWTClaim.AUDIENCE] == old_refresh[JWTClaim.AUDIENCE]
        assert new_access[JWTClaim.REFRESH_ID] == old_refresh[JWTClaim.JIT]

        assert float(new_access[JWTClaim.EXPIRES]) > float(old_access[JWTClaim.EXPIRES])
        assert float(new_access[JWTClaim.NOT_BEFORE]) > float(old_access[JWTClaim.NOT_BEFORE])
        assert float(new_access[JWTClaim.ISSUED_AT]) > float(old_access[JWTClaim.ISSUED_AT])

    async def test_revoke_refresh_token(self, dbsession: AsyncSession, token_issuer: TokenIssuer) -> None:
        refresh_token, _ = await token_issuer.issue_refresh_token(dbsession, 1, "test", extra_claims={"key": "value"})
        access_token, _ = token_issuer.issue_access_token(refresh_token)
        assert await token_issuer.validate_access_token(dbsession, access_token)
        assert await token_issuer.validate_refresh_token(dbsession, refresh_token)

        await token_issuer.revoke_refresh_token(dbsession, refresh_token)
        assert not await token_issuer.validate_access_token(dbsession, access_token)
        assert not await token_issuer.validate_refresh_token(dbsession, refresh_token)
