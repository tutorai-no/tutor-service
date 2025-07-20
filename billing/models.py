from django.contrib.auth import get_user_model
from django.db import models

from core.models import BaseModel

User = get_user_model()


class Plan(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    billing_interval = models.CharField(
        max_length=20,
        choices=[
            ("month", "Monthly"),
            ("year", "Yearly"),
        ],
        default="month",
    )
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "billing_plan"
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}"


class Subscription(BaseModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
        ("trial", "Trial"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="subscriptions"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "billing_subscription"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"


class Payment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("refunded", "Refunded"),
        ],
        default="pending",
    )
    stripe_payment_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "billing_payment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency}"


class Invoice(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invoices")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="invoices"
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("paid", "Paid"),
            ("overdue", "Overdue"),
        ],
        default="draft",
    )
    due_date = models.DateField()

    class Meta:
        db_table = "billing_invoice"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.username}"
