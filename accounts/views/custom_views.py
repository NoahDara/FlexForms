from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser as User
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.views import PasswordResetView
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.views.generic.edit import UpdateView
from ..forms import CustomUserCreationForm, CustomUserUpdateForm, LoginForm
from django.contrib.auth import logout
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin



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
