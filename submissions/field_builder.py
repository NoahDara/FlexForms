"""
submissions/field_builder.py

Responsible for ONE thing: given a FormField instance from the database,
return a configured Django form field with the correct widget, CSS classes,
and queryset (for relational types).

Nothing in here touches views, templates, or JSON serialisation.
That lives elsewhere. This module is the single source of truth for
DataType.code → Django field mapping.

Usage:
    from submissions.field_builder import build_django_field, get_field_name

    for form_field in form.fields.all():
        name  = get_field_name(form_field)
        field = build_django_field(form_field)
        dynamic_form.fields[name] = field
"""

from django import forms
from django.forms import (
    DateInput,
    DateTimeInput,
    TimeInput,
    TextInput,
    NumberInput,
    Textarea,
    CheckboxInput,
    URLInput,
    EmailInput,
    FileInput,
)
from data.models import Data


# ─────────────────────────────────────────────────────────────────────────────
# Field name helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_field_name(form_field) -> str:
    """
    Generate a stable, unique HTML input name for a FormField instance.

    Sectioned fields:  section__{section_uid}__{field_uid}
    Ungrouped fields:  ungrouped__{field_uid}

    UIDs are used (not label slugs) because labels can contain spaces,
    punctuation, and non-ASCII characters that are unsafe in input names.
    """
    if form_field.section_id:
        return f"section__{form_field.section_id}__{form_field.uid}"
    return f"ungrouped__{form_field.uid}"


def get_table_cell_name(table_uid, row_identifier, column_uid) -> str:
    """
    Generate a stable input name for a table cell.

    Dynamic rows:  table__{table_uid}__row__{row_index}__{column_uid}
    Fixed grid:    table__{table_uid}__row__{row_uid}__{column_uid}

    row_identifier is either an integer index (dynamic) or a UUID (fixed).
    """
    return f"table__{table_uid}__row__{row_identifier}__{column_uid}"


# ─────────────────────────────────────────────────────────────────────────────
# Widget factory helpers  (mirrors your existing CustomBaseForm patterns)
# ─────────────────────────────────────────────────────────────────────────────

def _text_input(field_id: str) -> TextInput:
    return TextInput(attrs={"class": "form-control", "id": field_id})


def _textarea(field_id: str) -> Textarea:
    return Textarea(attrs={"class": "form-control no-resize", "id": field_id, "rows": 4})


def _email_input(field_id: str) -> EmailInput:
    return EmailInput(attrs={"class": "form-control", "id": field_id})


def _number_input(field_id: str, **extra_attrs) -> NumberInput:
    attrs = {"class": "form-control", "id": field_id}
    attrs.update(extra_attrs)
    return NumberInput(attrs=attrs)


def _date_input(field_id: str) -> DateInput:
    return DateInput(attrs={"type": "date", "class": "form-control", "id": field_id})


def _datetime_input(field_id: str) -> DateTimeInput:
    return DateTimeInput(
        attrs={"type": "datetime-local", "class": "form-control", "id": field_id}
    )


def _time_input(field_id: str) -> TimeInput:
    return TimeInput(attrs={"type": "time", "class": "form-control", "id": field_id})


def _url_input(field_id: str) -> URLInput:
    return URLInput(attrs={"class": "form-control", "id": field_id})


def _phone_input(field_id: str) -> TextInput:
    return TextInput(attrs={"type": "tel", "class": "form-control", "id": field_id})


def _checkbox_input(field_id: str) -> CheckboxInput:
    return CheckboxInput(attrs={"class": "custom-control-input", "id": field_id})


def _file_input(field_id: str) -> FileInput:
    # Using FileInput instead of ClearableFileInput for cleaner submission UX.
    # The edit view handles the "keep existing file" logic separately via JSON.
    return FileInput(attrs={"class": "form-control", "id": field_id})


def _select_input(field_id: str) -> forms.Select:
    return forms.Select(
        attrs={
            "class": "form-select js-select2",
            "data-search": "on",
            "data-allow-clear": "true",
            "id": field_id,
        }
    )


def _multi_select_input(field_id: str) -> forms.SelectMultiple:
    return forms.SelectMultiple(
        attrs={
            "class": "form-select js-select2",
            "multiple": "multiple",
            "data-placeholder": "Select multiple options",
            "id": field_id,
        }
    )


