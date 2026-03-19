from django.db import models
from django.contrib.auth import get_user_model
from helpers.models import BaseModel
User = get_user_model()


class FormSubmission(BaseModel):
    """
    A single submission of a published Form by a user.

    All field answers are stored in a single JSONField called 'response'.
    The JSON is structured by section, preserving grouping and table row
    identity.

    Structure of response:

    {
      "sections": [
        {
          "section_uid": "...",
          "section_name": "Personal Details",
          "answers": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "date_of_birth": "1990-05-15"
          }
        },
        {
          "section_uid": "...",
          "section_name": "Employment History",
          "answers": {
            "employment_table": {
              "table_uid": "...",
              "table_type": "dynamic_rows",
              "columns": ["Company", "Title", "Start Date"],
              "rows": [
                {"row_index": 1, "Company": "Acme", "Title": "Dev", "Start Date": "2020-01-01"}
              ]
            }
          }
        }
      ],
      "ungrouped": {
        "additional_notes": "Some text here",
        "signature": [
          {
            "points": [
              {"x": 120, "y": 45, "time": 1700000001},
              {"x": 122, "y": 46, "time": 1700000002}
            ]
          }
        ],
        "cv_upload": "/media/submissions/uid/cv.pdf"
      }
    }
    """

    form = models.ForeignKey("forms.Form", on_delete=models.CASCADE,  related_name="submissions",  help_text="The form that was submitted",)
    status = models.CharField(max_length=100, default="draft")
    submitted_at = models.DateTimeField(auto_now_add=True,  help_text="Timestamp of when the form was submitted",)
    response = models.JSONField(default=dict, blank=True,
        help_text=(
            "The complete submission response stored as structured JSON. "
            "Grouped by section. Ungrouped fields sit under 'ungrouped'. "
            "See model docstring for full structure reference."
        ),
    )


    def __str__(self):
        user = self.created_by or "Anonymous"
        return f"{self.form.title} — {user} — {self.submitted_at:%Y-%m-%d %H:%M}"