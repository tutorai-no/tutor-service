"""
Testing settings for aksio project.
"""

from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1", "backend"]

# Database configuration for testing
# Use PostgreSQL if DATABASE_HOST is set (CI environment), otherwise SQLite
if os.getenv("DATABASE_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DATABASE_NAME", "aksio_db"),
            "USER": os.getenv("DATABASE_USER", "aksio_user"),
            "PASSWORD": os.getenv("DATABASE_PASSWORD", "aksio_password"),
            "HOST": os.getenv("DATABASE_HOST", "db"),
            "PORT": os.getenv("DATABASE_PORT", "5432"),
            "OPTIONS": {
                "application_name": "aksio-backend-test",
            },
            "TEST": {
                "NAME": "test_" + os.getenv("DATABASE_NAME", "aksio_db"),
            }
        }
    }
else:
    # Local testing with SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Password hashers (faster for testing)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Enable migrations for CI, disable for local testing
if os.getenv("DATABASE_HOST"):
    # CI environment - enable migrations
    pass
else:
    # Local testing - disable migrations for speed
    class DisableMigrations:
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return None

    MIGRATION_MODULES = DisableMigrations()

# Logging for testing
LOGGING["handlers"]["console"]["level"] = "CRITICAL" 
LOGGING["loggers"]["django"]["level"] = "CRITICAL"

# Disable caching for testing
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Media files for testing
MEDIA_ROOT = "/tmp/test_media"

# AI Configuration for testing
ENABLE_AI_FEATURES = False  # Disable AI features in tests
OPENAI_API_KEY = "test-key"  # Mock API key for tests