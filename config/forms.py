from django.forms import ModelForm
from .models import MailConfig


class MailConfigForm(ModelForm):
    class Meta:
        model = MailConfig
        fields = "__all__"
        exclude = ["is_active",]

    def __init__(self,  *args, **kwargs):
        super(MailConfigForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"