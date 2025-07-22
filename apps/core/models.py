from django.db import models
import uuid

class TimestampedModel(models.Model):
    """Base model with automatic timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class UUIDModel(models.Model):
    """Base model with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True

class UserOwnedModel(models.Model):
    """Base model for user-owned content."""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    class Meta:
        abstract = True