def _hidden_input(field_id: str) -> forms.HiddenInput:
    """
    Used for signature fields — the canvas writes stroke JSON here.
    """
    return forms.HiddenInput(attrs={"id": field_id, "class": "signature-data-input"})


# ─────────────────────────────────────────────────────────────────────────────
# Queryset builder for relational types
# ─────────────────────────────────────────────────────────────────────────────

def _get_data_queryset(form_field):
    """
    Return the Data queryset for choice-based field types.
    Scoped to the linked DataSource on the FormField.

    Raises ValueError if a relational field has no data_source — this is a
    configuration error that should have been caught at the FormField level.
    """
    if not form_field.data_source:
        raise ValueError(
            f"FormField '{form_field.label}' has type '{form_field.data_type.code}' "
            f"but no data_source is linked. Assign a DataSource in the admin."
        )
    return Data.objects.filter(source=form_field.data_source)


# ─────────────────────────────────────────────────────────────────────────────
# Table-type sentinel
# ─────────────────────────────────────────────────────────────────────────────

TABLE_TYPES = {"table_dynamic", "table_fixed"}
RELATIONAL_TYPES = {"foreign_key", "many_to_many"}
SKIP_AS_FORM_FIELD = TABLE_TYPES  # Tables are rendered separately in the template


def is_table_field(form_field) -> bool:
    return form_field.data_type.code in TABLE_TYPES


# ─────────────────────────────────────────────────────────────────────────────
# Core builder
# ─────────────────────────────────────────────────────────────────────────────

