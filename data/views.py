from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from .models import DataType, DataSource, Data
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from .forms import DataSourceForm, DataForm

# Create your views here.

class DataTypeListView(LoginRequiredMixin, SafeListView):
    model = DataType
    template_name = "data/data_type_index.html"
    context_object_name = "data_types"
    
class DataSourceListView(LoginRequiredMixin, SafeListView):
    model = DataSource
    template_name = "data/sources/index.html"
    context_object_name = 'data_sources'
    
class DataSourceCreateView(LoginRequiredMixin, CreateView):
    model = DataSource
    form_class = DataSourceForm
    template_name = "data/sources/create.html"
    
    def get_success_url(self):
        return reverse("data-create", kwargs={"uid": self.object.uid})
    
class DataSourceUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = DataSource
    form_class = DataSourceForm
    template_name = "data/sources/update.html"
    context_object_name = "data_source"
    success_url = reverse_lazy("data-source-index")
    
class DataSourceDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = DataSource
    success_url = reverse_lazy("data-source-index")
    
class DataSourceToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = DataSource
    success_url = reverse_lazy("data-source-index")
    
class DataCreateView(LoginRequiredMixin, CreateView):
    model = Data
    form_class = DataForm
    template_name = "data/create.html"
    
    def get_object(self):
        return get_object_or_404(DataSource, uid=self.kwargs["uid"])
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.source = self.get_object()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['source'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse_lazy("data-create", kwargs={"uid": self.kwargs["uid"]})
    
    
class DataUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = Data
    form_class = DataForm
    template_name = "data/update.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data : Data = self.get_object()
        context['source'] = data.source
        return context

    def get_success_url(self):
        data : Data = self.get_object()
        return reverse_lazy("data-create", kwargs={"uid": data.source.uid})
    
class DataDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = Data
    success_url = reverse_lazy("data-source-index")
    
class DataToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = Data

    def get_success_url(self):
        data : Data = self.get_object()
        return reverse_lazy("data-create", kwargs={"uid": data.source.uid})