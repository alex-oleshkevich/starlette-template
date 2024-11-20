import zoneinfo

import wtforms
from starlette_babel import gettext_lazy as _

from app.config import settings


class ProfileForm(wtforms.Form):
    first_name = wtforms.StringField(
        _("First name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
    )
    last_name = wtforms.StringField(
        _("Last name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
    )
    language = wtforms.SelectField(
        _("Select language"),
        choices=settings.i18n_locales,
        validators=[wtforms.validators.data_required()],
    )
    timezone = wtforms.SelectField(
        _("Time Zone"),
        choices=sorted([(zone, zone) for zone in zoneinfo.available_timezones() if "/" in zone]),
        validators=[wtforms.validators.data_required()],
    )
    submit = wtforms.SubmitField(_("Create account"))


class PasswordForm(wtforms.Form):
    current_password = wtforms.PasswordField(_("Current Password"), validators=[wtforms.validators.data_required()])
    password = wtforms.PasswordField(_("New Password"), validators=[wtforms.validators.data_required()])
    password_confirm = wtforms.PasswordField(
        _("Confirm New Password"),
        validators=[
            wtforms.validators.data_required(),
            wtforms.validators.equal_to("password", message=_("Passwords must match.")),
        ],
    )
