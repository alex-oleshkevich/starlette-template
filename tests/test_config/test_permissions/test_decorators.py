import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.config.permissions.decorators import permission_required
from app.contrib.permissions import AccessDeniedError, Permission
from tests.factories import AccessContextFactory, RequestFactory, RequestScopeFactory

_permission = Permission("test:permission")


async def _view(request: Request) -> Response:
    return Response("ok")


class TestPermissionRequired:
    async def test_allow_access(self) -> None:
        request = RequestFactory(
            scope=RequestScopeFactory(
                state={
                    "access_context": AccessContextFactory(
                        permissions={_permission},
                    )
                },
            ),
        )
        view = permission_required(_permission)(_view)
        response = await view(request)
        assert response.status_code == 200
        assert response.body == b"ok"

    async def test_deny_access(self) -> None:
        request = RequestFactory(
            scope=RequestScopeFactory(
                state={
                    "access_context": AccessContextFactory(
                        permissions={},
                    )
                },
            ),
        )
        with pytest.raises(AccessDeniedError):
            view = permission_required(_permission)(_view)
            await view(request)

    async def test_requires_request(self) -> None:
        async def view() -> Response:
            return Response("ok")

        with pytest.raises(ValueError, match="The first positional argument must be a Request instance"):
            wrapped_view = permission_required(_permission)(view)
            await wrapped_view()
