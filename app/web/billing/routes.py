from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_babel import gettext_lazy as _
from starlette_dispatch import RouteGroup

from app.config.dependencies import CurrentSubscription, DbSession
from app.config.templating import templates
from app.contexts.billing.repo import SubscriptionRepo

routes = RouteGroup()


@routes.get_or_post("/billing", name="billing")
async def subscriptions_view(
    request: Request, dbsession: DbSession, subscription: CurrentSubscription | None
) -> Response:
    repo = SubscriptionRepo(dbsession)
    plans = await repo.get_available_plans()
    return templates.TemplateResponse(
        request,
        "web/billing/index.html",
        {
            "page_title": _("Subscription"),
            "plans": plans,
            "subscription": subscription,
            "page_description": _("Manage your subscription plan and billing details."),
        },
    )


@routes.get_or_post("/billing/change-plan", name="billing.change-plan")
async def change_plan_view(request: Request) -> Response:
    return RedirectResponse(request.url_for("billing.stripe.change-plan"))