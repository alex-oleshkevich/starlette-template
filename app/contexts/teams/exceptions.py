from starlette_babel import gettext_lazy as _

from app.error_codes import ErrorCode
from app.exceptions import AppError


class TeamError(AppError):
    """Base class for team exceptions."""


class AlreadyMemberError(TeamError):
    """Raised when a user is already a member of a team."""

    error_code = ErrorCode(code="team.already_member", description=_("User is already a member of the team."))
