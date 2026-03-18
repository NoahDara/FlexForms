from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from ..models import Table
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView
from ..forms import TableColumnForm, TableForm, TableRowForm, TableCellForm
from helpers.mixins import UIDObjectMixin

# Create your views here
    
class TableListView(LoginRequiredMixin, SafeListView):
    model = Table
    template_name = "tables/index.html"
    context_object_name = 'tables'
    
class TableCreateView(LoginRequiredMixin, CreateView):
    model = Table
    form_class = TableForm
    template_name = "tables/create.html"
    
    def get_success_url(self):
        return reverse("table-preview", kwargs={"uid": self.object.uid})
    
class TablePreviewView(LoginRequiredMixin, UIDObjectMixin, DetailView):
    model = Table
    template_name = "tables/preview.html"
    context_object_name = 'table'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['column_form'] = TableColumnForm()
        context['row_form'] = TableRowForm()
        context['cell_form'] = TableCellForm()
        return context
    
class TableUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = Table
    form_class = TableForm
    template_name = "tables/update.html"
    context_object_name = "table"
    success_url = reverse_lazy("table-index")
    
class TableDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = Table
    success_url = reverse_lazy("table-index")
    
class TableToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = Table
    success_url = reverse_lazy("table-index")