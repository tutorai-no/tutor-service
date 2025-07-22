"""
App configuration for the billing app.
"""

from django.apps import AppConfig


class BillingConfig(AppConfig):
    """
    Configuration for the billing app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'
    verbose_name = 'Billing'
