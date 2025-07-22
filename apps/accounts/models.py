"""
User models for the accounts app.
"""
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from core.models import TimestampedModel


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular User with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        # Keep the original email casing as per test requirements
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimestampedModel):
    """
    Custom user model using email as the unique identifier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Email address used for login"
    )
    
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """
        Return the full name of the user.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """
        Return the short name for the user.
        """
        return self.first_name if self.first_name else self.email


class UserProfile(TimestampedModel):
    """
    Extended user profile information.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True,
        help_text="Short biography"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's timezone preference"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="Preferred language code"
    )
    
    class Meta:
        db_table = 'accounts_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email} - Profile"