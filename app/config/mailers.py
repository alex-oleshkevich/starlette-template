import typing

from mailers import Email, Mailer, create_transport_from_url
from mailers.message import Recipients
from mailers.preprocessors.cssliner import css_inliner
from starlette_babel import timezone

from app.config import settings
from app.config.templating import render_to_string

mail_transport = create_transport_from_url(settings.mail_url)
mailer = Mailer(
    transport=mail_transport,
    from_address=f"{settings.mail_default_from_name} <{settings.mail_default_from_address}>",
    preprocessors=[css_inliner],
)


async def send_mail(
    to: Recipients | None = None,
    subject: str | None = None,
    *,
    cc: Recipients | None = None,
    bcc: Recipients | None = None,
    html: str | None = None,
    text: str | None = None,
    from_address: Recipients | None = None,
    headers: dict[str, str] | None = None,
) -> None:
    """Send an email message to one or more recipients."""
    return await mailer.send(
        Email(
            to=to,
            cc=cc,
            bcc=bcc,
            subject=str(subject or ""),
            from_address=from_address,
            text=text,
            html=html,
            headers=headers,
        )
    )


async def send_templated_mail(
    to: str,
    subject: str,
    *,
    cc: Recipients | None = None,
    bcc: Recipients | None = None,
    text_template: str | None = None,
    html_template: str | None = None,
    context: typing.Mapping[str, typing.Any] | None = None,
    from_address: Recipients | None = None,
    headers: dict[str, str] | None = None,
    preheader: str = "",
) -> None:
    """Send an email message to one or more recipients.

    Text or HTML body are rendered from the templates."""
    context = dict(context or {})
    context.update(
        {
            "preheader": preheader,
            "app_name": settings.app_name,
            "app_url": settings.app_url,
            "sender_name": settings.mail_default_from_name,
            "settings": settings,
            "today": timezone.now(),
        },
    )
    text_content: str | None = render_to_string(text_template, context) if text_template else None
    html_content: str | None = render_to_string(html_template, context) if html_template else None
    await send_mail(
        to=to,
        cc=cc,
        bcc=bcc,
        subject=subject,
        html=html_content,
        text=text_content,
        from_address=from_address,
        headers=headers,
    )
