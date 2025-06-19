from django.db import models
from accounts.models import CustomUser


class CheckoutSessionRecord(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        help_text="The user who initiated the checkout.",
    )
    stripe_customer_id = models.CharField(max_length=255)
    stripe_checkout_session_id = models.CharField(max_length=255)
    stripe_price_id = models.CharField(max_length=255)
    has_access = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
