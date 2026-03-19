"""
submissions/deserialiser.py

Responsible for ONE thing: take an existing FormSubmission.response JSON
and produce a flat dict of { input_name: value } that pre-populates every
field when rendering the edit form.

This is the exact inverse of serialiser.py. It uses the same field name
patterns from field_builder.get_field_name() in reverse so every input
in the template gets its stored value back.

Nothing in here touches views, templates, or field building directly.

Output structure (flat dict keyed by HTML input name):

{
    # Scalar
    "section__{section_uid}__{field_uid}": "John Doe",

    # Boolean
    "ungrouped__{field_uid}": True,

    # Foreign key — returns the Data UID string (what ModelChoiceField expects)
    "section__{section_uid}__{field_uid}": "data-uid-string",

    # Many to many — returns list of Data UID strings
    "section__{section_uid}__{field_uid}": ["uid1", "uid2"],

    # Signature — returns the stroke JSON as a string (JS reads it back)
    "ungrouped__{field_uid}": '[ { "points": [...] } ]',

    # File — returns the stored path string (template renders a download link)
    "ungrouped__{field_uid}": "/media/submissions/...",

    # Table — returns a structured dict the template iterates over
    "table__{table_uid}": {
        "table_type": "dynamic_rows",
        "columns": [...],
        "rows": [...],
    }
}

Usage:
    from submissions.deserialiser import deserialise_submission

    initial = deserialise_submission(submission.response)
    # Pass initial into the template context; the view uses it to
    # pre-fill hidden inputs, set selected options, replay signatures, etc.
"""

import json


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def deserialise_submission(response_json: dict) -> dict:
    """
    Convert a stored FormSubmission.response JSON back into a flat
    { input_name: value } dict suitable for pre-populating the edit form.

    Parameters
    ----------
    response_json : dict
        The value of FormSubmission.response — the exact dict produced
        by serialiser.serialise_submission().

    Returns
    -------
    dict
        Flat mapping of HTML input name → pre-population value.
        Tables are stored under "table__{table_uid}" as a structured dict
        because they are rendered by the template, not by Django form fields.
    """
    initial = {}

    # ── 1. Sectioned answers ──────────────────────────────────────────────────
    for section in response_json.get("sections", []):
        section_uid = section.get("section_uid", "")
        answers     = section.get("answers", {})

        for field_uid, payload in answers.items():
            _deserialise_payload(
                payload    = payload,
                field_uid  = field_uid,
                section_uid = section_uid,
                initial    = initial,
            )

    # ── 2. Ungrouped answers ──────────────────────────────────────────────────
    for field_uid, payload in response_json.get("ungrouped", {}).items():
        _deserialise_payload(
            payload     = payload,
            field_uid   = field_uid,
            section_uid = None,
            initial     = initial,
        )

    return initial


# ─────────────────────────────────────────────────────────────────────────────
# Per-payload dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def _deserialise_payload(payload: dict, field_uid: str, section_uid, initial: dict):
    """
    Route a single field payload to the correct deserialiser and write
    its result into the initial dict.
    """
    if not isinstance(payload, dict):
        return

    data_type = payload.get("data_type", "")
    value     = payload.get("value")

    # Build the input name the same way field_builder.get_field_name() does
    if section_uid:
        input_name = f"section__{section_uid}__{field_uid}"
    else:
        input_name = f"ungrouped__{field_uid}"

    if data_type in ("table_dynamic", "table_fixed"):
        _deserialise_table(value, initial)
        return

    if data_type == "signature":
        initial[input_name] = _deserialise_signature(value)
        return

    if data_type == "foreign_key":
        initial[input_name] = _deserialise_foreign_key(value)
        return

    if data_type == "many_to_many":
        initial[input_name] = _deserialise_many_to_many(value)
        return

    if data_type in ("file", "image"):
        initial[input_name] = _deserialise_file(value)
        return

    if data_type == "boolean":
        initial[input_name] = _deserialise_boolean(value)
        return

    # All scalar types: char, text, email, url, phone,
    #                   number, float, percentage, date, datetime, time
    initial[input_name] = value if value is not None else ""


# ─────────────────────────────────────────────────────────────────────────────
# Scalar  (nothing to do — value is already the right Python type)
# ─────────────────────────────────────────────────────────────────────────────
# Handled inline above for brevity. Dates/times stored as strings are fed
# back as strings — Django's DateInput/DateTimeInput accept "YYYY-MM-DD"
# and "YYYY-MM-DDTHH:MM" strings directly as initial values.


# ─────────────────────────────────────────────────────────────────────────────
# Boolean
# ─────────────────────────────────────────────────────────────────────────────

def _deserialise_boolean(value) -> bool:
    """
    Returns the stored bool. The template checks this to set the
    'checked' attribute on the checkbox input.
    """
    if isinstance(value, bool):
        return value
    # Guard against accidental string storage
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


# ─────────────────────────────────────────────────────────────────────────────
# Relational
# ─────────────────────────────────────────────────────────────────────────────

def _deserialise_foreign_key(value) -> str:
    """
    Returns the UID string of the selected Data record, or "".
    ModelChoiceField.initial accepts the PK (UID) of the selected object.
    """
    if not value:
        return ""
    if isinstance(value, dict):
        return value.get("uid", "")
    return ""


