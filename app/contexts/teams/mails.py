from starlette.datastructures import URL
from starlette_babel import gettext_lazy as _

from app.config.mailers import send_templated_mail
from app.contexts.teams.models import TeamInvite, TeamMember


async def send_team_invitation_email(invite: TeamInvite, link: URL) -> None:
    """Email the invitee with a link to join the team.

    Team owner will also be BCC'd on the invite email.
    This is to ensure that the owner is aware of who is being invited to the team.
    """

    bcc: str | None = None
    recipient = invite.inviter.user.email
    team_owner_email = invite.team.owner.email
    if recipient != team_owner_email:
        bcc = team_owner_email

    await send_templated_mail(
        to=invite.email,
        bcc=bcc,
        subject=_("{user} invites you to join the team {team}").format(user=invite.inviter, team=invite.team),
        html_template="mails/team_invite.html",
        context={"user": invite.inviter, "team": invite.team, "link": link},
        headers={"x-invite-link": str(link)},
    )


async def send_team_member_joined_email(invitation: TeamInvite, team_member: TeamMember) -> None:
    bcc: str | None = None
    recipient = invitation.inviter.user.email
    team_owner_email = team_member.team.owner.email
    if recipient != team_owner_email:
        bcc = team_owner_email

    await send_templated_mail(
        to=recipient,
        bcc=bcc,
        subject=_("{user} has accepted your invitation").format(user=team_member.user),
        html_template="mails/team_invite_accepted.html",
        context={"user": team_member.user, "team": team_member.team},
    )
