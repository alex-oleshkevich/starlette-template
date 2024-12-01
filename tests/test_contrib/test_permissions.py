import dataclasses

import pytest

from app.contrib.permissions import (
    AccessDeniedError,
    Permission,
    PermissionGroup,
    Role,
    all_of,
    any_of,
    check_rule,
    check_rule_or_raise,
    get_defined_permission_groups,
    get_defined_permissions,
    get_defined_roles,
    has_permission,
    none_of,
)

admin_permission = Permission(id="admin", description="admin")
manager_permission = Permission(id="manager", description="manager")


@dataclasses.dataclass
class AccessContext:
    scopes: list[Permission]


class TestCheckRule:
    def test_check_rule(self) -> None:
        context = AccessContext(scopes=[admin_permission])
        assert check_rule(context, has_permission(admin_permission)) is True
        assert check_rule(context, has_permission(manager_permission)) is False

    def test_check_rule_or_raise(self) -> None:
        context = AccessContext(scopes=[admin_permission])
        check_rule_or_raise(context, has_permission(admin_permission))  # no exception

        with pytest.raises(AccessDeniedError):
            check_rule_or_raise(context, has_permission(manager_permission))


def test_has_permission() -> None:
    context = AccessContext(scopes=[admin_permission])
    rule = has_permission(admin_permission)
    assert rule(context) is True
    assert rule(AccessContext(scopes=[manager_permission])) is False


def test_any_of() -> None:
    context = AccessContext(scopes=[admin_permission])
    rule = any_of(has_permission(admin_permission))
    assert rule(context) is True

    rule = any_of(has_permission(admin_permission), has_permission(manager_permission))
    assert rule(context) is True

    rule = any_of(has_permission(manager_permission))
    assert rule(context) is False


def test_all_of() -> None:
    context = AccessContext(scopes=[admin_permission, manager_permission])
    rule = all_of(has_permission(admin_permission), has_permission(manager_permission))
    assert rule(context) is True

    rule = all_of(has_permission(manager_permission))
    assert rule(AccessContext(scopes=[admin_permission])) is False


def test_none_of() -> None:
    context = AccessContext(scopes=[])
    rule = none_of(has_permission(admin_permission), has_permission(manager_permission))
    assert rule(context) is True

    context = AccessContext(scopes=[admin_permission])
    rule = none_of(has_permission(admin_permission), has_permission(manager_permission))
    assert rule(context) is False


class TestPermission:
    def test_stringify(self) -> None:
        permission = Permission(id="admin", name="Admin permission")
        assert str(permission) == "Admin permission"

        permission = Permission(id="admin", name="")
        assert str(permission) == "admin"

    def test_equals(self) -> None:
        permission = Permission(id="admin", name="Admin permission")
        permission2 = Permission(id="admin", name="")
        assert permission == permission2

        with pytest.raises(NotImplementedError):
            assert permission == 1

    def test_rule_protocol(self) -> None:
        permission = Permission(id="admin", name="Admin permission")
        assert permission(AccessContext(scopes=[permission])) is True


class TestPermissionGroup:
    def test_permission_group(self) -> None:
        group = PermissionGroup(name="group", description="group1", permissions=[admin_permission, manager_permission])
        assert group.name == "group"
        assert group.description == "group1"
        assert admin_permission in group
        assert list(group) == [admin_permission, manager_permission]

    def test_nested_group(self) -> None:
        custom_permission = Permission(id="custom", description="custom")
        group = PermissionGroup(
            name="group",
            description="group1",
            permissions=[admin_permission, manager_permission],
            groups=[PermissionGroup(name="subgroup1", description="subgroup1", permissions=[custom_permission])],
        )
        assert custom_permission in group

    def test_iterable(self) -> None:
        custom_permission = Permission(id="custom", description="custom")
        group = PermissionGroup(
            name="group",
            description="group1",
            permissions=[admin_permission, manager_permission],
            groups=[PermissionGroup(name="subgroup1", description="subgroup1", permissions=[custom_permission])],
        )
        assert list(group) == [admin_permission, manager_permission, custom_permission]

    def test_stringify(self) -> None:
        group = PermissionGroup(name="subgroup1", description="subgroup1")
        assert str(group) == "subgroup1"

    def test_contains(self) -> None:
        permission_a = Permission(id="a")
        permission_b = Permission(id="b")
        group = PermissionGroup(name="subgroup1", permissions=[permission_a])
        assert permission_a in group
        assert permission_b not in group


class TestRole:
    def test_role(self) -> None:
        role = Role(id="role", description="role1")
        assert role.id == "role"
        assert role.description == "role1"
        assert list(role) == []

    def test_with_permissions(self) -> None:
        role = Role(id="role", description="role1", permissions=[admin_permission])
        assert admin_permission in role
        assert list(role) == [admin_permission]

    def test_with_group(self) -> None:
        group = PermissionGroup(name="group", description="group1", permissions=[admin_permission, manager_permission])
        role = Role(
            id="role",
            description="role1",
            groups=[group],
        )
        assert role.groups == [group]
        assert admin_permission in role
        assert list(role) == [admin_permission, manager_permission]

    def test_with_nested_role(self) -> None:
        role = Role(
            id="role",
            description="role1",
            roles=[
                Role(id="subrole", description="subrole1", permissions=[admin_permission, manager_permission]),
            ],
        )
        assert admin_permission in role
        assert list(role) == [admin_permission, manager_permission]

    def test_stringify(self) -> None:
        role_a = Role(id="role", name="Role")
        role_b = Role(id="role")
        assert str(role_a) == "Role"
        assert str(role_b) == "role"

    def test_contains(self) -> None:
        permission_a = Permission(id="a")
        permission_b = Permission(id="b")
        role = Role(id="role", name="Role", permissions=[permission_a])
        assert permission_a in role
        assert permission_b not in role


def test_get_defined_permissions() -> None:
    class Holder:
        admin = Permission(id="admin", description="admin")
        manager = Permission(id="manager", description="manager")

    permissions = [x.id for x in get_defined_permissions(Holder)]
    assert permissions == ["admin", "manager"]


def test_get_defined_permission_groups() -> None:
    group = PermissionGroup(name="admin", permissions=[])

    class Holder:
        admin = group

    groups = list(get_defined_permission_groups(Holder))
    assert groups == [group]


def test_get_defined_roles() -> None:
    role = Role(id="admin")

    class Holder:
        admin = role

    roles = list(get_defined_roles(Holder))
    assert roles == [role]
