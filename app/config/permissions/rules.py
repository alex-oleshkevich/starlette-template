from app.config.permissions.context import AccessContext
from app.contrib.permissions import Resource, Rule, all_of, any_of, has_permission, none_of

# re-export the following functions
_ = any_of, all_of, none_of, has_permission


def is_team_admin() -> Rule:
    """Check if the user is an admin of the team."""

    def rule(context: AccessContext, resource: Resource | None = None) -> bool:
        return any([context.team_member.team.owner == context.user, context.team_member.role.is_admin])

    return rule
