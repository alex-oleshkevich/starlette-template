import wtforms
from starlette_babel import gettext_lazy as _


class RegisterForm(wtforms.Form):
    email = wtforms.EmailField(_("Email"), validators=[wtforms.validators.data_required()])
    first_name = wtforms.EmailField(
        _("First name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
    )
    last_name = wtforms.EmailField(
        _("Last name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
    )
    password = wtforms.PasswordField(_("Password"), validators=[wtforms.validators.data_required()])
    password_confirm = wtforms.PasswordField(_("Confirm Password"), validators=[wtforms.validators.data_required()])
    submit = wtforms.SubmitField(_("Create account"))
