"""
Test cases for accounts models.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import User, UserProfile


class UserModelTestCase(TestCase):
    """Test cases for the User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
    
    def test_create_user_with_email(self):
        """Test creating a user with email."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password='adminpass123'
        )
        
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
    
    def test_user_string_representation(self):
        """Test User model string representation."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_full_name_property(self):
        """Test full_name property."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'Test User')
        
        # Test with empty names
        user.first_name = ''
        user.last_name = ''
        user.save()
        self.assertEqual(user.full_name, 'test@example.com')
    
    def test_get_short_name_method(self):
        """Test get_short_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), 'Test')
        
        # Test with empty first name
        user.first_name = ''
        user.save()
        self.assertEqual(user.get_short_name(), 'test@example.com')
    
    def test_email_unique_constraint(self):
        """Test that email must be unique."""
        User.objects.create_user(**self.user_data)
        
        # Try to create another user with same email
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='test@example.com',  # Same email
                first_name='Another',
                last_name='User',
                password='password123'
            )
    
    def test_email_case_insensitive(self):
        """Test email case handling."""
        user = User.objects.create_user(
            email='Test@Example.COM',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        # Email should be stored as entered
        self.assertEqual(user.email, 'Test@Example.COM')
    
    def test_timestamps_auto_populated(self):
        """Test that timestamp fields are auto-populated."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        self.assertEqual(user.created_at, user.updated_at)


class UserProfileModelTestCase(TestCase):
    """Test cases for the UserProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_create_user_profile(self):
        """Test creating a user profile."""
        profile = UserProfile.objects.create(
            user=self.user,
            bio='Test biography',
            timezone='America/New_York',
            language='en'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, 'Test biography')
        self.assertEqual(profile.timezone, 'America/New_York')
        self.assertEqual(profile.language, 'en')
    
    def test_user_profile_string_representation(self):
        """Test UserProfile model string representation."""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), 'test@example.com - Profile')
    
    def test_user_profile_default_values(self):
        """Test UserProfile model default values."""
        profile = UserProfile.objects.create(user=self.user)
        
        self.assertEqual(profile.bio, '')
        self.assertEqual(profile.timezone, 'UTC')
        self.assertEqual(profile.language, 'en')
    
    def test_user_profile_one_to_one_relationship(self):
        """Test one-to-one relationship with User."""
        profile = UserProfile.objects.create(user=self.user)
        
        # Access profile through user
        self.assertEqual(self.user.profile, profile)
        
        # Ensure only one profile per user
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)
    
    def test_user_profile_cascade_delete(self):
        """Test that profile is deleted when user is deleted."""
        profile = UserProfile.objects.create(user=self.user)
        profile_id = profile.id
        
        # Delete user
        self.user.delete()
        
        # Profile should be deleted too
        with self.assertRaises(UserProfile.DoesNotExist):
            UserProfile.objects.get(id=profile_id)
    
    def test_user_profile_timestamps(self):
        """Test that timestamp fields work correctly."""
        profile = UserProfile.objects.create(user=self.user)
        
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        
        # Update profile and check timestamps
        original_updated_at = profile.updated_at
        profile.bio = 'Updated bio'
        profile.save()
        
        self.assertGreater(profile.updated_at, original_updated_at)