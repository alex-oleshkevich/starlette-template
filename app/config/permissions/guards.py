from app.config.permissions import permissions, rules

TEAM_ACCESS = rules.any_of(
    rules.is_team_admin(),
    permissions.TEAM_ACCESS,
)

TEAM_MEMBER_ACCESS = rules.any_of(
    rules.is_team_admin(),
    rules.all_of(
        TEAM_ACCESS,
        permissions.TEAM_MEMBERS_ACCESS,
    ),
)

TEAM_ROLE_ACCESS = rules.any_of(
    rules.is_team_admin(),
    rules.all_of(
        TEAM_ACCESS,
        permissions.TEAM_ROLE_ACCESS,
    ),
)

BILLING_ACCESS = rules.any_of(
    rules.is_team_admin(),
    rules.all_of(
        TEAM_ACCESS,
        permissions.BILLING_ACCESS,
    ),
)
