from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import time
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse

from companies.models import Company
from core.email_service import get_email_service

def send_onboarding_reset_password_mail(request, user):
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build base reset URL
    reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    
    # Add source parameter with organization UID
    organization_uid = getattr(user, 'organization_uid', None)
    
    
    if organization_uid:
        # Add source parameter to URL
        reset_url = request.build_absolute_uri(reset_path)
        separator = '&' if '?' in reset_url else '?'
        reset_url = f"{reset_url}{separator}source={organization_uid}"
    else:
        # Fallback without source (for superusers or users without org)
        reset_url = request.build_absolute_uri(reset_path)
        settings.LOGGER.warning(f"User {user.username} has no organization_uid")
    
    system_company = Company.objects.first()
    subject = "You have been invited our daarah tech enterprise suite!"
    message = render_to_string('mail_list/welcome_user.html', {
        'user': user,
        'reset_url': reset_url,
        'system_company': system_company, 
    })
    
    get_email_service().send_email(
        subject=subject,
        html_message=message,
        message=message,
        recipient_list=[user.email],
    )
    
def send_password_reset_mail(request, user):
    """
    Send email to existing users who requested password reset.
    """
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build base reset URL
    reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    
    # Add source parameter with organization UID
    organization_uid = getattr(user, 'organization_uid', None)
    
    if organization_uid:
        # Add source parameter to URL
        reset_url = request.build_absolute_uri(reset_path)
        separator = '&' if '?' in reset_url else '?'
        reset_url = f"{reset_url}{separator}source={organization_uid}"
    else:
        # Fallback without source (for superusers or users without org)
        reset_url = request.build_absolute_uri(reset_path)
        settings.LOGGER.warning(f"User {user.username} has no organization_uid")
    
    system_company = Company.objects.first()
    subject = "Password Reset Request - Daarah Tech Enterprise Suite"
    message = render_to_string('mail_list/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
        'system_company': system_company, 
    })
    
    get_email_service().send_email(
        subject=subject,
        html_message=message,
        message=message,
        recipient_list=[user.email],
    )


def send_email_from_global_config(email_subject, email_content, user=None, email=None, html_file_path=None):
    if not html_file_path:
        html_file_path = "mail_list/global_email.html"
    if user:
        recipient_email = user.email
        username = user.username
    elif email:
        recipient_email = email
        username = email
    else:
        settings.LOGGER.error("No user or email provided for sending email.")
        return False
    
    
    email_html_content = render_to_string(
        html_file_path,
        {"username": username, "your_email_content": email_content}
    )
    
    # Use plain text version for the message parameter
    plain_message = strip_tags(email_html_content)
    
    try:
        get_email_service().send_email(
            subject=email_subject,
            message=plain_message,
            html_message=email_html_content,
            recipient_list=[recipient_email],
        )
        return True
    except Exception as e:
        error_message = f"Failed to send email to {recipient_email}: {str(e)}"
        settings.LOGGER.error(error_message)
        return False


def send_html_email(
    subject, html_template, text_content, from_email, to_emails, context={}
):
    """
    Sends an HTML email without attachments.

    Args:
        subject (str): Email subject.
        html_template (str): Path to the HTML template.
        text_content (str): Fallback plain text content.
        from_email (str): Sender's email address.
        to_emails (list): List of recipient email addresses.
        context (dict): Context to render the HTML template.

    Returns:
        int: Number of successfully delivered messages (1 if successful).
    """

    # Render the HTML template with the given context
    html_content = render_to_string(html_template, context)

    # Create the email object with plain text and HTML alternatives
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_emails)
    msg.attach_alternative(html_content, "text/html")

    # Send the email
    while True:
        try:
            settings.LOGGER.info(f"Sending email to {to_emails}")
            msg.send(fail_silently=False)
            break
        except Exception as e:
            settings.LOGGER.error(f"Error sending email: {e}")
            time.sleep(5)
    return msg.send()


def send_email_with_attachments(
    subject,
    html_template,
    text_content,
    from_email,
    to_emails,
    attachments=None,
    context={},
):
    # Render the HTML template to a string
    html_content = render_to_string(html_template, context)

    # Create the email message object
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_emails)
    msg.attach_alternative(html_content, "text/html")

    # Attach each file
    if attachments:
        for attachment in attachments:
            msg.attach(attachment[0], attachment[1].read(), attachment[2])

    # Send the email

    
    try:
        settings.LOGGER.info(f"Sending email to {to_emails}")
        msg.send(fail_silently=False)
    except Exception as e:
        settings.LOGGER.error(f"Error sending email: {e}")
        email_service = settings.EMAIL_SERVICE
        email_service.send_email(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=to_emails,
            html_message=html_content,
        )