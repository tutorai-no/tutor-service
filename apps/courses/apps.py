"""
App configuration for the courses app.
"""

from django.apps import AppConfig


class CoursesConfig(AppConfig):
    """
    Configuration for the courses app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    verbose_name = 'Courses'
