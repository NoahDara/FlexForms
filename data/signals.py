from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import DataType

DATA_TYPES = [
    {
        "code": "char",
        "name": "Short Text",
        "description": "A single-line text input for short answers such as names, titles, or codes. Maximum length applies."
    },
    {
        "code": "text",
        "name": "Long Text",
        "description": "A multi-line text area for longer answers such as descriptions, comments, or notes."
    },
    {
        "code": "email",
        "name": "Email",
        "description": "A text input that validates the entered value is a correctly formatted email address e.g. john@example.com."
    },
    {
        "code": "number",
        "name": "Number",
        "description": "An input that accepts whole numbers only e.g. age, quantity, or count. Decimals are not allowed."
    },
    {
        "code": "float",
        "name": "Float",
        "description": "An input that accepts numbers with decimal points e.g. prices, weights, or measurements."
    },
    {
        "code": "date",
        "name": "Date",
        "description": "A date picker that captures a calendar date with no time component e.g. date of birth or start date."
    },
    {
        "code": "datetime",
        "name": "Date & Time",
        "description": "A date and time picker that captures both a calendar date and a specific time e.g. appointment datetime or event schedule."
    },
    {
        "code": "time",
        "name": "Time",
        "description": "A time picker that captures a specific time of day with no date component e.g. shift start time."
    },
    {
        "code": "url",
        "name": "URL",
        "description": "A text input that validates the entered value is a correctly formatted web address e.g. https://example.com."
    },
    {
        "code": "phone",
        "name": "Phone Number",
        "description": "A text input for capturing a telephone or mobile number. Supports local and international formats."
    },
    {
        "code": "boolean",
        "name": "Checkbox (Yes/No)",
        "description": "A single checkbox that captures a true or false answer e.g. agree to terms, is active, or confirm declaration."
    },
    {
        "code": "file",
        "name": "File Upload",
        "description": "Allows the user to upload any file type e.g. PDF, Word document, or spreadsheet. The file is saved to storage and the path is recorded."
    },
    {
        "code": "image",
        "name": "Image Upload",
        "description": "Allows the user to upload an image file only e.g. JPG, PNG, or WebP. Useful for profile photos, ID copies, or supporting images."
    },
    {
        "code": "foreign_key",
        "name": "Foreign Key (Single Select)",
        "description": "A picker that lets the user select exactly one record from a linked data source e.g. select a department, country, or job title."
    },
    {
        "code": "many_to_many",
        "name": "Many to Many (Multi Select)",
        "description": "A picker that lets the user select multiple records from a linked data source e.g. select multiple skills, branches, or languages."
    },
    {
        "code": "signature",
        "name": "Signature",
        "description": "A canvas input where the user draws their signature using a mouse or touch. The stroke data is saved as JSON and can be rendered back at any time."
    },
    {
        "code": "table_dynamic",
        "name": "Table — Dynamic Rows",
        "description": "An embedded table where the admin defines column headers and users add as many rows as needed at submission time e.g. employment history or family members."
    },
    {
        "code": "table_fixed",
        "name": "Table — Fixed Grid",
        "description": "An embedded table where the admin defines both column headers and row labels. The grid is fixed and users only fill in the cell values e.g. monthly ratings or skill assessments."
    },
    {
        "code": "percentage",
        "name": "Percentage",
        "description": "A numeric input that accepts values between 0 and 100 representing a percentage e.g. commission rate, tax rate, or time allocation. Displayed with a % symbol."
    },
]


@receiver(post_migrate)
def seed_data_types(sender, **kwargs):
    # Only run for the app that owns DataType to avoid firing on every app's migration
    if sender.name != "data": 
        return

    for item in DATA_TYPES:
        DataType.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "description": item["description"],
            },
        )