from django.db import models
from helpers.models import BaseModel


class DataSource(BaseModel):
    """
    A reusable data source that powers choice-based fields such as dropdowns,
    multi-select, radio buttons, and foreign key fields across any form.

    A DataSource can be either:
      - STATIC:  Admin manually types in a list of options (stored as JSON)
      - DYNAMIC: Points to an existing Django model/table in the database,
                 specifying which field to use as the display label and which
                 field to use as the submitted value.

    DataSources are global and independent — they are created once and can be
    linked to any FormField or TableColumn across multiple forms.
    """

    class SourceType(models.TextChoices):
        STATIC = "static", "Static List"
        DYNAMIC = "dynamic", "Dynamic Model"

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Human-readable name for this data source e.g. 'Departments', 'Countries'",
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of what this data source represents",
    )

    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.STATIC,
        help_text="Whether options come from a static list or a live database model",
    )

    # --- Static source fields ---
    static_options = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "Used when source_type is STATIC. "
            "A list of option objects e.g. "
            '[{"label": "Human Resources", "value": "hr"}, ...]'
        ),
    )

    # --- Dynamic source fields ---
    model_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=(
            "Used when source_type is DYNAMIC. "
            "The app_label.ModelName of the target Django model e.g. 'employees.Department'"
        ),
    )

    label_field = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The model field to display as the option label e.g. 'name'",
    )

    value_field = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The model field to use as the submitted value e.g. 'uid' or 'id'",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Data Source"
        verbose_name_plural = "Data Sources"

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
