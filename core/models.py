from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides timestamp fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft delete functionality.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """
        Soft delete the model instead of hard delete.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """
        Permanently delete the model.
        """
        super().delete(using=using, keep_parents=keep_parents)


class BaseModelWithSoftDelete(BaseModel, SoftDeleteModel):
    """
    Base model that combines BaseModel and SoftDeleteModel.
    """
    class Meta:
        abstract = True