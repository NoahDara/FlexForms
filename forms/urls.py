from django.urls import path
from .views import (
    FormListView,
    FormCreateView,
    FormUpdateView,
    FormDeleteView,
    FormToggleActiveView,
    FormTogglePublishView,
    
    FormFieldCreateView,
    FormFieldUpdateView,
    FormFieldDeleteView,
    FormFieldToggleActiveView,
    
    FormSectionCreateView,
    FormSectionUpdateView,
    FormSectionDeleteView,
    FormSectionToggleActiveView,
)

urlpatterns = [
    path('', FormListView.as_view(), name='form-index'),
    path('create', FormCreateView.as_view(), name='form-create'),
    path('<uuid:uid>/update', FormUpdateView.as_view(), name='form-update'),
    path('source/<uuid:uid>/delete', FormDeleteView.as_view(), name='form-delete'),
    path('source/<uuid:uid>/toggle/active', FormToggleActiveView.as_view(), name='form-toggle-active'),
    path("<uuid:uid>/toggle/publish", FormTogglePublishView.as_view(), name="form-toggle-publish"),
    
    path('<uuid:uid>/field/create', FormFieldCreateView.as_view(), name='form-field-create'),
    path('field/<uuid:uid>/update', FormFieldUpdateView.as_view(), name='form-field-update'),
    path('field/<uuid:uid>/delete', FormFieldDeleteView.as_view(), name='form-field-delete'),
    path('field/<uuid:uid>/toggle/active', FormFieldToggleActiveView.as_view(), name='form-field-toggle-active'),
    
    path('<uuid:uid>/section/create', FormSectionCreateView.as_view(), name="form-section-create"),
    path('section/<uuid:uid>/update', FormSectionUpdateView.as_view(), name='form-section-update'),
    path('section/<uuid:uid>/delete', FormSectionDeleteView.as_view(), name='form-section-delete'),
    path('section/<uuid:uid>/toggle/active', FormSectionToggleActiveView.as_view(), name='form-section-toggle-active'),
]