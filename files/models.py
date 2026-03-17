from django.db import models
from helpers.models import BaseModel
from datasources.models import DataSource
from tables.models import TableConfig


class Form(BaseModel):
    """
    The top-level form definition created and managed by system admins.

    A Form holds all metadata about the form — its title, description, access
    control settings, and published state. The actual fields are defined via
    related FormField objects.

    A Form can optionally require users to be logged in before accessing it.
    When is_published is False the form is in draft mode and not visible to
    regular users.
    """

    title = models.CharField(
        max_length=255,
        help_text="The display title of the form shown to users",
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description or instructions shown at the top of the form",
    )

    requires_login = models.BooleanField(
        default=False,
        help_text=(
            "If True, only authenticated (logged in) users can access and submit this form"
        ),
    )

    is_published = models.BooleanField(
        default=False,
        help_text="If True, the form is live and accessible to users",
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp of when the form was first published",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Form"
        verbose_name_plural = "Forms"

    def __str__(self):
        return self.title


class FormSection(BaseModel):
    """
    An optional grouping layer within a Form that organizes related fields
    under a named section heading.

    Sections are scoped to a specific form — the same section name can exist
    independently on multiple forms. Fields that do not belong to any section
    are considered ungrouped and rendered separately.

    Sections are ordered via the 'order' field. Fields within each section
    are ordered by their own 'order' field on FormField.

    Examples of section names:
      - "Personal Details"
      - "Employment History"
      - "Next of Kin"
    """

    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name="sections",
        help_text="The form this section belongs to",
    )

    name = models.CharField(
        max_length=255,
        help_text="The section heading displayed to the user e.g. 'Personal Details'",
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional sub-heading or instructions shown under the section title",
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of this section within the form (top to bottom)",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Form Section"
        verbose_name_plural = "Form Sections"
        ordering = ["order"]

    def __str__(self):
        return f"{self.form.title} — {self.name}"


class FormField(BaseModel):
    """
    A single field definition within a Form.

    FormField stores everything needed to render and validate a field:
    the type, label, ordering, whether it is required, placeholder text,
    and links to external data (DataSource for choices, TableConfig for tables).

    Fields are always linked to a Form. They are optionally linked to a
    FormSection for grouping. Fields without a section are rendered as
    ungrouped at the end of the form or at the top before any sections.

    Field ordering is scoped per section (or per form for ungrouped fields)
    using the 'order' integer field.

    Supported field types include all standard Django form fields plus
    signature capture and two table types.
    """

    class FieldType(models.TextChoices):
        # Standard input types
        CHAR = "char", "Short Text"
        TEXT = "text", "Long Text"
        EMAIL = "email", "Email"
        NUMBER = "number", "Number"
        DECIMAL = "decimal", "Decimal"
        DATE = "date", "Date"
        DATETIME = "datetime", "Date & Time"
        TIME = "time", "Time"
        URL = "url", "URL"
        PHONE = "phone", "Phone Number"
        BOOLEAN = "boolean", "Checkbox (Yes/No)"

        # File types
        FILE = "file", "File Upload"
        IMAGE = "image", "Image Upload"

        # Choice types (require DataSource)
        DROPDOWN = "dropdown", "Dropdown"
        RADIO = "radio", "Radio Buttons"
        CHECKBOX_MULTI = "checkbox_multi", "Multiple Checkboxes"
        MULTI_SELECT = "multi_select", "Multi Select"

        # Relational types (require DataSource pointing to a model)
        FOREIGN_KEY = "foreign_key", "Foreign Key (Single)"
        MANY_TO_MANY = "many_to_many", "Many to Many (Multiple)"

        # Special types
        SIGNATURE = "signature", "Signature"

        # Table types (require TableConfig)
        TABLE_DYNAMIC = "table_dynamic", "Table — Dynamic Rows"
        TABLE_FIXED = "table_fixed", "Table — Fixed Grid"

    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name="fields",
        help_text="The form this field belongs to",
    )

    section = models.ForeignKey(
        FormSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fields",
        help_text="The section this field belongs to. Leave blank for ungrouped fields",
    )

    label = models.CharField(
        max_length=255,
        help_text="The field label displayed to the user e.g. 'Full Name'",
    )

    field_name = models.SlugField(
        max_length=255,
        help_text=(
            "Auto-generated slug used as the key in submission JSON "
            "e.g. 'full_name'. Must be unique within a form."
        ),
    )

    field_type = models.CharField(
        max_length=30,
        choices=FieldType.choices,
        help_text="The type of input to render for this field",
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Display order of this field. Ordered within its section, "
            "or within the form if no section is assigned."
        ),
    )

    is_required = models.BooleanField(
        default=False,
        help_text="If True, the user must fill in this field before submitting",
    )

    placeholder = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional placeholder text shown inside the input before the user types",
    )

    help_text = models.TextField(
        blank=True,
        null=True,
        help_text="Optional helper text shown below the field to guide the user",
    )

    # --- Choice / Relational fields ---
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_fields",
        help_text=(
            "Required for choice-based and relational field types: "
            "dropdown, radio, checkbox_multi, multi_select, foreign_key, many_to_many"
        ),
    )

    # --- Table fields ---
    table = models.ForeignKey(
        TableConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_fields",
        help_text="Required when field_type is table_dynamic or table_fixed",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Form Field"
        verbose_name_plural = "Form Fields"
        ordering = ["order"]
        unique_together = [("form", "field_name")]

    def __str__(self):
        return f"{self.form.title} — {self.label} ({self.get_field_type_display()})"
