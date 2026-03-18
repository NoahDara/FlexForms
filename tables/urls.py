from django.urls import path
from .views import (
    TableListView,
    TableCreateView,
    TableUpdateView,
    TablePreviewView,
    TableDeleteView,
    TableToggleActiveView
)

urlpatterns = [
    path("", TableListView.as_view(), name="table-index"),
    path("create", TableCreateView.as_view(), name="table-create"),
    path("<uuid:uid>", TablePreviewView.as_view(), name="table-preview"),
    path("<uuid:uid>/update", TableUpdateView.as_view(), name="table-update"),
    path("<uuid:uid>/toggle/active", TableToggleActiveView.as_view(), name="table-toggle-active"),
    path("<uuid:uid>/delete", TableDeleteView.as_view(), name="table-delete"),
]
