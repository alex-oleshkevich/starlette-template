from starlette.requests import Request
from starlette.responses import Response
from starlette_dispatch import RouteGroup

from app.config.dependencies import DbSession
from app.config.templating import templates
from app.contrib import forms
from app.web.register.forms import RegisterForm

routes = RouteGroup()


@routes.get_or_post("/register", name="register")
async def register_view(request: Request, dbsession: DbSession) -> Response:
    form = await forms.create_form(request, RegisterForm)
    return templates.TemplateResponse("web/register/register.html", {"request": request, "form": form})
