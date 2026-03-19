"""
submissions/pdf_generator.py

Generates a styled PDF for a FormSubmission and saves it to
    downloads/submissions/{submission_uid}.pdf

Usage:
    from submissions.pdf_generator import generate_submission_pdf

    path = generate_submission_pdf(submission)
    # returns: "downloads/submissions/3fca3559-....pdf"

    # From a view — serve as download:
    from django.core.files.storage import default_storage
    from django.http import FileResponse

    path = generate_submission_pdf(submission)
    return FileResponse(
        default_storage.open(path, "rb"),
        as_attachment=True,
        filename=f"submission_{submission.uid}.pdf",
        content_type="application/pdf",
    )
"""

import io
import os
import json

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
    Image,
)
from reportlab.platypus.flowables import Flowable


# ─────────────────────────────────────────────────────────────────────────────
# Brand colours  (adjust to match your project)
# ─────────────────────────────────────────────────────────────────────────────

PRIMARY      = colors.HexColor("#1B2A4A")   # deep navy  — header bg
ACCENT       = colors.HexColor("#2C6FEF")   # blue       — section header bg
ACCENT_LIGHT = colors.HexColor("#EEF3FD")   # pale blue  — section header text bg
MUTED        = colors.HexColor("#8094AE")   # grey       — labels
WHITE        = colors.white
BLACK        = colors.HexColor("#1C2B36")
ROW_ALT      = colors.HexColor("#F5F6FA")   # table alt row
BORDER       = colors.HexColor("#DBE0EB")
SUCCESS      = colors.HexColor("#1EAB6D")
DANGER       = colors.HexColor("#E85347")


# ─────────────────────────────────────────────────────────────────────────────
# Page layout
# ─────────────────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4
MARGIN_L = 20 * mm
MARGIN_R = 20 * mm
MARGIN_T = 18 * mm
MARGIN_B = 18 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


# ─────────────────────────────────────────────────────────────────────────────
# Paragraph styles
# ─────────────────────────────────────────────────────────────────────────────

