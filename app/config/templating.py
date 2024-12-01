import typing

import jinja2
from starlette.templating import Jinja2Templates
from starlette_babel.contrib.jinja import configure_jinja_env

from app.config import settings
from app.config.templating_context import app_processor, authenticated_processor

jinja_env = jinja2.Environment(
    autoescape=True,
    loader=jinja2.ChoiceLoader(
        [
            jinja2.PackageLoader(f"{settings.package_name}.resources"),
        ],
    ),
)

# add l10n and i18n helpers
configure_jinja_env(jinja_env)

templates = Jinja2Templates(
    env=jinja_env,
    context_processors=[
        app_processor,
        authenticated_processor,
    ],
)


def render_to_string(template: str, context: typing.Mapping[str, typing.Any] | None = None) -> str:
    """Render a template to a string."""
    return templates.get_template(template).render(context or {})
