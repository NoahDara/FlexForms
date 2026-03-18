from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from ..models import Form, FormField
from helpers.views import SafeListView, SafeDeleteView, SafeUpdateView, ToggleActiveView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from ..forms import FormFieldForm, FormSectionForm
from django.core.exceptions import ValidationError
# Create your views here.


class FormFieldCreateView(LoginRequiredMixin, CreateView):
    model = FormField
    form_class = FormFieldForm
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
        context['section_form'] = FormSectionForm()
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error('label', e)  # surfaces on the label field specifically
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("form-field-create", kwargs={"uid": self.kwargs["uid"]})
    
    
class FormFieldUpdateView(LoginRequiredMixin, SafeUpdateView):
    model = FormField
    form_class = FormFieldForm
    template_name = "forms/fields/update.html"
    context_object_name = "field"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        field: FormField = self.get_object()
        form_obj = field.form
        context['form_instance'] = form_obj
        context['ungrouped_fields'] = form_obj.fields.filter(section__isnull=True)
        return context

    def get_success_url(self):
        field: FormField = self.get_object()
        return reverse_lazy("form-field-create", kwargs={"uid": field.form.uid})
    
class FormFieldDeleteView(LoginRequiredMixin, SafeDeleteView):
    model = FormField
    success_url = reverse_lazy("form-index")
    
class FormFieldToggleActiveView(LoginRequiredMixin, ToggleActiveView):
    model = FormField

    def get_success_url(self):
        field : FormField = self.get_object()
        return reverse_lazy("from-field-create", kwargs={"uid": field.form.uid})