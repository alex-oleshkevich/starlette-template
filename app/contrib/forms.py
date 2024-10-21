import typing

import wtforms
from anyio.to_thread import run_sync
from starlette.requests import Request

FormValidator = typing.Callable[[wtforms.Form, wtforms.Field], None]
F = typing.TypeVar("F", bound=wtforms.Form)


def is_submitted(request: Request) -> bool:
    return request.method in ["POST", "PUT", "PATCH"]


async def create_form(
    request: Request,
    form_class: type[F],
    *,
    obj: typing.Any | None = None,
    prefix: str = "",
    data: typing.Mapping[str, typing.Any] | None = None,
) -> F:
    if is_submitted(request):
        form_data = await request.form()
        return form_class(form_data, obj=obj, prefix=prefix, data=data)
    return form_class(obj=obj, prefix=prefix, data=data)


async def validate_on_submit(
    request: Request,
    form: wtforms.Form,
    extra_validators: typing.Mapping[str, typing.Sequence[FormValidator]] | None = None,
) -> bool | None:
    if is_submitted(request):
        return await run_sync(form.validate, extra_validators)
    return None