def _deserialise_many_to_many(value) -> list:
    """
    Returns a list of UID strings of selected Data records.
    ModelMultipleChoiceField.initial accepts a list of PKs.
    """
    if not value or not isinstance(value, list):
        return []
    return [item.get("uid", "") for item in value if isinstance(item, dict)]


# ─────────────────────────────────────────────────────────────────────────────
# File / image
# ─────────────────────────────────────────────────────────────────────────────

def _deserialise_file(value) -> dict | None:
    """
    Returns a dict with 'path' and 'original_name' so the template can
    render a download link next to the file input.

    We never pre-populate a FileInput with a file — browsers block this
    for security. Instead the template shows the existing file as a link
    and lets the user optionally replace it.

    {
        "path": "submissions/uid/field_uid/abc123.pdf",
        "original_name": "CV_JohnDoe.pdf"
    }
    """
    if not value:
        return None
    if isinstance(value, str):
        # Older format: just a path string
        return {"path": value, "original_name": value.split("/")[-1]}
    if isinstance(value, dict):
        return {
            "path":          value.get("value") or value.get("path", ""),
            "original_name": value.get("original_name", ""),
        }
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Signature
# ─────────────────────────────────────────────────────────────────────────────

def _deserialise_signature(value) -> str:
    """
    Returns the stroke data as a JSON string so the template can write it
    into a data-signature attribute on the canvas element.

    JavaScript reads data-signature and calls signaturePad.fromData(...)
    after page load to replay the signature on the canvas.

    Returns "" if no signature was captured.
    """
    if not value:
        return ""
    if isinstance(value, str):
        # Already a JSON string — validate it parses cleanly
        try:
            json.loads(value)
            return value
        except (json.JSONDecodeError, ValueError):
            return ""
    # Stored as a parsed list/dict — serialise back to string
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Tables
# ─────────────────────────────────────────────────────────────────────────────

def _deserialise_table(value, initial: dict):
    """
    Tables are not Django form fields so they don't go into `initial`
    under an input_name. Instead they are stored under:

        "table__{table_uid}"

    The template iterates over this structure directly to render the
    pre-populated table rows and cells.

    For dynamic tables:   renders one <tr> per saved row + one blank row
    For fixed tables:     renders the full grid with values filled in

    Each cell carries its own data_type so the template knows which input
    widget to render in that cell.
    """
    if not value or not isinstance(value, dict):
        return

    table_uid = value.get("table_uid")
    if not table_uid:
        return

    key = f"table__{table_uid}"

    initial[key] = {
        "table_type": value.get("table_type"),
        "columns":    value.get("columns", []),
        "rows":       _deserialise_table_rows(value),
    }


def _deserialise_table_rows(value: dict) -> list:
    """
    Normalise the rows list from the stored JSON into a consistent shape
    that the template can iterate over without branching on table_type.

    Each row in the output:
    {
        "row_identifier": "0"  or  "row-uid-string",   ← for input name generation
        "row_label":      ""   or  "Communication",     ← for fixed grid <th>
        "cells": {
            "col_uid": {
                "header":    "Company",
                "data_type": "char",
                "value":     "Acme Corp"
            },
            ...
        }
    }
    """
    table_type = value.get("table_type")
    rows       = value.get("rows", [])
    normalised = []

    for row in rows:
        if table_type == "dynamic_rows":
            normalised.append({
                "row_identifier": str(row.get("row_index", "")),
                "row_label":      "",
                "cells":          row.get("cells", {}),
            })
        else:
            # fixed_grid
            normalised.append({
                "row_identifier": row.get("row_uid", ""),
                "row_label":      row.get("row_label", ""),
                "cells":          row.get("cells", {}),
            })

    return normalised


# ─────────────────────────────────────────────────────────────────────────────
# Convenience helpers used by the template context builder in the view
# ─────────────────────────────────────────────────────────────────────────────

def get_field_initial(initial: dict, input_name: str):
    """
    Safe lookup of a single field's initial value from the deserialised dict.
    Returns None if the key is not present.
    """
    return initial.get(input_name)


def get_table_initial(initial: dict, table_uid: str) -> dict | None:
    """
    Safe lookup of a table's pre-population data from the deserialised dict.
    Returns None if this table has no saved data.
    """
    return initial.get(f"table__{table_uid}")


def get_file_url(initial: dict, input_name: str, request=None) -> dict | None:
    """
    Returns the file metadata dict for a file/image field, with an
    absolute URL added if a request is provided.

    Used by the template to render the existing file download link.

    Returns:
    {
        "path":          "submissions/uid/...",
        "original_name": "CV_JohnDoe.pdf",
        "url":           "https://example.com/media/submissions/..."  ← if request given
    }
    """
    from django.core.files.storage import default_storage

    file_data = initial.get(input_name)
    if not file_data or not isinstance(file_data, dict):
        return None

    path = file_data.get("path", "")
    if not path:
        return None

    result = {
        "path":          path,
        "original_name": file_data.get("original_name", path.split("/")[-1]),
    }

    try:
        url = default_storage.url(path)
        if request:
            result["url"] = request.build_absolute_uri(url)
        else:
            result["url"] = url
    except Exception:
        result["url"] = ""

    return result