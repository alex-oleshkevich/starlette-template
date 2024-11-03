from __future__ import annotations

import datetime
import uuid

import sqlalchemy as sa
from colorhash import ColorHash
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlette.datastructures import URL
from starlette.requests import Request

from app.config import crypto
from app.config.sqla.columns import DateTimeTz, IntPk
from app.config.sqla.models import Base, WithTimestamps
from app.contexts.users.models import User


class Team(Base, WithTimestamps):
    """A team is a group of users that work together.
    This is like a namespace for users and resources."""

    __tablename__ = "teams"

    id: Mapped[IntPk]
    name: Mapped[str] = mapped_column()
    logo: Mapped[str | None] = mapped_column()
    owner_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"))

    owner: Mapped[User] = relationship(User)
    members: Mapped[list[TeamMember]] = relationship("TeamMember", cascade="all, delete-orphan", back_populates="team")
    roles: Mapped[list[TeamRole]] = relationship("TeamRole", cascade="all, delete-orphan", back_populates="team")
    invites: Mapped[list[TeamInvite]] = relationship("TeamInvite", cascade="all, delete-orphan", back_populates="team")

    @property
    def color_hash(self) -> str:
        return ColorHash(self.name).hex

    @property
    def initials(self) -> str:
        return "".join(part[0] for part in self.name.split()[:2]).upper()


class TeamRole(Base, WithTimestamps):
    """A role is a set of permissions that can be assigned to a team member.

    Extension strategies:
    1. add a `permissions` relationship to a list of permissions.
    2. add one or more boolean columns for each permission.
    3. add a column "permissions" with a JSONB type to store a list of permissions.
    4. add a column "permissions" with the python class name that implements the permissions.

    Each strategy is valid and has its own trade-offs. Choose the one that fits your needs.
    The permission framework can work with any of these strategies."""

    __tablename__ = "team_roles"

    id: Mapped[IntPk]
    name: Mapped[str] = mapped_column()
    team_id: Mapped[int] = mapped_column(sa.ForeignKey("teams.id"))

    is_admin: Mapped[bool] = mapped_column(
        sa.Boolean(), default=False, server_default=sa.false(), doc="Admins can manage the team."
    )

    team: Mapped[Team] = relationship(Team, back_populates="roles")
    members: Mapped[list[TeamMember]] = relationship("TeamMember", back_populates="role")
    invites: Mapped[list[TeamInvite]] = relationship("TeamInvite", cascade="all, delete-orphan", back_populates="role")


class TeamMember(Base, WithTimestamps):
    """A team member is a user that belongs to a team."""

    __tablename__ = "team_members"
    __table_args__ = (sa.UniqueConstraint("team_id", "user_id"),)

    id: Mapped[IntPk]
    is_service: Mapped[bool] = mapped_column(
        sa.Boolean(),
        default=False,
        server_default=sa.false(),
        doc="Service accounts are used for integrations and not real users.",
    )
    suspended_at: Mapped[DateTimeTz | None] = mapped_column()
    team_id: Mapped[int] = mapped_column(sa.ForeignKey("teams.id"))
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"))
    role_id: Mapped[int] = mapped_column(sa.ForeignKey("team_roles.id"))

    team: Mapped[Team] = relationship(Team, back_populates="members")
    user: Mapped[User] = relationship(User)
    role: Mapped[TeamRole] = relationship(TeamRole, back_populates="members")
    invites: Mapped[list[TeamInvite]] = relationship(
        "TeamInvite", cascade="all, delete-orphan", back_populates="inviter"
    )

    def suspend(self) -> None:
        self.suspended_at = datetime.datetime.now(datetime.UTC)

    def __str__(self) -> str:
        return str(self.user)


class InvitationToken:
    def __init__(self) -> None:
        self.plain_token = str(uuid.uuid4().hex)

    @property
    def hashed_token(self) -> str:
        return crypto.hash_value(self.plain_token)

    def make_url(self, request: Request) -> URL:
        return request.url_for("teams.members.accept_invite", token=self.plain_token)


class TeamInvite(Base, WithTimestamps):
    """A team invite is a pending invitation to join a team."""

    __tablename__ = "team_invites"
    __table_args__ = (
        sa.UniqueConstraint("team_id", "email"),
        sa.UniqueConstraint("team_id", "token"),
    )

    id: Mapped[IntPk]
    email: Mapped[str]
    token: Mapped[str] = mapped_column(doc="Hashed token to verify the invite.")
    team_id: Mapped[int] = mapped_column(sa.ForeignKey("teams.id"))
    role_id: Mapped[int] = mapped_column(sa.ForeignKey("team_roles.id"))
    inviter_id: Mapped[int] = mapped_column(sa.ForeignKey("team_members.id"))

    team: Mapped[Team] = relationship(Team, back_populates="invites")
    role: Mapped[TeamRole] = relationship(TeamRole, back_populates="invites")
    inviter: Mapped[TeamMember] = relationship(TeamMember, back_populates="invites")

    def __str__(self) -> str:
        return self.email
