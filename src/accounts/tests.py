from django.core import mail
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from unittest.mock import patch
from rest_framework_simplejwt.exceptions import TokenError

class RegistrationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')

    @patch('django.core.mail.send_mail')  
    def test_user_registration_success(self, mock_send_mail):
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongP@ssw0rd!',
            'password_confirm': 'StrongP@ssw0rd!'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())

        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['testuser@example.com'])

    def test_user_registration_weak_password(self):
        data = {
            'username': 'testuser2',
            'email': 'testuser2@example.com',
            'password': 'password', # Weak password
            'password_confirm': 'password'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_password_mismatch(self):
        data = {
            'username': 'testuser3',
            'email': 'testuser3@example.com',
            'password': 'StrongP@ssw0rd!',
            'password_confirm': 'DifferentP@ssw0rd!'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_missing_fields(self):
        data = {
            'username': 'testuser4',
            # 'email' is missing
            'password': 'StrongP@ssw0rd!',
            'password_confirm': 'StrongP@ssw0rd!'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_registration_existing_username(self):
        User.objects.create_user(username='existinguser', email='existing@example.com', password='StrongP@ss1')
        data = {
            'username': 'existinguser',
            'email': 'newemail@example.com',
            'password': 'StrongP@ssw0rd!',
            'password_confirm': 'StrongP@ssw0rd!'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_user_registration_existing_email(self):
        User.objects.create_user(username='user1', email='duplicate@example.com', password='StrongP@ss1')
        data = {
            'username': 'newuser',
            'email': 'duplicate@example.com',
            'password': 'StrongP@ssw0rd!',
            'password_confirm': 'StrongP@ssw0rd!'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class LoginTests(APITestCase):
    def setUp(self):
        self.login_url = reverse('login')
        self.user = User.objects.create_user(username='loginuser', email='login@example.com', password='StrongP@ss1')

    def test_login_with_username_success(self):
        data = {
            'username': 'loginuser',
            'password': 'StrongP@ss1'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_email_success(self):
        data = {
            'username': 'login@example.com',  # Using email in 'username' field
            'password': 'StrongP@ss1'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        data = {
            'username': 'loginuser',
            'password': 'WrongPassword!'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_login_missing_fields(self):
        data = {
            'username': 'loginuser',
            # 'password' is missing
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

# Token Refresh Tests
class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.token_refresh_url = reverse('token_refresh')
        self.user = User.objects.create_user(username='refreshuser', email='refresh@example.com', password='StrongP@ss1')
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)

    def test_token_refresh_success(self):
        data = {
            'refresh': self.refresh_token
        }
        response = self.client.post(self.token_refresh_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid_token(self):
        data = {
            'refresh': 'invalidtoken123'
        }
        response = self.client.post(self.token_refresh_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_token_refresh_expired_token(self):
        # Mock TokenError instead of generic Exception
        with patch('rest_framework_simplejwt.tokens.RefreshToken.check_exp') as mock_check_exp:
            mock_check_exp.side_effect = TokenError('Token has expired')
            data = {
                'refresh': self.refresh_token
            }
            response = self.client.post(self.token_refresh_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertIn('detail', response.data)


class LogoutTests(APITestCase):
    def setUp(self):
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(username='logoutuser', email='logout@example.com', password='StrongP@ss1')
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_logout_success(self):
        self.authenticate()
        data = {
            'refresh': self.refresh_token
        }
        response = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        token = OutstandingToken.objects.get(token=self.refresh_token)
        self.assertTrue(BlacklistedToken.objects.filter(token=token).exists())

    def test_logout_invalid_token(self):
        self.authenticate()
        data = {
            'refresh': 'invalidtoken123'
        }
        response = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_without_authentication(self):
        data = {
            'refresh': self.refresh_token
        }
        response = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.password_reset_url = reverse('password_reset')
        self.user = User.objects.create_user(username='resetuser', email='reset@example.com', password='StrongP@ss1')

    @patch('django.core.mail.send_mail')  # Correct patch path
    def test_password_reset_request_success(self, mock_send_mail):
        expected_email = "reset@example.com"
        data = {
            'email': expected_email
        }
        response = self.client.post(self.password_reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [expected_email])

    def test_password_reset_request_nonexistent_email(self):
        data = {
            'email': 'nonexistent@example.com'
        }
        response = self.client.post(self.password_reset_url, data, format='json')
        # Return 200 to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)

    def test_password_reset_request_invalid_email(self):
        data = {
            'email': 'invalidemail'
        }
        response = self.client.post(self.password_reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

class PasswordResetConfirmTests(APITestCase):
    def setUp(self):
        self.password_reset_confirm_url = reverse('password_reset_confirm')
        self.user = User.objects.create_user(username='confirmuser', email='confirm@example.com', password='StrongP@ss1')
        self.token = default_token_generator.make_token(self.user)
        self.uid = str(self.user.pk)  # Send UID as string

    @patch('django.core.mail.send_mail')  # If applicable
    def test_password_reset_confirm_success(self, mock_send_mail):
        data = {
            'token': self.token,
            'uid': self.uid,  # Send UID as string
            'password': 'NewStrongP@ssw0rd!',
            'password_confirm': 'NewStrongP@ssw0rd!'
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongP@ssw0rd!'))
        mock_send_mail.assert_not_called()

    def test_password_reset_confirm_invalid_token(self):
        data = {
            'token': 'invalidtoken123',
            'uid': self.uid,
            'password': 'NewStrongP@ssw0rd!',
            'password_confirm': 'NewStrongP@ssw0rd!'
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)

    def test_password_reset_confirm_password_mismatch(self):
        data = {
            'token': self.token,
            'uid': self.uid,
            'password': 'NewStrongP@ssw0rd!',
            'password_confirm': 'DifferentP@ssw0rd!'
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_password_reset_confirm_weak_password(self):
        data = {
            'token': self.token,
            'uid': self.uid,
            'password': 'weakpass',
            'password_confirm': 'weakpass'
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class UserProfileTests(APITestCase):
    def setUp(self):
        self.profile_url = reverse('profile')
        self.user = User.objects.create_user(username='profileuser', email='profile@example.com', password='StrongP@ss1')
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_retrieve_profile_success(self):
        self.authenticate()
        response = self.client.get(self.profile_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'profileuser')
        self.assertEqual(response.data['email'], 'profile@example.com')

    def test_update_profile_success(self):
        self.authenticate()
        data = {
            "username": self.user.username,
            'first_name': 'John',
            'last_name': 'Doe'
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')

    def test_access_profile_without_authentication(self):
        response = self.client.get(self.profile_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_invalid_data(self):
        self.authenticate()
        data = {
        'non-existing-field': 'newemail@example.com'  
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
