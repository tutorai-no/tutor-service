"""
Celery configuration for Aksio backend.

This module configures Celery for background task processing including
document processing, AI content generation, and notification tasks.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aksio.settings")

app = Celery("aksio")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Task routing
    task_routes={
        "core.tasks.send_email": {"queue": "email"},
        "assessments.tasks.*": {"queue": "ai_processing"},
        "document_processing.tasks.*": {"queue": "document_processing"},
        "learning.tasks.*": {"queue": "analytics"},
        "chat.tasks.*": {"queue": "ai_processing"},
    },
    # Task time limits
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    # Task retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Results backend
    result_expires=3600,  # 1 hour
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task acknowledgment
    task_acks_late=True,
    worker_disable_rate_limits=False,
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "core.tasks.cleanup_expired_sessions",
            "schedule": 3600.0,  # Every hour
        },
        "update-user-analytics": {
            "task": "learning.tasks.update_user_analytics",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "process-spaced-repetition": {
            "task": "assessments.tasks.process_spaced_repetition_updates",
            "schedule": 900.0,  # Every 15 minutes
        },
        "generate-daily-reports": {
            "task": "core.tasks.generate_daily_reports",
            "schedule": {
                "hour": 6,  # 6 AM UTC
                "minute": 0,
            },
        },
        "cleanup-temp-files": {
            "task": "core.tasks.cleanup_temp_files",
            "schedule": 7200.0,  # Every 2 hours
        },
    },
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f"Request: {self.request!r}")
    return "Debug task completed successfully"
