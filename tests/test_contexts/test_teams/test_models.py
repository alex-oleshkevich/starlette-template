from app.contexts.teams.models import Team


class TestTeamModel:
    def test_color_hash(self) -> None:
        team = Team(name="My Team")
        assert team.color_hash == "#3a4f78"

    def test_initials(self) -> None:
        team = Team(name="My Team")
        assert team.initials == "MT"

        team = Team(name="Team")
        assert team.initials == "T"

        team = Team(name="My Cool Team")
        assert team.initials == "MC"
