"""
App configuration for the assessments app.
"""

from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    """
    Configuration for the assessments app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assessments'
    verbose_name = 'Assessments'
