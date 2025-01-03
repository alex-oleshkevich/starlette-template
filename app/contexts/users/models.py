import datetime

import sqlalchemy as sa
from colorhash import ColorHash
from sqlalchemy.orm import Mapped, mapped_column
from starlette.authentication import BaseUser
from starlette_auth.authentication import HasSessionAuthHash

from app.config.sqla.columns import DateTimeTz, IntPk
from app.config.sqla.models import Base, WithTimestamps


class User(Base, WithTimestamps, BaseUser, HasSessionAuthHash):
    __tablename__ = "users"

    id: Mapped[IntPk]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    first_name: Mapped[str] = mapped_column(server_default="", default="")
    last_name: Mapped[str] = mapped_column(server_default="", default="")
    photo: Mapped[str] = mapped_column(server_default="", default="")
    language: Mapped[str] = mapped_column(server_default="en", default="en")
    timezone: Mapped[str] = mapped_column(server_default="UTC", default="UTC")
    is_service: Mapped[bool] = mapped_column(
        server_default=sa.false(), default=False, doc="Service accounts are used for integrations and not real users."
    )
    last_sign_in: Mapped[DateTimeTz | None] = mapped_column(doc="Last time the user signed in.")
    disabled_at: Mapped[DateTimeTz | None] = mapped_column(doc="Time the user was disabled.")
    email_confirmed_at: Mapped[DateTimeTz | None] = mapped_column(doc="Time the user confirmed their email.")
    deleted_at: Mapped[DateTimeTz | None] = mapped_column(doc="Time the user was deleted.")

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def identity(self) -> str:
        return str(self.id)

    @property
    def is_active(self) -> bool:
        return self.disabled_at is None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_confirmed(self) -> bool:
        return self.email_confirmed_at is not None

    @property
    def display_name(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.email

    @property
    def color_hash(self) -> str:
        return ColorHash(self.display_name).hex

    @property
    def initials(self) -> str:
        return "".join(part[0] for part in self.display_name.split()[:2]).upper()

    def deactivate(self) -> None:
        self.deleted_at = datetime.datetime.now(datetime.UTC)
        self.email = f"{self.id}@deleted.tld"

    def get_password_hash(self) -> str:
        return self.password

    def get_preferred_language(self) -> str:
        return self.language

    def get_timezone(self) -> str:
        return self.timezone

    def __str__(self) -> str:
        return self.display_name

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, User)
        return self.id == other.id
