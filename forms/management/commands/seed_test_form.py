"""
forms/management/commands/seed_test_form.py

Creates a complete test form covering every major field type and table variant.

Run with:
    python manage.py seed_test_form

What gets created:
    DataSource      — "Departments" with 5 options
    Table           — "Employment History" (dynamic_rows)
    Table           — "Skill Assessment" (fixed_grid)
    Form            — "Employee Onboarding Form" with:
                        Section 1 — Personal Details
                            char, email, phone, date, boolean
                        Section 2 — Employment Details
                            foreign_key (Departments), many_to_many (Departments)python manage.py seed_test_form
                            datetime, number, float, percentage
                        Section 3 — Employment History Table (dynamic)
                        Section 4 — Skill Assessment Table (fixed)
                      Ungrouped —
                            url, text, signature, file

Re-running is safe — existing objects are fetched by name, not duplicated.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from data.models import DataSource, Data, DataType
from forms.models import Form, FormSection, FormField
from tables.models import Table, TableColumn, TableRow, TableCell


class Command(BaseCommand):
    help = "Seed a complete test form covering all field types and both table variants."

    def handle(self, *args, **options):
        self.stdout.write("\n── Seeding test form ────────────────────────────────")

        with transaction.atomic():
            self._create_data_source()
            self._create_dynamic_table()
            self._create_fixed_table()
            self._create_form()

        self.stdout.write(self.style.SUCCESS("\n✓ Test form seeded successfully.\n"))
        self.stdout.write(f"  Form title : {self.form.title}")
        self.stdout.write(f"  Form UID   : {self.form.uid}")
        self.stdout.write(f"  Published  : {self.form.is_published}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _dt(self, code: str) -> DataType:
        """Fetch a DataType by code — raises clearly if the seed is missing."""
        try:
            return DataType.objects.get(code=code)
        except DataType.DoesNotExist:
            raise RuntimeError(
                f"DataType '{code}' not found. "
                f"Run migrations first so the post_migrate signal seeds DataType records."
            )

    def _log(self, label: str, name: str):
        self.stdout.write(f"  {'Created' if self._created else 'Exists '} {label}: {name}")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. DataSource — Departments
    # ──────────────────────────────────────────────────────────────────────────

    def _create_data_source(self):
        self.stdout.write("\n[1] DataSource")

        self.source, created = DataSource.objects.get_or_create(
            code="departments",
            defaults={
                "name":        "Departments",
                "description": "Company department list used for form dropdowns.",
            },
        )
        self._created = created
        self._log("DataSource", self.source.name)

        department_names = [
            "Engineering",
            "Human Resources",
            "Finance",
            "Marketing",
            "Operations",
        ]

        for dept_name in department_names:
            obj, created = Data.objects.get_or_create(
                source=self.source,
                name=dept_name,
                defaults={"description": f"{dept_name} department"},
            )
            self._created = created
            self._log("  Data", obj.name)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Table — Employment History (dynamic_rows)
    # ──────────────────────────────────────────────────────────────────────────

    def _create_dynamic_table(self):
        self.stdout.write("\n[2] Table — Employment History (dynamic_rows)")

        self.dynamic_table, created = Table.objects.get_or_create(
            name="Employment History",
            defaults={
                "description": "Previous employment records — users add as many rows as needed.",
                "table_type":  "dynamic_rows",
            },
        )
        self._created = created
        self._log("Table", self.dynamic_table.name)

        columns = [
            ("Company Name",  "char",     False),
            ("Job Title",     "char",     False),
            ("Start Date",    "date",     False),
            ("End Date",      "date",     False),
            ("Reason for Leaving", "text", False),
        ]

        for order, (header, code, required) in enumerate(columns):
            col, created = TableColumn.objects.get_or_create(
                table=self.dynamic_table,
                header=header,
                defaults={
                    "data_type":   self._dt(code),
                    "order":       order,
                    "is_required": required,
                },
            )
            self._created = created
            self._log(f"    Column[{order}]", col.header)

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Table — Skill Assessment (fixed_grid)
    # ──────────────────────────────────────────────────────────────────────────

    def _create_fixed_table(self):
        self.stdout.write("\n[3] Table — Skill Assessment (fixed_grid)")

        self.fixed_table, created = Table.objects.get_or_create(
            name="Skill Assessment",
            defaults={
                "description": "Self-assessed skill ratings — grid is fixed by the admin.",
                "table_type":  "fixed_grid",
            },
        )
        self._created = created
        self._log("Table", self.fixed_table.name)

        # Columns: Rating (number) | Comments (text)
        col_defs = [
            ("Rating (1–5)",  "number", False),
            ("Comments",       "text",   False),
        ]
        self.fixed_cols = []
        for order, (header, code, required) in enumerate(col_defs):
            col, created = TableColumn.objects.get_or_create(
                table=self.fixed_table,
                header=header,
                defaults={
                    "data_type":   self._dt(code),
                    "order":       order,
                    "is_required": required,
                },
            )
            self._created = created
            self._log(f"    Column[{order}]", col.header)
            self.fixed_cols.append(col)

        # Rows: one per skill
        row_labels = [
            "Communication",
            "Problem Solving",
            "Teamwork",
            "Technical Knowledge",
        ]
        self.fixed_rows = []
        for order, label in enumerate(row_labels):
            row, created = TableRow.objects.get_or_create(
                table=self.fixed_table,
                row_label=label,
                defaults={"order": order},
            )
            self._created = created
            self._log(f"    Row[{order}]", row.row_label)
            self.fixed_rows.append(row)

        # Cell override example:
        # "Technical Knowledge / Rating" → percentage instead of number
        # This demonstrates the TableCell override mechanism.
        tech_row = next(r for r in self.fixed_rows if r.row_label == "Technical Knowledge")
        rating_col = self.fixed_cols[0]

        cell, created = TableCell.objects.get_or_create(
            table=self.fixed_table,
            row=tech_row,
            column=rating_col,
            defaults={
                "data_type": self._dt("percentage"),
            },
        )
        self._created = created
        self._log("    CellOverride", f"{tech_row.row_label} / {rating_col.header} → percentage")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Form — Employee Onboarding
    # ──────────────────────────────────────────────────────────────────────────

    def _create_form(self):
        self.stdout.write("\n[4] Form")

        self.form, created = Form.objects.get_or_create(
            title="Employee Onboarding Form",
            defaults={
                "description":     "Complete all sections before your first day. Fields marked * are required.",
                "requires_login":  True,
                "is_published":    True,
            },
        )
        self._created = created
        self._log("Form", self.form.title)

        self._create_section_1_personal()
        self._create_section_2_employment()
        self._create_section_3_dynamic_table()
        self._create_section_4_fixed_table()
        self._create_ungrouped_fields()

    # ── Section 1 — Personal Details ──────────────────────────────────────────

    def _create_section_1_personal(self):
        self.stdout.write("\n  [Section 1] Personal Details")

        section, _ = FormSection.objects.get_or_create(
            form=self.form,
            name="Personal Details",
            defaults={
                "description": "Basic personal information.",
                "order":       0,
            },
        )

        fields = [
            # (label,              code,      required, help_text,                           data_source)
            ("Full Name",          "char",    True,  "Enter your legal full name.",           None),
            ("Email Address",      "email",   True,  "Your work email address.",              None),
            ("Phone Number",       "phone",   False, "Include country code e.g. +263...",    None),
            ("Date of Birth",      "date",    True,  "Format: DD/MM/YYYY",                   None),
            ("I agree to the terms & conditions", "boolean", True, "You must agree to proceed.", None),
        ]

        for order, (label, code, required, help_text, source) in enumerate(fields):
            field, created = FormField.objects.get_or_create(
                form=self.form,
                label=label,
                defaults={
                    "section":     section,
                    "data_type":   self._dt(code),
                    "order":       order,
                    "is_required": required,
                    "help_text":   help_text,
                    "data_source": source,
                },
            )
            self._created = created
            self._log(f"    Field[{order}]", f"{label} ({code})")

    # ── Section 2 — Employment Details ────────────────────────────────────────

    def _create_section_2_employment(self):
        self.stdout.write("\n  [Section 2] Employment Details")

        section, _ = FormSection.objects.get_or_create(
            form=self.form,
            name="Employment Details",
            defaults={
                "description": "Information about your role and contract.",
                "order":       1,
            },
        )

        fields = [
            ("Department",           "foreign_key",   True,  "Select your primary department.",           self.source),
            ("Additional Departments", "many_to_many", False, "Any other departments you will work with.", self.source),
            ("Start Date & Time",    "datetime",      True,  "Your official start date and time.",        None),
            ("Salary (USD)",         "float",         False, "Gross annual salary in USD.",               None),
            ("Years of Experience",  "number",        True,  "Total years of relevant experience.",       None),
            ("Commission Rate",      "percentage",    False, "Your agreed commission rate if applicable.", None),
        ]

        for order, (label, code, required, help_text, source) in enumerate(fields):
            field, created = FormField.objects.get_or_create(
                form=self.form,
                label=label,
                defaults={
                    "section":     section,
                    "data_type":   self._dt(code),
                    "order":       order,
                    "is_required": required,
                    "help_text":   help_text,
                    "data_source": source,
                },
            )
            self._created = created
            self._log(f"    Field[{order}]", f"{label} ({code})")

    # ── Section 3 — Employment History (dynamic table) ────────────────────────

    def _create_section_3_dynamic_table(self):
        self.stdout.write("\n  [Section 3] Employment History Table (dynamic_rows)")

        section, _ = FormSection.objects.get_or_create(
            form=self.form,
            name="Employment History",
            defaults={
                "description": "List all previous employers. Add as many rows as needed.",
                "order":       2,
            },
        )

        field, created = FormField.objects.get_or_create(
            form=self.form,
            label="Employment History",
            defaults={
                "section":     section,
                "data_type":   self._dt("table_dynamic"),
                "order":       0,
                "is_required": False,
                "help_text":   "Leave blank if this is your first job.",
                "table":       self.dynamic_table,
            },
        )
        self._created = created
        self._log("    Field[0]", "Employment History (table_dynamic)")

    # ── Section 4 — Skill Assessment (fixed grid) ─────────────────────────────

    def _create_section_4_fixed_table(self):
        self.stdout.write("\n  [Section 4] Skill Assessment Table (fixed_grid)")

        section, _ = FormSection.objects.get_or_create(
            form=self.form,
            name="Skill Assessment",
            defaults={
                "description": "Rate yourself on each skill. Technical Knowledge uses a percentage score.",
                "order":       3,
            },
        )

        field, created = FormField.objects.get_or_create(
            form=self.form,
            label="Skill Assessment",
            defaults={
                "section":     section,
                "data_type":   self._dt("table_fixed"),
                "order":       0,
                "is_required": False,
                "help_text":   "Rate 1 (lowest) to 5 (highest). Technical Knowledge uses a % score.",
                "table":       self.fixed_table,
            },
        )
        self._created = created
        self._log("    Field[0]", "Skill Assessment (table_fixed)")

    # ── Ungrouped fields ──────────────────────────────────────────────────────

    def _create_ungrouped_fields(self):
        self.stdout.write("\n  [Ungrouped Fields]")

        ungrouped = [
            # (label,                  code,        required, help_text,                              source, table)
            ("LinkedIn Profile",       "url",       False, "e.g. https://linkedin.com/in/yourname",  None,   None),
            ("Additional Notes",       "text",      False, "Any other information you'd like to add.", None,  None),
            ("Signature",              "signature", True,  "Draw your signature to confirm this submission.", None, None),
            ("CV / Resume",            "file",      True,  "Upload your CV in PDF or Word format.",   None,   None),
        ]

        for order, (label, code, required, help_text, source, table) in enumerate(ungrouped):
            field, created = FormField.objects.get_or_create(
                form=self.form,
                label=label,
                defaults={
                    "section":     None,        # ungrouped
                    "data_type":   self._dt(code),
                    "order":       order,
                    "is_required": required,
                    "help_text":   help_text,
                    "data_source": source,
                    "table":       table,
                },
            )
            self._created = created
            self._log(f"    Field[{order}]", f"{label} ({code})")