from django.urls import path
from .views import (
    DashboardTemplateView,
)


urlpatterns = [
    path('home/', DashboardTemplateView.as_view(), name="dashboard"),
]
