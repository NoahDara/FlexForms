import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import FormSubmission


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pretty_json(data: dict | list | None, indent: int = 2) -> str:
    """Return syntax-highlighted HTML for arbitrary JSON data."""
    if data is None:
        return "<em>—</em>"
    raw = json.dumps(data, indent=indent, default=str)
    # Basic token colouring without external deps
    import re

    def colourise(match):
        token = match.group(0)
        if token.startswith('"') and token.endswith('":'):
            return f'<span style="color:#6ea8fe;font-weight:600">{token}</span>'
        if token.startswith('"'):
            return f'<span style="color:#a8d8a8">{token}</span>'
        if token in ("true", "false", "null"):
            return f'<span style="color:#ffb347">{token}</span>'
        if re.fullmatch(r"-?\d+(\.\d+)?", token):
            return f'<span style="color:#e9967a">{token}</span>'
        return token

    coloured = re.sub(
        r'"[^"\\]*(?:\\.[^"\\]*)*"(?=\s*:)|"[^"\\]*(?:\\.[^"\\]*)*"|-?\d+(?:\.\d+)?|true|false|null',
        colourise,
        raw,
    )
    return (
        '<pre style="'
        "background:#1e1e2e;color:#cdd6f4;padding:12px 16px;"
        "border-radius:6px;overflow:auto;font-size:12px;"
        'line-height:1.6;margin:0">'
        f"{coloured}</pre>"
    )


# ---------------------------------------------------------------------------
# Inlines  (extend later if you add child models)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# List filters
# ---------------------------------------------------------------------------

