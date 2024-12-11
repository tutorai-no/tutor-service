import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


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
