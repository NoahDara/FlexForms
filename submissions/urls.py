from django.urls import path
from .views import (
    SubmissionCreateView,
    SubmissionEditView,
    SubmissionDetailView
)

urlpatterns = [
    path("submit/<uuid:form_uid>/", SubmissionCreateView.as_view(), name="submission-create"),
    path("submissions/<uuid:uid>/edit/", SubmissionEditView.as_view(), name="submission-edit"),
    path("submissions/<uuid:uid>/", SubmissionDetailView.as_view(), name="submission-detail")
]
