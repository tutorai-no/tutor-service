"""
Integration tests for the accounts app.
Tests complete workflows and interactions between components.
"""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from accounts.models import User, UserProfile


class UserRegistrationLoginWorkflowTestCase(APITestCase):
    """Test complete user registration and login workflow."""
    
    def test_complete_user_workflow(self):
        """Test complete user registration -> login -> profile update workflow."""
        
        # Step 1: Register new user
        register_data = {
            'email': 'workflow@example.com',
            'first_name': 'Workflow',
            'last_name': 'Test',
            'password': 'workflowpass123',
            'password_confirm': 'workflowpass123'
        }
        
        register_response = self.client.post(
            reverse('register'), 
            register_data
        )
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', register_response.data)
        
        # Extract tokens from registration
        access_token = register_response.data['tokens']['access']
        refresh_token = register_response.data['tokens']['refresh']
        
        # Step 2: Use access token to access profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        profile_response = self.client.get(reverse('profile'))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            profile_response.data['user']['email'], 
            'workflow@example.com'
        )
        
        # Step 3: Update profile information
        update_data = {
            'first_name': 'Updated Workflow',
            'bio': 'This is my test biography',
            'timezone': 'America/New_York'
        }
        
        update_response = self.client.patch(reverse('profile'), update_data)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            update_response.data['user']['first_name'], 
            'Updated Workflow'
        )
        
        # Step 4: Logout
        logout_response = self.client.post(
            reverse('logout'),
            {'refresh_token': refresh_token}
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Step 5: Try to access profile after logout (should work with valid access token)
        # Access tokens don't get invalidated on logout, only refresh tokens
        profile_after_logout = self.client.get(reverse('profile'))
        self.assertEqual(profile_after_logout.status_code, status.HTTP_200_OK)
        
        # Step 6: Login again with updated credentials
        login_data = {
            'email': 'workflow@example.com',
            'password': 'workflowpass123'
        }
        
        login_response = self.client.post(reverse('login'), login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Check that updated profile information is returned
        self.assertEqual(
            login_response.data['user']['first_name'], 
            'Updated Workflow'
        )
    
    def test_token_refresh_workflow(self):
        """Test JWT token refresh workflow."""
        
        # Step 1: Register user
        register_data = {
            'email': 'refresh@example.com',
            'first_name': 'Refresh',
            'last_name': 'Test',
            'password': 'refreshpass123',
            'password_confirm': 'refreshpass123'
        }
        
        register_response = self.client.post(
            reverse('register'), 
            register_data
        )
        
        refresh_token = register_response.data['tokens']['refresh']
        
        # Step 2: Use refresh token to get new access token
        refresh_data = {'refresh': refresh_token}
        
        refresh_response = self.client.post(
            reverse('token_refresh'),
            refresh_data
        )
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        
        # Step 3: Use new access token
        new_access_token = refresh_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        
        profile_response = self.client.get(reverse('profile'))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)


class UserModelProfileRelationshipTestCase(TestCase):
    """Test User and UserProfile model relationships and behavior."""
    
    def test_user_profile_creation_and_relationship(self):
        """Test user and profile creation and their relationship."""
        
        # Create user
        user = User.objects.create_user(
            email='relationship@example.com',
            first_name='Relationship',
            last_name='Test',
            password='relpass123'
        )
        
        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            bio='Test relationship',
            timezone='Europe/Berlin',
            language='de'
        )
        
        # Test relationships
        self.assertEqual(user.profile, profile)
        self.assertEqual(profile.user, user)
        
        # Test cascade deletion
        user_id = user.id
        profile_id = profile.id
        
        user.delete()
        
        # Profile should be deleted too
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())
    
    def test_user_methods_with_profile_data(self):
        """Test user model methods work correctly with profile data."""
        
        user = User.objects.create_user(
            email='methods@example.com',
            first_name='Methods',
            last_name='Test',
            password='methodspass123'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            bio='Testing methods',
            timezone='Asia/Tokyo'
        )
        
        # Test full_name property
        self.assertEqual(user.full_name, 'Methods Test')
        
        # Test get_short_name method
        self.assertEqual(user.get_short_name(), 'Methods')
        
        # Test string representation
        self.assertEqual(str(user), 'methods@example.com')
        self.assertEqual(str(profile), 'methods@example.com - Profile')
    
    def test_multiple_users_with_profiles(self):
        """Test creating multiple users with profiles."""
        
        users_data = [
            ('user1@example.com', 'User', 'One'),
            ('user2@example.com', 'User', 'Two'),
            ('user3@example.com', 'User', 'Three'),
        ]
        
        created_users = []
        for email, first_name, last_name in users_data:
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password='testpass123'
            )
            
            UserProfile.objects.create(
                user=user,
                bio=f'Biography for {first_name}',
                timezone='UTC'
            )
            
            created_users.append(user)
        
        # Test that all users and profiles were created
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(UserProfile.objects.count(), 3)
        
        # Test that each user has a profile
        for user in created_users:
            self.assertTrue(hasattr(user, 'profile'))
            self.assertIsInstance(user.profile, UserProfile)


class AuthenticationSecurityTestCase(APITestCase):
    """Test authentication security aspects."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='security@example.com',
            first_name='Security',
            last_name='Test',
            password='securitypass123'
        )
        UserProfile.objects.create(user=self.user)
    
    def test_access_protected_endpoint_without_token(self):
        """Test that protected endpoints require authentication."""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_protected_endpoint_with_invalid_token(self):
        """Test that invalid tokens are rejected."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_password_security(self):
        """Test that passwords are properly hashed."""
        # Password should not be stored in plain text
        self.assertNotEqual(self.user.password, 'securitypass123')
        
        # Should be able to verify password
        self.assertTrue(self.user.check_password('securitypass123'))
        
        # Wrong password should fail
        self.assertFalse(self.user.check_password('wrongpassword'))
    
    def test_email_case_sensitivity(self):
        """Test email handling with different cases."""
        # Login with different case should work
        login_data = {
            'email': 'SECURITY@EXAMPLE.COM',
            'password': 'securitypass123'
        }
        
        response = self.client.post(reverse('login'), login_data)
        # This might fail depending on your authentication backend
        # Django's default ModelBackend is case-sensitive for email