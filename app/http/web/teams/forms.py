import typing

import wtforms
from starlette_babel import gettext_lazy as _

from app.contexts.teams.models import TeamRole
from app.contrib import forms


class GeneralSettingsForm(wtforms.Form):
    name = wtforms.StringField(_("Name"), [wtforms.validators.data_required(), wtforms.validators.length(max=255)])
    logo = forms.PhotoField(
        _("Logo"),
        [wtforms.validators.optional()],
        render_kw={"accept": "image/jpg"},
        description=_("Upload a logo for your team. We recommend 800x600 JPG image."),
    )


class InviteForm(wtforms.Form):
    email = wtforms.TextAreaField(
        _("Emails"),
        [wtforms.validators.data_required(), wtforms.validators.length(max=2000)],
        description=_("Enter email addresses separated by commas."),
    )
    role = wtforms.SelectField(_("Role"), [wtforms.validators.data_required()], coerce=int)

    def setup(self, roles: typing.Sequence[TeamRole]) -> None:
        self.role.choices = [(r.id, r.name) for r in roles]

    def validate_email(self, field: wtforms.TextAreaField) -> None:
        emails = (field.data or "").split(",")
        for email in emails:
            if "@" not in email:
                raise wtforms.validators.ValidationError(_("Invalid email address."))


class EditRoleForm(wtforms.Form):
    name = wtforms.StringField(_("Name"), [wtforms.validators.data_required(), wtforms.validators.length(max=255)])
    permissions = wtforms.SelectMultipleField(_("Permissions"), [wtforms.validators.optional()])
    is_admin = wtforms.BooleanField(
        _("Team administrator"),
        description=_("Members of this team would have all permissions."),
        validators=[wtforms.validators.optional()],
    )
