import wtforms
from starlette_babel import gettext_lazy as _
from starlette_sqlalchemy import Collection

from app.contexts.teams.models import TeamRole
from app.contrib import forms


class GeneralSettingsForm(wtforms.Form):
    name = wtforms.StringField(_("Name"), [wtforms.validators.data_required()])
    logo = forms.PhotoField(
        _("Logo"),
        [wtforms.validators.optional()],
        render_kw={"accept": "image/jpg"},
        description=_("Upload a logo for your team. We recommend 800x600 JPG image."),
    )


class InviteForm(wtforms.Form):
    email = wtforms.TextAreaField(
        _("Emails"),
        [wtforms.validators.data_required()],
        description=_("Enter email addresses separated by commas."),
    )
    role = wtforms.SelectField(_("Role"), [wtforms.validators.data_required()], coerce=int)

    def setup(self, roles: Collection[TeamRole]) -> None:
        self.role.choices = [(r.id, r.name) for r in roles]

    def validate_email(self, field: wtforms.TextAreaField) -> None:
        emails = (field.data or "").split(",")
        for email in emails:
            if "@" not in email:
                raise wtforms.validators.ValidationError(_("Invalid email address."))
