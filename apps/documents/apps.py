"""
App configuration for the documents app.
"""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """
    Configuration for the documents app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'
    verbose_name = 'Documents'
