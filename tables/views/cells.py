from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from ..models import TableCell, Table
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from ..forms import TableCellForm , TableColumnForm, TableRowForm

# Create your views here.


    
class TableCellCreateView(LoginRequiredMixin, CreateView):
    model = TableCell
    form_class = TableCellForm
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
        context['column_form'] = TableColumnForm() 
        context['row_form'] = TableRowForm()
        context['cell_form'] = self.get_form()      
        return context

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("table-preview", kwargs={"uid": self.kwargs["uid"]})
    
    
class TableCellUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = TableCell
    form_class = TableCellForm
    template_name = "tables/cells/update.html"
    context_object_name = "cell"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cell : TableCell = self.get_object()
        context['table'] = cell.table
        return context

    def get_success_url(self):
        cell : TableCell = self.get_object()
        return reverse_lazy("table-preview", kwargs={"uid": cell.table.uid})
    
class TableCellDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = TableCell
    success_url = reverse_lazy("table-index")
    
class TableCellToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = TableCell

    def get_success_url(self):
        cell : TableCell = self.get_object()
        return reverse_lazy("table-preview", kwargs={"uid": cell.table.uid})