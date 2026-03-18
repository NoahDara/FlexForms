from django.urls import path
from .views import (
    TableListView,
    TableCreateView,
    TableUpdateView,
    TablePreviewView,
    TableDeleteView,
    TableToggleActiveView,
    
    TableColumnCreateView,
    TableColumnUpdateView,
    TableColumnDeleteView,
    TableColumnToggleActiveView,
    
    TableRowCreateView,
    TableRowUpdateView,
    TableRowDeleteView,
    TableRowToggleActiveView,
    
    TableCellCreateView,
    TableCellUpdateView,
    TableCellDeleteView,
    TableCellToggleActiveView
)

urlpatterns = [
    path("", TableListView.as_view(), name="table-index"),
    path("create", TableCreateView.as_view(), name="table-create"),
    path("<uuid:uid>", TablePreviewView.as_view(), name="table-preview"),
    path("<uuid:uid>/update", TableUpdateView.as_view(), name="table-update"),
    path("<uuid:uid>/toggle/active", TableToggleActiveView.as_view(), name="table-toggle-active"),
    path("<uuid:uid>/delete", TableDeleteView.as_view(), name="table-delete"),
    
    path('<uuid:uid>/column/create', TableColumnCreateView.as_view(), name="table-column-name"),
    path('column/<uuid:uid>/update', TableColumnUpdateView.as_view(), name="table-column-update"),
    path("column/<uuid:uid>/toggle/active", TableColumnToggleActiveView.as_view(), name="table-column-toggle-active"),
    path("column/<uuid:uid>/delete", TableColumnDeleteView.as_view(), name="table-column-delete"),
    
    path('<uuid:uid>/row/create', TableRowCreateView.as_view(), name="table-row-create"),
    path('row/<uuid:uid>/update', TableRowUpdateView.as_view(), name="table-row-update"),
    path('row/<uuid:uid>/toggle/active', TableRowToggleActiveView.as_view(), name="table-row-toggle-active"),
    path('row/<uuid:uid>/delete', TableRowDeleteView.as_view(), name="table-row-delete"),
    
    path('<uuid:uid>/cell/create', TableCellCreateView.as_view(), name="table-cell-create"),
    path('cell/<uuid:uid>/update', TableCellUpdateView.as_view(), name="table-cell-update"),
    path('cell/<uuid:uid>/toggle/active', TableCellToggleActiveView.as_view(), name="table-cell-toggle-active"),
    path('cell/<uuid:uid>/delete', TableCellDeleteView.as_view(), name="table-cell-delete"),
]
