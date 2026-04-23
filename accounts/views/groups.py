from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.urls import reverse_lazy
from django.db.models import Prefetch
from django.contrib import messages
from django.shortcuts import redirect

from accounts.forms import GroupForm
from accounts.mixins import ACTIONS, MANAGED_PERMISSIONS, GroupPermissionFormMixin  #



class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    template_name = 'accounts/groups/list.html'
    context_object_name = 'groups'
    permission_required = 'auth.view_group'

    def get_queryset(self):
        return (
            Group.objects
            .prefetch_related(
                'permissions',
                Prefetch(
                    'user_set',
                    # Limit to 4 users for the avatar display — avoids
                    # fetching the entire user list for large groups
                    to_attr='preview_members',
                )
            )
            .order_by('name')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build a human-readable permission summary per group
        # e.g. "Form: View, Change · Submissions: View"
        summaries = {}
        for group in context['groups']:
            group_perm_codenames = {
                p.codename for p in group.permissions.all()
            }
            parts = []
            for label, config in MANAGED_PERMISSIONS.items():
                granted = []
                for action in ACTIONS:
                    codename = f"{action}_{config['model']}"
                    if codename in group_perm_codenames:
                        granted.append(action.capitalize())
                if granted:
                    parts.append(f"{label}: {', '.join(granted)}")
            summaries[group.pk] = ' · '.join(parts) if parts else 'No permissions assigned'

        context['permission_summaries'] = summaries
        return context


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                      GroupPermissionFormMixin, CreateView):
    model = Group
    form_class = GroupForm  
    template_name = 'accounts/groups/form.html'
    success_url = reverse_lazy('group-index')
    permission_required = 'auth.add_group'

    def get_context_data(self, **kwargs):
        # object is None on create — mixin handles this gracefully
        self.object = None
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        group = form.save()
        self.object = group
        self.save_permissions(group)
        messages.success(self.request, f'Group "{group.name}" created successfully.')
        return redirect(self.success_url)


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                      GroupPermissionFormMixin, UpdateView):
    model = Group
    form_class = GroupForm  
    template_name = 'accounts/groups/form.html'
    success_url = reverse_lazy('group-index')
    permission_required = 'auth.change_group'
    context_object_name = 'group'

    def form_valid(self, form):
        group = form.save()
        self.save_permissions(group)
        messages.success(self.request, f'Group "{group.name}" updated successfully.')
        return redirect(self.success_url)


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    template_name = 'accounts/groups/confirm_delete.html'
    success_url = reverse_lazy('group-index')
    permission_required = 'auth.delete_group'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Warn the admin how many users will be affected
        context['affected_users'] = self.object.user_set.count()
        return context

    def form_valid(self, form):
        group = self.get_object()
        messages.warning(
            self.request,
            f'Group "{group.name}" has been deleted.'
        )
        return super().form_valid(form)