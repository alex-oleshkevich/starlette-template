import datetime

from sqlalchemy.orm import Mapped, mapped_column
from starlette.authentication import BaseUser

from app.config.sqla.columns import DateTimeTz, IntPk
from app.config.sqla.models import Base, WithTimestamps


class User(BaseUser, Base, WithTimestamps):
    __tablename__ = "users"

    id: Mapped[IntPk]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    first_name: Mapped[str] = mapped_column(server_default="", default="")
    last_name: Mapped[str] = mapped_column(server_default="", default="")
    photo: Mapped[str] = mapped_column(server_default="", default="")
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
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def deactivate(self) -> None:
        self.deleted_at = datetime.datetime.now(datetime.UTC)
        self.email = f"{self.id}@deleted.tld"

    def __str__(self) -> str:
        return self.display_name
