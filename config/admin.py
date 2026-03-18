from django.contrib import admin
from django import forms
from .models import MailConfig
from simple_history.admin import SimpleHistoryAdmin
class MailConfigForm(forms.ModelForm):
    password = forms.CharField(
        label="SMTP Password",
        required=False,
        widget=forms.PasswordInput,
        help_text="Enter a new password to replace the existing one. Leave blank to keep current."
    )

    class Meta:
        model = MailConfig
        exclude = ("email_host_password_encrypted",)

    def save(self, commit=True):
        obj = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            obj.email_host_password = pwd  # setter encrypts
        if commit:
            obj.save()
        return obj

@admin.register(MailConfig)
class MailConfigAdmin(SimpleHistoryAdmin):
    form = MailConfigForm
    list_display = ("email_host", "email_port", "email_host_user", "is_active", "updated")
    list_filter = ("email_host", "send_email", "is_active")
    search_fields = ("email_host", "email_host_user")
    readonly_fields = ("created", "updated")

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    # def has_delete_permission(self, request, obj=None):
    #     return request.user.is_superuser
