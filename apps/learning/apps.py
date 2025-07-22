"""
App configuration for the learning app.
"""

from django.apps import AppConfig


class LearningConfig(AppConfig):
    """
    Configuration for the learning app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning'
    verbose_name = 'Learning'
