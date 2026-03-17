from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.audit_dashboard, name='audit_dashboard'),
    path('export-reports/', views.export_reports, name='export_reports'),
]