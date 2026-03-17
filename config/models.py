from django.db import models

# Create your models here.
class MailConfig(models.Model):
    email_host = models.CharField(max_length=255, help_text="The SMTP server address (e.g., smtp.gmail.com).")
    email_port = models.PositiveIntegerField(default=587)
    email_host_user = models.CharField()
    email_host_password = models.CharField()
    default_system_user_email = models.EmailField(blank=True, null=True)
    default_recipient = models.EmailField(blank=True, null=True)
    email_use_tls = models.BooleanField(default=False, verbose_name="EMAIL USE TLS")
    email_use_ssl = models.BooleanField(default=False, verbose_name="EMAIL USE SSL")
    send_email = models.BooleanField(default=True, verbose_name="Enable Email Sending",help_text="Send emails when checked; test mode when unchecked.")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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

    def __str__(self):
        return f"{self.email_host} ({'Active' if self.is_active else 'Inactive'})"