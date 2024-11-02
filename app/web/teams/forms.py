import wtforms
from starlette_babel import gettext_lazy as _

from app.contrib import forms


class GeneralSettingsForm(wtforms.Form):
    name = wtforms.StringField(_("Name"), [wtforms.validators.data_required()])
    photo = forms.PhotoField(
        _("Logo"),
        [wtforms.validators.optional()],
        render_kw={"accept": "image/jpg"},
        description=_("Upload a logo for your team. We recommend 800x600 JPG image."),
    )
