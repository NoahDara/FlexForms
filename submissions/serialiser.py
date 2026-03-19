"""
submissions/serialiser.py

Responsible for ONE thing: take raw POST data + FILES from a submitted
dynamic form and produce the structured JSON dict that gets saved into
FormSubmission.response.

Nothing in here touches views, templates, or field building.
That lives in field_builder.py. This module is the single source of
truth for POST data → submission JSON.

The output structure mirrors the docstring on FormSubmission.response:

{
  "sections": [
    {
      "section_uid": "...",
      "section_name": "Personal Details",
      "answers": {
        "field_uid": {
            "label": "Full Name",
            "value": "John Doe",
            "data_type": "char"
        },
        ...
      }
    }
  ],
  "ungrouped": {
    "field_uid": {
        "label": "Additional Notes",
        "value": "Some text",
        "data_type": "text"
    },
    ...
  }
}

Table answers are embedded directly inside their section's (or ungrouped's)
answers dict, keyed by field_uid, with the table structure nested inside.

Usage:
    from submissions.serialiser import serialise_submission

    response_json = serialise_submission(form_definition, post_data, files)
"""

import json
import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from submissions.field_builder import get_field_name, TABLE_TYPES


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def serialise_submission(form_definition, post_data, files, submission_uid=None):
    """
    Build the structured response JSON from raw POST + FILES.

    Parameters
    ----------
    form_definition : forms.Form
        The Form model instance (not a Django form — the DB Form object).
    post_data : QueryDict
        request.POST from the submission view.
    files : MultiValueDict
        request.FILES from the submission view.
    submission_uid : str | UUID | None
        The UID of the FormSubmission being created or updated.
        Used to build the file upload path. If None a new UUID is generated.

    Returns
    -------
    dict
        The structured response JSON ready to assign to
        FormSubmission.response.
    """
    if submission_uid is None:
        submission_uid = str(uuid.uuid4())

    response = {
        "sections": [],
        "ungrouped": {},
    }

    # ── 1. Process sectioned fields ───────────────────────────────────────────
    sections = form_definition.sections.prefetch_related(
        "fields__data_type",
        "fields__data_source",
        "fields__table__columns__data_type",
        "fields__table__columns__data_source",
        "fields__table__rows",
        "fields__table__cell_configs__data_type",
        "fields__table__cell_configs__data_source",
        "fields__table__cell_configs__row",
        "fields__table__cell_configs__column",
    ).order_by("order")

    for section in sections:
        section_answers = {}

        for form_field in section.fields.order_by("order"):
            key, value = _serialise_field(form_field, post_data, files, submission_uid)
            if key is not None:
                section_answers[key] = value

        response["sections"].append({
            "section_uid":  str(section.uid),
            "section_name": section.name,
            "answers":      section_answers,
        })

    # ── 2. Process ungrouped fields ───────────────────────────────────────────
    ungrouped_fields = (
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

    for form_field in ungrouped_fields:
        key, value = _serialise_field(form_field, post_data, files, submission_uid)
        if key is not None:
            response["ungrouped"][key] = value

    return response


# ─────────────────────────────────────────────────────────────────────────────
# Per-field dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def _serialise_field(form_field, post_data, files, submission_uid):
    """
    Dispatch a single FormField to the right serialiser based on its
    data_type.code.

    Returns
    -------
    (str, dict) — the field UID string key and the value payload dict,
                  or (None, None) if the field should be skipped entirely.
    """
    code     = form_field.data_type.code
    field_uid = str(form_field.uid)

    if code in TABLE_TYPES:
        payload = _serialise_table_field(form_field, post_data, files, submission_uid)
    elif code in ("file", "image"):
        payload = _serialise_file_field(form_field, files, submission_uid)
    elif code == "signature":
        payload = _serialise_signature_field(form_field, post_data)
    elif code in ("foreign_key", "many_to_many"):
        payload = _serialise_relational_field(form_field, post_data)
    elif code == "boolean":
        payload = _serialise_boolean_field(form_field, post_data)
    else:
        payload = _serialise_scalar_field(form_field, post_data)

    return field_uid, payload


# ─────────────────────────────────────────────────────────────────────────────
# Scalar fields  (char, text, email, url, phone, number, float, percentage,
#                 date, datetime, time)
# ─────────────────────────────────────────────────────────────────────────────

def _serialise_scalar_field(form_field, post_data):
    input_name = get_field_name(form_field)
    raw        = post_data.get(input_name, "").strip()

    return {
        "label":     form_field.label,
        "data_type": form_field.data_type.code,
        "value":     raw or None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Boolean
# ─────────────────────────────────────────────────────────────────────────────

def _serialise_boolean_field(form_field, post_data):
    input_name = get_field_name(form_field)
    # Checkbox: present in POST = True, absent = False
    raw = post_data.get(input_name)

    return {
        "label":     form_field.label,
        "data_type": "boolean",
        "value":     raw is not None,   # True / False
    }


# ─────────────────────────────────────────────────────────────────────────────
# Relational fields  (foreign_key, many_to_many)
# ─────────────────────────────────────────────────────────────────────────────

def _serialise_relational_field(form_field, post_data):
    """
    Stores the selected Data record(s) as a dict with uid + name so the
    response is human-readable without a DB lookup.

    foreign_key  → single dict  { uid, name }  or None
    many_to_many → list of      { uid, name }  (may be empty)
    """
    from data.models import Data

    input_name = get_field_name(form_field)
    code       = form_field.data_type.code

    if code == "foreign_key":
        selected_uid = post_data.get(input_name, "").strip()
        if not selected_uid:
            return {"label": form_field.label, "data_type": code, "value": None}

        try:
            obj = Data.objects.get(uid=selected_uid, source=form_field.data_source)
            value = {"uid": str(obj.uid), "name": obj.name}
        except Data.DoesNotExist:
            value = None

        return {"label": form_field.label, "data_type": code, "value": value}

    # many_to_many
    selected_uids = post_data.getlist(input_name)
    if not selected_uids:
        return {"label": form_field.label, "data_type": code, "value": []}

    objs = Data.objects.filter(uid__in=selected_uids, source=form_field.data_source)
    value = [{"uid": str(obj.uid), "name": obj.name} for obj in objs]
    return {"label": form_field.label, "data_type": code, "value": value}


# ─────────────────────────────────────────────────────────────────────────────
# File / image fields
# ─────────────────────────────────────────────────────────────────────────────

def _serialise_file_field(form_field, files, submission_uid):
    """
    Saves the uploaded file to storage under:
        submissions/{submission_uid}/{field_uid}/{original_filename}

    Stores the relative storage path in the JSON, not a full URL.
    The template/view resolves the URL when rendering.
    """
    input_name = get_field_name(form_field)
    uploaded   = files.get(input_name)

    if not uploaded:
        return {
            "label":     form_field.label,
            "data_type": form_field.data_type.code,
            "value":     None,
        }

    # Build a safe storage path
    _, ext      = os.path.splitext(uploaded.name)
    safe_name   = f"{uuid.uuid4().hex}{ext}"
    upload_path = f"submissions/{submission_uid}/{form_field.uid}/{safe_name}"

    saved_path = default_storage.save(upload_path, ContentFile(uploaded.read()))

    return {
        "label":         form_field.label,
        "data_type":     form_field.data_type.code,
        "value":         saved_path,
        "original_name": uploaded.name,
        "content_type":  uploaded.content_type,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Signature field
# ─────────────────────────────────────────────────────────────────────────────

def _serialise_signature_field(form_field, post_data):
    """
    The signature canvas writes stroke JSON into a hidden input.
    We receive it as a raw JSON string and store it parsed (not as a
    string-inside-JSON) so it's directly usable when rendering back.

    If the hidden input is empty the signature is considered blank.
    """
    input_name = get_field_name(form_field)
    raw        = post_data.get(input_name, "").strip()

    if not raw:
        return {
            "label":     form_field.label,
            "data_type": "signature",
            "value":     None,
        }

    try:
        stroke_data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Corrupted canvas data — treat as empty
        stroke_data = None

    return {
        "label":     form_field.label,
        "data_type": "signature",
        "value":     stroke_data,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Table fields
# ─────────────────────────────────────────────────────────────────────────────

def _serialise_table_field(form_field, post_data, files, submission_uid):
    """
    Dispatch to the correct table serialiser based on table_type.
    """
    table = form_field.table

    if table is None:
        return {
            "label":     form_field.label,
            "data_type": form_field.data_type.code,
            "value":     None,
        }

    if table.table_type == "dynamic_rows":
        return _serialise_dynamic_table(form_field, table, post_data, files, submission_uid)

    if table.table_type == "fixed_grid":
        return _serialise_fixed_table(form_field, table, post_data, files, submission_uid)

    return {
        "label":     form_field.label,
        "data_type": form_field.data_type.code,
        "value":     None,
    }


def _serialise_dynamic_table(form_field, table, post_data, files, submission_uid):
    """
    Dynamic rows: admin defines columns, user adds rows freely.

    POST key pattern per cell:
        table__{table_uid}__row__{row_index}__{column_uid}

    Row index starts at 0. We scan upward until we find no data for a given
    index. Rows where every cell is blank or None are skipped (not captured).

    Output:
    {
        "label": "Employment History",
        "data_type": "table_dynamic",
        "value": {
            "table_uid":  "...",
            "table_type": "dynamic_rows",
            "columns": [
                {"uid": "...", "header": "Company", "data_type": "char"}
            ],
            "rows": [
                {
                    "row_index": 0,
                    "cells": {
                        "column_uid": {"value": "Acme Corp", "data_type": "char"}
                    }
                }
            ]
        }
    }
    """
    columns  = list(table.columns.order_by("order"))
    table_uid = str(table.uid)

    column_meta = [
        {
            "uid":       str(col.uid),
            "header":    col.header,
            "data_type": col.data_type.code,
        }
        for col in columns
    ]

    rows = []
    row_index = 0

    while True:
        cells   = {}
        has_any = False

        for col in columns:
            cell_name = f"table__{table_uid}__row__{row_index}__{col.uid}"
            code      = col.data_type.code

            if code in ("file", "image"):
                uploaded = files.get(cell_name)
                if uploaded:
                    has_any    = True
                    _, ext     = os.path.splitext(uploaded.name)
                    safe_name  = f"{uuid.uuid4().hex}{ext}"
                    save_path  = f"submissions/{submission_uid}/tables/{table_uid}/{safe_name}"
                    saved      = default_storage.save(save_path, ContentFile(uploaded.read()))
                    cell_value = {"path": saved, "original_name": uploaded.name}
                else:
                    cell_value = None

            elif code == "boolean":
                raw        = post_data.get(cell_name)
                cell_value = raw is not None
                if cell_value:
                    has_any = True

            elif code in ("foreign_key", "many_to_many"):
                from data.models import Data as DataModel
                if code == "foreign_key":
                    uid_val = post_data.get(cell_name, "").strip()
                    if uid_val:
                        has_any = True
                        try:
                            obj        = DataModel.objects.get(uid=uid_val, source=col.data_source)
                            cell_value = {"uid": str(obj.uid), "name": obj.name}
                        except DataModel.DoesNotExist:
                            cell_value = None
                    else:
                        cell_value = None
                else:
                    uid_list = post_data.getlist(cell_name)
                    if uid_list:
                        has_any = True
                        objs       = DataModel.objects.filter(uid__in=uid_list, source=col.data_source)
                        cell_value = [{"uid": str(o.uid), "name": o.name} for o in objs]
                    else:
                        cell_value = []

            else:
                raw = post_data.get(cell_name, "").strip()
                if raw:
                    has_any    = True
                    cell_value = raw
                else:
                    cell_value = None

            cells[str(col.uid)] = {
                "header":    col.header,
                "data_type": code,
                "value":     cell_value,
            }

        # If no cell in this row had any value, we've passed the last row
        if not has_any:
            break

        rows.append({"row_index": row_index, "cells": cells})
        row_index += 1

    return {
        "label":     form_field.label,
        "data_type": "table_dynamic",
        "value": {
            "table_uid":  table_uid,
            "table_type": "dynamic_rows",
            "columns":    column_meta,
            "rows":       rows,
        },
    }


def _serialise_fixed_table(form_field, table, post_data, files, submission_uid):
    """
    Fixed grid: both rows and columns are admin-defined.
    Users only fill in cell values.

    POST key pattern per cell:
        table__{table_uid}__row__{row_uid}__{column_uid}

    Cell data_type is resolved by checking TableCell overrides first,
    then falling back to the column's data_type. This mirrors the same
    precedence rule used when rendering the table in the template.

    Output:
    {
        "label": "Skill Assessment",
        "data_type": "table_fixed",
        "value": {
            "table_uid":  "...",
            "table_type": "fixed_grid",
            "columns": [
                {"uid": "...", "header": "Rating", "data_type": "number"}
            ],
            "rows": [
                {
                    "row_uid":   "...",
                    "row_label": "Communication",
                    "cells": {
                        "column_uid": {"value": "4", "data_type": "number"}
                    }
                }
            ]
        }
    }
    """
    columns   = list(table.columns.order_by("order"))
    rows      = list(table.rows.order_by("order"))
    table_uid = str(table.uid)

    # Build a lookup: (row_uid, col_uid) → TableCell override
    cell_overrides = {
        (str(cc.row_id), str(cc.column_id)): cc
        for cc in table.cell_configs.select_related("data_type", "data_source")
    }

    column_meta = [
        {
            "uid":       str(col.uid),
            "header":    col.header,
            "data_type": col.data_type.code,
        }
        for col in columns
    ]

    serialised_rows = []

    for row in rows:
        row_uid = str(row.uid)
        cells   = {}

        for col in columns:
            col_uid   = str(col.uid)
            cell_name = f"table__{table_uid}__row__{row_uid}__{col_uid}"

            # Resolve effective data_type and data_source for this cell
            override    = cell_overrides.get((row_uid, col_uid))
            data_type   = override.data_type.code if override else col.data_type.code
            data_source = (override.data_source if override else col.data_source)

            if data_type in ("file", "image"):
                uploaded = files.get(cell_name)
                if uploaded:
                    _, ext    = os.path.splitext(uploaded.name)
                    safe_name = f"{uuid.uuid4().hex}{ext}"
                    save_path = f"submissions/{submission_uid}/tables/{table_uid}/{safe_name}"
                    saved     = default_storage.save(save_path, ContentFile(uploaded.read()))
                    cell_value = {"path": saved, "original_name": uploaded.name}
                else:
                    cell_value = None

            elif data_type == "boolean":
                raw        = post_data.get(cell_name)
                cell_value = raw is not None

            elif data_type in ("foreign_key", "many_to_many"):
                from data.models import Data as DataModel
                if data_type == "foreign_key":
                    uid_val = post_data.get(cell_name, "").strip()
                    if uid_val:
                        try:
                            obj        = DataModel.objects.get(uid=uid_val, source=data_source)
                            cell_value = {"uid": str(obj.uid), "name": obj.name}
                        except DataModel.DoesNotExist:
                            cell_value = None
                    else:
                        cell_value = None
                else:
                    uid_list = post_data.getlist(cell_name)
                    if uid_list:
                        objs       = DataModel.objects.filter(uid__in=uid_list, source=data_source)
                        cell_value = [{"uid": str(o.uid), "name": o.name} for o in objs]
                    else:
                        cell_value = []
            else:
                cell_value = post_data.get(cell_name, "").strip() or None

            cells[col_uid] = {
                "header":    col.header,
                "data_type": data_type,
                "value":     cell_value,
            }

        serialised_rows.append({
            "row_uid":   row_uid,
            "row_label": row.row_label,
            "cells":     cells,
        })

    return {
        "label":     form_field.label,
        "data_type": "table_fixed",
        "value": {
            "table_uid":  table_uid,
            "table_type": "fixed_grid",
            "columns":    column_meta,
            "rows":       serialised_rows,
        },
    }