"""
Settings initialization for aksio project.
"""

import os

# Import base settings first
from .base import *

# Determine environment and load appropriate settings
environment = os.getenv('DJANGO_ENV', 'development').lower()

if environment == 'production':
    from .production import *
else:
    # Default to development
    from .development import *