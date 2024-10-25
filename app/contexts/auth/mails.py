from starlette.datastructures import URL
from starlette_babel import gettext_lazy as _

from app.config.mailers import send_templated_mail
from app.contexts.users.models import User


async def send_reset_password_link_mail(user: User, link: URL) -> None:
    await send_templated_mail(
        to=user.email,
        subject=_("Reset your password"),
        html_template="mails/reset_password.html",
        context={"user": user, "link": link},
    )


async def send_password_changed_mail(user: User) -> None:
    await send_templated_mail(
        to=user.email,
        subject=_("Your password has been changed"),
        html_template="mails/password_changed.html",
        context={"user": user},
    )
