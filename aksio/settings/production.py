"""
Production settings for aksio project.
"""

import os
from .base import *

# Production mode
DEBUG = False

# Security - Get secret key from environment
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # Required, will fail if not set

# Allowed hosts configuration
ALLOWED_HOSTS = []
# Add allowed hosts from environment variable
if os.getenv("DJANGO_ALLOWED_HOSTS"):
    ALLOWED_HOSTS.extend(
        host.strip() 
        for host in os.getenv("DJANGO_ALLOWED_HOSTS").split(",") 
        if host.strip()
    )
# Add Cloud Run service URL
ALLOWED_HOSTS.extend([
    ".run.app",  # Default Cloud Run domain
    "backend.aksio.app",
    "api.aksio.app",
    "aksio.app",
    "www.aksio.app",
    "127.0.0.1",  # Cloud Run health checks
    "localhost",  # Alternative health check host
])

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://aksio.app",
    "https://www.aksio.app",
    "http://localhost:3000",  # For local frontend development
]
CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = [
    "https://aksio.app",
    "https://www.aksio.app", 
    "https://backend.aksio.app",
    "https://api.aksio.app",
]

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Force HTTPS for Cloud Run behind proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Google Cloud SQL Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "disable",  # Cloud SQL proxy handles SSL
        },
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}

# Static files - Use Whitenoise for now (simpler than GCS for starting)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Add Whitenoise middleware (right after SecurityMiddleware)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Media files - Google Cloud Storage (when you need it)
if os.getenv("GCS_BUCKET_NAME"):
    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    GS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    GS_DEFAULT_ACL = "publicRead"
    GS_QUERYSTRING_AUTH = False
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
else:
    # Local media storage fallback
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Neo4j settings (optional for now)
if os.getenv("NEO4J_URL"):
    NEO4J_URI = os.getenv("NEO4J_URL")
    NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@aksio.app")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Production logging - Cloud Run logs to stdout
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Reduce SQL query logging
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",  # Only log errors
            "propagate": False,
        },
        "aksio": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Cache configuration (optional, using database for now)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# API settings
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",  # Remove browsable API in production
]

# Remove debug toolbar
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]