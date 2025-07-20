import hashlib
import uuid
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class with configurable page size.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def generate_unique_slug(base_slug: str, model_class, slug_field: str = "slug") -> str:
    """
    Generate a unique slug for a model instance.

    Args:
        base_slug: Base slug to make unique
        model_class: Django model class
        slug_field: Field name for the slug

    Returns:
        Unique slug string
    """
    original_slug = base_slug
    counter = 1

    while model_class.objects.filter(**{slug_field: base_slug}).exists():
        base_slug = f"{original_slug}-{counter}"
        counter += 1

    return base_slug


def send_notification_email(
    subject: str,
    template_name: str,
    context: dict[str, Any],
    recipient_list: list[str],
    from_email: str | None = None,
) -> bool:
    """
    Send a notification email using a template.

    Args:
        subject: Email subject
        template_name: Template name (without .html)
        context: Template context dictionary
        recipient_list: List of recipient email addresses
        from_email: Optional from email address

    Returns:
        True if email was sent successfully
    """
    try:
        html_message = render_to_string(f"emails/{template_name}.html", context)
        text_message = render_to_string(f"emails/{template_name}.txt", context)

        send_mail(
            subject=subject,
            message=text_message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        return True
    except Exception as e:
        # Log the error
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send email: {e}")
        return False


def hash_string(input_string: str) -> str:
    """
    Generate a SHA-256 hash of a string.

    Args:
        input_string: String to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(input_string.encode()).hexdigest()


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        Random API key string
    """
    return str(uuid.uuid4()).replace("-", "")


def format_duration(seconds: int) -> str:
    """
    Format seconds into a human-readable duration string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{hours}h"


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Calculate estimated reading time for text.

    Args:
        text: Text to analyze
        words_per_minute: Reading speed in words per minute

    Returns:
        Estimated reading time in minutes
    """
    word_count = len(text.split())
    reading_time = word_count / words_per_minute
    return max(1, int(reading_time))  # Minimum 1 minute


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, "_")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1)
        filename = name[: 255 - len(ext) - 1] + "." + ext

    return filename


def get_client_ip(request) -> str:
    """
    Get the client IP address from a request.

    Args:
        request: Django request object

    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def is_business_hours() -> bool:
    """
    Check if current time is within business hours (9 AM - 5 PM UTC).

    Returns:
        True if within business hours
    """
    current_time = timezone.now()
    current_hour = current_time.hour

    # Business hours: 9 AM to 5 PM UTC
    return 9 <= current_hour < 17
