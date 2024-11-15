import click

from app.cli.locale import locale_group
from app.cli.mails import mails_group
from app.cli.seed import seed_command
from app.cli.settings import settings_group
from app.cli.stripe import stripe_group

console_app = click.Group()
console_app.add_command(locale_group)
console_app.add_command(mails_group)
console_app.add_command(seed_command)
console_app.add_command(settings_group)
console_app.add_command(stripe_group)
