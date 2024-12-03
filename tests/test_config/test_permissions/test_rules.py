from app.config.permissions.rules import is_team_admin
from app.contexts.teams.models import TeamMember
from tests.factories import AccessContextFactory, TeamMemberFactory, TeamRoleFactory, UserFactory


def test_is_team_admin(team_member: TeamMember) -> None:
    access_context = AccessContextFactory(team_member=team_member)
    assert is_team_admin()(access_context)

    user = UserFactory()
    team_role = TeamRoleFactory(team=team_member.team, is_admin=False)
    team_member = TeamMemberFactory(role=team_role, team=team_member.team, user=user)
    access_context = AccessContextFactory(team_member=team_member)
    assert not is_team_admin()(access_context)
