import wtforms
from starlette_babel import gettext_lazy as _


class ProfileForm(wtforms.Form):
    first_name = wtforms.StringField(
        _("First name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
    )
    last_name = wtforms.StringField(
        _("Last name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
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
