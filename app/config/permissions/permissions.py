from starlette_babel import gettext_lazy as _

from app.contrib.permissions import Permission

TEAM_ACCESS = Permission("team.access", _("View team information"))
TEAM_MEMBERS_ACCESS = Permission("team_member.access", _("View, invite, and modify team members"))
TEAM_ROLE_ACCESS = Permission("team_role.access", _("View and modify team roles"))
BILLING_ACCESS = Permission("billing.access", _("View and modify billing info"))
