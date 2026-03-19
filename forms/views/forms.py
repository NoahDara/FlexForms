from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from helpers.mixins import UIDObjectMixin
from ..models import Form
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from ..forms import FormForm
from django.views import View
from django.contrib import messages

class FormListView(LoginRequiredMixin, SafeListView):
    model = Form
    template_name = "forms/index.html"
    context_object_name = 'forms'
    
class FormCreateView(LoginRequiredMixin, CreateView):
    model = Form
    form_class = FormForm
    template_name = "forms/create.html"
    
    def get_success_url(self):
        return reverse("form-field-create", kwargs={"uid": self.object.uid})
    
class FormUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = Form
    form_class = FormForm
    template_name = "forms/update.html"
    context_object_name = "form_"
    success_url = reverse_lazy("form-index")
    
class FormDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = Form
    success_url = reverse_lazy("form-index")
    
class FormToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = Form
    success_url = reverse_lazy("form-index")
    
class FormTogglePublishView(LoginRequiredMixin, UIDObjectMixin, View):
    
    def get(self, request, *args, **kwargs):
        form = get_object_or_404(Form, uid=self.kwargs["uid"])
        form.is_published = not form.is_published
        form.save()
        state = "published" if form.is_published else "unpublished"
        messages.success(request, f'"{form.title}" has been {state}.')
        return redirect("form-index")