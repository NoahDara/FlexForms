# models.py
from django.db import models
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from helpers.models import BaseModel

class MailConfig(BaseModel):
    email_host = models.CharField(
        max_length=255,
        help_text="The SMTP server address (e.g., smtp.gmail.com)."
    )
    email_port = models.PositiveIntegerField(default=587)
    email_host_user = models.CharField(max_length=255, unique=True)
    email_host_password_encrypted = models.CharField(max_length=500, blank=True, null=True)
    default_system_user_email = models.EmailField(blank=True, null=True)
    default_recipient = models.EmailField(blank=True, null=True)
    
    email_use_tls = models.BooleanField(default=False, verbose_name="EMAIL USE TLS")
    email_use_ssl = models.BooleanField(default=False, verbose_name="EMAIL USE SSL")
    
    
    send_email = models.BooleanField(
        default=True,
        verbose_name="Enable Email Sending",
        help_text="Send emails when checked; test mode when unchecked."
    )

    def save(self, *args, **kwargs):
        if self.is_active:
            MailConfig.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def email_backend(self):
        return (
            "django.core.mail.backends.smtp.EmailBackend"
            if self.send_email
            else "django.core.mail.backends.console.EmailBackend"
        )

    # -----------------------
    # Encryption helpers
    # -----------------------
    def _get_fernet(self):
        if not hasattr(settings, "MAIL_CONFIG_SECRET_KEY"):
            raise ValueError("MAIL_CONFIG_SECRET_KEY must be configured correctly")
        return Fernet(settings.MAIL_CONFIG_SECRET_KEY.encode())

    @property
    def email_host_password(self):
        """Decrypt password at runtime."""
        if not self.email_host_password_encrypted:
            return None
        try:
            return self._get_fernet().decrypt(
                self.email_host_password_encrypted.encode()
            ).decode()
        except InvalidToken:
            return None

    @email_host_password.setter
    def email_host_password(self, raw_password):
        """Encrypt password before saving."""
        if raw_password:
            token = self._get_fernet().encrypt(raw_password.encode()).decode()
            self.email_host_password_encrypted = token
        else:
            self.email_host_password_encrypted = None

    def __str__(self):
        return f"{self.email_host} ({'Active' if self.is_active else 'Inactive'})"
