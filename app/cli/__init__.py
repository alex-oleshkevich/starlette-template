import click

from app.cli.mails import mails_group

app = click.Group()
app.add_command(mails_group)
