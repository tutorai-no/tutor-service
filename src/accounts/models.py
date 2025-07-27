import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime


class Subscription(models.Model):
    """
    Model representing different subscription tiers.
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)  # e.g., 9999.99
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """
    Custom user model with UUID as primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscribers",
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True, default="N/A")
    date_of_birth = models.DateField(blank=True, null=True)

    heard_about_us = models.CharField(max_length=100, blank=True, null=True)
    other_heard_about_us = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username


class SubscriptionHistory(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="subscription_history"
    )
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.subscription.name}"


class Streak(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="streak"
    )
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(auto_now=True)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.current_streak}"

    def check_if_broken_streak(self):
        if (datetime.now().date() - self.end_date).total_seconds() > 36 * 60 * 60:
            self.current_streak = 0
            self.start_date = datetime.now().date()
            self.end_date = datetime.now().date()
            self.save()

    def increment_streak(self):
        today_date = datetime.now().date()
        if self.current_streak == 0:
            self.current_streak = 1
            self.end_date = today_date
            self.save()
            return

        if not (
            today_date.month == self.end_date.month
            and today_date.year == self.end_date.year
        ):
            self.current_streak += 1
            self.end_date = today_date
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
            self.save()


class Activity(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"


class Feedback(models.Model):
    """
    Model representing feedback.
    """

    # UUID for feedback
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="feedbacks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    feedback_type = models.CharField(max_length=100)
    feedback_text = models.TextField()
    feedback_screenshot = models.ImageField(
        upload_to="feedback_screenshots", blank=True, null=True
    )

    def __str__(self):
        return f"{self.feedback_type} - {self.user.username}"


class UserApplication(models.Model):
    """
    Model representing a user's request to access TutorAI.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    heard_about_us = models.CharField(max_length=100)
    other_heard_about_us = models.CharField(max_length=255, blank=True, null=True)
    inspiration = models.TextField(max_length=250)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    review_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.status}"
