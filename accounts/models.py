import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    """Custom user model with enhanced features."""

    # Core identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    # Profile information
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    # University information
    university = models.CharField(max_length=200, blank=True, null=True)
    study_level = models.CharField(
        max_length=50,
        choices=[
            ("bachelor", "Bachelor"),
            ("master", "Master"),
            ("phd", "PhD"),
            ("other", "Other"),
        ],
        blank=True,
        null=True,
    )
    study_year = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    field_of_study = models.CharField(max_length=200, blank=True, null=True)

    # User preferences
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(
        max_length=10,
        default="en",
        choices=[
            ("en", "English"),
            ("no", "Norwegian"),
            ("sv", "Swedish"),
            ("da", "Danish"),
        ],
    )

    # Learning preferences
    preferred_study_time = models.CharField(
        max_length=20,
        choices=[
            ("morning", "Morning (6-12)"),
            ("afternoon", "Afternoon (12-18)"),
            ("evening", "Evening (18-24)"),
            ("night", "Night (24-6)"),
        ],
        blank=True,
        null=True,
    )
    daily_study_goal_minutes = models.PositiveIntegerField(
        default=60, null=True, blank=True
    )

    # Marketing and acquisition
    acquisition_source = models.CharField(
        max_length=100, blank=True, null=True, help_text="How they heard about us"
    )
    acquisition_details = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Additional details about acquisition",
    )

    # Status and activity
    is_verified = models.BooleanField(default=False)
    last_active_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed = models.BooleanField(default=False)

    # Future Stripe integration fields (placeholder)
    stripe_customer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Stripe Customer ID (future integration)",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["university", "study_level"]),
            models.Index(fields=["is_active", "is_verified"]),
            models.Index(fields=["last_active_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_premium_user(self):
        """Check if user has premium features (placeholder for future billing)."""
        # TODO: Implement with Stripe subscription logic
        return False


class UserProfile(models.Model):
    """Extended user profile information."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Bio and description
    bio = models.TextField(max_length=500, blank=True, null=True)
    learning_goals = models.TextField(max_length=1000, blank=True, null=True)

    # Study preferences
    study_style = models.CharField(
        max_length=20,
        choices=[
            ("visual", "Visual"),
            ("auditory", "Auditory"),
            ("kinesthetic", "Kinesthetic"),
            ("reading", "Reading/Writing"),
            ("mixed", "Mixed"),
        ],
        default="mixed",
    )

    difficulty_preference = models.CharField(
        max_length=20,
        choices=[
            ("easy", "Start Easy"),
            ("medium", "Balanced"),
            ("hard", "Challenge Me"),
            ("adaptive", "Adaptive"),
        ],
        default="adaptive",
    )

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    study_reminders = models.BooleanField(default=True)
    progress_reports = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)

    # Privacy settings
    profile_public = models.BooleanField(default=False)
    show_progress = models.BooleanField(default=True)
    show_study_time = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"


class UserActivity(models.Model):
    """Track user activities for analytics."""

    ACTIVITY_TYPES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("course_create", "Course Created"),
        ("document_upload", "Document Upload"),
        ("study_session_start", "Study Session Started"),
        ("study_session_end", "Study Session Ended"),
        ("quiz_complete", "Quiz Completed"),
        ("flashcard_review", "Flashcard Review"),
        ("chat_message", "Chat Message"),
        ("goal_achieved", "Goal Achieved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")

    # Activity details
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    session_id = models.UUIDField(
        help_text="Frontend session ID for grouping activities"
    )

    # Context information
    resource_type = models.CharField(
        max_length=50, blank=True, help_text="e.g., course, quiz, flashcard"
    )
    resource_id = models.UUIDField(
        null=True, blank=True, help_text="ID of the resource"
    )

    # Performance and metadata
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional activity data"
    )

    # Device and location info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=[
            ("desktop", "Desktop"),
            ("tablet", "Tablet"),
            ("mobile", "Mobile"),
            ("unknown", "Unknown"),
        ],
        default="unknown",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "activity_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["session_id"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"


class UserStreak(models.Model):
    """Track user learning streaks and consistency."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="streak")

    # Current streak data
    current_streak_days = models.PositiveIntegerField(default=0)
    longest_streak_days = models.PositiveIntegerField(default=0)

    # Streak timing
    current_streak_start = models.DateField(auto_now_add=True)
    last_activity_date = models.DateField(auto_now=True)

    # Overall statistics
    total_study_days = models.PositiveIntegerField(default=0)
    total_study_sessions = models.PositiveIntegerField(default=0)

    # Milestone tracking
    streak_milestones_achieved = models.JSONField(
        default=list, help_text="List of streak milestones reached (e.g., [7, 14, 30])"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_streaks"

    def __str__(self):
        return f"{self.user.username} - {self.current_streak_days} days"

    def is_streak_active(self):
        """Check if current streak is still active."""
        from datetime import date, timedelta

        return self.last_activity_date >= date.today() - timedelta(days=1)

    def check_if_broken_streak(self):
        """
        Sophisticated streak checking with 36-hour grace period.
        Migrated from src/accounts/models.py
        """
        from datetime import datetime, timedelta

        from django.utils import timezone

        now = timezone.now()
        last_activity_datetime = timezone.make_aware(
            datetime.combine(self.last_activity_date, datetime.min.time())
        )

        # 36-hour grace period (more forgiving than 24 hours)
        grace_period = timedelta(hours=36)

        if (now - last_activity_datetime) > grace_period:
            # Streak is broken
            if self.current_streak_days > self.longest_streak_days:
                self.longest_streak_days = self.current_streak_days

            self.current_streak_days = 0
            self.current_streak_start = now.date()
            self.last_activity_date = now.date()
            # Don't save here - let the calling method handle saving
            return True  # Streak was broken

        return False  # Streak intact

    def increment_streak(self):
        """
        Advanced streak increment logic.
        Migrated and enhanced from src/accounts/models.py
        """
        from django.utils import timezone

        today = timezone.now().date()
        study_activity_today = False

        # Check if streak should be broken first
        if self.check_if_broken_streak():
            # Streak was just broken, so we start fresh
            self.current_streak_days = 1
            self.current_streak_start = today
            self.last_activity_date = today
            study_activity_today = True
        else:
            # Only increment if this is a new day
            if self.last_activity_date < today:
                self.current_streak_days += 1
                self.last_activity_date = today
                study_activity_today = True

                # Update longest streak if needed
                if self.current_streak_days > self.longest_streak_days:
                    self.longest_streak_days = self.current_streak_days

                # Check for milestone achievements
                milestones = [7, 14, 30, 60, 90, 180, 365]
                for milestone in milestones:
                    if (
                        self.current_streak_days == milestone
                        and milestone not in self.streak_milestones_achieved
                    ):
                        self.streak_milestones_achieved.append(milestone)

        # Only update total study tracking if there was actual activity today
        if study_activity_today:
            self.total_study_days += 1

        # Always increment session count since this method represents a study session
        self.total_study_sessions += 1

        self.save()
        return self.current_streak_days


class UserFeedback(models.Model):
    """User feedback and support requests."""

    FEEDBACK_TYPES = [
        ("bug_report", "Bug Report"),
        ("feature_request", "Feature Request"),
        ("general_feedback", "General Feedback"),
        ("support_request", "Support Request"),
        ("complaint", "Complaint"),
        ("praise", "Praise"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feedback")

    # Feedback content
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Attachments
    screenshot = models.ImageField(
        upload_to="feedback/screenshots/", blank=True, null=True
    )

    # Context information
    page_url = models.URLField(blank=True, help_text="Page where feedback was given")
    browser_info = models.TextField(blank=True)

    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )

    # Admin response
    admin_response = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_feedback",
    )

    # Satisfaction rating (1-5 stars)
    satisfaction_rating = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_feedback"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["feedback_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.title}"


class UserApplication(models.Model):
    """Applications for platform access (if using waitlist/approval system)."""

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Application details
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Background information
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    university = models.CharField(max_length=200, blank=True, null=True)
    study_level = models.CharField(max_length=50, blank=True, null=True)
    field_of_study = models.CharField(max_length=200, blank=True, null=True)

    # Acquisition and motivation
    acquisition_source = models.CharField(max_length=100, blank=True, null=True)
    acquisition_details = models.CharField(max_length=255, blank=True, null=True)
    motivation = models.TextField(
        max_length=500, blank=True, null=True, help_text="Why they want to use Aksio"
    )

    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Review information
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # User creation (after approval)
    created_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_applications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["email"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.username} - {self.get_status_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
