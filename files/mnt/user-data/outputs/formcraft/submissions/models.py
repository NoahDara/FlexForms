from django.db import models
from django.contrib.auth import get_user_model
from helpers.models import BaseModel
from core.models import Form, FormField

User = get_user_model()


class FormSubmission(BaseModel):
    """
    A single submission of a published Form by a user.

    FormSubmission is the top-level container for a user's response to a form.
    It stores who submitted the form, when, and whether the submission is
    complete.

    The submitted_by field is nullable to support forms where requires_login
    is False — anonymous users can submit without an account. When
    requires_login is True on the Form, submitted_by will always be populated.

    All field answers are stored as related SubmissionAnswer objects, each
    holding the answer for one FormField as a structured JSON value.
    """

    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="The form that was submitted",
    )

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_submissions",
        help_text=(
            "The user who submitted the form. "
            "Null for anonymous submissions on forms that do not require login."
        ),
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of when the form was submitted",
    )

    is_complete = models.BooleanField(
        default=False,
        help_text=(
            "True when the submission has been fully completed and submitted. "
            "False indicates a saved draft mid-way through the form."
        ),
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Form Submission"
        verbose_name_plural = "Form Submissions"

    def __str__(self):
        user = self.submitted_by or "Anonymous"
        return f"{self.form.title} — {user} — {self.submitted_at:%Y-%m-%d %H:%M}"


class SubmissionAnswer(BaseModel):
    """
    Stores the answer for a single FormField within a FormSubmission.

    Each SubmissionAnswer corresponds to exactly one FormField and one
    FormSubmission. The answer is stored as a JSONField to accommodate all
    possible field types uniformly:

      - Text / Char / Email / Number / Date:
          Plain value — e.g. "John Doe" or "2024-01-15"

      - File / Image:
          Storage path string — e.g. "/media/submissions/<uid>/cv.pdf"

      - Signature:
          Storage path to saved signature image — e.g. "/media/signatures/<uid>.png"

      - Dropdown / Radio / Foreign Key:
          Single selected value — e.g. "hr" or "uuid-of-department"

      - Checkbox Multi / Multi Select / Many to Many:
          List of selected values — e.g. ["hr", "finance"]

      - Table (dynamic_rows):
          {
            "table_uid": "...",
            "table_type": "dynamic_rows",
            "columns": ["Company", "Title", "Start Date"],
            "rows": [
              {"row_index": 1, "Company": "Acme", "Title": "Dev", "Start Date": "2020-01-01"},
              {"row_index": 2, "Company": "Globe", "Title": "Lead", "Start Date": "2022-07-01"}
            ]
          }

      - Table (fixed_grid):
          {
            "table_uid": "...",
            "table_type": "fixed_grid",
            "rows": [
              {
                "row_uid": "...",
                "row_label": "Service Quality",
                "January": 4,
                "February": 5,
                "March": 3
              },
              ...
            ]
          }

    The FK to FormField is intentionally kept so that answers remain
    queryable — e.g. "show all answers to the email field across all
    submissions" — without having to dig through JSON.
    """

    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name="answers",
        help_text="The submission this answer belongs to",
    )

    field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
        related_name="answers",
        help_text="The form field this answer responds to",
    )

    value = models.JSONField(
        default=None,
        null=True,
        blank=True,
        help_text=(
            "The submitted value for this field stored as JSON. "
            "Structure varies by field type — see model docstring for full reference."
        ),
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Submission Answer"
        verbose_name_plural = "Submission Answers"
        unique_together = [("submission", "field")]

    def __str__(self):
        return f"{self.submission} — {self.field.label}"
