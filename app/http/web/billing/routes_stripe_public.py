import logging

import stripe
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette_dispatch import RouteGroup

from app.contexts.billing.exceptions import BillingError
from app.contexts.billing.stripe import (
    cancel_stripe_subscription,
    create_stripe_subscription,
    update_stripe_subscription,
)
from app.http.dependencies import DbSession, Settings
from app.http.responses import JSONErrorResponse

routes = RouteGroup()
logger = logging.getLogger(__name__)


@routes.post("/stripe/webhook")
async def webhook_handler_view(request: Request, dbsession: DbSession, settings: Settings) -> Response:
    try:
        signature = request.headers.get("Stripe-Signature", "")
        data = await request.body()
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            data,
            sig_header=signature,
            api_key=settings.stripe_secret_key,
            secret=settings.stripe_webhook_secret,
        )
        match event.type:
            case "checkout.session.completed":
                if not isinstance(event.data.object, stripe.checkout.Session):
                    logger.error("stripe webhook error: event data is not a stripe.Checkout.Session")
                    return JSONErrorResponse(status_code=400)

                subscription = await create_stripe_subscription(dbsession, event.data.object)
                await dbsession.commit()
                logger.info(
                    "stripe subscription has been created",
                    extra={
                        "team_id": subscription.team_id,
                        "subscription_id": subscription.id,
                    },
                )

            case "customer.subscription.updated":
                if not isinstance(event.data.object, stripe.Subscription):
                    logger.error("stripe webhook error: event data is not a stripe.Subscription")
                    return JSONErrorResponse(status_code=400)

                subscription = await update_stripe_subscription(dbsession, event.data.object)
                logger.info(
                    "stripe subscription has been upgraded",
                    extra={
                        "team_id": subscription.team_id,
                        "subscription_id": subscription.id,
                    },
                )
                await dbsession.commit()
            case "customer.subscription.deleted":
                if not isinstance(event.data.object, stripe.Subscription):
                    logger.error("stripe webhook error: event data is not a stripe.Subscription")
                    return JSONErrorResponse(status_code=400)

                team_id = await cancel_stripe_subscription(dbsession, event.data.object)
                await dbsession.commit()
                logger.info(
                    "stripe subscription has been deleted",
                    extra={
                        "team_id": team_id,
                    },
                )
    except BillingError as ex:
        logger.exception("stripe webhook error")
        return JSONErrorResponse(status_code=400, error_code=ex.error_code)
    else:
        return JSONResponse({}, status_code=200)
