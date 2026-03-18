from django import forms
from .models import MailConfig
from helpers.forms import CustomBaseForm

class MailConfigForm(CustomBaseForm):
    # A visible password field (not the raw DB column).
    # We will exclude the real DB field from the form below.
    password_mask = "********"   # placeholder shown as dots
    password = forms.CharField(
        label="SMTP Password",
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Leave blank to keep current password. Enter a new password to replace it."
    )

    class Meta:
        model = MailConfig
        # Do not include the raw encrypted DB column in the form
        exclude = ("email_host_password_encrypted",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing an existing config, show the mask so the field appears as dots.
        if self.instance and self.instance.pk:
            self.fields["password"].initial = self.password_mask
            # discourage browser autofill
            self.fields["password"].widget.attrs["autocomplete"] = "new-password"

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        # If user left it blank or left the mask unchanged -> treat as no change
        if not pwd or pwd == self.password_mask:
            return None
        return pwd

    def save(self, commit=True):
        obj = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        # Only call the model setter (which encrypts) if a real new password was provided
        if pwd:
            obj.email_host_password = pwd   # setter handles encryption
        if commit:
            obj.save()
        return obj
