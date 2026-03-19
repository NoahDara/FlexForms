"""
submissions/templatetags/submission_tags.py

Custom template tags and filters used by the submission detail templates.

Register this app's templatetags by ensuring 'submissions' is in
INSTALLED_APPS and loading the tags in templates with:

    {% load submission_tags %}

Filters provided:

    dict_get      — look up a dict key that isn't a valid identifier
                    (needed because table cell dicts are keyed by UUID strings)

    file_url      — resolve a stored relative file path to a usable URL
                    via Django's default_storage
"""

from django import template
from django.core.files.storage import default_storage
import json as _json
register = template.Library()


@register.filter
def dict_get(d, key):
    """
    Look up a key in a dict from the template.

    Usage:
        {{ row.cells|dict_get:col.uid }}

    Returns None if the dict is None or the key is missing.
    This is necessary because Django templates cannot do dict[variable_key]
    directly — dot notation only works for string literals, not variables.
    """
    if not d or not isinstance(d, dict):
        return None
    return d.get(str(key))


@register.filter
def file_url(path):
    """
    Resolve a relative storage path to a URL.

    Usage:
        {{ payload.value|file_url }}
        {{ cell.value.path|file_url }}

    Returns an empty string if the path is blank or storage lookup fails.
    Works with any Django storage backend (local, S3, GCS, etc.) because
    it delegates to default_storage.url() rather than constructing a path
    manually.
    """
    if not path or not isinstance(path, str):
        return ""
    try:
        return default_storage.url(path)
    except Exception:
        return ""
    


@register.filter
def to_json(value):
    """
    Serialise a Python object to a JSON string safe for use in a
    data attribute or inline script.
    Returns empty string if value is None or serialisation fails.
    """
    if value is None:
        return ""
    try:
        return _json.dumps(value)
    except (TypeError, ValueError):
        return ""