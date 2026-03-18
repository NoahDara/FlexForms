# FlexForms

> Build and publish dynamic forms in Django with support for sections, table fields, file uploads, signatures and data-driven choices.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-4.x-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-required-blue)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Status](https://img.shields.io/badge/status-in%20development-orange)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Apps](#apps)
- [Models](#models)
  - [datasources](#datasources)
  - [tables](#tables)
  - [core](#core)
  - [submissions](#submissions)
- [Supported Field Types](#supported-field-types)
- [Submission JSON Structure](#submission-json-structure)
- [Getting Started](#getting-started)
- [Requirements](#requirements)
- [Contributing](#contributing)

---

## Overview

FlexForms is a Django-based dynamic form builder that allows system administrators to create, configure and publish forms entirely through the application — no code changes required. Once published, users can access and submit forms through a clean interface.

Forms support rich field types including file uploads, signature capture, and two types of embedded table inputs. All submitted data is stored as structured JSON preserving section groupings and table row identity.

---

## Features

- Create and publish forms with full draft / live state control
- Restrict form access to authenticated users only via a single `requires_login` toggle
- Organize fields into named sections within each form with independent ordering
- Supports all standard Django field types plus signature capture and table fields
- **Two table types:**
  - **Dynamic Rows** — admin defines column headers, users add as many rows as needed at submission time
  - **Fixed Grid** — admin defines both column headers and row labels; each cell has its own data type
- Tables are global and reusable across multiple forms
- Data sources power choice-based fields (dropdown, radio, multi-select, foreign key, many-to-many) from either a static list or a live Django model
- Data sources are global and reusable across multiple forms
- Submissions stored as structured JSON preserving section grouping and table row identity
- Draft submission support — users can save progress before final submission
- Full audit history on every model via `django-simple-history`
- Soft delete and UUID primary keys across all models via shared `BaseModel`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Django 4.x |
| Database | PostgreSQL (required for JSONField support) |
| Audit Trail | django-simple-history |
| Signature Capture | Signature Pad (JavaScript) |
| File Storage | Django file storage (local or S3-compatible) |

---

## Project Structure

```
flexforms/
│
├── helpers/
│   └── models.py               # BaseModel — inherited by all models
│
├── datasources/
│   ├── models.py               # DataSource
│   ├── admin.py
│   ├── apps.py
│   └── migrations/
│
├── tables/
│   ├── models.py               # TableConfig, TableColumn, TableRow, TableCell
│   ├── admin.py
│   ├── apps.py
│   └── migrations/
│
├── core/
│   ├── models.py               # Form, FormSection, FormField
│   ├── admin.py
│   ├── apps.py
│   └── migrations/
│
├── submissions/
│   ├── models.py               # FormSubmission, SubmissionAnswer
│   ├── admin.py
│   ├── apps.py
│   └── migrations/
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## Apps

| App | Responsibility |
|---|---|
| `helpers` | Shared abstract `BaseModel` inherited by all models across the project |
| `datasources` | Global reusable option lists — static JSON lists or live Django model references |
| `tables` | Global reusable table definitions — column headers, row labels, and per-cell type configs |
| `core` | The heart of the system — form definitions, sections, and field configurations |
| `submissions` | User responses — one submission per form fill, one answer row per field |

### Dependency Flow

```
datasources ◄─── core ───► tables
                  │
                  ▼
            submissions
```

`datasources` and `tables` are fully independent. `core` depends on both. `submissions` depends on `core`.

---

## Models

### `datasources`

#### `DataSource`

A reusable source of options for all choice-based and relational field types. Created independently and linked to any `FormField` or `TableColumn` across multiple forms.

| Field | Type | Description |
|---|---|---|
| `name` | CharField | Unique human-readable name e.g. `"Departments"` |
| `description` | TextField | Optional description |
| `source_type` | CharField | `static` or `dynamic` |
| `static_options` | JSONField | List of `{label, value}` objects — used when `source_type` is `static` |
| `model_reference` | CharField | `app_label.ModelName` of the target Django model — used when `source_type` is `dynamic` |
| `label_field` | CharField | Model field to display as the option label e.g. `"name"` |
| `value_field` | CharField | Model field to use as the submitted value e.g. `"uid"` |

---

### `tables`

#### `TableConfig`

A global reusable table definition. Can be embedded in any form via `FormField`. Supports two table types.

| Field | Type | Description |
|---|---|---|
| `name` | CharField | Unique name e.g. `"Employment History Table"` |
| `description` | TextField | Optional description |
| `table_type` | CharField | `dynamic_rows` or `fixed_grid` |

#### `TableColumn`

A single column inside a `TableConfig`. Defines the header label and data type for that column.

| Field | Type | Description |
|---|---|---|
| `table` | FK → TableConfig | Parent table |
| `header` | CharField | Column header label e.g. `"Company Name"` |
| `column_type` | CharField | Data type for cells in this column |
| `order` | PositiveIntegerField | Left-to-right display order |
| `is_required` | BooleanField | Whether cells in this column must be filled |
| `data_source` | FK → DataSource | Required when `column_type` is `dropdown` or `radio` |

#### `TableRow`

A named row label inside a `fixed_grid` `TableConfig`. Only used when `table_type` is `fixed_grid`.

| Field | Type | Description |
|---|---|---|
| `table` | FK → TableConfig | Parent table |
| `row_label` | CharField | Row label e.g. `"Service Quality"` |
| `order` | PositiveIntegerField | Top-to-bottom display order |

#### `TableCell`

Per-cell data type override for a `fixed_grid` table. By default a cell inherits its type from the column. This model allows overriding at the individual cell level.

| Field | Type | Description |
|---|---|---|
| `table` | FK → TableConfig | Parent table |
| `row` | FK → TableRow | Row this cell sits in |
| `column` | FK → TableColumn | Column this cell sits in |
| `cell_type` | CharField | Optional override for the cell data type |
| `data_source` | FK → DataSource | Required when `cell_type` overrides to `dropdown` or `radio` |

> `unique_together` constraint on `(table, row, column)` — each cell can only have one config.

---

### `core`

#### `Form`

The top-level form definition created and managed by system admins.

| Field | Type | Description |
|---|---|---|
| `title` | CharField | Display title shown to users |
| `description` | TextField | Optional instructions shown at the top of the form |
| `requires_login` | BooleanField | If `True`, only authenticated users can access the form |
| `is_published` | BooleanField | If `True`, the form is live and visible to users |
| `published_at` | DateTimeField | Timestamp of when the form was first published |

#### `FormSection`

An optional grouping layer within a form. Fields are grouped under named section headings. Sections are scoped to a specific form — the same name can exist independently on multiple forms.

| Field | Type | Description |
|---|---|---|
| `form` | FK → Form | Parent form |
| `name` | CharField | Section heading e.g. `"Personal Details"` |
| `description` | TextField | Optional sub-heading shown under the section title |
| `order` | PositiveIntegerField | Top-to-bottom display order within the form |

#### `FormField`

A single field definition within a form. Stores everything needed to render and validate the field.

| Field | Type | Description |
|---|---|---|
| `form` | FK → Form | Parent form |
| `section` | FK → FormSection (nullable) | Section this field belongs to. Null = ungrouped |
| `label` | CharField | Field label shown to the user |
| `field_name` | SlugField | Auto-generated key used in submission JSON. Unique per form. |
| `field_type` | CharField | One of 18 supported field types (see below) |
| `order` | PositiveIntegerField | Display order within its section (or form if ungrouped) |
| `is_required` | BooleanField | Whether the field must be filled before submitting |
| `placeholder` | CharField | Placeholder text shown inside the input |
| `help_text` | TextField | Helper text shown below the field |
| `data_source` | FK → DataSource (nullable) | Required for choice and relational field types |
| `table` | FK → TableConfig (nullable) | Required for table field types |

> `unique_together` constraint on `(form, field_name)`.

---

### `submissions`

#### `FormSubmission`

A single user response to a published form.

| Field | Type | Description |
|---|---|---|
| `form` | FK → Form | The form that was submitted |
| `submitted_by` | FK → User (nullable) | Null for anonymous submissions |
| `submitted_at` | DateTimeField | Submission timestamp |
| `is_complete` | BooleanField | `False` = saved draft, `True` = fully submitted |

#### `SubmissionAnswer`

One answer per `FormField` per `FormSubmission`. The answer is stored as JSON to accommodate all field types uniformly.

| Field | Type | Description |
|---|---|---|
| `submission` | FK → FormSubmission | Parent submission |
| `field` | FK → FormField | The field this answer responds to |
| `value` | JSONField | The submitted value — structure varies by field type |

> `unique_together` constraint on `(submission, field)`.

---

## Supported Field Types

| Category | Field Type | `field_type` value |
|---|---|---|
| Text | Short Text | `char` |
| Text | Long Text | `text` |
| Text | Email | `email` |
| Text | URL | `url` |
| Text | Phone Number | `phone` |
| Numeric | Number | `number` |
| Numeric | Decimal | `decimal` |
| Date & Time | Date | `date` |
| Date & Time | Date & Time | `datetime` |
| Date & Time | Time | `time` |
| Boolean | Checkbox (Yes/No) | `boolean` |
| File | File Upload | `file` |
| File | Image Upload | `image` |
| Choice | Dropdown | `dropdown` |
| Choice | Radio Buttons | `radio` |
| Choice | Multiple Checkboxes | `checkbox_multi` |
| Choice | Multi Select | `multi_select` |
| Relational | Foreign Key (single) | `foreign_key` |
| Relational | Many to Many (multiple) | `many_to_many` |
| Special | Signature | `signature` |
| Special | Table — Dynamic Rows | `table_dynamic` |
| Special | Table — Fixed Grid | `table_fixed` |

---

## Submission JSON Structure

All answers are stored in `SubmissionAnswer.value` as JSON. Below are examples per field type.

### Standard fields
```json
"full_name": "John Doe"
"email": "john@example.com"
"date_of_birth": "1990-05-15"
```

### File / Image / Signature
```json
"cv_upload": "/media/submissions/uid/cv.pdf"
"signature": "/media/signatures/uid.png"
```

### Choice fields (single)
```json
"department": "hr"
```

### Choice fields (multiple)
```json
"services": ["hr", "finance", "it"]
```

### Table — Dynamic Rows
```json
{
  "table_uid": "uuid-of-tableconfig",
  "table_type": "dynamic_rows",
  "columns": ["Company Name", "Job Title", "Start Date", "End Date"],
  "rows": [
    {"row_index": 1, "Company Name": "Acme Corp", "Job Title": "Developer", "Start Date": "2020-01-01", "End Date": "2022-06-30"},
    {"row_index": 2, "Company Name": "Globe Ltd", "Job Title": "Tech Lead", "Start Date": "2022-07-01", "End Date": "2024-01-01"}
  ]
}
```

### Table — Fixed Grid
```json
{
  "table_uid": "uuid-of-tableconfig",
  "table_type": "fixed_grid",
  "rows": [
    {"row_uid": "uuid-1", "row_label": "Service Quality", "January": 4, "February": 5, "March": 3},
    {"row_uid": "uuid-2", "row_label": "Response Time", "January": 3, "February": 4, "March": 5}
  ]
}
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/NoahDara/FlexForms.git
cd FlexForms
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your database

In `settings.py` set your PostgreSQL database:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "flexforms",
        "USER": "your_db_user",
        "PASSWORD": "your_db_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

### 5. Add apps to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    "simple_history",
    "datasources",
    "tables",
    "core",
    "submissions",
]
```

### 6. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

---

## Requirements

```
Django>=4.2
psycopg2-binary
django-simple-history
```

---

## Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you would like to change.

---

## License

MIT
