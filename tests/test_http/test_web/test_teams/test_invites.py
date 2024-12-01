import limits
import pytest
import sqlalchemy as sa
from mailers.pytest_plugin import Mailbox
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.contexts.teams.models import InvitationToken, Team, TeamInvite, TeamMember, TeamRole
from app.contrib.testing import TestAuthClient, as_htmx_response
from app.http.dependencies import Settings
from tests.factories import TeamInviteFactory, TeamMemberFactory, TeamRoleFactory, UserFactory


class TestInvitations:
    def test_invite_form(self, auth_client: TestClient) -> None:
        response = auth_client.get("/app/teams/members/invite")
        assert response.status_code == 200

    def test_invite_member(
        self,
        auth_client: TestClient,
        team: Team,
        team_user_role: TeamRole,
        mailbox: Mailbox,
    ) -> None:
        response = auth_client.get("/app/teams/members/invite")
        assert response.status_code == 200

        response = auth_client.post(
            "/app/teams/members/invite",
            data={
                "email": "user@localhost.tld",
                "role": str(team_user_role.id),
            },
        )
        assert response.status_code == 204
        assert len(mailbox) == 1
        assert mailbox[0]["bcc"] is None

        assert as_htmx_response(response).triggers("toast")
        assert as_htmx_response(response).triggers("modals-close")

    def test_duplicate_invitation(
        self,
        auth_client: TestClient,
        team: Team,
        team_user_role: TeamRole,
        mailbox: Mailbox,
        team_member: TeamMember,
    ) -> None:
        TeamInviteFactory(team=team, email="user@localhost.tld", role=team_user_role, inviter=team_member)

        response = auth_client.post(
            "/app/teams/members/invite",
            data={
                "email": "user@localhost.tld",
                "role": str(team_user_role.id),
            },
        )
        assert response.status_code == 400
        assert len(mailbox) == 0
        assert "One or more of the emails you entered is already invited." in response.text

    def test_notifies_team_owner(
        self, auth_client: TestClient, team: Team, team_user_role: TeamRole, mailbox: Mailbox, dbsession_sync: Session
    ) -> None:
        """Team owner should be BCC'd on the invite email.
        This is to ensure that the owner is aware of who is being invited to the team."""

        user = UserFactory()
        team.owner = user
        dbsession_sync.commit()

        response = auth_client.post(
            "/app/teams/members/invite",
            data={
                "email": "user@localhost.tld",
                "role": str(team_user_role.id),
            },
        )
        assert response.status_code == 204
        assert len(mailbox) == 1
        assert mailbox[0]["bcc"] == user.email

        assert as_htmx_response(response).triggers("toast")
        assert as_htmx_response(response).triggers("modals-close")

    def test_invite_member_invalid_email(
        self,
        auth_client: TestClient,
        team_user_role: TeamRole,
        mailbox: Mailbox,
    ) -> None:
        response = auth_client.post(
            "/app/teams/members/invite",
            data={
                "email": "userlocalhost.tld",
                "role": str(team_user_role.id),
            },
        )
        assert response.status_code == 200
        assert len(mailbox) == 0
        assert "Invalid email address" in response.text

        assert not as_htmx_response(response).triggers("toast")
        assert not as_htmx_response(response).triggers("modals-close")

    def test_invite_multiple_members(
        self,
        auth_client: TestClient,
        team_user_role: TeamRole,
        mailbox: Mailbox,
    ) -> None:
        response = auth_client.post(
            "/app/teams/members/invite",
            data={
                "email": "user@localhost.tld, user2@localhost.tld",
                "role": str(team_user_role.id),
            },
        )
        assert response.status_code == 204
        assert len(mailbox) == 2

        as_htmx_response(response).triggers("toast")
        as_htmx_response(response).triggers("modals-close")

    async def test_accept_invite_when_authenticated(
        self,
        auth_client: TestAuthClient,
        team_member: TeamMember,
        dbsession_sync: Session,
        mailbox: Mailbox,
    ) -> None:
        invitee = TeamMemberFactory()
        token = InvitationToken()
        team_invite_id = TeamInviteFactory(
            team=team_member.team, token=token.hashed_token, email=invitee.user.email, inviter=team_member
        ).id

        auth_client.force_team(invitee.team)
        await auth_client.force_user(invitee.user)
        response = auth_client.get(f"/teams/members/accept-invite/{token.plain_token}")
        assert response.status_code == 302
        assert response.headers["location"] == f"http://testserver/app/?team_id={team_member.team_id}"

        assert dbsession_sync.scalars(
            sa.select(TeamMember).where(
                TeamMember.user_id == invitee.user_id, TeamMember.team_id == team_member.team_id
            )
        ).one_or_none()
        assert not dbsession_sync.scalars(sa.select(TeamInvite).where(TeamInvite.id == team_invite_id)).one_or_none()
        assert mailbox[0]["to"] == team_member.user.email
        assert not mailbox[0]["bcc"]

    async def test_accept_invite_when_authenticated_notifies_team_owner(
        self,
        auth_client: TestAuthClient,
        team_member: TeamMember,
        dbsession_sync: Session,
        mailbox: Mailbox,
    ) -> None:
        invitee = TeamMemberFactory()
        token = InvitationToken()

        # team member, who is not the team owner, invites a user
        user = UserFactory()
        inviter = TeamMemberFactory(team=team_member.team, role=TeamRoleFactory(is_admin=True), user=user)
        TeamInviteFactory(team=team_member.team, token=token.hashed_token, email=invitee.user.email, inviter=inviter)

        auth_client.force_team(invitee.team)
        await auth_client.force_user(invitee.user)
        response = auth_client.get(f"/teams/members/accept-invite/{token.plain_token}")
        assert response.status_code == 302

        assert mailbox[0]["to"] == inviter.user.email
        assert mailbox[0]["bcc"] == team_member.user.email

    async def test_already_accepted(
        self,
        auth_client: TestAuthClient,
        team: Team,
        team_user_role: TeamRole,
        mailbox: Mailbox,
        team_member: TeamMember,
    ) -> None:
        """Test a case when user is already a team member."""
        user = UserFactory()
        TeamMemberFactory(team=team, user=user, role=team_user_role)
        token = InvitationToken()
        TeamInviteFactory(team=team_member.team, token=token.hashed_token, email=user.email, inviter=team_member)

        auth_client.force_team(team)
        await auth_client.force_user(user)
        response = auth_client.get(f"/teams/members/accept-invite/{token.plain_token}")
        assert response.status_code == 302
        assert response.headers["location"] == "http://testserver/app/"

        response = auth_client.get(response.headers["location"])
        assert response.status_code == 200
        assert "You are already a member of this team." in response.text

    def test_no_invitation(self, auth_client: TestClient, team_member: TeamMember) -> None:
        response = auth_client.get("/teams/members/accept-invite/somemissingtoken")
        assert "Invalid or expired invitation" in response.text

    def test_with_deleted_inviter(
        self, auth_client: TestClient, team_member: TeamMember, dbsession_sync: Session
    ) -> None:
        user = UserFactory()
        token = InvitationToken()
        inviter = TeamMemberFactory(team=team_member.team, user=user)
        _ = TeamInviteFactory(team=inviter.team, token=token.hashed_token, inviter=inviter)

        dbsession_sync.delete(inviter)
        dbsession_sync.commit()
        response = auth_client.get(f"/teams/members/accept-invite/{token.plain_token}")
        assert response.status_code == 400

    def test_with_deleted_role(self, auth_client: TestClient, team_member: TeamMember, dbsession_sync: Session) -> None:
        token = InvitationToken()
        _ = TeamInviteFactory(
            team=team_member.team, token=token.hashed_token, inviter=team_member, role=team_member.role
        )

        old_role = team_member.role
        team_member.role = TeamRoleFactory(team=team_member.team)
        dbsession_sync.delete(old_role)
        dbsession_sync.commit()
        response = auth_client.get(f"/teams/members/accept-invite/{token.plain_token}")
        assert response.status_code == 400

    def test_invitation_flow_with_user_registration_and_without_autologin(
        self,
        client: TestClient,
        team_member: TeamMember,
        monkeypatch: pytest.MonkeyPatch,
        settings: Settings,
    ) -> None:
        # enable auto login
        monkeypatch.setattr(settings, "register_auto_login", True)

        token = InvitationToken()
        invitation = TeamInviteFactory(team=team_member.team, token=token.hashed_token, inviter=team_member)

        # user clicks on the invitation link without being authenticated
        response = client.get(f"/teams/members/accept-invite/{token.plain_token}")
        assert response.status_code == 302
        assert response.headers["location"] == "http://testserver/register"

        response = client.get(response.headers["location"])
        assert response.status_code == 200
        assert invitation.email in response.text

        # perform registration
        response = client.post(
            "/register",
            data={
                "email": invitation.email,
                "first_name": "John",
                "last_name": "Doe",
                "password": "password",
                "password_confirm": "password",
                "terms": "1",
            },
        )
        assert response.status_code == 302
        assert response.headers["location"] == f"http://testserver/teams/members/accept-invite/{token.plain_token}"

        response = client.get(response.headers["location"])
        assert response.status_code == 302
        assert response.headers["location"] == f"http://testserver/app/?team_id={team_member.team_id}"

        response = client.get(response.headers["location"])
        assert response.status_code == 200
        assert team_member.team.name in response.text

    def test_invitation_flow_with_user_registration_and_autologin(
        self,
        client: TestClient,
        team_member: TeamMember,
        monkeypatch: pytest.MonkeyPatch,
        settings: Settings,
    ) -> None:
        # enable auto login
        monkeypatch.setattr(settings, "register_auto_login", False)

        token = InvitationToken()
        invitation = TeamInviteFactory(team=team_member.team, token=token.hashed_token, inviter=team_member)

        # user clicks on the invitation link without being authenticated
        response = client.get(f"/teams/members/accept-invite/{token.plain_token}")
        assert response.status_code == 302
        assert response.headers["location"] == "http://testserver/register"

        # perform registration
        response = client.post(
            "/register",
            data={
                "email": invitation.email,
                "first_name": "John",
                "last_name": "Doe",
                "password": "password",
                "password_confirm": "password",
                "terms": "1",
            },
        )
        assert response.status_code == 302
        assert response.headers["location"] == "http://testserver/login"

        response = client.post(
            response.headers["location"],
            data={
                "email": invitation.email,
                "password": "password",
            },
        )
        assert response.status_code == 302
        assert response.headers["location"] == f"http://testserver/teams/members/accept-invite/{token.plain_token}"

        response = client.get(response.headers["location"])
        assert response.status_code == 302
        assert response.headers["location"] == f"http://testserver/app/?team_id={team_member.team_id}"

        response = client.get(response.headers["location"])
        assert response.status_code == 200
        assert team_member.team.name in response.text

    def test_cancel_invitation(
        self, auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session
    ) -> None:
        response = auth_client.post("/app/teams/invites/cancel/-1")
        assert response.status_code == 404

        user = UserFactory()
        team_member = TeamMemberFactory(team=team_member.team, user=user)
        invitation = TeamInviteFactory(team=team_member.team, inviter=team_member)
        response = auth_client.post(f"/app/teams/invites/cancel/{invitation.id}")
        assert response.status_code == 204

        assert not dbsession_sync.scalars(sa.select(TeamInvite).where(TeamInvite.id == invitation.id)).one_or_none()

    def test_resend_invitation(
        self, auth_client: TestAuthClient, monkeypatch: pytest.MonkeyPatch, team_member: TeamMember, mailbox: Mailbox
    ) -> None:
        monkeypatch.setattr("app.http.web.teams.routes.resent_invite_rate_limit", limits.parse("100/minute"))

        response = auth_client.post("/app/teams/invites/resend/-1")
        assert response.status_code == 404
        assert len(mailbox) == 0

        user = UserFactory()
        team_member = TeamMemberFactory(team=team_member.team, user=user)
        invitation = TeamInviteFactory(team=team_member.team, inviter=team_member)

        response = auth_client.post(f"/app/teams/invites/resend/{invitation.id}")
        assert response.status_code == 204
        assert len(mailbox) == 1

    def test_resend_invitation_limit(
        self,
        auth_client: TestAuthClient,
        monkeypatch: pytest.MonkeyPatch,
        team_member: TeamMember,
        mailbox: Mailbox,
        dbsession_sync: Session,
    ) -> None:
        monkeypatch.setattr("app.http.web.teams.routes.resent_invite_rate_limit", limits.parse("1/minute"))

        user = UserFactory()
        team_member = TeamMemberFactory(team=team_member.team, user=user)
        invitation: TeamInvite = TeamInviteFactory(team=team_member.team, inviter=team_member)

        response = auth_client.post(f"/app/teams/invites/resend/{invitation.id}")
        assert response.status_code == 204

        invitation = dbsession_sync.scalars(
            sa.select(TeamInvite).where(TeamInvite.team_id == team_member.team_id)
        ).one()
        response = auth_client.post(f"/app/teams/invites/resend/{invitation.id}")
        assert response.status_code == 429
