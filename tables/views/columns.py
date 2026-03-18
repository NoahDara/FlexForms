from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from ..models import TableColumn, Table
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from ..forms import TableColumnForm , TableRowForm, TableCellForm

# Create your views here.


    
class TableColumnCreateView(LoginRequiredMixin, CreateView):
    model = TableColumn
    form_class = TableColumnForm
    template_name = "tables/preview.html" 
    
    def get_object(self):
        return get_object_or_404(Table, uid=self.kwargs["uid"])
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.table = self.get_object()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = self.get_object()
        context['table'] = table
        context['column_form'] = kwargs.get('form', self.get_form())
        context['row_form'] = TableRowForm()
        context['cell_form'] = TableCellForm()
        return context

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("table-preview", kwargs={"uid": self.kwargs["uid"]})
    
    
class TableColumnUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = TableColumn
    form_class = TableColumnForm
    template_name = "tables/columns/update.html"
    context_object_name = "column"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        column : TableColumn = self.get_object()
        context['table'] = column.table
        return context

    def get_success_url(self):
        column : TableColumn = self.get_object()
        return reverse_lazy("table-preview", kwargs={"uid": column.table.uid})
    
class TableColumnDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = TableColumn
    success_url = reverse_lazy("table-index")
    
class TableColumnToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = TableColumn

    def get_success_url(self):
        column : TableColumn = self.get_object()
        return reverse_lazy("table-preview", kwargs={"uid": column.table.uid})