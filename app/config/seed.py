from app.config.crypto import make_password
from tests.factories import (
    SubscriptionPlanFactory,
    TeamFactory,
    TeamMemberFactory,
    TeamRoleFactory,
    UserFactory,
)


def seed_database() -> None:
    user = UserFactory(
        first_name="John",
        last_name="Doe",
        email="admin@localhost.tld",
        password=make_password("password"),
    )

    # subscription plans
    _ = SubscriptionPlanFactory(name="Starter")
    _ = SubscriptionPlanFactory(name="Pro")
    _ = SubscriptionPlanFactory(name="Enterprise")

    # primary team
    team = TeamFactory(name="John's team", owner=user)
    admin_role = TeamRoleFactory(team=team, name="Admin", is_admin=True)
    user_role = TeamRoleFactory(team=team, name="User", is_admin=False)
    _ = TeamMemberFactory(team=team, user=user, role=admin_role)
    TeamMemberFactory.build_batch(5, team=team, role=user_role)
