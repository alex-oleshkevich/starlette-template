import click

from app.cli.mails import mails_group
from app.cli.settings import settings_group

console_app = click.Group()
console_app.add_command(mails_group)
console_app.add_command(settings_group)