def _styles():
    return {
        "form_title": ParagraphStyle(
            "form_title",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=WHITE,
            leading=26,
            alignment=TA_LEFT,
        ),
        "form_subtitle": ParagraphStyle(
            "form_subtitle",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#B8C8E8"),
            leading=13,
            alignment=TA_LEFT,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=WHITE,
            leading=14,
            alignment=TA_LEFT,
        ),
        "field_label": ParagraphStyle(
            "field_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=MUTED,
            leading=14,
            spaceAfter=2,
        ),
        "field_value": ParagraphStyle(
            "field_value",
            fontName="Helvetica",
            fontSize=12,
            textColor=BLACK,
            leading=16,
        ),
        "field_value_italic": ParagraphStyle(
            "field_value_italic",
            fontName="Helvetica-Oblique",
            fontSize=11,
            textColor=MUTED,
            leading=15,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=WHITE,
            leading=15,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontName="Helvetica",
            fontSize=11,
            textColor=BLACK,
            leading=15,
        ),
        "table_label_cell": ParagraphStyle(
            "table_label_cell",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=BLACK,
            leading=15,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=11,
            alignment=TA_CENTER,
        ),
        "badge_yes": ParagraphStyle(
            "badge_yes",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=SUCCESS,
            leading=15,
        ),
        "badge_no": ParagraphStyle(
            "badge_no",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=DANGER,
            leading=15,
        ),
        "url_value": ParagraphStyle(
            "url_value",
            fontName="Helvetica",
            fontSize=12,
            textColor=ACCENT,
            leading=16,
        ),
        "attachment_note": ParagraphStyle(
            "attachment_note",
            fontName="Helvetica",
            fontSize=11,
            textColor=BLACK,
            leading=16,
        ),
        "attachment_label": ParagraphStyle(
            "attachment_label",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=ACCENT,
            leading=15,
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Custom flowables
# ─────────────────────────────────────────────────────────────────────────────

class HeaderBanner(Flowable):
    """
    Full-width navy banner containing form title, description, and metadata.
    """
    def __init__(self, title, description, submitted_at, status, width):
        super().__init__()
        self.title       = title
        self.description = description
        self.submitted_at = submitted_at
        self.status      = status
        self.width       = width
        self.height      = 52 * mm

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        # Background
        c.setFillColor(PRIMARY)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Accent stripe on left edge
        c.setFillColor(ACCENT)
        c.rect(0, 0, 4, h, fill=1, stroke=0)

        # Title
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(12, h - 20 * mm, self.title)

        # Description
        if self.description:
            c.setFillColor(colors.HexColor("#B8C8E8"))
            c.setFont("Helvetica", 8)
            # Truncate long descriptions
            desc = self.description if len(self.description) <= 100 else self.description[:97] + "..."
            c.drawString(12, h - 27 * mm, desc)

        # Metadata row
        c.setFillColor(colors.HexColor("#8BADD4"))
        c.setFont("Helvetica", 7.5)
        meta = f"Submitted: {self.submitted_at}"
        c.drawString(12, 6 * mm, meta)

        # Status badge
        status_color = SUCCESS if self.status == "submitted" else colors.HexColor("#F4A723")
        label        = "SUBMITTED" if self.status == "submitted" else "DRAFT"
        badge_w      = 22 * mm
        badge_x      = w - badge_w - 10
        badge_y      = h - 14 * mm
        c.setFillColor(status_color)
        c.roundRect(badge_x, badge_y, badge_w, 6 * mm, 2, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(badge_x + badge_w / 2, badge_y + 1.8 * mm, label)


class SectionHeader(Flowable):
    """
    Full-width coloured section header bar.
    """
    def __init__(self, title, width):
        super().__init__()
        self.title  = title
        self.width  = width
        self.height = 8 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(ACCENT)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(4, 2.5 * mm, self.title.upper())


# ─────────────────────────────────────────────────────────────────────────────
# Signature flowable  — draws stroke data from signature_pad onto the canvas
# ─────────────────────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".svg"
}


class SignatureFlowable(Flowable):
    """
    Renders signature_pad stroke data as actual drawn lines in the PDF.

    signature_pad stores data as a list of stroke groups:
    [
      {
        "points": [
          {"x": 120, "y": 45, "time": ..., "pressure": ...},
          ...
        ]
      },
      ...
    ]

    We scale the original canvas coordinates (typically ~500×180px)
    down to fit the PDF box while preserving aspect ratio, then draw
    each stroke as a polyline with rounded line caps.
    """

    def __init__(self, stroke_data: list, width: float, height: float = 35 * mm):
        super().__init__()
        self.stroke_data = stroke_data
        self.width       = width
        self.height      = height

    def draw(self):
        c = self.canv

        # Draw a white background + border
        c.setFillColor(WHITE)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=1)

        if not self.stroke_data:
            return

        # Find bounding box of all points to scale correctly
        all_x = []
        all_y = []
        for stroke in self.stroke_data:
            for pt in stroke.get("points", []):
                all_x.append(pt.get("x", 0))
                all_y.append(pt.get("y", 0))

        if not all_x:
            return

        src_w = max(all_x) - min(all_x) or 1
        src_h = max(all_y) - min(all_y) or 1
        min_x = min(all_x)
        min_y = min(all_y)

        # Add padding inside the box
        pad    = 4 * mm
        box_w  = self.width  - pad * 2
        box_h  = self.height - pad * 2

        scale  = min(box_w / src_w, box_h / src_h)

        # Offset to centre the signature in the box
        drawn_w = src_w * scale
        drawn_h = src_h * scale
        off_x   = pad + (box_w - drawn_w) / 2
        # PDF Y axis is bottom-up; flip the signature vertically
        off_y   = pad + (box_h - drawn_h) / 2

        def tx(x):
            return off_x + (x - min_x) * scale

        def ty(y):
            # Flip: large source y → small PDF y
            return self.height - off_y - (y - min_y) * scale

        # Draw each stroke
        c.setStrokeColor(BLACK)
        c.setLineWidth(1.2)
        c.setLineCap(1)   # round caps
        c.setLineJoin(1)  # round joins

        for stroke in self.stroke_data:
            points = stroke.get("points", [])
            if len(points) < 2:
                # Single dot — draw a small circle
                if points:
                    px, py = tx(points[0]["x"]), ty(points[0]["y"])
                    c.circle(px, py, 0.8, fill=1, stroke=0)
                continue

            p = c.beginPath()
            p.moveTo(tx(points[0]["x"]), ty(points[0]["y"]))
            for pt in points[1:]:
                p.lineTo(tx(pt["x"]), ty(pt["y"]))
            c.drawPath(p, stroke=1, fill=0)


# ─────────────────────────────────────────────────────────────────────────────
# Attachment notice box  (for non-image file fields)
# ─────────────────────────────────────────────────────────────────────────────

def _attachment_notice(filename: str, st: dict) -> list:
    """
    Render a clean, boxed notice for non-image file attachments.
    Tells the reader the file exists and to access it via the portal.
    """
    icon_line = Paragraph(
        "📎  <b>Attachment</b>",
        st["attachment_label"],
    )
    file_line = Paragraph(
        f"<b>File:</b> {filename}",
        st["attachment_note"],
    )
    note_line = Paragraph(
        "This document has been submitted as part of this form. "
        "To view or download the original file, please log in to the portal "
        "and open this submission.",
        st["attachment_note"],
    )

    # Wrap in a single-cell table to get the shaded background + border
    inner = [icon_line, Spacer(1, 3), file_line, Spacer(1, 4), note_line]
    box   = Table([[inner]], colWidths=[CONTENT_W / 2 - 6])
    box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ACCENT_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.8, ACCENT),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return [box]


