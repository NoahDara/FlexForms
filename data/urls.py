from django.urls import path
from .views import (
    DataTypeListView,
    
    DataSourceListView,
    DataSourceCreateView,
    DataSourceUpdateView,
    DataSourceDeleteView,
    DataSourceToggleActiveView,
    
    DataCreateView,
    DataUpdateView,
    DataDeleteView,
    DataToggleActiveView
)

urlpatterns = [
    path('types', DataTypeListView.as_view(), name='data-type-index'),

    path('sources', DataSourceListView.as_view(), name='data-source-index'),
    path('sources/create', DataSourceCreateView.as_view(), name='data-source-create'),
    path('sources/<uuid:uid>/update', DataSourceUpdateView.as_view(), name='data-source-update'),
    path('source/<uuid:uid>/delete', DataSourceDeleteView.as_view(), name='data-source-delete'),
    path('source/<uuid:uid>/toggle/active', DataSourceToggleActiveView.as_view(), name='data-source-toggle-active'),

    path('sources/<uuid:uid>/data/create', DataCreateView.as_view(), name='data-create'),
    path('<uuid:uid>/update', DataUpdateView.as_view(), name='data-update'),
    path('<uuid:uid>/delete', DataDeleteView.as_view(), name='data-delete'),
    path('<uuid:uid>/toggle/active', DataToggleActiveView.as_view(), name='data-toggle-active'),
]