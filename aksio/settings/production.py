"""
Production settings for aksio project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    "backend.aksio.app",
    "api.aksio.app",
    # Add your production domain here
]

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://aksio.app",
    "https://www.aksio.app",
    # Add your frontend domain here
]

CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = [
    "https://aksio.app",
    "https://www.aksio.app",
    "https://backend.aksio.app",
    "https://api.aksio.app",
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Database configuration for production (Google Cloud SQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# Static files (Google Cloud Storage)
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# Cache configuration
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    # Use Redis if available (recommended for production)
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "aksio",
            "TIMEOUT": 300,  # 5 minutes default timeout
        }
    }
else:
    # Fallback to local memory cache (not recommended for production)
    # This is only suitable for single-instance deployments
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "aksio-cache",
        }
    }

# Session configuration
if REDIS_URL:
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

# Logging for production
LOGGING["handlers"]["console"]["level"] = "WARNING"
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["django.db.backends"]["level"] = "ERROR"
