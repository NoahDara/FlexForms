from django.db import models

# Create your models here.
# models.py
from django.contrib.auth import get_user_model
from django.db import models

from audit.mixins import TimestampMixin

# USER LOGIN TRACKING
class LoginHistory(TimestampMixin):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    login_time = models.DateTimeField(auto_now_add=True)
    channel = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user} logged in at {self.login_time} via {self.channel}"


# Navigation Event
class NavigationEvent(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    url = models.CharField(max_length=255)
    method = models.CharField(max_length=255)
    payload = models.JSONField()
    parameters = models.TextField()
    headers = models.JSONField()
    coming_from = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} visited {self.url} at {self.timestamp}"

# models.py
class LogoutHistory(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    logout_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} logged out at {self.logout_time}"