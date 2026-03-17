from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic import (
    TemplateView,
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.core.mail import get_connection
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse

from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from ..forms import MailConfigForm
from ..models import MailConfig


class MailConfigListView(LoginRequiredMixin, ListView):
    model = MailConfig
    context_object_name = "mail_configs"
    template_name = "mail_config/index.html"


class MailConfigCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = MailConfig
    form_class = MailConfigForm
    template_name = "mail_config/create.html"
    success_message = "MailConfig created successfully"

    def get_success_url(self):
        return reverse("mail-config-index")


class MailConfigUpdateView(LoginRequiredMixin,  SuccessMessageMixin, UpdateView):
    model = MailConfig
    context_object_name = "mail_config"
    template_name = "mail_config/update.html"
    form_class = MailConfigForm
    success_message = "MailConfig updated successfully"

    def get_success_url(self):
        return reverse("mail-config-index")


class MailConfigDeleteView(LoginRequiredMixin, TemplateView):
    def get(self, request, pk, *args, **kwargs):
        obj = MailConfig.objects.get(pk=pk)  
        obj.delete()
        messages.success(request, f"{obj} deleted successfully")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
class MailConfigStatusToggleTemplateView(LoginRequiredMixin, TemplateView):
    def get(self, request, pk, *args, **kwargs):
        obj = MailConfig.objects.get(pk=pk)  
        obj.is_active = not obj.is_active
        obj.save()
        messages.success(request, f"{obj} status updated successfully")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class TestMailConfigConnection(LoginRequiredMixin, TemplateView):
    def get(self, request, pk, **kwargs):
        try:
            obj = MailConfig.objects.get(pk=pk)
            connection = get_connection(
                backend=obj.email_backend,
                host=obj.email_host,
                port=obj.email_port,
                username=obj.email_host_user,
                password=obj.email_host_password,
                use_tls=obj.email_use_tls,
                use_ssl=obj.email_use_ssl,
            )
            connection.open()  
            connection.close()
            messages.success(request, "Email connection test successful.")
        except Exception as e:
            messages.error(request, f"Email connection failed: {e}")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))