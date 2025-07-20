from uuid import uuid4

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.utils import timezone

from .models import (
    User,
    UserActivity,
    UserApplication,
    UserFeedback,
    UserProfile,
    UserStreak,
)

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "university",
        "study_level",
        "is_verified",
        "is_staff",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "is_staff",
        "is_active",
        "is_verified",
        "study_level",
        "university",
        "language",
        "created_at",
    ]
    search_fields = ["username", "email", "first_name", "last_name", "university"]
    readonly_fields = ["id", "created_at", "updated_at", "last_login", "date_joined"]
    ordering = ["-created_at"]

    fieldsets = UserAdmin.fieldsets + (
        (
            "Profile Information",
            {
                "fields": (
                    "phone_number",
                    "avatar",
                    "university",
                    "study_level",
                    "study_year",
                    "field_of_study",
                )
            },
        ),
        (
            "Preferences",
            {
                "fields": (
                    "timezone",
                    "language",
                    "preferred_study_time",
                    "daily_study_goal_minutes",
                )
            },
        ),
        ("Marketing", {"fields": ("acquisition_source", "acquisition_details")}),
        (
            "Status",
            {"fields": ("is_verified", "last_active_at", "onboarding_completed")},
        ),
        ("Integration", {"fields": ("stripe_customer_id",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Profile Information",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "university",
                    "study_level",
                )
            },
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "study_style", "difficulty_preference", "created_at"]
    list_filter = ["study_style", "difficulty_preference", "email_notifications"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Profile", {"fields": ("user", "bio", "learning_goals")}),
        ("Study Preferences", {"fields": ("study_style", "difficulty_preference")}),
        (
            "Notification Settings",
            {
                "fields": (
                    "email_notifications",
                    "study_reminders",
                    "progress_reports",
                    "marketing_emails",
                )
            },
        ),
        (
            "Privacy Settings",
            {"fields": ("profile_public", "show_progress", "show_study_time")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "activity_type",
        "resource_type",
        "device_type",
        "created_at",
    ]
    list_filter = ["activity_type", "resource_type", "device_type", "created_at"]
    search_fields = ["user__username", "activity_type", "resource_type"]
    readonly_fields = ["id", "created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Activity", {"fields": ("user", "activity_type", "session_id")}),
        ("Resource Context", {"fields": ("resource_type", "resource_id")}),
        ("Performance", {"fields": ("duration_seconds", "metadata")}),
        ("Device Information", {"fields": ("ip_address", "user_agent", "device_type")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "current_streak_days",
        "longest_streak_days",
        "last_activity_date",
        "total_study_sessions",
    ]
    list_filter = ["current_streak_days", "longest_streak_days"]
    search_fields = ["user__username"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Streak Information",
            {"fields": ("user", "current_streak_days", "longest_streak_days")},
        ),
        ("Timing", {"fields": ("current_streak_start", "last_activity_date")}),
        ("Statistics", {"fields": ("total_study_days", "total_study_sessions")}),
        ("Milestones", {"fields": ("streak_milestones_achieved",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "feedback_type",
        "status",
        "priority",
        "satisfaction_rating",
        "created_at",
    ]
    list_filter = [
        "feedback_type",
        "status",
        "priority",
        "satisfaction_rating",
        "created_at",
    ]
    search_fields = ["title", "description", "user__username"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Feedback", {"fields": ("user", "feedback_type", "title", "description")}),
        ("Attachments", {"fields": ("screenshot",)}),
        ("Context", {"fields": ("page_url", "browser_info")}),
        ("Management", {"fields": ("status", "priority")}),
        (
            "Admin Response",
            {"fields": ("admin_response", "resolved_at", "resolved_by")},
        ),
        ("Satisfaction", {"fields": ("satisfaction_rating",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(UserApplication)
class UserApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "email",
        "full_name",
        "university",
        "acquisition_source",
        "status",
        "created_at",
    ]
    list_filter = ["status", "acquisition_source", "study_level", "created_at"]
    search_fields = ["username", "email", "first_name", "last_name", "university"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at", "full_name"]

    actions = ["approve_applications", "reject_applications"]

    fieldsets = (
        ("Application Details", {"fields": ("username", "email", "phone_number")}),
        ("Personal Information", {"fields": ("first_name", "last_name", "full_name")}),
        ("Background", {"fields": ("university", "study_level", "field_of_study")}),
        (
            "Acquisition",
            {"fields": ("acquisition_source", "acquisition_details", "motivation")},
        ),
        ("Status", {"fields": ("status",)}),
        ("Review", {"fields": ("reviewed_by", "review_notes", "reviewed_at")}),
        ("User Creation", {"fields": ("created_user",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def approve_applications(self, request, queryset):
        """Approve selected applications and create user accounts."""
        approved_count = 0

        for application in queryset.filter(status="pending"):
            try:
                # Generate temporary password
                password = str(uuid4().hex[:18])

                # Create user account
                user = User.objects.create_user(
                    username=application.username,
                    email=application.email,
                    password=password,
                    first_name=application.first_name,
                    last_name=application.last_name,
                    phone_number=application.phone_number,
                    university=application.university,
                    study_level=application.study_level,
                    field_of_study=application.field_of_study,
                    acquisition_source=application.acquisition_source,
                    acquisition_details=application.acquisition_details,
                )

                # Update application
                application.status = "approved"
                application.reviewed_by = request.user
                application.reviewed_at = timezone.now()
                application.created_user = user
                application.save()

                # Send approval email
                self.send_approval_email(application, password)
                approved_count += 1

            except Exception as e:
                self.message_user(
                    request,
                    f"Error approving {application.username}: {str(e)}",
                    level="ERROR",
                )

        if approved_count > 0:
            self.message_user(
                request, f"Successfully approved {approved_count} application(s)."
            )

    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        """Reject selected applications."""
        rejected_count = 0

        for application in queryset.filter(status="pending"):
            application.status = "rejected"
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()

            # Send rejection email
            self.send_rejection_email(application)
            rejected_count += 1

        if rejected_count > 0:
            self.message_user(
                request, f"Successfully rejected {rejected_count} application(s)."
            )

    reject_applications.short_description = "Reject selected applications"

    def send_approval_email(self, application, password):
        """Send approval email to applicant."""
        subject = "Your Aksio Access Request Approved"
        message = (
            f"Hello {application.first_name},\n\n"
            "Congratulations! Your request to access Aksio has been approved.\n\n"
            "You can now log in using your credentials:\n\n"
            f"Username: {application.username}\n"
            f"Temporary password: {password}\n\n"
            "Please log in and change your password as soon as possible.\n\n"
            "Welcome to Aksio!\n\n"
            "Best regards,\n"
            "The Aksio Team"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail the approval process
            pass

    def send_rejection_email(self, application):
        """Send rejection email to applicant."""
        subject = "Your Aksio Access Request"
        message = (
            f"Hello {application.first_name},\n\n"
            "Thank you for your interest in Aksio.\n\n"
            "After careful consideration, we are unable to approve your access request at this time.\n\n"
            "If you have any questions, please contact our support team.\n\n"
            "Best regards,\n"
            "The Aksio Team"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail the rejection process
            pass
