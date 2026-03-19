"""
submissions/views.py

Two views:

    SubmissionCreateView  — dynamically builds a form from a Form definition,
                            handles draft + submit, saves JSON via serialiser.

    SubmissionEditView    — loads an existing FormSubmission, deserialises the
                            JSON back into initial values, re-renders the same
                            dynamic form pre-populated.

Both views share a mixin (SubmissionFormMixin) that owns all the shared logic:
    - fetching and validating the Form definition
    - building the dynamic Django form from field_builder
    - building the template context (sections, fields, table structures)
    - dispatching to serialiser on POST
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from forms.models import Form, FormField
from submissions.models import FormSubmission
from submissions.field_builder import (
    build_django_field,
    build_cell_field,
    get_field_name,
    is_table_field,
)
from submissions.serialiser import serialise_submission
from submissions.deserialiser import (
    deserialise_submission,
    get_field_initial,
    get_table_initial,
    get_file_url,
)


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic form class builder
# ─────────────────────────────────────────────────────────────────────────────

def build_dynamic_form(form_definition, post_data=None, files=None, initial=None):
    """
    Construct a Django Form class dynamically from a Form DB definition.

    Iterates all FormFields on the form. Table fields are skipped —
    they are rendered directly in the template, not as Django form fields.

    Parameters
    ----------
    form_definition : forms.Form
        The Form model instance.
    post_data : QueryDict | None
        request.POST for bound forms, None for unbound.
    files : MultiValueDict | None
        request.FILES for bound forms, None for unbound.
    initial : dict | None
        Pre-population values from the deserialiser (edit view).

    Returns
    -------
    django.forms.Form instance
    """
    from django import forms as django_forms

    fields = {}

    all_fields = (
        form_definition.fields
        .select_related("data_type", "data_source", "section", "table")
        .order_by("section__order", "order")
    )

    for form_field in all_fields:
        if is_table_field(form_field):
            continue  # Rendered separately in the template

        try:
            django_field = build_django_field(form_field)
        except (ValueError, NotImplementedError):
            # Skip misconfigured fields rather than crashing the whole form
            continue

        if django_field is None:
            continue

        name = get_field_name(form_field)
        fields[name] = django_field

    # Build a fresh Form class with these fields
    DynamicFormClass = type("DynamicSubmissionForm", (django_forms.Form,), fields)

    if post_data is not None:
        return DynamicFormClass(data=post_data, files=files or {}, initial=initial or {})

    return DynamicFormClass(initial=initial or {})


# ─────────────────────────────────────────────────────────────────────────────
# Shared mixin
# ─────────────────────────────────────────────────────────────────────────────

class SubmissionFormMixin:
    """
    Shared logic for create and edit views.

    Subclasses must implement:
        get_submission()  → FormSubmission | None
        get_success_url() → str
    """

    template_name = "submissions/form.html"

    # ── Form definition lookup ────────────────────────────────────────────────

    def get_form_definition(self):
        """
        Return the Form model instance from the URL kwarg 'form_uid'.
        Only published forms are accessible to non-staff users.
        """
        qs = Form.objects.prefetch_related(
            "sections__fields__data_type",
            "sections__fields__data_source",
            "sections__fields__table__columns__data_type",
            "sections__fields__table__columns__data_source",
            "sections__fields__table__rows",
            "sections__fields__table__cell_configs__data_type",
            "sections__fields__table__cell_configs__data_source",
            "sections__fields__table__cell_configs__row",
            "sections__fields__table__cell_configs__column",
            "fields__data_type",
            "fields__data_source",
            "fields__table__columns__data_type",
            "fields__table__columns__data_source",
            "fields__table__rows",
            "fields__table__cell_configs__data_type",
            "fields__table__cell_configs__data_source",
        )

        form_definition = get_object_or_404(qs, uid=self.kwargs["form_uid"])

        # Non-staff users cannot access unpublished forms
        if not form_definition.is_published:
            if not (self.request.user.is_authenticated and self.request.user.is_staff):
                from django.http import Http404
                raise Http404("This form is not published.")

        # Forms requiring login — enforce it
        if form_definition.requires_login and not self.request.user.is_authenticated:
            from django.conf import settings
            login_url = getattr(settings, "LOGIN_URL", "/accounts/login/")
            return redirect(f"{login_url}?next={self.request.path}")

        return form_definition

    # ── Template context builder ───────────────────────────────────────────────

    def build_context(self, form_definition, django_form, initial=None):
        """
        Build the full template context for the submission form.

        Returns a dict with:
            form_definition  — the Form DB object (title, description)
            django_form      — the bound/unbound Django form
            sections         — ordered list of section context dicts
            ungrouped_fields — ordered list of ungrouped field context dicts
            initial          — the deserialised initial dict (for JS/template use)
        """
        initial = initial or {}

        sections_ctx      = self._build_sections_context(form_definition, django_form, initial)
        ungrouped_ctx     = self._build_ungrouped_context(form_definition, django_form, initial)

        return {
            "form_definition":  form_definition,
            "django_form":      django_form,
            "sections":         sections_ctx,
            "ungrouped_fields": ungrouped_ctx,
            "initial":          initial,
        }

    def _build_sections_context(self, form_definition, django_form, initial):
        sections_ctx = []

        for section in form_definition.sections.order_by("order"):
            fields_ctx = []

            for form_field in section.fields.order_by("order"):
                field_ctx = self._build_field_context(form_field, django_form, initial)
                fields_ctx.append(field_ctx)

            sections_ctx.append({
                "section":  section,
                "fields":   fields_ctx,
            })

        return sections_ctx

    def _build_ungrouped_context(self, form_definition, django_form, initial):
        ungrouped_ctx = []

        ungrouped = (
            form_definition.fields
            .filter(section__isnull=True)
            .select_related(
                "data_type",
                "data_source",
                "table",
            )
            .prefetch_related(
                "table__columns__data_type",
                "table__columns__data_source",
                "table__rows",
                "table__cell_configs__data_type",
                "table__cell_configs__data_source",
                "table__cell_configs__row",
                "table__cell_configs__column",
            )
            .order_by("order")
        )

        for form_field in ungrouped:
            field_ctx = self._build_field_context(form_field, django_form, initial)
            ungrouped_ctx.append(field_ctx)

        return ungrouped_ctx

    def _build_field_context(self, form_field, django_form, initial):
        """
        Build the context dict for a single field. For table fields this
        includes the pre-populated table structure. For all other fields
        it includes the bound Django form field (BoundField).
        """
        code       = form_field.data_type.code
        input_name = get_field_name(form_field)

        base = {
            "form_field":  form_field,
            "input_name":  input_name,
            "data_type":   code,
            "label":       form_field.label,
            "is_required": form_field.is_required,
            "help_text":   form_field.help_text or "",
        }

        # ── Table fields ──────────────────────────────────────────────────────
        if code in ("table_dynamic", "table_fixed"):
            base["table_data"] = self._build_table_context(form_field, initial)
            return base

        # ── Signature ─────────────────────────────────────────────────────────
        if code == "signature":
            signature_json = initial.get(input_name, "")
            base["signature_initial"] = signature_json
            # BoundField still exists so the hidden input renders correctly
            if input_name in django_form.fields:
                base["bound_field"] = django_form[input_name]
            return base

        # ── File / image ──────────────────────────────────────────────────────
        if code in ("file", "image"):
            base["existing_file"] = get_file_url(initial, input_name, self.request)
            if input_name in django_form.fields:
                base["bound_field"] = django_form[input_name]
            return base

        # ── All other fields ──────────────────────────────────────────────────
        if input_name in django_form.fields:
            base["bound_field"] = django_form[input_name]

        return base

    def _build_table_context(self, form_field, initial):
        """
        Build the table rendering context for a table field.

        For the create view (no initial): returns column definitions and
        one blank row for dynamic tables, full grid for fixed tables.

        For the edit view (initial present): returns saved rows pre-populated.
        """
        table     = form_field.table
        code      = form_field.data_type.code

        if not table:
            return None

        columns = list(table.columns.select_related("data_type", "data_source").order_by("order"))

        # Check if we have saved data for this table
        saved = get_table_initial(initial, str(table.uid))

        if code == "table_dynamic":
            return self._build_dynamic_table_context(table, columns, saved)

        if code == "table_fixed":
            return self._build_fixed_table_context(table, columns, saved)

        return None

    def _build_dynamic_table_context(self, table, columns, saved):
        """
        Dynamic rows table context.

        Columns: from the DB definition.
        Rows:    from saved data (edit) or one blank row (create).

        Each row carries a row_index used to build cell input names.
        A blank template row is always included at the end — JS uses it
        to clone new rows when "Add Row" is clicked.
        """
        col_ctx = [
            {
                "uid":         str(col.uid),
                "header":      col.header,
                "data_type":   col.data_type.code,
                "is_required": col.is_required,
                "data_source": col.data_source,
            }
            for col in columns
        ]

        rows_ctx = []

        if saved and saved.get("rows"):
            # Edit view — pre-populate saved rows
            for row in saved["rows"]:
                row_index = row.get("row_identifier", "0")
                cells_ctx = self._build_dynamic_row_cells(col_ctx, row.get("cells", {}), row_index, str(table.uid))
                rows_ctx.append({"row_index": row_index, "cells": cells_ctx})
        else:
            # Create view — start with one blank row at index 0
            cells_ctx = self._build_dynamic_row_cells(col_ctx, {}, "0", str(table.uid))
            rows_ctx.append({"row_index": "0", "cells": cells_ctx})

        return {
            "table":       table,
            "table_type":  "dynamic_rows",
            "columns":     col_ctx,
            "rows":        rows_ctx,
            "table_uid":   str(table.uid),
        }

    def _build_dynamic_row_cells(self, col_ctx, saved_cells, row_index, table_uid):
        """
        Build the cell context list for a single dynamic row.
        Each cell has a rendered Django form field widget and an input_name.
        """
        cells = []

        for col in col_ctx:
            col_uid    = col["uid"]
            input_name = f"table__{table_uid}__row__{row_index}__{col_uid}"
            saved_cell = saved_cells.get(col_uid, {})
            saved_val  = saved_cell.get("value") if saved_cell else None

            cell_field = build_cell_field(
                data_type_code=col["data_type"],
                data_source=col.get("data_source"),
                required=col["is_required"],
            )

            # Set initial value on the field's widget for rendering
            cell_field.initial = saved_val

            cells.append({
                "col_uid":    col_uid,
                "header":     col["header"],
                "data_type":  col["data_type"],
                "input_name": input_name,
                "field":      cell_field,
                "value":      saved_val,
            })

        return cells

    def _build_fixed_table_context(self, table, columns, saved):
        """
        Fixed grid table context.

        Both rows and columns come from the DB.
        Cell overrides (TableCell) are resolved here.
        Pre-populated values come from saved data on edit.
        """
        rows = list(table.rows.order_by("order"))

        # Build cell override lookup: (row_uid, col_uid) → TableCell
        cell_overrides = {
            (str(cc.row_id), str(cc.column_id)): cc
            for cc in table.cell_configs.select_related("data_type", "data_source")
        }

        col_ctx = [
            {
                "uid":    str(col.uid),
                "header": col.header,
            }
            for col in columns
        ]

        # Build saved cell lookup for edit view
        saved_rows_lookup = {}
        if saved and saved.get("rows"):
            for row in saved["rows"]:
                saved_rows_lookup[row["row_identifier"]] = row.get("cells", {})

        rows_ctx = []

        for row in rows:
            row_uid       = str(row.uid)
            saved_cells   = saved_rows_lookup.get(row_uid, {})
            cells_ctx     = []

            for col in columns:
                col_uid    = str(col.uid)
                input_name = f"table__{table.uid}__row__{row_uid}__{col_uid}"

                # Resolve effective data_type and data_source
                override    = cell_overrides.get((row_uid, col_uid))
                data_type   = override.data_type.code if override else col.data_type.code
                data_source = (override.data_source if override else col.data_source)

                saved_cell = saved_cells.get(col_uid, {})
                saved_val  = saved_cell.get("value") if saved_cell else None

                cell_field = build_cell_field(
                    data_type_code=data_type,
                    data_source=data_source,
                    required=col.is_required,
                )
                cell_field.initial = saved_val

                cells_ctx.append({
                    "col_uid":    col_uid,
                    "data_type":  data_type,
                    "input_name": input_name,
                    "field":      cell_field,
                    "value":      saved_val,
                })

            rows_ctx.append({
                "row_uid":   row_uid,
                "row_label": row.row_label,
                "cells":     cells_ctx,
            })

        return {
            "table":      table,
            "table_type": "fixed_grid",
            "columns":    col_ctx,
            "rows":       rows_ctx,
            "table_uid":  str(table.uid),
        }

    # ── POST handler ──────────────────────────────────────────────────────────

    def handle_post(self, request, form_definition, submission=None):
        """
        Shared POST logic for create and edit.

        Validates the Django form (non-table fields).
        If valid, serialises the full POST + FILES into JSON and saves.
        Determines status from the submit button pressed.

        Returns HttpResponse — either a redirect on success or a re-render
        with errors on failure.
        """
        django_form = build_dynamic_form(
            form_definition,
            post_data=request.POST,
            files=request.FILES,
        )

        # Determine intended status from which button was pressed
        action = request.POST.get("action", "submit")
        status = "draft" if action == "draft" else "submitted"

        # For drafts — skip required field validation
        if status == "draft":
            for field in django_form.fields.values():
                field.required = False

        if not django_form.is_valid():
            # Re-render with errors
            ctx = self.build_context(form_definition, django_form)
            return self.render_to_response(ctx)

        # Serialise POST data → structured JSON
        submission_uid = str(submission.uid) if submission else None
        response_json  = serialise_submission(
            form_definition=form_definition,
            post_data=request.POST,
            files=request.FILES,
            submission_uid=submission_uid,
        )

        if submission:
            # Edit — update existing
            submission.response = response_json
            submission.status   = status
            submission.save()
        else:
            # Create — build new
            created_by = request.user if request.user.is_authenticated else None
            submission = FormSubmission.objects.create(
                form        = form_definition,
                response    = response_json,
                status      = status,
            )

        label = "Draft saved" if status == "draft" else "Form submitted successfully"
        messages.success(request, label)
        return redirect(self.get_success_url(submission))

    def get_success_url(self, submission):
        return reverse("submission-detail", kwargs={"uid": submission.uid})


# ─────────────────────────────────────────────────────────────────────────────
# Create view
# ─────────────────────────────────────────────────────────────────────────────

class SubmissionCreateView(SubmissionFormMixin, TemplateView):
    """
    Render and process the create form for a specific Form definition.

    URL pattern:
        path("submit/<uuid:form_uid>/", SubmissionCreateView.as_view(), name="submission-create")
    """

    def get(self, request, *args, **kwargs):
        form_definition = self.get_form_definition()

        # get_form_definition may return a redirect for login/unpublished
        if hasattr(form_definition, "status_code"):
            return form_definition

        django_form = build_dynamic_form(form_definition)
        ctx         = self.build_context(form_definition, django_form)
        return self.render_to_response(ctx)

    def post(self, request, *args, **kwargs):
        form_definition = self.get_form_definition()

        if hasattr(form_definition, "status_code"):
            return form_definition

        return self.handle_post(request, form_definition, submission=None)


# ─────────────────────────────────────────────────────────────────────────────
# Edit view
# ─────────────────────────────────────────────────────────────────────────────

class SubmissionEditView(SubmissionFormMixin, TemplateView):
    """
    Load an existing FormSubmission, deserialise its JSON, and render
    the same dynamic form pre-populated with all saved values.

    URL pattern:
        path("submissions/<uuid:uid>/edit/", SubmissionEditView.as_view(), name="submission-edit")
    """

    def get_submission(self):
        return get_object_or_404(
            FormSubmission.objects.select_related("form"),
            uid=self.kwargs["uid"],
        )

    def get(self, request, *args, **kwargs):
        submission      = self.get_submission()
        form_definition = submission.form

        # Deserialise stored JSON → flat initial dict
        initial     = deserialise_submission(submission.response)
        django_form = build_dynamic_form(form_definition, initial=initial)

        ctx = self.build_context(form_definition, django_form, initial=initial)
        ctx["submission"] = submission
        return self.render_to_response(ctx)

    def post(self, request, *args, **kwargs):
        submission      = self.get_submission()
        form_definition = submission.form
        return self.handle_post(request, form_definition, submission=submission)


# ─────────────────────────────────────────────────────────────────────────────
# Detail view  (read-only, renders from JSON without building a Django form)
# ─────────────────────────────────────────────────────────────────────────────

class SubmissionDetailView(TemplateView):
    """
    Read-only view of a submitted FormSubmission.
    Renders directly from the stored JSON — no form rebuilding needed.

    URL pattern:
        path("submissions/<uuid:uid>/", SubmissionDetailView.as_view(), name="submission-detail")
    """

    template_name = "submissions/details.html"

    def get(self, request, *args, **kwargs):
        submission = get_object_or_404(
            FormSubmission.objects.select_related("form"),
            uid=self.kwargs["uid"],
        )

        return self.render_to_response({
            "submission":    submission,
            "form_definition": submission.form,
            "response":      submission.response,
            "sections":      submission.response.get("sections", []),
            "ungrouped":     submission.response.get("ungrouped", {}),
        })