# ─────────────────────────────────────────────────────────────────────────────
# Value renderers  (payload → list of Paragraph flowables)
# ─────────────────────────────────────────────────────────────────────────────

def _render_value(payload: dict, st: dict) -> list:
    """
    Given a field payload dict, return a list of Platypus flowables
    that represent the field's value.
    """
    dt  = payload.get("data_type", "")
    val = payload.get("value")

    if val is None or val == "" or val == []:
        return [Paragraph("—", st["field_value_italic"])]

    # ── Boolean ───────────────────────────────────────────────────────────────
    if dt == "boolean":
        style = st["badge_yes"] if val else st["badge_no"]
        text  = "✓  Yes" if val else "✗  No"
        return [Paragraph(text, style)]

    # ── Foreign key ───────────────────────────────────────────────────────────
    if dt == "foreign_key":
        name = val.get("name", "—") if isinstance(val, dict) else str(val)
        return [Paragraph(name, st["field_value"])]

    # ── Many to many ──────────────────────────────────────────────────────────
    if dt == "many_to_many":
        if not isinstance(val, list) or not val:
            return [Paragraph("—", st["field_value_italic"])]
        items = ", ".join(item.get("name", "") for item in val if isinstance(item, dict))
        return [Paragraph(items or "—", st["field_value"])]

    # ── URL ───────────────────────────────────────────────────────────────────
    if dt == "url":
        return [Paragraph(f'<link href="{val}">{val}</link>', st["url_value"])]

    # ── Email ─────────────────────────────────────────────────────────────────
    if dt == "email":
        return [Paragraph(f'<link href="mailto:{val}">{val}</link>', st["url_value"])]

    # ── Percentage ────────────────────────────────────────────────────────────
    if dt == "percentage":
        return [Paragraph(f"{val}%", st["field_value"])]

    # ── Signature ─────────────────────────────────────────────────────────────
    if dt == "signature":
        # val is the parsed stroke list from signature_pad
        stroke_data = val if isinstance(val, list) else []
        if not stroke_data:
            return [Paragraph("No signature captured.", st["field_value_italic"])]
        return [SignatureFlowable(stroke_data, width=CONTENT_W / 2 - 6, height=35 * mm)]

    # ── File — check extension to decide if it can be embedded as an image ────
    if dt in ("file", "image"):
        if isinstance(val, dict):
            orig = val.get("original_name", "")
            path = val.get("value") or val.get("path", "")
        else:
            orig = str(val).split("/")[-1]
            path = str(val)

        _, ext = os.path.splitext(orig.lower())
        is_image_file = ext in IMAGE_EXTENSIONS

        if is_image_file:
            # Try to embed the image inline
            try:
                if default_storage.exists(path):
                    with default_storage.open(path, "rb") as f:
                        img_data = f.read()
                    img_buf = io.BytesIO(img_data)
                    img = Image(img_buf, width=60 * mm, height=40 * mm)
                    img.hAlign = "LEFT"
                    return [img]
            except Exception:
                pass
            # Fallback if storage read fails
            return [Paragraph(f"Image: {orig} — locate at: {path}", st["attachment_note"])]

        # Non-image file — render a styled attachment notice box
        return _attachment_notice(orig, st)

    # ── Fallback — all scalars ────────────────────────────────────────────────
    return [Paragraph(str(val), st["field_value"])]


