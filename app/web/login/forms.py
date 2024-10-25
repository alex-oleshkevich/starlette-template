import wtforms
from starlette_babel import gettext_lazy as _


class LoginForm(wtforms.Form):
    email = wtforms.EmailField(_("Email"), validators=[wtforms.validators.data_required()])
    password = wtforms.PasswordField(_("Password"), validators=[wtforms.validators.data_required()])
    submit = wtforms.SubmitField(_("Log in"))


class ForgotPasswordForm(wtforms.Form):
    email = wtforms.EmailField(_("Email"), validators=[wtforms.validators.data_required()])
    submit = wtforms.SubmitField(_("Reset Password"))


class ChangePasswordForm(wtforms.Form):
    password = wtforms.PasswordField(_("New password"), validators=[wtforms.validators.data_required()])
    password_confirm = wtforms.PasswordField(
        _("Confirm password"),
        validators=[
            wtforms.validators.data_required(),
            wtforms.validators.length(min=8, message=_("Password must be at least 8 characters long.")),
            wtforms.validators.equal_to("password", message=_("Passwords must match.")),
        ],
    )
    submit = wtforms.SubmitField(_("Reset Password"))
