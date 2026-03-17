class AutoExtraFieldsAdminMixin:
    """
    A mixin you can use with ModelAdmin to automatically include
    common fields like uid, created, updated in list_display and readonly_fields
    if they exist on the model.
    """

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))

        # Add them as readonly if present
        for field in ["uid", "created", "updated"]:
            if hasattr(self.model, field) and field not in readonly_fields:
                readonly_fields.append(field)
        return readonly_fields