class StatusFilter(admin.SimpleListFilter):
    title = "status"
    parameter_name = "status"

    _CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    def lookups(self, request, model_admin):
        # Show only statuses that actually exist in the DB plus the known ones
        qs_statuses = (
            FormSubmission.objects.values_list("status", flat=True)
            .distinct()
            .order_by("status")
        )
        seen = set()
        choices = []
        for label_value, label_display in self._CHOICES:
            seen.add(label_value)
            choices.append((label_value, label_display))
        for s in qs_statuses:
            if s not in seen:
                choices.append((s, s.replace("_", " ").title()))
        return choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class HasUngroupedFilter(admin.SimpleListFilter):
    title = "has ungrouped fields"
    parameter_name = "has_ungrouped"

    def lookups(self, request, model_admin):
        return [("yes", "Yes"), ("no", "No")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(response__ungrouped={}).exclude(
                response__ungrouped__isnull=True
            )
        if self.value() == "no":
            return queryset.filter(response__ungrouped={}) | queryset.filter(
                response__ungrouped__isnull=True
            )
        return queryset


# ---------------------------------------------------------------------------
# Main ModelAdmin
# ---------------------------------------------------------------------------

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------
    list_display = (
        "uid",
        "form_title",
        "status_badge",
        "created_by_display",
        "submitted_at",
        "section_count",
        "has_ungrouped_display",
    )
    list_display_links = ("uid", "form_title")
    list_filter = (StatusFilter, HasUngroupedFilter, "submitted_at", "form")
    search_fields = (
        "form__title",
        "created_by__username",
        "created_by__email",
        "status",
    )
    date_hierarchy = "submitted_at"
    ordering = ("-submitted_at",)
    list_per_page = 25
    show_full_result_count = True

    # ------------------------------------------------------------------
    # Detail view layout
    # ------------------------------------------------------------------
    readonly_fields = (
        "submitted_at",
        "created_by",
        "form_link",
        "response_sections_display",
        "response_ungrouped_display",
        "response_raw_display",
    )

    fieldsets = (
        (
            "Submission Info",
            {
                "fields": ("form_link", "status", "created_by", "submitted_at"),
            },
        ),
        (
            "Response — Sections",
            {
                "fields": ("response_sections_display",),
                "description": (
                    "Answers grouped by form section. "
                    "Tables are shown with their rows expanded."
                ),
            },
        ),
        (
            "Response — Ungrouped Fields",
            {
                "fields": ("response_ungrouped_display",),
                "classes": ("collapse",),
            },
        ),
        (
            "Raw JSON",
            {
                "fields": ("response_raw_display",),
                "classes": ("collapse",),
                "description": "Full response payload as stored in the database.",
            },
        ),
    )

    # ------------------------------------------------------------------
    # List-view computed columns
    # ------------------------------------------------------------------

    @admin.display(description="Form", ordering="form__title")
    def form_title(self, obj):
        return obj.form.title

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            "draft": "#6c757d",
            "submitted": "#0d6efd",
            "approved": "#198754",
            "rejected": "#dc3545",
        }
        colour = colours.get(obj.status, "#6c757d")
        return format_html(
            '<span style="'
            "background:{};color:#fff;padding:2px 10px;"
            "border-radius:12px;font-size:11px;font-weight:600;"
            'text-transform:uppercase;letter-spacing:.5px">{}</span>',
            colour,
            obj.status,
        )

    @admin.display(description="Submitted by")
    def created_by_display(self, obj):
        if obj.created_by:
            return str(obj.created_by)
        return format_html('<em style="color:#aaa">Anonymous</em>')

    @admin.display(description="Sections", ordering="form__title")
    def section_count(self, obj):
        sections = (obj.response or {}).get("sections", [])
        return len(sections)

    @admin.display(description="Ungrouped?", boolean=True)
    def has_ungrouped_display(self, obj):
        return bool((obj.response or {}).get("ungrouped"))

    # ------------------------------------------------------------------
    # Detail-view readonly fields
    # ------------------------------------------------------------------

    @admin.display(description="Form")
    def form_link(self, obj):
        from django.urls import reverse

        url = reverse("admin:forms_form_change", args=[obj.form_id])
        return format_html('<a href="{}">{}</a>', url, obj.form.title)

    @admin.display(description="Sections")
    def response_sections_display(self, obj):
        sections = (obj.response or {}).get("sections", [])
        if not sections:
            return format_html("<em>No sections recorded.</em>")

        parts = []
        for section in sections:
            name = section.get("section_name", section.get("section_uid", "—"))
            answers = section.get("answers", {})

            rows_html = []
            for field_key, value in answers.items():
                # Detect table fields
                if isinstance(value, dict) and value.get("table_type"):
                    cell = self._render_table(value)
                else:
                    cell = format_html(
                        '<span style="color:#212529">{}</span>',
                        str(value) if not isinstance(value, (dict, list)) else json.dumps(value),
                    )
                rows_html.append(
                    format_html(
                        "<tr>"
                        '<td style="padding:6px 12px;font-weight:600;color:#495057;'
                        'white-space:nowrap;vertical-align:top;width:220px">{}</td>'
                        '<td style="padding:6px 12px;vertical-align:top">{}</td>'
                        "</tr>",
                        field_key,
                        cell,
                    )
                )

            section_html = format_html(
                '<div style="margin-bottom:20px">'
                '<div style="font-size:13px;font-weight:700;color:#343a40;'
                "background:#f8f9fa;padding:8px 12px;"
                'border-left:4px solid #0d6efd;margin-bottom:4px">{}</div>'
                '<table style="width:100%;border-collapse:collapse;'
                'border:1px solid #dee2e6;background:#fff">'
                "{}"
                "</table>"
                "</div>",
                name,
                mark_safe("".join(rows_html)),
            )
            parts.append(section_html)

        return mark_safe("".join(parts))

    def _render_table(self, table_data: dict) -> str:
        columns = table_data.get("columns", [])
        rows = table_data.get("rows", [])
        table_type = table_data.get("table_type", "")

        header_cells = "".join(
            f'<th style="padding:5px 10px;background:#e9ecef;'
            f'border:1px solid #ced4da;font-size:12px">{col}</th>'
            for col in columns
        )
        body_rows = []
        for row in rows:
            cells = "".join(
                f'<td style="padding:5px 10px;border:1px solid #dee2e6;font-size:12px">'
                f'{row.get(col, "")}</td>'
                for col in columns
            )
            body_rows.append(f"<tr>{cells}</tr>")

        return (
            f'<div style="font-size:11px;color:#6c757d;margin-bottom:4px">'
            f"Type: <strong>{table_type}</strong></div>"
            f'<table style="border-collapse:collapse;font-size:12px">'
            f"<thead><tr>{header_cells}</tr></thead>"
            f"<tbody>{''.join(body_rows)}</tbody>"
            f"</table>"
        )

    @admin.display(description="Ungrouped fields")
    def response_ungrouped_display(self, obj):
        ungrouped = (obj.response or {}).get("ungrouped")
        if not ungrouped:
            return format_html("<em>None</em>")

        rows_html = []
        for field_key, value in ungrouped.items():
            # Signature — list of stroke dicts
            if field_key == "signature" or (
                isinstance(value, list)
                and value
                and isinstance(value[0], dict)
                and "points" in value[0]
            ):
                cell = format_html(
                    '<em style="color:#6c757d">Signature captured ({} stroke{})</em>',
                    len(value),
                    "s" if len(value) != 1 else "",
                )
            elif isinstance(value, str) and value.startswith("/media/"):
                cell = format_html(
                    '<a href="{url}" target="_blank">{url}</a>', url=value
                )
            elif isinstance(value, (dict, list)):
                cell = mark_safe(_pretty_json(value))
            else:
                cell = format_html("{}", str(value))

            rows_html.append(
                format_html(
                    "<tr>"
                    '<td style="padding:6px 12px;font-weight:600;color:#495057;'
                    'white-space:nowrap;width:220px">{}</td>'
                    '<td style="padding:6px 12px">{}</td>'
                    "</tr>",
                    field_key,
                    cell,
                )
            )

        return mark_safe(
            '<table style="width:100%;border-collapse:collapse;'
            'border:1px solid #dee2e6;background:#fff">'
            + "".join(rows_html)
            + "</table>"
        )

    @admin.display(description="Raw response JSON")
    def response_raw_display(self, obj):
        return mark_safe(_pretty_json(obj.response))

    # ------------------------------------------------------------------
    # Permissions — submissions should never be added manually
    # ------------------------------------------------------------------

    def has_add_permission(self, request):
        return False