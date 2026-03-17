"""
helpers/utilities.py
--------------------
Provides the @can_export decorator for marking model properties / methods
as exportable columns in ExportListMixin.

Usage on a model
----------------
    from helpers.utilities import can_export

    class Employee(BaseModel):

        @can_export(label="Created By", position="after")   # appended after regular fields
        @property
        def created_by(self):
            first = self.history.order_by("history_date").first()
            return first.history_user if first else None

        @can_export(label="Full Name")                       # defaults to after
        @property
        def full_name(self):
            return f"{self.first_name} {self.last_name}"

        @can_export(label="Tags")
        def tag_list(self):                                  # plain method is fine too
            return ", ".join(t.name for t in self.tags.all())

Decorator parameters
--------------------
    label    (str)  – Column header shown in the Excel file.
                      Defaults to the property/method name, title-cased.
    position (str)  – "after"  → appended after regular fields but
                                  before the forced trailing fields
                                  (is_active / created / updated).
                      "before" → prepended before all regular fields.
                      Defaults to "after".
    order    (int)  – Relative sort key among all @can_export fields
                      that share the same position. Lower = further left.
                      Defaults to 0 (stable insertion order).

How ExportListMixin picks them up
----------------------------------
Call  get_exportable_fields(model)  from within the mixin to retrieve a list of:
    [{"attname": str, "label": str, "position": str, "order": int}, ...]

The mixin then resolves values by calling  getattr(obj, attname)  and, if the
result is callable, calls it with no arguments.
"""

from __future__ import annotations

import inspect
from typing import Callable

# Sentinel attribute name stamped onto decorated callables
_EXPORT_META_ATTR = "_can_export_meta"


# ── Decorator ────────────────────────────────────────────────────────────────

def can_export(
    label:    str | None = None,
    position: str        = "after",
    order:    int        = 0,
):
    """
    Mark a model property or method as an exportable column.

    Can be used with or without arguments:

        @can_export                          # bare  – all defaults
        @can_export()                        # called – all defaults
        @can_export(label="My Col")          # custom label
        @can_export(label="X", order=1)      # custom label + ordering
    """
    if position not in ("after", "before"):
        raise ValueError("@can_export position must be 'after' or 'before'.")

    def decorator(func_or_prop):
        # Unwrap @property so we can stamp metadata onto the underlying function
        if isinstance(func_or_prop, property):
            inner = func_or_prop.fget
        else:
            inner = func_or_prop

        col_label = label or inner.__name__.replace("_", " ").title()

        setattr(inner, _EXPORT_META_ATTR, {
            "label":    col_label,
            "position": position,
            "order":    order,
        })

        # Re-wrap as property if it was one
        return func_or_prop

    # Support bare usage: @can_export  (no parentheses, func passed directly)
    # In that case the first positional arg is actually the function/property.
    if callable(label) or isinstance(label, property):
        # Called as @can_export without ()
        _target = label
        label   = None
        return decorator(_target)

    return decorator


# ── Introspection helper ──────────────────────────────────────────────────────

def get_exportable_fields(model) -> list[dict]:
    """
    Inspect *model* (the class, not an instance) and return metadata for every
    attribute decorated with @can_export, sorted by (position_rank, order).

    Returns a list of dicts:
        {
            "attname":  str,   # attribute name to getattr() on an instance
            "label":    str,   # column header
            "position": str,   # "after" | "before"
            "order":    int,   # relative sort key
        }
    """
    found = []

    for name, obj in inspect.getmembers(model):
        # Retrieve the underlying function regardless of property / plain method
        if isinstance(obj, property):
            inner = obj.fget
        elif callable(obj):
            inner = obj
        else:
            # For classes (not instances) getmembers may return raw functions
            inner = obj if callable(obj) else None

        if inner is None:
            continue

        meta = getattr(inner, _EXPORT_META_ATTR, None)
        if meta is None:
            continue

        found.append({
            "attname":  name,
            "label":    meta["label"],
            "position": meta["position"],
            "order":    meta["order"],
        })

    # Sort: "before" fields first (among themselves by order),
    #       then "after" fields (among themselves by order).
    position_rank = {"before": 0, "after": 1}
    found.sort(key=lambda f: (position_rank[f["position"]], f["order"]))

    return found


# ── Value resolver (used by the mixin) ───────────────────────────────────────

def resolve_exportable_value(obj, attname: str) -> str:
    """
    Safely retrieve and stringify the value of a @can_export attribute.

    * Properties  → accessed normally (no call needed).
    * Methods     → called with no arguments.
    * None / ""   → returns "".
    * Anything    → str(value).
    """
    try:
        value = getattr(obj, attname)
        if callable(value):
            value = value()
        if value is None:
            return ""
        return str(value)
    except Exception:
        return ""