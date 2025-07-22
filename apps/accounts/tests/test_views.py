"""
Test cases for accounts views and API endpoints.
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, UserProfile


class AccountsAPITestCase(APITestCase):
    """Test cases for accounts API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('profile')
        self.token_refresh_url = reverse('token_refresh')
        
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        
        # Create a test user
        self.user = User.objects.create_user(
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            password='existingpass123'
        )
        UserProfile.objects.create(user=self.user)


class RegisterViewTestCase(AccountsAPITestCase):
    """Test cases for user registration endpoint."""
    
    def test_successful_registration(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response structure
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        
        # Check tokens
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Check user was created
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        
        # Check user profile was created
        user = User.objects.get(email='test@example.com')
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_registration_with_invalid_data(self):
        """Test registration with invalid data."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_with_mismatched_passwords(self):
        """Test registration with mismatched passwords."""
        invalid_data = self.user_data.copy()
        invalid_data['password_confirm'] = 'differentpass'
        
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_with_existing_email(self):
        """Test registration with existing email."""
        # First registration
        self.client.post(self.register_url, self.user_data)
        
        # Second registration with same email
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTestCase(AccountsAPITestCase):
    """Test cases for user login endpoint."""
    
    def test_successful_login(self):
        """Test successful user login."""
        login_data = {
            'email': 'existing@example.com',
            'password': 'existingpass123'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        
        # Check tokens
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Check user data
        self.assertEqual(response.data['user']['email'], 'existing@example.com')
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'existing@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_with_nonexistent_email(self):
        """Test login with non-existent email."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_with_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        login_data = {
            'email': 'existing@example.com',
            'password': 'existingpass123'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials."""
        # Missing password
        response = self.client.post(self.login_url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing email
        response = self.client.post(self.login_url, {'password': 'password123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTestCase(AccountsAPITestCase):
    """Test cases for user logout endpoint."""
    
    def setUp(self):
        """Set up test data with authentication."""
        super().setUp()
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.refresh_token = str(self.refresh)
    
    def test_successful_logout(self):
        """Test successful user logout."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        logout_data = {'refresh_token': self.refresh_token}
        response = self.client.post(self.logout_url, logout_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_logout_without_token(self):
        """Test logout without refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.post(self.logout_url, {})
        # Should still return 200 even without token
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_logout_with_invalid_token(self):
        """Test logout with invalid refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        logout_data = {'refresh_token': 'invalid-token'}
        response = self.client.post(self.logout_url, logout_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_logout_without_authentication(self):
        """Test logout without authentication."""
        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileViewTestCase(AccountsAPITestCase):
    """Test cases for user profile endpoint."""
    
    def setUp(self):
        """Set up test data with authentication."""
        super().setUp()
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_profile(self):
        """Test retrieving user profile."""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        
        user_data = response.data['user']
        self.assertEqual(user_data['email'], 'existing@example.com')
        self.assertEqual(user_data['first_name'], 'Existing')
        self.assertEqual(user_data['last_name'], 'User')
    
    def test_update_profile(self):
        """Test updating user profile."""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated biography',
            'timezone': 'Europe/London'
        }
        
        response = self.client.put(self.profile_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        
        # Check updated data
        user_data = response.data['user']
        self.assertEqual(user_data['first_name'], 'Updated')
        self.assertEqual(user_data['last_name'], 'Name')
        self.assertEqual(user_data['bio'], 'Updated biography')
        self.assertEqual(user_data['timezone'], 'Europe/London')
    
    def test_partial_profile_update(self):
        """Test partial profile update using PATCH."""
        update_data = {'first_name': 'Partially Updated'}
        
        response = self.client.patch(self.profile_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only specified field was updated
        user_data = response.data['user']
        self.assertEqual(user_data['first_name'], 'Partially Updated')
        self.assertEqual(user_data['last_name'], 'User')  # Should remain unchanged
    
    def test_profile_access_without_authentication(self):
        """Test profile access without authentication."""
        self.client.credentials()  # Remove authentication
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTestCase(AccountsAPITestCase):
    """Test cases for JWT token refresh endpoint."""
    
    def setUp(self):
        """Set up test data with tokens."""
        super().setUp()
        self.refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(self.refresh)
    
    def test_successful_token_refresh(self):
        """Test successful token refresh."""
        refresh_data = {'refresh': self.refresh_token}
        
        response = self.client.post(self.token_refresh_url, refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid token."""
        refresh_data = {'refresh': 'invalid-refresh-token'}
        
        response = self.client.post(self.token_refresh_url, refresh_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh_without_token(self):
        """Test token refresh without providing token."""
        response = self.client.post(self.token_refresh_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HealthCheckTestCase(AccountsAPITestCase):
    """Test cases for health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        url = reverse('accounts_health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('app', response.data)
        self.assertIn('users_count', response.data)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['app'], 'accounts')