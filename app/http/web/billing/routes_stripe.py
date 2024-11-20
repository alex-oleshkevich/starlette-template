import stripe
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_babel import gettext_lazy as _
from starlette_dispatch import RouteGroup
from starlette_flash import flash

from app.config import settings
from app.config.templating import templates
from app.http.dependencies import RequireSubscription, Settings

stripe.api_key = settings.stripe_secret_key
routes = RouteGroup()


@routes.get("/billing/stripe/open-portal", name="billing.stripe.open-portal")
def create_portal_session_view(
    request: Request, settings: Settings, current_subscription: RequireSubscription
) -> Response:
    stripe.api_key = settings.stripe_secret_key
    return_url = request.url_for("billing")
    portal_session = stripe.billing_portal.Session.create(
        return_url=str(return_url),
        customer=current_subscription.remote_customer_id,
    )
    return RedirectResponse(portal_session.url)


@routes.get_or_post("/billing/stripe/change-plan", name="billing.stripe.change-plan")
async def change_plan_view(request: Request) -> Response:
    return templates.TemplateResponse(
        request,
        "web/billing/stripe_pricing_table.html",
        {
            "page_title": _("Change Plan"),
        },
    )


@routes.get_or_post("/billing/stripe/confirm")
async def stripe_confirm_view(request: Request) -> Response:
    flash(request).success(_("Subscription activated. Thank your for supporting us!"))
    return RedirectResponse(request.url_for("home"))
