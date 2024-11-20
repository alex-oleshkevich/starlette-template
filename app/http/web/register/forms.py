import wtforms
from starlette_babel import gettext_lazy as _


class RegisterForm(wtforms.Form):
    email = wtforms.EmailField(_("Email"), validators=[wtforms.validators.data_required()])
    first_name = wtforms.StringField(
        _("First name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
    )
    last_name = wtforms.StringField(
        _("Last name"), validators=[wtforms.validators.data_required(), wtforms.validators.length(min=1, max=50)]
    )
    password = wtforms.PasswordField(
        _("Password"), validators=[wtforms.validators.data_required(), wtforms.validators.length(max=255)]
    )
    password_confirm = wtforms.PasswordField(
        _("Confirm Password"),
        validators=[
            wtforms.validators.data_required(),
            wtforms.validators.equal_to("password", message=_("Passwords must match.")),
        ],
    )
    terms = wtforms.BooleanField(
        _("I agree to the terms and conditions"), validators=[wtforms.validators.data_required()]
    )
    submit = wtforms.SubmitField(_("Create account"))
