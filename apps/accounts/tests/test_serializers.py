"""
Test cases for accounts serializers.
"""

from django.test import TestCase
from django.contrib.auth import authenticate
from accounts.models import User, UserProfile
from accounts.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileDetailSerializer
)


class UserRegistrationSerializerTestCase(TestCase):
    """Test cases for UserRegistrationSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
    
    def test_valid_registration_data(self):
        """Test serializer with valid registration data."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('testpass123'))
        
        # Check that profile was created
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
    
    def test_password_mismatch(self):
        """Test validation with mismatched passwords."""
        data = self.valid_data.copy()
        data['password_confirm'] = 'differentpass'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Passwords do not match', str(serializer.errors))
    
    def test_invalid_email(self):
        """Test validation with invalid email."""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_weak_password(self):
        """Test validation with weak password."""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['password_confirm'] = '123'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_duplicate_email(self):
        """Test validation with duplicate email."""
        # Create first user
        User.objects.create_user(
            email='test@example.com',
            first_name='Existing',
            last_name='User',
            password='password123'
        )
        
        # Try to create second user with same email
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {'email': 'test@example.com'}
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        required_fields = ['first_name', 'last_name', 'password', 'password_confirm']
        for field in required_fields:
            self.assertIn(field, serializer.errors)


class UserLoginSerializerTestCase(TestCase):
    """Test cases for UserLoginSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_valid_login_data(self):
        """Test serializer with valid login credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        serializer = UserLoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
    
    def test_invalid_email(self):
        """Test validation with invalid email."""
        data = {
            'email': 'wrong@example.com',
            'password': 'testpass123'
        }
        
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Invalid email or password', str(serializer.errors))
    
    def test_invalid_password(self):
        """Test validation with invalid password."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Invalid email or password', str(serializer.errors))
    
    def test_inactive_user(self):
        """Test validation with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User account is disabled', str(serializer.errors))
    
    def test_missing_credentials(self):
        """Test validation with missing credentials."""
        # Missing password
        data = {'email': 'test@example.com'}
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Must include email and password', str(serializer.errors))
        
        # Missing email
        data = {'password': 'testpass123'}
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Must include email and password', str(serializer.errors))


class UserProfileSerializerTestCase(TestCase):
    """Test cases for UserProfileSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.user.is_verified = True
        self.user.save()
    
    def test_user_profile_serialization(self):
        """Test serializing user profile data."""
        serializer = UserProfileSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertTrue(data['is_verified'])
        self.assertIn('id', data)
        self.assertIn('date_joined', data)
    
    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated."""
        data = {
            'email': 'newemail@example.com',
            'first_name': 'Updated',
            'is_verified': False,
            'date_joined': '2023-01-01T00:00:00Z'
        }
        
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        
        # Check that updatable fields were updated
        self.assertEqual(updated_user.first_name, 'Updated')
        
        # Check that read-only fields were not updated
        self.assertEqual(updated_user.email, 'test@example.com')  # Should not change
        self.assertTrue(updated_user.is_verified)  # Should not change


class UserProfileDetailSerializerTestCase(TestCase):
    """Test cases for UserProfileDetailSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            bio='Test biography',
            timezone='America/New_York',
            language='es'
        )
    
    def test_detailed_profile_serialization(self):
        """Test serializing detailed user profile data."""
        serializer = UserProfileDetailSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertEqual(data['bio'], 'Test biography')
        self.assertEqual(data['timezone'], 'America/New_York')
        self.assertEqual(data['language'], 'es')
    
    def test_update_user_and_profile_data(self):
        """Test updating both user and profile data."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated biography',
            'timezone': 'Europe/London',
            'language': 'fr'
        }
        
        serializer = UserProfileDetailSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        
        # Check user fields
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        
        # Check profile fields
        updated_user.refresh_from_db()
        self.assertEqual(updated_user.profile.bio, 'Updated biography')
        self.assertEqual(updated_user.profile.timezone, 'Europe/London')
        self.assertEqual(updated_user.profile.language, 'fr')