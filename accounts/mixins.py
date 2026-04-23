from django.contrib.auth.models import Group, Permission


# ──────────────────────────────────────────────────────────────────────────────
# Permission matrix configuration
# Defines which models appear in the permission matrix and in what order.
# To add a new model, add an entry here — nothing else needs to change.
# ──────────────────────────────────────────────────────────────────────────────

MANAGED_PERMISSIONS = {
    'Form': {
        'app': 'forms',
        'model': 'form',
    },
    'Form Field': {
        'app': 'forms',
        'model': 'formfield',
    },
    'Form Submission': {
        'app': 'submissions',
        'model': 'formsubmission',
    },
    'Table': {
        'app': 'tables',
        'model': 'table',
    },
    'Data Source': {
        'app': 'data',
        'model': 'datasource',
    },
    'Users': {
        'app': 'auth',
        'model': 'user',
    },
    'Groups': {
        'app': 'auth',
        'model': 'group',
    },
}

ACTIONS = ['view', 'add', 'change', 'delete']


def build_permission_matrix(existing_permissions=None):
    """
    Builds the matrix data structure used by the template.

    Returns a list of row dicts:
    [
        {
            'label': 'Form',
            'cells': [
                {
                    'permission_id': 42,
                    'codename': 'view_form',
                    'action': 'view',
                    'checked': True,
                },
                ...
            ]
        },
        ...
    ]

    existing_permissions: a set/list of Permission PKs already assigned to the
    group. Pass None or empty for the create form.
    """
    existing_ids = set(existing_permissions or [])
    matrix = []

    for label, config in MANAGED_PERMISSIONS.items():
        cells = []
        for action in ACTIONS:
            codename = f"{action}_{config['model']}"
            try:
                perm = Permission.objects.get(
                    codename=codename,
                    content_type__app_label=config['app'],
                )
                cells.append({
                    'permission_id': perm.pk,
                    'codename': codename,
                    'action': action,
                    'checked': perm.pk in existing_ids,
                })
            except Permission.DoesNotExist:
                # Permission not in DB yet (e.g. migrations not run)
                cells.append({
                    'permission_id': None,
                    'codename': codename,
                    'action': action,
                    'checked': False,
                })
        matrix.append({
            'label': label,
            'cells': cells,
        })

    return matrix


# ──────────────────────────────────────────────────────────────────────────────
# Mixin: builds and saves the permission matrix
# ──────────────────────────────────────────────────────────────────────────────

class GroupPermissionFormMixin:
    """
    Shared mixin for GroupCreateView and GroupUpdateView.

    Adds the permission matrix to context and handles saving the M2M
    permissions from the submitted checkbox values.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        existing = []
        if self.object:
            existing = list(
                self.object.permissions.values_list('pk', flat=True)
            )
        context['permission_matrix'] = build_permission_matrix(existing)
        context['actions'] = ACTIONS
        return context

    def save_permissions(self, group):
        """
        Reads 'permissions' from POST data (a list of permission PKs as strings)
        and sets them on the group, replacing any previous assignment.
        Only touches the permissions defined in MANAGED_PERMISSIONS —
        any other permissions already on the group are left untouched.
        """
        # Collect all managed permission PKs so we only replace those
        managed_pks = set()
        for config in MANAGED_PERMISSIONS.values():
            for action in ACTIONS:
                codename = f"{action}_{config['model']}"
                try:
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type__app_label=config['app'],
                    )
                    managed_pks.add(perm.pk)
                except Permission.DoesNotExist:
                    pass

        # PKs submitted via checkboxes
        submitted_pks = set(
            int(pk) for pk in self.request.POST.getlist('permissions')
            if pk.isdigit()
        )

        # Only keep submitted PKs that are within the managed set
        new_managed_pks = submitted_pks & managed_pks

        # Permissions on the group outside managed scope — preserve them
        existing_unmanaged = set(
            group.permissions
            .exclude(pk__in=managed_pks)
            .values_list('pk', flat=True)
        )

        # Final set = unmanaged (preserved) + new managed selections
        group.permissions.set(existing_unmanaged | new_managed_pks)