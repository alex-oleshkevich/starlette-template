from unittest import mock

import jinja2
from mailers.pytest_plugin import Mailbox
from starlette.templating import Jinja2Templates

from app.config.mailers import send_mail, send_templated_mail
from app.config.settings import Config


async def test_from_address(mailbox: Mailbox, settings: Config) -> None:
    await send_mail(to="me@me.com", subject="Test", text="Test body")
    assert mailbox[0]["from"] == f"{settings.mail_default_from_name} <{settings.mail_default_from_address}>"


async def test_send_mail(mailbox: Mailbox) -> None:
    await send_mail(to="me@me.com", subject="Test", text="Test body")
    assert mailbox[0]["to"] == "me@me.com"
    assert mailbox[0]["subject"] == "Test"
    assert mailbox[0].get_content() == "Test body\n"


async def test_send_templated_mail(mailbox: Mailbox) -> None:
    templates = Jinja2Templates(
        env=jinja2.Environment(
            autoescape=True,
            loader=jinja2.DictLoader(
                {
                    "text.txt": "Test body",
                    "text.html": "<b>Test body</b>",
                }
            ),
        ),
    )

    with mock.patch("app.config.templating.templates", templates):
        await send_templated_mail(to="me@me.com", subject="Test", text_template="text.txt", html_template="text.html")
    assert len(mailbox) == 1
    assert mailbox[0]["to"] == "me@me.com"
    assert mailbox[0]["subject"] == "Test"
    assert mailbox[0].get_payload(0).get_content() == "Test body\n"  # type: ignore[union-attr]
    assert mailbox[0].get_payload(1).get_content() == "<html><head></head><body><b>Test body</b>\n</body></html>"  # type: ignore[union-attr]
