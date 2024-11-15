import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from starlette_babel import gettext_lazy as _

from app.config.crypto import amake_password
from app.contexts.billing.models import Subscription
from app.contexts.teams.models import Team, TeamMember, TeamRole
from app.contexts.users.models import User


async def register_user(
    dbsession: AsyncSession,
    first_name: str,
    last_name: str,
    email: str,
    plain_password: str,
    photo_url: str | None = None,
    language: str = "en",
    timezone: str = "UTC",
    subscription_status: Subscription.Status = Subscription.Status.TRIALING,
    subscription_duration: datetime.timedelta = datetime.timedelta(days=30),
    *,
    auto_confirm: bool = False,
    auto_renew_subscription: bool = True,
) -> User:
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        photo=photo_url,
        language=language,
        timezone=timezone,
        password=await amake_password(plain_password),
        email_confirmed_at=datetime.datetime.now(datetime.UTC) if auto_confirm else None,
    )
    team = Team(name=_("{name}'s team").format(name=first_name), owner=user)
    team_role = TeamRole(name="Owners", team=team, is_admin=True)
    team_member = TeamMember(team=team, user=user, role=team_role)
    dbsession.add_all([user, team, team_role, team_member])
    await dbsession.flush()
    return user
