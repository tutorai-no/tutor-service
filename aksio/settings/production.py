"""
Production settings for aksio project.
"""

from .base import *

# Production mode
DEBUG = False

ALLOWED_HOSTS = [
    os.getenv("ALLOWED_HOSTS", "").split(","),  # Set via environment
    "backend.aksio.app",
    "api.aksio.app",
]

# Flatten ALLOWED_HOSTS if it's a nested list
ALLOWED_HOSTS = [host.strip() for sublist in ALLOWED_HOSTS for host in (sublist if isinstance(sublist, list) else [sublist]) if host.strip()]

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://aksio.app",
    "https://www.aksio.app",
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

# Google Cloud SQL Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),  # Cloud SQL private IP
        "PORT": os.getenv("DATABASE_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "require",
        },
        "CONN_MAX_AGE": 60,
    }
}

# Google Cloud Storage for static/media files
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GS_DEFAULT_ACL = "publicRead"

# Production Neo4j (you'll need to set this up)
NEO4J_URI = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Production email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Production logging - less verbose
LOGGING["handlers"]["console"]["level"] = "WARNING"
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["django.db.backends"]["level"] = "ERROR"
LOGGING["loggers"]["aksio"]["level"] = "INFO"

# Add file logging for production
LOGGING["handlers"]["file"] = {
    "level": "INFO",
    "class": "logging.FileHandler", 
    "filename": "/tmp/aksio.log",
    "formatter": "verbose",
}

# Add file handler to all loggers
for logger_name in ["django", "aksio"] + [app for app in INSTALLED_APPS if not app.startswith("django")]:
    if logger_name in LOGGING["loggers"]:
        LOGGING["loggers"][logger_name]["handlers"].append("file")