def build_django_field(form_field) -> forms.Field | None:
    """
    Given a FormField instance, return a configured Django form field.

    Returns None for table_dynamic and table_fixed — those are handled
    by the template directly, not by the Django form field machinery.

    Parameters
    ----------
    form_field : FormField
        A FormField instance with .data_type, .label, .is_required,
        .help_text, .data_source, and .uid populated.

    Returns
    -------
    forms.Field | None
    """
    code = form_field.data_type.code

    # Tables are not Django fields — signal the caller to skip
    if code in SKIP_AS_FORM_FIELD:
        return None

    field_name = get_field_name(form_field)
    field_id   = f"{field_name}-id"

    # Shared kwargs for every field type
    base_kwargs = dict(
        label     = form_field.label,
        required  = form_field.is_required,
        help_text = form_field.help_text or "",
    )

    # ── Text types ────────────────────────────────────────────────────────────

    if code == "char":
        return forms.CharField(
            widget=_text_input(field_id),
            max_length=255,
            **base_kwargs,
        )

    if code == "text":
        return forms.CharField(
            widget=_textarea(field_id),
            **base_kwargs,
        )

    if code == "email":
        return forms.EmailField(
            widget=_email_input(field_id),
            **base_kwargs,
        )

    if code == "url":
        return forms.URLField(
            widget=_url_input(field_id),
            **base_kwargs,
        )

    if code == "phone":
        return forms.CharField(
            widget=_phone_input(field_id),
            max_length=30,
            **base_kwargs,
        )

    # ── Numeric types ─────────────────────────────────────────────────────────

    if code == "number":
        return forms.IntegerField(
            widget=_number_input(field_id),
            **base_kwargs,
        )

    if code == "float":
        return forms.FloatField(
            widget=_number_input(field_id, step="any"),
            **base_kwargs,
        )

    if code == "percentage":
        return forms.FloatField(
            widget=_number_input(field_id, min=0, max=100, step="0.01"),
            min_value=0,
            max_value=100,
            **base_kwargs,
        )

    # ── Date / time types ─────────────────────────────────────────────────────

    if code == "date":
        return forms.DateField(
            widget=_date_input(field_id),
            **base_kwargs,
        )

    if code == "datetime":
        return forms.DateTimeField(
            widget=_datetime_input(field_id),
            **base_kwargs,
        )

    if code == "time":
        return forms.TimeField(
            widget=_time_input(field_id),
            **base_kwargs,
        )

    # ── Boolean ───────────────────────────────────────────────────────────────

    if code == "boolean":
        # BooleanField is never truly required (unchecked = False, not missing)
        return forms.BooleanField(
            widget=_checkbox_input(field_id),
            required=False,         # override: unchecked is a valid answer
            label=form_field.label,
            help_text=form_field.help_text or "",
        )

    # ── File types ────────────────────────────────────────────────────────────

    if code == "file":
        return forms.FileField(
            widget=_file_input(field_id),
            **base_kwargs,
        )

    if code == "image":
        return forms.ImageField(
            widget=_file_input(field_id),
            **base_kwargs,
        )

    # ── Relational types ──────────────────────────────────────────────────────

    if code == "foreign_key":
        qs = _get_data_queryset(form_field)
        return forms.ModelChoiceField(
            queryset=qs,
            widget=_select_input(field_id),
            empty_label="— Select —",
            **base_kwargs,
        )

    if code == "many_to_many":
        qs = _get_data_queryset(form_field)
        return forms.ModelMultipleChoiceField(
            queryset=qs,
            widget=_multi_select_input(field_id),
            **base_kwargs,
        )

    # ── Signature ─────────────────────────────────────────────────────────────

    if code == "signature":
        # The actual drawing happens on the canvas in the template.
        # JS serialises stroke data → writes to this hidden input.
        # On save the hidden input value (JSON string) is what we store.
        return forms.CharField(
            widget=_hidden_input(field_id),
            required=form_field.is_required,
            label=form_field.label,
            help_text=form_field.help_text or "",
        )

    # ── Unknown / unhandled ───────────────────────────────────────────────────

    raise NotImplementedError(
        f"No field builder defined for DataType code '{code}'. "
        f"Add a handler in submissions/field_builder.py."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Table cell field builder  (same logic, used inside table renderers)
# ─────────────────────────────────────────────────────────────────────────────

def build_cell_field(data_type_code: str, data_source=None, required: bool = False) -> forms.Field:
    """
    Build a Django form field for a single table cell.

    Used by both dynamic-row columns and fixed-grid cell overrides.
    The field has no label (labels are the column headers in <th> elements).

    Parameters
    ----------
    data_type_code : str
        DataType.code value — same codes as build_django_field.
    data_source : DataSource | None
        Required for foreign_key and many_to_many codes.
    required : bool
        Whether the cell must be filled in.
    """
    # Cells don't have UIDs of their own — the containing <td> identifies them.
    # We pass an empty string for field_id; the template sets the actual id
    # attribute on the rendered <input> using the input name.
    field_id = ""

    base = dict(label="", required=required, help_text="")

    if data_type_code == "char":
        return forms.CharField(widget=_text_input(field_id), max_length=255, **base)

    if data_type_code == "text":
        return forms.CharField(widget=_textarea(field_id), **base)

    if data_type_code == "email":
        return forms.EmailField(widget=_email_input(field_id), **base)

    if data_type_code == "url":
        return forms.URLField(widget=_url_input(field_id), **base)

    if data_type_code == "phone":
        return forms.CharField(widget=_phone_input(field_id), max_length=30, **base)

    if data_type_code == "number":
        return forms.IntegerField(widget=_number_input(field_id), **base)

    if data_type_code == "float":
        return forms.FloatField(widget=_number_input(field_id, step="any"), **base)

    if data_type_code == "percentage":
        return forms.FloatField(
            widget=_number_input(field_id, min=0, max=100, step="0.01"),
            min_value=0,
            max_value=100,
            **base,
        )

    if data_type_code == "date":
        return forms.DateField(widget=_date_input(field_id), **base)

    if data_type_code == "datetime":
        return forms.DateTimeField(widget=_datetime_input(field_id), **base)

    if data_type_code == "time":
        return forms.TimeField(widget=_time_input(field_id), **base)

    if data_type_code == "boolean":
        return forms.BooleanField(widget=_checkbox_input(field_id), required=False, label="", help_text="")

    if data_type_code == "file":
        return forms.FileField(widget=_file_input(field_id), **base)

    if data_type_code == "image":
        return forms.ImageField(widget=_file_input(field_id), **base)

    if data_type_code == "foreign_key":
        if not data_source:
            raise ValueError("data_source is required for foreign_key cell type.")
        qs = Data.objects.filter(source=data_source)
        return forms.ModelChoiceField(
            queryset=qs, widget=_select_input(field_id), empty_label="— Select —", **base
        )

    if data_type_code == "many_to_many":
        if not data_source:
            raise ValueError("data_source is required for many_to_many cell type.")
        qs = Data.objects.filter(source=data_source)
        return forms.ModelMultipleChoiceField(
            queryset=qs, widget=_multi_select_input(field_id), **base
        )

    raise NotImplementedError(
        f"No cell field builder defined for DataType code '{data_type_code}'."
    )