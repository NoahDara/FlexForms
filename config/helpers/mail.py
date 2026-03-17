from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from config.models import MailConfig

class DynamicEmailBackend:
    def __new__(cls, *args, **kwargs):
        try:
            mail_config = MailConfig.objects.filter(is_active=True).first()
        except Exception:
            # Prevent DB access issues during initial setup
            return ConsoleBackend(*args, **kwargs)

        if mail_config and mail_config.send_email:
            kwargs.update({
                "host": mail_config.email_host or "",
                "port": mail_config.email_port or 587,
                "username": mail_config.email_host_user or "",
                "password": mail_config.email_host_password or "",
                "use_tls": mail_config.email_use_tls,
                "use_ssl": mail_config.email_use_ssl,
            })
            return SMTPBackend(*args, **kwargs)
        else:
            return ConsoleBackend(*args, **kwargs)

def get_active_mail_config():
    return MailConfig.objects.filter(is_active=True).first()