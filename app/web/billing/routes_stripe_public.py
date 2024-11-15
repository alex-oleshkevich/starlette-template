import logging

import stripe
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette_dispatch import RouteGroup

from app.config import settings
from app.config.dependencies import DbSession
from app.contexts.billing.exceptions import BillingError
from app.contexts.billing.stripe import (
    cancel_stripe_subscription,
    create_stripe_subscription,
    update_stripe_subscription,
)
from app.error_handlers import ErrorResponse

stripe.api_key = settings.stripe_secret_key
routes = RouteGroup()
logger = logging.getLogger(__name__)


@routes.post("/stripe/webhook")
async def webhook_handler_view(request: Request, dbsession: DbSession) -> Response:
    try:
        data = await request.json()
        event = stripe.Event.construct_from(data, stripe.api_key)
        match event.type:
            case "checkout.session.completed":
                await create_stripe_subscription(dbsession, event.data.object)
                await dbsession.commit()
                logger.info("stripe subscription has been created")
            case "customer.subscription.updated":
                await update_stripe_subscription(dbsession, event.data.object)
                logger.info("stripe subscription has been upgraded")
                await dbsession.commit()
            case "customer.subscription.deleted":
                await cancel_stripe_subscription(dbsession, event.data.object)
                await dbsession.commit()
                logger.info("stripe subscription has been deleted")
    except BillingError as ex:
        logger.exception("stripe webhook error")
        return ErrorResponse(status_code=400, error_code=ex.error_code)
    else:
        return JSONResponse({}, status_code=200)
