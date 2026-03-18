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
from helpers.mixins import UIDObjectMixin
from helpers.views import ToggleActiveView, SafeDeleteView, SafeListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from ..forms import MailConfigForm
from ..models import MailConfig


class MailConfigListView(LoginRequiredMixin, SafeListView):
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


class MailConfigUpdateView(LoginRequiredMixin, UIDObjectMixin,  SuccessMessageMixin, UpdateView):
    model = MailConfig
    context_object_name = "mail_config"
    template_name = "mail_config/update.html"
    form_class = MailConfigForm
    success_message = "MailConfig updated successfully"

    def get_success_url(self):
        return reverse("mail-config-index")
    
class MailConfigDetailView(LoginRequiredMixin, DetailView):
    model = MailConfig
    context_object_name = "mail_config"
    template_name = "mail_config/details.html"


class MailConfigDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = MailConfig
    success_url = reverse_lazy("mail-config-index")
    
class MailConfigToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = MailConfig
    success_url = reverse_lazy("mail-config-index")

class TestMailConfigConnection(LoginRequiredMixin, UIDObjectMixin, TemplateView):
    model = MailConfig
    def get(self, request, **kwargs):
        try:
            obj = self.get_object()
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
            messages.success(request, "Email connection successful!")
        except Exception as e:
            messages.error(request, f"Email connection failed: {e}")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))