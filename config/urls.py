from django.urls import path
from .views import (
    MailConfigListView,
    MailConfigCreateView,
    MailConfigUpdateView,
    MailConfigDetailView,
    MailConfigDeleteView,
    MailConfigToggleActiveView,
    TestMailConfigConnection,
)

urlpatterns = [
    path('mail/index/', MailConfigListView.as_view(), name='mail-config-index'),
    path('mail/create/', MailConfigCreateView.as_view(), name='mail-config-create'),
    path('mail/<uuid:uid>/details/', MailConfigDetailView.as_view(), name="mail-config-detail"),
    path('mail/<uuid:uid>/update/', MailConfigUpdateView.as_view(), name='mail-config-update'),
    path('mail/<uuid:uid>/delete/', MailConfigDeleteView.as_view(), name='mail-config-delete'),
    path("config/<uuid:uid>/toggle/active", MailConfigToggleActiveView.as_view(), name="mail-config-toggle-active"),
    path('mail/<uuid:uid>/test_connection/', TestMailConfigConnection.as_view(), name='mail-config-test-connection'),
]