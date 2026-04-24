from django.http.response import HttpResponse as HttpResponse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.views import PasswordResetView
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.views import PasswordResetView
from django.conf import settings




# Custom email reset
class CustomPasswordResetView(PasswordResetView):
    email_template_name = "account/password_reset_email.html"
    html_email_template_name = "account/password_reset_email.html"

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        html_email = render_to_string(html_email_template_name, context)
        email_message = EmailMessage(
            subject_template_name,
            html_email,
            from_email,
            [to_email],
        )

        email_message.content_subtype = "html"
        settings.LOGGER.info(email_message)
        email_message.send()
