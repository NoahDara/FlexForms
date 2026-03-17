from django.contrib import admin
from .models import MailConfig
# Register your models here.

@admin.register(MailConfig)
class MailConfigAdmin(admin.ModelAdmin):
    list_display = ('email_host', 'email_port', 'email_host_user', 'is_active', 'created',  'updated')
    list_filter = ('email_host', 'send_email' )
    search_fields = ('email_host_user', )
    date_hierarchy = 'updated'