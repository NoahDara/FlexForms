from django.urls import path
from .views import (
    MailConfigListView,
    MailConfigCreateView,
    MailConfigUpdateView,
    MailConfigDeleteView,
    MailConfigStatusToggleTemplateView,
    TestMailConfigConnection,
)

urlpatterns = [
    path('mail/index/', MailConfigListView.as_view(), name='mail-config-index'),
    path('mail/create/', MailConfigCreateView.as_view(), name='mail-config-create'),
    path('mail/<int:pk>/update/', MailConfigUpdateView.as_view(), name='mail-config-update'),
    path('mail/<int:pk>/delete/', MailConfigDeleteView.as_view(), name='mail-config-delete'),
    path('mail/<int:pk>/toggle-status/', MailConfigStatusToggleTemplateView.as_view(), name='mail-config-toggle-status'),
    path('mail/<int:pk>/test_connection/', TestMailConfigConnection.as_view(), name='mail-config-test-connection'),
]