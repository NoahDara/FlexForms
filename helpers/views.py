from django.views.generic import ListView, UpdateView, DeleteView, DetailView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages
from .mixins import UIDObjectMixin, ExportListMixin
from django.db.models import ProtectedError
class SafeListView(ExportListMixin, ListView):
    """
    Base ListView that filters by company for non-superusers.
    Checks for actual database fields, not properties or methods.
    """
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Apply company filtering only for non-superusers
        # if self.request.user and not self.request.user.is_superuser:

        return qs
    
class SafeUpdateView(UIDObjectMixin, UpdateView):
    success_url = reverse_lazy('/')
    success_message = "Updated successfully."

    def form_valid(self, form):
        self.object = self.get_object()
        messages.success(self.request, f"{self.object} {self.success_message}")
        return super().form_valid(form)


class SafeDeleteView(UIDObjectMixin, DeleteView):
    success_url = reverse_lazy('/')
    success_message = "Deleted successfully."
    error_message = "Cannot delete this item because it is protected by related records."

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            model_name = self.object._meta.verbose_name.title()
            messages.warning(request, f"{model_name} {self.success_message}")
        except ProtectedError as e:
            protected_objects = e.protected_objects 
            related_names = {obj._meta.verbose_name.title() for obj in protected_objects}
            error_detail = f"{self.error_message} Related object(s): {', '.join(related_names)}."
            messages.error(request, error_detail)
        return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
    
class ToggleActiveView(UIDObjectMixin, View):
    success_url = reverse_lazy('/')
    success_message = "Status updated successfully."

    def get_success_url(self):
        return self.success_url

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()           
        if hasattr(self.object, 'is_active'):
            self.object.is_active = not self.object.is_active
            self.object.save()
            if self.success_message:
                status = "activated" if self.object.is_active else "deactivated"
                messages.success(request, f"{self.object} {self.success_message} ({status})")
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()      
        if hasattr(self.object, 'is_active'):
            self.object.is_active = not self.object.is_active
            self.object.save()
            if self.success_message:
                status = "activated" if self.object.is_active else "deactivated"
                messages.success(request, f"{self.object} {self.success_message} ({status})")
        return HttpResponseRedirect(self.get_success_url())