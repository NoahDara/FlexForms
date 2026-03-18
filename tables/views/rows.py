from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from ..models import TableRow, Table
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from ..forms import TableColumnForm, TableRowForm , TableCellForm

# Create your views here.


    
class TableRowCreateView(LoginRequiredMixin, CreateView):
    model = TableRow
    form_class = TableRowForm
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
        context['cell_form'] = TableCellForm()
        context['row_form'] = self.get_form()      
        return context

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("table-preview", kwargs={"uid": self.kwargs["uid"]})
    
    
class TableRowUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = TableRow
    form_class = TableRowForm
    template_name = "tables/rows/update.html"
    context_object_name = "row"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        row : TableRow = self.get_object()
        context['table'] = row.table
        return context

    def get_success_url(self):
        row : TableRow = self.get_object()
        return reverse_lazy("table-preview", kwargs={"uid": row.table.uid})
    
class TableRowDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = TableRow
    success_url = reverse_lazy("table-index")
    
class TableRowToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = TableRow

    def get_success_url(self):
        row : TableRow = self.get_object()
        return reverse_lazy("table-preview", kwargs={"uid": row.table.uid})