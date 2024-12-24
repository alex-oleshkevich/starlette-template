import typing

from pydantic import BaseModel, ConfigDict, model_validator
from starlette_babel import gettext_lazy as _


class ProfileSerializer(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    photo: str
    language: str
    timezone: str
    color_hash: str

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateValidator(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    photo: str | None = None
    language: str | None = None
    timezone: str | None = None

    model_config = ConfigDict(from_attributes=True)


ProfileUpdateSerializer = ProfileSerializer


class ChangePasswordValidator(BaseModel):
    current_password: str
    password: str
    password_confirm: str

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def check_passwords_match(self) -> typing.Self:
        if self.password != self.password_confirm:
            raise ValueError(_("Passwords did not match."))
        return self


class ChangePasswordSerializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
