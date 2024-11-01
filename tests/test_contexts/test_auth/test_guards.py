import datetime

import pytest

from app.contexts.auth import authentication
from tests.factories import UserFactory


async def test_is_active_guard() -> None:
    user = UserFactory(disabled_at=None)
    assert await authentication.is_active_guard(user) is None  # type: ignore[func-returns-value]

    user = UserFactory(disabled_at=datetime.datetime.now(datetime.UTC))
    with pytest.raises(authentication.UserDisabledError):
        await authentication.is_active_guard(user)
