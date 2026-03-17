from django.contrib import admin

from audit.models import LoginHistory, NavigationEvent

# Register your models here.
admin.site.register(LoginHistory)
admin.site.register(NavigationEvent)
