from django.urls import path
from accounts.views.groups import (
    GroupListView,
    GroupCreateView,
    GroupUpdateView,
    GroupDeleteView,
)

urlpatterns = [
    path('',              GroupListView.as_view(),   name='group-index'),
    path('create/',       GroupCreateView.as_view(),  name='group-create'),
    path('<int:pk>/',     GroupUpdateView.as_view(),  name='group-update'),
    path('<int:pk>/delete/', GroupDeleteView.as_view(), name='group-delete'),
]