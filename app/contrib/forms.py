from __future__ import annotations

import typing

import wtforms
from anyio.to_thread import run_sync
from starlette.datastructures import UploadFile
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


class PhotoField(wtforms.FileField):
    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.clear_input = wtforms.BooleanField(name=self.name + "_clear", default=False, _form=kwargs.get("_form"))

    def process(self, formdata: typing.Any, data: typing.Any = ..., extra_filters: typing.Any = None) -> None:
        super().process(formdata, data, extra_filters)
        self.clear_input.process(formdata, data, extra_filters)

    def process_formdata(self, valuelist: typing.Any) -> None:
        super().process_formdata(valuelist)
        self.clear_input.process_formdata(valuelist)

    def process_data(self, value: str) -> None:
        super().process_data(value)
        self.clear_input.process_data(value=False)

    @property
    def clear(self) -> bool:
        return self.clear_input.data

    @property
    def is_uploaded(self) -> bool:
        return isinstance(self.data, UploadFile)

    @property
    def value(self) -> str:
        return self.data if isinstance(self.data, str) else ""
