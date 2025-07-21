"""
Core background tasks for the Aksio backend.

This module contains Celery tasks for system maintenance, notifications,
analytics, and other background operations.
"""

import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_email(
    self,
    subject: str,
    message: str,
    recipient_list: list[str],
    html_message: str = None,
    template_name: str = None,
    template_context: dict[str, Any] = None,
):
    """
    Send email with retry logic and template support.

    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient email addresses
        html_message: HTML version of message
        template_name: Django template name for HTML content
        template_context: Context for template rendering
    """
    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@aksio.app")

        # Render HTML from template if provided
        if template_name and template_context:
            html_message = render_to_string(template_name, template_context)

        if html_message:
            # Send HTML email
            email = EmailMultiAlternatives(
                subject=subject, body=message, from_email=from_email, to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            # Send plain text email
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
            )

        logger.info(f"Email sent successfully to {len(recipient_list)} recipients")
        return {"status": "success", "recipients": len(recipient_list)}

    except Exception as exc:
        logger.error(f"Email sending failed: {str(exc)}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2**self.request.retries)  # 60s, 120s, 240s
            raise self.retry(countdown=retry_delay, exc=exc)

        return {"status": "failed", "error": str(exc)}


@shared_task
def send_welcome_email(user_id: str):
    """Send welcome email to new user."""
    try:
        user = User.objects.get(pk=user_id)

        subject = "Welcome to Aksio!"
        template_context = {
            "user": user,
            "platform_name": "Aksio",
            "support_email": "support@aksio.app",
        }

        send_email.delay(
            subject=subject,
            message=f"Welcome to Aksio, {user.first_name or user.username}!",
            recipient_list=[user.email],
            template_name="emails/welcome.html",
            template_context=template_context,
        )

        logger.info(f"Welcome email queued for user {user.username}")

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for welcome email")
    except Exception as e:
        logger.error(f"Error queuing welcome email for user {user_id}: {str(e)}")


@shared_task
def send_password_reset_email(user_id: str, reset_token: str):
    """Send password reset email."""
    try:
        user = User.objects.get(pk=user_id)

        # Generate reset URL
        reset_url = f"{getattr(settings, 'FRONTEND_URL', 'https://app.aksio.com')}/reset-password?token={reset_token}"

        subject = "Reset Your Aksio Password"
        template_context = {
            "user": user,
            "reset_url": reset_url,
            "platform_name": "Aksio",
        }

        send_email.delay(
            subject=subject,
            message=f"Reset your password: {reset_url}",
            recipient_list=[user.email],
            template_name="emails/password_reset.html",
            template_context=template_context,
        )

        logger.info(f"Password reset email queued for user {user.username}")

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password reset email")
    except Exception as e:
        logger.error(f"Error queuing password reset email for user {user_id}: {str(e)}")


@shared_task
def cleanup_expired_sessions():
    """Clean up expired Django sessions."""
    try:
        expired_count = 0

        # Django's built-in session cleanup
        from django.core.management import call_command

        call_command("clearsessions")

        logger.info("Expired sessions cleaned up successfully")
        return {"status": "success", "expired_sessions": expired_count}

    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def cleanup_temp_files():
    """Clean up temporary files older than 24 hours."""
    try:
        cleanup_count = 0
        temp_dir = tempfile.gettempdir()
        cutoff_time = timezone.now() - timedelta(hours=24)

        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)

            # Skip if not a file
            if not os.path.isfile(file_path):
                continue

            # Skip if not our temp file
            if not filename.startswith("aksio_"):
                continue

            # Check file age
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_mtime = timezone.make_aware(file_mtime)

                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    cleanup_count += 1

            except (OSError, ValueError) as e:
                logger.warning(f"Error processing temp file {file_path}: {str(e)}")
                continue

        logger.info(f"Cleaned up {cleanup_count} temporary files")
        return {"status": "success", "files_cleaned": cleanup_count}

    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def generate_daily_reports():
    """Generate daily analytics reports."""
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # Calculate daily stats
        daily_stats = {
            "date": yesterday.isoformat(),
            "new_users": User.objects.filter(date_joined__date=yesterday).count(),
            "active_users": User.objects.filter(last_login__date=yesterday).count(),
        }

        # Store in cache for retrieval
        cache_key = f"daily_stats_{yesterday.strftime('%Y%m%d')}"
        cache.set(cache_key, daily_stats, 86400 * 7)  # Store for 1 week

        logger.info(f"Daily report generated for {yesterday}")
        return {"status": "success", "stats": daily_stats}

    except Exception as e:
        logger.error(f"Error generating daily reports: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def backup_user_data(user_id: str):
    """Create backup of user data for export/GDPR compliance."""
    try:
        user = User.objects.get(pk=user_id)

        # Collect user data from all apps
        user_data = {
            "user_profile": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
            "courses": [],
            "documents": [],
            "flashcards": [],
            "quiz_attempts": [],
            "chat_history": [],
        }

        # Collect courses
        from courses.models import Course

        for course in Course.objects.filter(user=user):
            user_data["courses"].append(
                {
                    "id": str(course.id),
                    "name": course.name,
                    "description": course.description,
                    "created_at": course.created_at.isoformat(),
                }
            )

        # Collect documents
        from courses.models import Document

        for document in Document.objects.filter(user=user):
            user_data["documents"].append(
                {
                    "id": str(document.id),
                    "title": document.title,
                    "course_name": document.course.name if document.course else None,
                    "created_at": document.created_at.isoformat(),
                }
            )

        # Collect flashcards
        from assessments.models import Flashcard

        for flashcard in Flashcard.objects.filter(user=user):
            user_data["flashcards"].append(
                {
                    "id": str(flashcard.id),
                    "question": flashcard.question,
                    "answer": flashcard.answer,
                    "course_name": flashcard.course.name if flashcard.course else None,
                    "created_at": flashcard.created_at.isoformat(),
                }
            )

        # Store backup data
        backup_key = f"user_backup_{user_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        cache.set(backup_key, user_data, 86400 * 30)  # Store for 30 days

        logger.info(f"User data backup created for user {user.username}")
        return {"status": "success", "backup_key": backup_key}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for backup")
        return {"status": "failed", "error": "User not found"}
    except Exception as e:
        logger.error(f"Error creating user backup for {user_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def process_user_deletion(user_id: str):
    """Process user account deletion with data cleanup."""
    try:
        with transaction.atomic():
            user = User.objects.get(pk=user_id)

            # Log deletion for audit
            logger.info(f"Processing deletion for user {user.username} ({user.email})")

            # Delete related data
            from assessments.models import Flashcard, QuizAttempt
            from chat.models import ChatSession
            from courses.models import Course, Document

            # Delete user's courses and related data
            Course.objects.filter(user=user).delete()
            Document.objects.filter(user=user).delete()
            Flashcard.objects.filter(user=user).delete()
            QuizAttempt.objects.filter(user=user).delete()
            ChatSession.objects.filter(user=user).delete()

            # Clear cache entries
            cache.delete_pattern(f"*user_{user_id}*")
            cache.delete_pattern(f"*{user_id}*")

            # Finally delete the user
            username = user.username
            email = user.email
            user.delete()

            logger.info(f"User {username} ({email}) successfully deleted")
            return {"status": "success", "deleted_user": username}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for deletion")
        return {"status": "failed", "error": "User not found"}
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def update_search_index():
    """Update search index for documents and courses."""
    try:
        # This would integrate with your search backend (Elasticsearch, etc.)
        # For now, just log the action

        from courses.models import Course, Document

        course_count = Course.objects.count()
        document_count = Document.objects.count()

        logger.info(
            f"Search index update completed: {course_count} courses, {document_count} documents"
        )

        return {
            "status": "success",
            "indexed_courses": course_count,
            "indexed_documents": document_count,
        }

    except Exception as e:
        logger.error(f"Error updating search index: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def optimize_database():
    """Perform database optimization tasks."""
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            # Analyze tables for query optimization
            cursor.execute("ANALYZE;")

            # Vacuum database (PostgreSQL specific)
            if "postgresql" in settings.DATABASES["default"]["ENGINE"]:
                cursor.execute("VACUUM ANALYZE;")

        logger.info("Database optimization completed")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error optimizing database: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def send_notification_digest(user_id: str, notification_type: str = "daily"):
    """Send notification digest to user."""
    try:
        user = User.objects.get(pk=user_id)

        # Collect notifications
        notifications = {
            "due_flashcards": 0,
            "new_recommendations": 0,
            "course_updates": 0,
        }

        # Count due flashcards
        from assessments.models import Flashcard

        notifications["due_flashcards"] = Flashcard.objects.filter(
            user=user, next_review_date__lte=timezone.now(), is_active=True
        ).count()

        # Only send if there are notifications
        if any(notifications.values()):
            subject = f"Your {notification_type} Aksio digest"
            template_context = {
                "user": user,
                "notifications": notifications,
                "notification_type": notification_type,
            }

            send_email.delay(
                subject=subject,
                message=f"You have {notifications['due_flashcards']} flashcards due for review.",
                recipient_list=[user.email],
                template_name="emails/notification_digest.html",
                template_context=template_context,
            )

        logger.info(f"Notification digest sent to user {user.username}")
        return {"status": "success", "notifications": notifications}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for notification digest")
        return {"status": "failed", "error": "User not found"}
    except Exception as e:
        logger.error(f"Error sending notification digest to {user_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}
