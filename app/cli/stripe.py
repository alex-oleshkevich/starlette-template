import anyio
import click

from app.config.database import new_dbsession
from app.contexts.billing.stripe import sync_stripe_products

stripe_group = click.Group("stripe", help="Stripe commands")


@stripe_group.command("sync-plans")
def sync_plans() -> None:
    async def main() -> None:
        try:
            async with new_dbsession() as dbsession:
                await sync_stripe_products(dbsession)
        except Exception as e:
            raise click.ClickException(str(e)) from e

    anyio.run(main)
