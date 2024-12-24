import typing

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, model_validator
from starlette_babel import gettext_lazy as _


def is_terms_accepted(value: bool) -> int:
    if not value:
        raise ValueError(_("Terms of use must be accepted."))
    return value


class RegisterValidator(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    password_confirm: str
    terms: typing.Annotated[bool, AfterValidator(is_terms_accepted)]

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def check_passwords_match(self) -> typing.Self:
        if self.password != self.password_confirm:
            raise ValueError(_("Passwords did not match."))
        return self


class RegisterSerializer(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    photo: str
    language: str
    timezone: str
    color_hash: str

    model_config = ConfigDict(from_attributes=True)