# ─────────────────────────────────────────────────────────────────────────────
# Field pair builder  (two fields side by side in a 2-col layout table)
# ─────────────────────────────────────────────────────────────────────────────

def _field_pair(left_label, left_flowables, right_label, right_flowables, st, col_w):
    """
    Build a two-column label/value layout table for up to two fields.
    right_* can be None for a single full-width field.
    """
    half = (col_w - 6) / 2

    def _cell(label, flowables):
        return [
            Paragraph(label.upper(), st["field_label"]),
            Spacer(1, 1),
            *flowables,
        ]

    if right_label is None:
        # Full-width single field
        data  = [[_cell(left_label, left_flowables)]]
        t     = Table(data, colWidths=[col_w])
    else:
        data  = [[_cell(left_label, left_flowables), _cell(right_label, right_flowables)]]
        t     = Table(data, colWidths=[half, half])

    t.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",(0, 0), (-1, -1), 4),
        ("TOPPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0,0), (-1, -1), 4),
    ]))
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Table renderers
# ─────────────────────────────────────────────────────────────────────────────

def _build_dynamic_table(table_value: dict, st: dict, col_w: float) -> list:
    """
    Render a dynamic_rows table as a styled reportlab Table.
    """
    columns = table_value.get("columns", [])
    rows    = table_value.get("rows", [])

    if not columns or not rows:
        return [Paragraph("No entries recorded.", st["field_value_italic"])]

    # Header row
    header = [Paragraph(col["header"], st["table_header"]) for col in columns]
    data   = [header]

    for row in rows:
        cells_data = row.get("cells", {})
        row_cells  = []
        for col in columns:
            cell    = cells_data.get(col["uid"], {})
            val     = cell.get("value")
            dt      = cell.get("data_type", "char")
            payload = {"data_type": dt, "value": val}
            # Flatten to plain text for table cells
            text = _cell_text(payload)
            row_cells.append(Paragraph(text, st["table_cell"]))
        data.append(row_cells)

    n_cols = len(columns)
    col_widths = [col_w / n_cols] * n_cols

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(data)))
    return [t]


def _build_fixed_table(table_value: dict, st: dict, col_w: float) -> list:
    """
    Render a fixed_grid table as a styled reportlab Table.
    Row labels on the left, column headers across the top.
    """
    columns = table_value.get("columns", [])
    rows    = table_value.get("rows", [])

    if not columns or not rows:
        return [Paragraph("No entries recorded.", st["field_value_italic"])]

    # Header row: empty first cell + column headers
    header = [Paragraph("", st["table_header"])] + [
        Paragraph(col["header"], st["table_header"]) for col in columns
    ]
    data = [header]

    for row in rows:
        cells_data = row.get("cells", {})
        row_label  = row.get("row_label", "")
        row_cells  = [Paragraph(row_label, st["table_label_cell"])]
        for col in columns:
            cell    = cells_data.get(col["uid"], {})
            val     = cell.get("value")
            dt      = cell.get("data_type", "char")
            payload = {"data_type": dt, "value": val}
            text    = _cell_text(payload)
            row_cells.append(Paragraph(text, st["table_cell"]))
        data.append(row_cells)

    n_cols = len(columns) + 1  # +1 for row label column
    label_w  = col_w * 0.25
    data_w   = (col_w - label_w) / len(columns)
    col_widths = [label_w] + [data_w] * len(columns)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(data)))
    return [t]


