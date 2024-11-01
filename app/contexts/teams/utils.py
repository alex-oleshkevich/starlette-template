import typing

from starlette.responses import Response

from app.contexts.teams.models import Team

T = typing.TypeVar("T", bound=Response)


def remember_team(response: T, team: Team) -> T:
    response.set_cookie("team_id", str(team.id), path="/")
    return response
