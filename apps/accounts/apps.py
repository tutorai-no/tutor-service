"""
App configuration for the accounts app.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration for the accounts app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Accounts'
    
    def ready(self):
        """
        Import signals when the app is ready and fix admin compatibility.
        """
        # Fix Django admin LogEntry to work with UUID User model
        from django.contrib.admin.models import LogEntry
        from django.db import models
        
        # Remove the foreign key constraint for LogEntry.user
        # This prevents the UUID/BigInt type mismatch
        user_field = LogEntry._meta.get_field('user')
        user_field.remote_field.db_constraint = False
        
        # Import signals here to ensure they are registered
        # from . import signals  # Uncomment when you add signals