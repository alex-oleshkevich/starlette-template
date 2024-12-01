import pytest

from app.config.permissions import guards, permissions
from app.config.permissions.context import Guard
from app.contrib.permissions import Permission
from tests.factories import AccessContextFactory, TeamMemberFactory, TeamRoleFactory, UserFactory


@pytest.mark.parametrize(
    "is_admin, permission_list, expected",
    [
        (True, [], True),
        (False, [], False),
        (False, [permissions.TEAM_ACCESS], True),
    ],
)
def test_team_access(is_admin: bool, permission_list: list[Permission], expected: bool) -> None:
    access_context = AccessContextFactory(
        scopes=permission_list,
        user=UserFactory(),
        team_member=TeamMemberFactory(role=TeamRoleFactory(is_admin=is_admin)),
    )
    guard = Guard(access_context)
    assert guard.check(guards.TEAM_ACCESS) is expected


@pytest.mark.parametrize(
    "is_admin, permission_list, expected",
    [
        (True, [], True),
        (False, [], False),
        (False, [permissions.TEAM_MEMBERS_ACCESS], False),
        (False, [permissions.TEAM_MEMBERS_ACCESS, permissions.TEAM_ACCESS], True),
    ],
)
def test_team_member_access(is_admin: bool, permission_list: list[Permission], expected: bool) -> None:
    access_context = AccessContextFactory(
        scopes=permission_list,
        user=UserFactory(),
        team_member=TeamMemberFactory(role=TeamRoleFactory(is_admin=is_admin)),
    )
    guard = Guard(access_context)
    assert guard.check(guards.TEAM_MEMBER_ACCESS) is expected


@pytest.mark.parametrize(
    "is_admin, permission_list, expected",
    [
        (True, [], True),
        (False, [], False),
        (False, [permissions.TEAM_ROLE_ACCESS], False),
        (False, [permissions.TEAM_ROLE_ACCESS, permissions.TEAM_ACCESS], True),
    ],
)
def test_team_role_access(is_admin: bool, permission_list: list[Permission], expected: bool) -> None:
    access_context = AccessContextFactory(
        scopes=permission_list,
        user=UserFactory(),
        team_member=TeamMemberFactory(role=TeamRoleFactory(is_admin=is_admin)),
    )
    guard = Guard(access_context)
    assert guard.check(guards.TEAM_ROLE_ACCESS) is expected


@pytest.mark.parametrize(
    "is_admin, permission_list, expected",
    [
        (True, [], True),
        (False, [], False),
        (False, [permissions.BILLING_ACCESS], False),
        (False, [permissions.BILLING_ACCESS, permissions.TEAM_ACCESS], True),
    ],
)
def test_billing_access(is_admin: bool, permission_list: list[Permission], expected: bool) -> None:
    access_context = AccessContextFactory(
        scopes=permission_list,
        user=UserFactory(),
        team_member=TeamMemberFactory(role=TeamRoleFactory(is_admin=is_admin)),
    )
    guard = Guard(access_context)
    assert guard.check(guards.BILLING_ACCESS) is expected
