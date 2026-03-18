from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from helpers.mixins import UIDObjectMixin
from ..models import Form, FormSection
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from ..forms import FormFieldForm, FormSectionForm
from django.views import View
from django.contrib import messages

class FormSectionCreateView(LoginRequiredMixin, CreateView):
    model = FormSection
    form_class = FormSectionForm
    template_name = "forms/fields/create.html"

    def get_object(self):
        return get_object_or_404(Form, uid=self.kwargs["uid"])

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.form = self.get_object()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_obj = self.get_object()
        context['form_instance'] = form_obj
        context['form_sections'] = form_obj.sections.prefetch_related('fields').all()
        context['ungrouped_fields'] = form_obj.fields.filter(section__isnull=True)
        context['section_form'] = kwargs.get('form', self.get_form())
        # Keep field form fresh so the rest of the page still works
        context['form'] = FormFieldForm()
        return context

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("form-field-create", kwargs={"uid": self.kwargs["uid"]})
    
    
class FormSectionUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = FormSection
    form_class = FormSectionForm
    template_name = "forms/sections/update.html"
    context_object_name = "section"


    def get_success_url(self):
        section : FormSection = self.get_object()
        return reverse_lazy("form-field-create", kwargs={"uid": section.form.uid})
    
class FormSectionDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = FormSection
    success_url = reverse_lazy("form-index")
    
class FormSectionToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = FormSection

    def get_success_url(self):
        section : FormSection = self.get_object()
        return reverse_lazy("from-section-create", kwargs={"uid": section.form.uid})