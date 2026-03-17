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


def logout_view(request):
    logout(request)
    return redirect('login')

class LoginUserView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("dashboard")  

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)

            employee = getattr(user, "employee", None)
            
            if user.is_active:
                if employee:
                    messages.success(self.request, f"You have successfully logged in as {employee}")
                else:
                    messages.success(self.request, f"You have successfully logged in as {user}")
            else:
                messages.warning(self.request, "Your account is inactive. Please contact system administrator.")

            # Handle the 'next' parameter for redirection
            next_url = self.request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
                return redirect(next_url)
            
            # Default to success_url if 'next' is not set or not safe
            return super().form_valid(form)
        else:
            messages.warning(
                self.request, "Please check your credentials and try again"
            )
            return redirect("login")

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)


class UserListView(LoginRequiredMixin, ListView, ):
    model = User
    template_name = "registration/index.html"


def register_user(request):
    if request.method == "GET":
        return render(
            request, "registration/create.html", {"form": CustomUserCreationForm}
        )
    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, ("User created successfully"))
        return redirect("users-index")
    else:
        messages.success(request, ("Something went wrong please try again"))
        return redirect("register-user")


class UserUpdateView(SuccessMessageMixin, UpdateView):
    model = User
    form_class = CustomUserUpdateForm
    success_message = "User updated successfully"
    context_object_name = "user"

    def get_template_names(self):
        user = self.get_object()
        if self.request.user.is_superuser:
            return ["registration/update.html"]
        return ["registration/self_update.html"]
        

    def get_success_url(self):
        user = self.get_object()
        if self.request.user.is_superuser:
            return reverse("users-index")
        return reverse("dashboard")
        

    def form_valid(self, form):
        password = form.cleaned_data.get("password")
        if password:
            form.instance.password = make_password(password)

        return super().form_valid(form)

    # def get_required_permissions(self):
    #     return ['Can change user']

class UserDeleteView(LoginRequiredMixin, TemplateView):
    def get(self, request, **kwargs):
        obj = User.objects.get(pk=self.request.GET.get('pk'))
        obj.is_deleted = True
        obj.save()
        messages.warning(self.request, 'User Deleted successfully')
        return redirect('users-index')   

     
class UserDeactivateView(LoginRequiredMixin, SuccessMessageMixin, View):
    def get(self, request, **kwargs):
        obj = get_object_or_404(User, pk=kwargs.get("pk"))
        if obj.is_active:
            obj.is_active = False
            messages.success(request, f"{obj} has been deactivated successfully")
        else:
            obj.is_active = True
            messages.success(request, f"{obj} has been activated successfully")
        obj.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))