from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'