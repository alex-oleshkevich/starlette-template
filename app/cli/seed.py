import click

from app.config.seed import seed_database


@click.command("seed")
def seed_command() -> None:
    """Seed the database with initial data."""
    seed_database()