def _cell_text(payload: dict) -> str:
    """
    Convert a cell payload to a plain text string for table cells.
    """
    dt  = payload.get("data_type", "")
    val = payload.get("value")

    if val is None or val == "":
        return "—"
    if dt == "boolean":
        return "Yes" if val else "No"
    if dt == "foreign_key":
        return val.get("name", "—") if isinstance(val, dict) else str(val)
    if dt == "many_to_many":
        if isinstance(val, list):
            return ", ".join(i.get("name", "") for i in val if isinstance(i, dict)) or "—"
        return "—"
    if dt == "percentage":
        return f"{val}%"
    if dt in ("file", "image"):
        if isinstance(val, dict):
            return val.get("original_name", "[file]")
        return "[file]"
    return str(val)


def _table_style(n_rows: int) -> TableStyle:
    style = [
        # Header
        ("BACKGROUND",   (0, 0), (-1, 0),  ACCENT),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  11),
        ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, 0),  8),
        ("BOTTOMPADDING",(0, 0), (-1, 0),  8),
        # Data rows
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 11),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID",         (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS",(0,1), (-1, -1), [WHITE, ROW_ALT]),
    ]
    return TableStyle(style)


# ─────────────────────────────────────────────────────────────────────────────
# Page header/footer callback
# ─────────────────────────────────────────────────────────────────────────────

def _make_page_callback(form_title: str, submission_uid: str):
    def on_page(canvas, doc):
        canvas.saveState()
        w, h = A4

        # Footer line
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_L, MARGIN_B - 4 * mm, w - MARGIN_R, MARGIN_B - 4 * mm)

        # Footer text
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN_L, MARGIN_B - 8 * mm, form_title)
        canvas.drawCentredString(w / 2, MARGIN_B - 8 * mm, str(submission_uid))
        canvas.drawRightString(w - MARGIN_R, MARGIN_B - 8 * mm, f"Page {doc.page}")

        canvas.restoreState()
    return on_page


# ─────────────────────────────────────────────────────────────────────────────
# Main builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_story(submission, st: dict) -> list:
    response  = submission.response or {}
    form_def  = submission.form
    story     = []

    # ── Cover banner ──────────────────────────────────────────────────────────
    submitted_at = (
        submission.submitted_at.strftime("%d %B %Y, %H:%M")
        if submission.submitted_at else "—"
    )
    story.append(HeaderBanner(
        title       = form_def.title,
        description = form_def.description or "",
        submitted_at= submitted_at,
        status      = submission.status,
        width       = CONTENT_W,
    ))
    story.append(Spacer(1, 6 * mm))

    # ── Sections ──────────────────────────────────────────────────────────────
    for section in response.get("sections", []):
        section_name = section.get("section_name", "")
        answers      = section.get("answers", {})

        if not answers:
            continue

        story.append(KeepTogether([
            SectionHeader(section_name, CONTENT_W),
            Spacer(1, 3 * mm),
        ]))

        # Separate table fields from scalar fields
        scalar_fields = []
        table_fields  = []
        for field_uid, payload in answers.items():
            if payload.get("data_type") in ("table_dynamic", "table_fixed"):
                table_fields.append(payload)
            else:
                scalar_fields.append(payload)

        # Render scalar fields in pairs (2-column grid)
        _render_scalar_fields(scalar_fields, story, st)

        # Render table fields full-width
        for payload in table_fields:
            label      = payload.get("label", "")
            table_val  = payload.get("value")
            dt         = payload.get("data_type")
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(label.upper(), st["field_label"]))
            story.append(Spacer(1, 1))
            if table_val:
                if dt == "table_dynamic":
                    story.extend(_build_dynamic_table(table_val, st, CONTENT_W))
                else:
                    story.extend(_build_fixed_table(table_val, st, CONTENT_W))
            else:
                story.append(Paragraph("No entries recorded.", st["field_value_italic"]))
            story.append(Spacer(1, 3 * mm))

        story.append(Spacer(1, 4 * mm))

    # ── Ungrouped fields ──────────────────────────────────────────────────────
    ungrouped = response.get("ungrouped", {})
    if ungrouped:
        story.append(KeepTogether([
            SectionHeader("Additional Information", CONTENT_W),
            Spacer(1, 3 * mm),
        ]))

        scalar_fields = []
        table_fields  = []
        for field_uid, payload in ungrouped.items():
            if payload.get("data_type") in ("table_dynamic", "table_fixed"):
                table_fields.append(payload)
            else:
                scalar_fields.append(payload)

        _render_scalar_fields(scalar_fields, story, st)

        for payload in table_fields:
            label     = payload.get("label", "")
            table_val = payload.get("value")
            dt        = payload.get("data_type")
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(label.upper(), st["field_label"]))
            story.append(Spacer(1, 1))
            if table_val:
                if dt == "table_dynamic":
                    story.extend(_build_dynamic_table(table_val, st, CONTENT_W))
                else:
                    story.extend(_build_fixed_table(table_val, st, CONTENT_W))
            else:
                story.append(Paragraph("No entries recorded.", st["field_value_italic"]))
            story.append(Spacer(1, 3 * mm))

    return story


