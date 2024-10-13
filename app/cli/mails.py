import anyio
import click

from app.config.mailers import send_mail

mails_group = click.Group(name="mail", help="Mail commands.")


@mails_group.command("test")
@click.argument("recipient", type=str)
@click.option("--subject", "-s", type=str, default="This is a test message", help="The subject of the message")
@click.option(
    "--message", "-m", type=str, default="If you see this, the email delivery works.", help="The message body"
)
def send_test_mail_command(recipient: str, subject: str, message: str) -> None:
    async def main() -> None:
        await send_mail(to=recipient, subject=subject, text=message)
        click.echo("Mail sent.")

    anyio.run(main)
