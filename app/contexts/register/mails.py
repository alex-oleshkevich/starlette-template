from starlette.datastructures import URL
from starlette_babel import gettext_lazy as _

from app.config.mailers import send_templated_mail
from app.contexts.users.models import User


async def send_email_verification_link(user: User, link: URL) -> None:
    await send_templated_mail(
        to=user.email,
        subject=_("Verify your account"),
        html_template="mails/verify_email.html",
        context={"user": user, "link": link},
    )