def _render_scalar_fields(fields: list, story: list, st: dict):
    """
    Render a list of scalar field payloads into the story in a 2-column grid.
    Full-width types (text, signature, file, image, url) always get their own row.
    """
    FULL_WIDTH_TYPES = {"text", "signature", "file", "image", "url"}

    # Pair up fields: skip full-width ones, which go solo
    i = 0
    while i < len(fields):
        payload = fields[i]
        dt      = payload.get("data_type", "")
        label   = payload.get("label", "")

        if dt in FULL_WIDTH_TYPES:
            # Full-width field
            value_flowables = _render_value(payload, st)
            story.append(_field_pair(label, value_flowables, None, None, st, CONTENT_W))
            i += 1
        elif i + 1 < len(fields) and fields[i + 1].get("data_type") not in FULL_WIDTH_TYPES:
            # Pair this field with the next
            next_payload = fields[i + 1]
            left_flow  = _render_value(payload, st)
            right_flow = _render_value(next_payload, st)
            story.append(_field_pair(
                label, left_flow,
                next_payload.get("label", ""), right_flow,
                st, CONTENT_W,
            ))
            i += 2
        else:
            # Last odd field — full width
            value_flowables = _render_value(payload, st)
            story.append(_field_pair(label, value_flowables, None, None, st, CONTENT_W))
            i += 1

    story.append(Spacer(1, 2 * mm))


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_submission_pdf(submission) -> str:
    """
    Generate a styled PDF for a FormSubmission and save it to storage.

    Parameters
    ----------
    submission : FormSubmission
        Must have .form, .response, .status, .submitted_at, .uid populated.

    Returns
    -------
    str
        The relative storage path where the PDF was saved, e.g.:
        "downloads/submissions/3fca3559-....pdf"
    """
    st      = _styles()
    buf     = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize   = A4,
        leftMargin = MARGIN_L,
        rightMargin= MARGIN_R,
        topMargin  = MARGIN_T,
        bottomMargin = MARGIN_B + 6 * mm,   # extra space for footer
        title      = submission.form.title,
        author     = "FlexForms",
        subject    = f"Submission {submission.uid}",
    )

    page_cb = _make_page_callback(submission.form.title, str(submission.uid))
    story   = _build_story(submission, st)

    doc.build(story, onFirstPage=page_cb, onLaterPages=page_cb)

    # ── Save to storage ───────────────────────────────────────────────────────
    buf.seek(0)
    save_path = f"downloads/submissions/{submission.uid}.pdf"

    # Overwrite if it already exists
    if default_storage.exists(save_path):
        default_storage.delete(save_path)

    default_storage.save(save_path, ContentFile(buf.read()))

    return save_path