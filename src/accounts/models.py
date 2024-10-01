# accounts/models.py

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
    Custom user model extending AbstractUser to include subscription.
    """
    email = models.EmailField(unique=True)  # Enforce unique emails
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscribers'
    )
    # Add any additional fields you need here

    def __str__(self):
        return self.username
class SubscriptionHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscription_history')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)  # When the subscription ended or will end

    def __str__(self):
        return f"{self.user.username} - {self.subscription.name}"

