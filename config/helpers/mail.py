from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from config.models import MailConfig
from django.conf import settings


class DynamicEmailBackend:
    """
    Dynamic email backend that routes to company-specific SMTP or default SMTP.
    """
    
    def __new__(cls, *args, **kwargs):
        # Extract company from kwargs if provuided

        
        try:
            mail_config = get_active_mail_config()
        except Exception:
            # During migrations/setup, use console to avouid DB access issues
            return ConsoleBackend(*args, **kwargs)

        if mail_config and mail_config.send_email:
            # Use company-specific SMTP config
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
            # Use default Django SMTP settings (not console!)
            # Only use console if explicitly no credentials configured
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                return ConsoleBackend(*args, **kwargs)
            
            return SMTPBackend(*args, **kwargs)


def get_active_mail_config():
    """
    Get active mail configuration for a specific.
    """

    
    try:
        return MailConfig.objects.filter(is_active=True).first()
    except Exception as e:
        settings.LOGGER.error(f"Error occurred {e}.")
        return None