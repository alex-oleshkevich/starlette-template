import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.contrib.urls import abs_url_for, media_url, pathname_matches, static_url, url_matches
from tests.factories import RequestFactory, RequestScopeFactory


class TestStaticURL:
    def test_static_url(self) -> None:
        app = Starlette(
            routes=[
                Mount("/static", app=StaticFiles(packages=["tests.contrib"]), name="static"),
                Mount("/custom", app=StaticFiles(packages=["tests.contrib"]), name="custom"),
            ]
        )
        http_request = RequestFactory.build(scope=RequestScopeFactory(app=app))
        assert static_url(http_request, "style.css") == "http://testserver/static/style.css"
        assert static_url(http_request, "style.css", path_name="custom") == "http://testserver/custom/style.css"

    def test_static_url_no_cache(self) -> None:
        app = Starlette(
            routes=[
                Mount("/static", app=StaticFiles(packages=["tests.contrib"]), name="static"),
            ]
        )
        http_request = RequestFactory.build(scope=RequestScopeFactory(app=app))
        assert "v=1" in static_url(http_request, "style.css", no_cache=True).query

    @pytest.mark.parametrize("path", ["http://test.tld/style.css", "https://test.tld/style.css"])
    def test_static_url_with_http_host(self, http_request: Request, path: str) -> None:
        assert str(static_url(http_request, path)).startswith(path)


class TestMediaURL:
    def test_media_url(self, http_request: Request) -> None:
        assert str(media_url(http_request, "file.txt")).startswith("http://testserver/media/file.txt")

    @pytest.mark.parametrize("path", ["http://test.tld/file.txt", "https://test.tld/file.txt"])
    def test_media_url_with_http_host(self, http_request: Request, path: str) -> None:
        assert str(media_url(http_request, path)).startswith(path)


def test_abs_url_for() -> None:
    app = Starlette(
        routes=[
            Route("/admin", lambda request: None, name="admin"),
            Route("/admin/view/{id}", lambda request: None, name="admin.view"),
        ]
    )
    http_request = RequestFactory.build(scope=RequestScopeFactory(app=app))
    assert abs_url_for(http_request, "admin") == "http://testserver/admin"
    assert abs_url_for(http_request, "admin.view", id="test") == "http://testserver/admin/view/test"


class TestURLMatches:
    def test_url_matches(self) -> None:
        app = Starlette(
            routes=[
                Route("/admin", lambda request: None, name="admin"),
                Route("/admin/view/{id}", lambda request: None, name="admin.view"),
            ]
        )
        http_request = RequestFactory.build(scope=RequestScopeFactory(app=app, path="/admin"))
        assert url_matches(http_request, http_request.url_for("admin"))
        assert not url_matches(http_request, http_request.url_for("admin.view", id="test"))


class TestPathnameMatches:
    def test_pathname_matches(self) -> None:
        app = Starlette(
            routes=[
                Route("/admin", lambda request: None, name="admin"),
                Route("/admin/view/{id}", lambda request: None, name="admin.view"),
            ]
        )

        http_request = RequestFactory.build(scope=RequestScopeFactory(app=app, path="/admin"))
        assert pathname_matches(http_request, pathname="admin")
        assert not pathname_matches(http_request, pathname="admin.view", path_params=dict(id="test"))
