import click
from pydantic.fields import FieldInfo
from rich import box
from rich.table import Table

from app.cli.console import console
from app.config import settings

settings_group = click.Group(name="settings", help="Print settings.")


@settings_group.command("show")
def show_settings_command() -> None:
    table = Table(box=box.MINIMAL)
    table.add_column("Property")
    table.add_column("Value")
    table.add_column("Default")

    field: FieldInfo
    for name, field in settings.__fields__.items():
        table.add_row(name, repr(getattr(settings, name)), str(field.default))

    console.print(table)
