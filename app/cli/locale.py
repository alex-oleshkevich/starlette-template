import click
from babel.messages.frontend import CommandLineInterface

from app.config import settings

locale_group = click.Group(name="locale", help="Manage locales")

locale_dir = settings.resources_dir / "locale"


@locale_group.command("collect")
@click.option("--domain", default="messages")
def collect_command(domain: str) -> None:
    cli = CommandLineInterface()
    cli.run(
        [
            "",  # This is the program name
            "extract",
            "-F",
            "pybabel.ini",
            "-o",
            str(locale_dir / f"{domain}.pot"),
            str(settings.package_dir),
        ]
    )

    for locale in settings.i18n_locales:
        locale_file = locale_dir / locale / "LC_MESSAGES" / f"{domain}.po"
        if not locale_file.exists():
            cli.run(
                [
                    "",  # This is the program name
                    "init",
                    "-D",
                    domain,
                    "-l",
                    locale,
                    "-w",
                    120,
                    "-d",
                    locale_dir,
                    "-i",
                    locale_dir / f"{domain}.pot",
                ]
            )

        cli.run(
            [
                "",  # This is the program name
                "update",
                "-D",
                domain,
                "-w",
                120,
                "-l",
                locale,
                "-d",
                str(locale_dir),
                "-i",
                str(locale_dir / f"{domain}.pot"),
            ]
        )


@locale_group.command("compile")
@click.option("--domain", default="messages")
def compile_command(domain: str) -> None:
    cli = CommandLineInterface()
    cli.run(
        [
            "",  # This is the program name
            "compile",
            "-D",
            domain,
            "-d",
            str(locale_dir),
            "--statistics",
        ]
    )
