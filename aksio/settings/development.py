"""
Development settings for aksio project.
"""

from .base import *

# Development mode
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1", 
    "0.0.0.0",
    "backend",  # Docker container name
    "testserver",  # For Django test client
]

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins for development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",    # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8000",    # Django dev server
    "http://127.0.0.1:8000",
]

# Email backend for development (print to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development logging - more verbose
LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["loggers"]["aksio"]["level"] = "DEBUG"