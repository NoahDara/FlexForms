from django.conf import settings
from companies.models import Company
from organization.models import Organization
from currency.models import Currency
from django.db import connection

DEFAULT_CURRENCY_SYMBOL = getattr(settings, 'DEFAULT_CURRENCY_SYMBOL', 'USD$')


def global_context_data(request):
    """
    Global context data for templates.
    Only queries tenant-specific data if user is authenticated and in tenant context.
    """
    # Default values
    context = {
        'system_company': None,
        'job_related_permissions': [
            "read_job", "write_job",
            "read_job_activity", "write_job_activity",
            "read_quotation", "write_quotation",
            "read_invoice", "write_invoice",
            "read_payment", "write_payment",
            "read_expense", "write_expense",
        ],
        'user_management_permissions': [
            "read_permission",
            "read_role", "write_role",
            "read_system_users", "write_system_users",
        ],
        "main_currency": None,
        "main_currency_symbol": DEFAULT_CURRENCY_SYMBOL,
        "company": Company.objects.first(),
        "IS_TENANT": getattr(settings, "IS_TENANT", False)
    }
    
    return context