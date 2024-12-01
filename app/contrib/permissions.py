from __future__ import annotations

import dataclasses
import types
import typing


class PermissionContext(typing.Protocol):
    permissions: set[Permission]


@dataclasses.dataclass(frozen=True, slots=True)
class Permission:
    id: str
    name: str = ""
    description: str = ""

    def __str__(self) -> str:
        return str(self.name or self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            raise NotImplementedError()
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __call__(self, context: PermissionContext, resource: Resource | None = None) -> bool:
        return self in context.permissions


@dataclasses.dataclass(frozen=True, slots=True)
class PermissionGroup:
    name: str
    description: str = ""
    permissions: list[Permission] = dataclasses.field(default_factory=list)
    groups: list[PermissionGroup] = dataclasses.field(default_factory=list)

    def __contains__(self, permission: Permission) -> bool:
        return permission in list(self)

    def __iter__(self) -> typing.Iterator[Permission]:
        yield from iter(self.permissions)
        for group in self.groups:
            yield from iter(group)

    def __str__(self) -> str:
        return str(self.name)


@dataclasses.dataclass(frozen=True, slots=True)
class Role:
    id: str
    name: str = ""
    description: str = ""
    roles: list[Role] = dataclasses.field(default_factory=list)
    permissions: list[Permission] = dataclasses.field(default_factory=list)
    groups: list[PermissionGroup] = dataclasses.field(default_factory=list)

    def __contains__(self, permission: Permission) -> bool:
        return permission in list(self)

    def __iter__(self) -> typing.Iterator[Permission]:
        yield from iter(self.permissions)
        for role in self.roles:
            yield from iter(role)
        for group in self.groups:
            yield from iter(group)

    def __str__(self) -> str:
        return str(self.name or self.id)


class AccessError(Exception):
    """Base class for all access errors."""


class AccessDeniedError(AccessError):
    """Raised when access is denied."""


AccessContext = typing.Any
Resource = typing.Any


class Rule(typing.Protocol):  # pragma: no cover
    """A rule that checks if a given context satisfies some condition."""

    def __call__(self, context: AccessContext, resource: Resource | None = None) -> bool: ...


def check_rule(context: AccessContext, rule: Rule, resource: Resource | None = None) -> bool:
    """Check if the given rule is satisfied in the given context."""
    return rule(context, resource)


def check_rule_or_raise(context: AccessContext, rule: Rule, resource: Resource | None = None) -> None:
    """Check if the given rule is satisfied in the given context, raise PermissionError if not."""
    if not check_rule(context, rule, resource):
        raise AccessDeniedError()
    return None


def has_permission(permission: Permission) -> Rule:
    """Create a rule that checks if the given permission is in the context."""

    def rule(context: PermissionContext, resource: Resource | None = None) -> bool:
        return permission(context, resource)

    return rule


def any_of(*rules: Rule) -> Rule:
    """Create a rule that checks if any of the given rules are satisfied."""

    def rule(context: AccessContext, resource: Resource | None = None) -> bool:
        return any(rule(context, resource) for rule in rules)

    return rule


def all_of(*rules: Rule) -> Rule:
    """Create a rule that checks if all of the given rules are satisfied."""

    def rule(context: AccessContext, resource: Resource | None = None) -> bool:
        return all(rule(context, resource) for rule in rules)

    return rule


def none_of(*rules: Rule) -> Rule:
    """Create a rule that checks if none of the given rules are satisfied."""

    def rule(context: AccessContext, resource: Resource | None = None) -> bool:
        return not any(rule(context, resource) for rule in rules)

    return rule


def get_defined_permissions(obj: type | types.ModuleType) -> typing.Generator[Permission, None, None]:
    """Get all permissions defined in a module or class."""
    for value in vars(obj).values():
        if isinstance(value, Permission):
            yield value


def get_defined_permission_groups(obj: typing.Any) -> typing.Generator[PermissionGroup, None, None]:
    """Get all permissions groups defined in a module or class."""
    for value in vars(obj).values():
        if isinstance(value, PermissionGroup):
            yield value


def get_defined_roles(obj: typing.Any) -> typing.Generator[Role, None, None]:
    """Get all roles defined in a module or class."""
    for value in vars(obj).values():
        if isinstance(value, Role):
            yield value
