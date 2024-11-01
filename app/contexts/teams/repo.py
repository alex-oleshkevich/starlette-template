import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette_sqlalchemy import Collection, Repo

from app.contexts.teams.models import Team, TeamMember


class TeamRepo(Repo[Team]):
    model_class = Team
    base_query = sa.select(Team).order_by(Team.name)

    def __init__(self, dbsession: AsyncSession) -> None:
        super().__init__(dbsession)
        self.memberships = TeamMemberRepo(dbsession)

    async def get_memberships(self, user_id: int) -> Collection[TeamMember]:
        stmt = self.memberships.get_base_query().where(TeamMember.user_id == user_id)
        return await self.query.all(stmt)

    async def get_joined_teams(self, user_id: int) -> list[Team]:
        memberships = await self.get_memberships(user_id)
        return [membership.team for membership in memberships]

    async def get_team_member(self, team_id: int, user_id: int) -> TeamMember | None:
        stmt = self.memberships.get_base_query().where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]


class TeamMemberRepo(Repo[TeamMember]):
    model_class = TeamMember
    base_query = (
        sa.select(TeamMember)
        .options(
            joinedload(TeamMember.team),
            joinedload(TeamMember.user),
        )
        .where(
            TeamMember.disabled_at.is_(None),
            TeamMember.is_service.is_(False),
        )
        .order_by(TeamMember.id)
    )
