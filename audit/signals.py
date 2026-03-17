# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import LoginHistory
from django.http import HttpRequest

# signals.py
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from audit.models import LogoutHistory

@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    LogoutHistory.objects.create(user=user)


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    channel = request.META.get('HTTP_USER_AGENT', 'unknown')
    if 'Mobile' in channel:
        channel = 'mobile'
    else:
        channel = 'web'
    LoginHistory.objects.create(user=user, channel=channel)