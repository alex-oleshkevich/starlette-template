from unittest import mock

import jinja2
from starlette.templating import Jinja2Templates

from app.config.templating import render_to_string


async def test_render_to_string() -> None:
    templates = Jinja2Templates(
        env=jinja2.Environment(
            autoescape=True,
            loader=jinja2.DictLoader(
                {
                    "text.txt": "hello",
                    "context.txt": "hello {{ name }}",
                }
            ),
        ),
    )

    with mock.patch("app.config.templating.templates", templates):
        assert render_to_string("text.txt") == "hello"
        assert render_to_string("context.txt", {"name": "world"}) == "hello world"
