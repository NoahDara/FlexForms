from django.urls import path
from .views import (
    SubmissionCreateView,
    SubmissionEditView,
    SubmissionDetailView,
    SubmissionPDFView,
    
    SubmissionListView,
    SubmissionDeleteView,
    SubmissionToggleActiveView
)

urlpatterns = [
    path("submit/<uuid:form_uid>/", SubmissionCreateView.as_view(), name="submission-create"),
    path("submissions/<uuid:uid>/edit/", SubmissionEditView.as_view(), name="submission-edit"),
    path("submissions/<uuid:uid>/", SubmissionDetailView.as_view(), name="submission-detail"),
    path("submissions/<uuid:uid>/pdf/", SubmissionPDFView.as_view(), name="submission-pdf"),
    
    path('submissions', SubmissionListView.as_view(), name='submission-index'),
    path('submissions/<uuid:uid>/delete', SubmissionDeleteView.as_view(), name='submission-delete'),
    path('submissions/<uuid:uid>/toggle/active', SubmissionToggleActiveView.as_view(), name='submission-toggle-active'),
]
