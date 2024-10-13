import click

settings_group = click.Group(name="settings", help="Print settings.")


@settings_group.command("show")
def show_settings_command() -> None:
    pass
