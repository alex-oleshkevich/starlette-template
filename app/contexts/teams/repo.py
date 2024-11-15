import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, with_expression
from starlette_sqlalchemy import Collection, Page, PageNumberPaginator, Repo

from app.config.crypto import hash_value
from app.contexts.teams.exceptions import AlreadyMemberError
from app.contexts.teams.models import Team, TeamInvite, TeamMember, TeamRole
from app.contexts.users.models import User


class TeamRepo(Repo[Team]):
    model_class = Team
    base_query = sa.select(Team).order_by(Team.name)

    def __init__(self, dbsession: AsyncSession) -> None:
        super().__init__(dbsession)
        self.memberships = TeamMemberRepo(dbsession)
        self.invites = TeamInvitesRepo(dbsession)
        self.roles = TeamRolesRepo(dbsession)

    async def get_active_memberships(self, user_id: int) -> Collection[TeamMember]:
        stmt = self.memberships.get_base_query().where(TeamMember.user_id == user_id, TeamMember.suspended_at.is_(None))
        return await self.query.all(stmt)

    async def get_joined_teams(self, user_id: int) -> list[Team]:
        memberships = await self.get_active_memberships(user_id)
        return [membership.team for membership in memberships]

    async def get_team_member(self, team_id: int, user_id: int) -> TeamMember | None:
        stmt = self.memberships.get_base_query().where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]

    async def get_team_member_by_id(self, team_id: int, member_id: int) -> TeamMember | None:
        stmt = self.memberships.get_base_query().where(TeamMember.id == member_id, TeamMember.team_id == team_id)
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]

    async def get_team_members_paginated(self, team_id: int, *, page: int = 1, page_size: int = 50) -> Page[TeamMember]:
        stmt = self.memberships.get_base_query().where(TeamMember.team_id == team_id)
        pager = PageNumberPaginator(self.dbsession)
        return await pager.paginate(stmt, page=page, page_size=page_size)

    async def get_invites_paginated(self, team_id: int, *, page: int = 1, page_size: int = 50) -> Page[TeamInvite]:
        stmt = self.invites.get_base_query().where(TeamInvite.team_id == team_id)
        paginator = PageNumberPaginator(self.dbsession)
        return await paginator.paginate(stmt, page=page, page_size=page_size)

    async def get_role(self, team_id: int, role_id: int, *, load_members: bool = False) -> TeamRole | None:
        stmt = self.roles.get_base_query().where(TeamRole.team_id == team_id, TeamRole.id == role_id)
        if load_members:
            stmt = stmt.options(selectinload(TeamRole.members))
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]

    async def get_roles(self, team_id: int) -> Collection[TeamRole]:
        stmt = self.roles.get_base_query().where(TeamRole.team_id == team_id)
        return await self.query.all(stmt)

    async def get_roles_paginated(self, team_id: int, *, page: int, page_size: int = 50) -> Page[TeamRole]:
        stmt = (
            self.roles.get_base_query()
            .where(TeamRole.team_id == team_id)
            .options(
                with_expression(
                    TeamRole.members_count,
                    sa.select(sa.func.count()).where(TeamMember.role_id == TeamRole.id).scalar_subquery(),
                )
            )
        )
        paginator = PageNumberPaginator(self.dbsession)
        return await paginator.paginate(stmt, page=page, page_size=page_size)

    async def get_invitation(self, team_id: int, invite_id: int) -> TeamInvite | None:
        stmt = self.invites.get_base_query().where(TeamInvite.team_id == team_id, TeamInvite.id == invite_id)
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]

    async def get_invitation_by_token(self, token: str) -> TeamInvite | None:
        stmt = self.invites.get_base_query().where(TeamInvite.token == hash_value(token))
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]

    async def accept_invitation(self, user: User, invitation: TeamInvite) -> TeamMember:
        current_member = await self.query.one_or_none(
            sa.select(TeamMember).where(TeamMember.team == invitation.team, TeamMember.user == user)
        )
        if current_member:
            raise AlreadyMemberError()

        team_member = TeamMember(
            user=user,
            team=invitation.team,
            role=invitation.role,
        )
        self.dbsession.add(team_member)
        await self.dbsession.delete(invitation)
        await self.dbsession.flush()
        return team_member


class TeamMemberRepo(Repo[TeamMember]):
    model_class = TeamMember
    base_query = (
        sa.select(TeamMember)
        .options(
            joinedload(TeamMember.team).joinedload(Team.owner),
            joinedload(TeamMember.user),
            joinedload(TeamMember.role),
        )
        .where(
            TeamMember.is_service.is_(False),
        )
        .order_by(TeamMember.id)
    )


class TeamInvitesRepo(Repo[TeamInvite]):
    model_class = TeamInvite
    base_query = (
        sa.select(TeamInvite)
        .options(
            joinedload(TeamInvite.role),
            joinedload(TeamInvite.team).joinedload(Team.owner),
            joinedload(TeamInvite.inviter).joinedload(TeamMember.user),
        )
        .order_by(TeamInvite.created_at)
    )


class TeamRolesRepo(Repo[TeamRole]):
    model_class = TeamRole
    base_query = sa.select(TeamRole).order_by(TeamRole.name)
