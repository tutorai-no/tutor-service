from django.core import mail

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.exceptions import TokenError
from unittest.mock import patch

from accounts.models import Subscription

User = get_user_model()


class RegistrationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.subscription = Subscription.objects.create(
            name="Premium", description="Premium subscription", price=19.99
        )

    @patch("django.core.mail.send_mail")
    def test_user_registration_with_subscription_success(self, mock_send_mail):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
            "subscription": self.subscription.id,  # Include subscription if desired
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["testuser@example.com"])

    @patch("django.core.mail.send_mail")
    def test_user_registration_success(self, mock_send_mail):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["testuser@example.com"])

    def test_user_registration_username_too_short(self):
        data = {
            "username": "ab",  # Too short
            "email": "shortuser@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_registration_duplicate_username_case_sensitive(self):
        User.objects.create_user(
            username="TestUser", email="unique@example.com", password="StrongP@ss1"
        )
        data = {
            "username": "testuser",  # Different case
            "email": "newemail@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_registration_weak_password(self):
        data = {
            "username": "testuser2",
            "email": "testuser2@example.com",
            "password": "password",  # Weak password
            "password_confirm": "password",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_user_registration_all_special_characters_password(self):
        data = {
            "username": "testuser2",
            "email": "testuser2@example.com",
            "password": """!"#$%&'()*+,-./0123456789:;<=>? @abcdefghijklmnopqrstuvwxyz[]^_`abcdefghijklmnopqrstuvwxyz{|}~""",
            "password_confirm": """!"#$%&'()*+,-./0123456789:;<=>? @abcdefghijklmnopqrstuvwxyz[]^_`abcdefghijklmnopqrstuvwxyz{|}~""",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_registration_password_mismatch(self):
        data = {
            "username": "testuser3",
            "email": "testuser3@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "DifferentP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_user_registration_missing_fields(self):
        data = {
            "username": "testuser4",
            # 'email' is missing
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_registration_existing_username(self):
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongP@ss1",
        )
        data = {
            "username": "existinguser",
            "email": "newemail@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_user_registration_existing_email(self):
        User.objects.create_user(
            username="user1", email="duplicate@example.com", password="StrongP@ss1"
        )
        data = {
            "username": "newuser",
            "email": "duplicate@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_with_very_long_username(self):
        data = {
            "username": "a" * 150,  # Assuming max length is less
            "email": "longusername@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_registration_with_non_ascii_username(self):
        data = {
            "username": "用户测试测用",  # Non-ASCII characters
            "email": "unicode@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_with_invalid_email(self):
        """
        Ensure that registration fails with an invalid email format.
        """
        data = {
            "username": "invalidemailuser",
            "email": "invalidemail",  # Invalid email format
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_password_storage_is_hashed(self):
        data = {
            "username": "hashuser",
            "email": "hashuser@example.com",
            "password": "StrongP@ssw0rd!",
            "password_confirm": "StrongP@ssw0rd!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="hashuser")
        self.assertNotEqual(user.password, "StrongP@ssw0rd!")
        self.assertTrue(user.check_password("StrongP@ssw0rd!"))


class LoginTests(APITestCase):
    def setUp(self):
        self.login_url = reverse("login")
        self.user = User.objects.create_user(
            username="loginuser", email="login@example.com", password="StrongP@ss1"
        )

    def test_login_with_username_success(self):
        data = {"username": "loginuser", "password": "StrongP@ss1"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_email_success(self):
        data = {
            "username": "login@example.com",  # Using email in 'username' field
            "password": "StrongP@ss1",
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        data = {"username": "loginuser", "password": "WrongPassword!"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_missing_fields(self):
        data = {
            "username": "loginuser",
            # 'password' is missing
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_username_case_insensitive(self):
        data = {"username": "LoginUser", "password": "StrongP@ss1"}  # Different case
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_correct_email_wrong_password(self):
        """
        Ensure that logging in with a correct email but wrong password fails.
        """
        data = {
            "username": "login@example.com",  # Assuming email can be used as username
            "password": "WrongPassword!",  # Incorrect password
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_with_one_users_username_and_another_users_password(self):
        """
        Ensure that logging in with one user's username and another user's password fails.
        """
        data = {
            "username": "user1",  # Valid username for user1
            "password": "Password2!",  # Valid password for user2, invalid for user1
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_superuser_success(self):
        superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="AdminP@ssw0rd!"
        )
        data = {"username": "admin", "password": "AdminP@ssw0rd!"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_staff_user_success(self):
        staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="StaffP@ssw0rd!",
            is_staff=True,
        )
        data = {"username": "staffuser", "password": "StaffP@ssw0rd!"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.token_refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")
        self.user = User.objects.create_user(
            username="refreshuser", email="refresh@example.com", password="StrongP@ss1"
        )
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

        self.password_reset_confirm_url = reverse("password_reset_confirm")
        self.token = default_token_generator.make_token(self.user)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def test_token_refresh_success(self):
        data = {"refresh": self.refresh_token}
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid_token(self):
        data = {"refresh": "invalidtoken123"}
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_refresh_expired_token(self):
        # Mock TokenError instead of generic Exception
        with patch(
            "rest_framework_simplejwt.tokens.RefreshToken.check_exp"
        ) as mock_check_exp:
            mock_check_exp.side_effect = TokenError("Token has expired")
            data = {"refresh": self.refresh_token}
            response = self.client.post(self.token_refresh_url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertIn("detail", response.data)

    def test_token_refresh_after_logout(self):
        # First logout to blacklist the token
        self.authenticate()
        data = {"refresh": self.refresh_token}
        self.client.post(self.logout_url, data, format="json")

        # Attempt to refresh using the blacklisted token
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_refresh_with_blacklisted_token(self):
        # Blacklist the refresh token
        refresh = RefreshToken.for_user(self.user)
        refresh.blacklist()

        data = {"refresh": str(refresh)}
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Token is blacklisted")


class LogoutTests(APITestCase):
    def setUp(self):
        self.logout_url = reverse("logout")
        self.user = User.objects.create_user(
            username="logoutuser", email="logout@example.com", password="StrongP@ss1"
        )
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def test_logout_success(self):
        self.authenticate()
        data = {"refresh": self.refresh_token}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        token = OutstandingToken.objects.get(token=self.refresh_token)
        self.assertTrue(BlacklistedToken.objects.filter(token=token).exists())

    def test_logout_invalid_token(self):
        self.authenticate()
        data = {"refresh": "invalidtoken123"}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_without_authentication(self):
        data = {"refresh": self.refresh_token}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_already_blacklisted_token(self):
        self.authenticate()
        data = {"refresh": self.refresh_token}
        # First logout
        response1 = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_205_RESET_CONTENT)

        # Attempt second logout with the same token
        response2 = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_without_logging_in(self):
        """
        Ensure that logging out without authentication fails.
        """
        data = {"refresh": self.refresh_token}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("rest_framework_simplejwt.tokens.RefreshToken.verify")
    def test_logout_with_expired_token(self, mock_verify):
        mock_verify.side_effect = TokenError("Token has expired")
        data = {"refresh": self.refresh_token}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.password_reset_url = reverse("password_reset")
        self.user = User.objects.create_user(
            username="resetuser", email="reset@example.com", password="StrongP@ss1"
        )

    @patch("django.core.mail.send_mail")
    def test_password_reset_request_success(self, mock_send_mail):
        expected_email = "reset@example.com"
        data = {"email": expected_email}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [expected_email])

    def test_password_reset_request_nonexistent_email(self):
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.password_reset_url, data, format="json")
        # Return 200 to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_request_invalid_email(self):
        data = {"email": "invalidemail"}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(len(mail.outbox), 0)


class PasswordResetConfirmTests(APITestCase):
    def setUp(self):
        self.password_reset_confirm_url = reverse("password_reset_confirm")
        self.user = User.objects.create_user(
            username="confirmuser", email="confirm@example.com", password="StrongP@ss1"
        )
        self.token = default_token_generator.make_token(self.user)
        self.uid = str(self.user.pk)  # Send UID as string

    @patch("django.core.mail.send_mail")  # If applicable
    def test_password_reset_confirm_success(self, mock_send_mail):
        data = {
            "token": self.token,
            "uid": self.uid,  # Send UID as string
            "password": "NewStrongP@ssw0rd!",
            "password_confirm": "NewStrongP@ssw0rd!",
        }
        response = self.client.post(
            self.password_reset_confirm_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongP@ssw0rd!"))
        mock_send_mail.assert_not_called()

    def test_password_reset_confirm_invalid_token(self):
        data = {
            "token": "invalidtoken123",
            "uid": self.uid,
            "password": "NewStrongP@ssw0rd!",
            "password_confirm": "NewStrongP@ssw0rd!",
        }
        response = self.client.post(
            self.password_reset_confirm_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)

    def test_password_reset_confirm_password_mismatch(self):
        data = {
            "token": self.token,
            "uid": self.uid,
            "password": "NewStrongP@ssw0rd!",
            "password_confirm": "DifferentP@ssw0rd!",
        }
        response = self.client.post(
            self.password_reset_confirm_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_password_reset_confirm_weak_password(self):
        data = {
            "token": self.token,
            "uid": self.uid,
            "password": "weakpass",
            "password_confirm": "weakpass",
        }
        response = self.client.post(
            self.password_reset_confirm_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_password_reset_confirm_with_expired_token(self):
        with patch(
            "django.contrib.auth.tokens.default_token_generator.check_token"
        ) as mock_check_token:
            mock_check_token.return_value = False  # Simulate expired token
            data = {
                "token": self.token,
                "uid": self.uid,
                "password": "NewStrongP@ssw0rd!",
                "password_confirm": "NewStrongP@ssw0rd!",
            }
            response = self.client.post(
                self.password_reset_confirm_url, data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("token", response.data)


class UserProfileTests(APITestCase):
    def setUp(self):
        self.profile_url = reverse("profile")
        self.user = User.objects.create_user(
            username="profileuser", email="profile@example.com", password="StrongP@ss1"
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def test_retrieve_profile_success(self):
        self.authenticate()
        response = self.client.get(self.profile_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "profileuser")
        self.assertEqual(response.data["email"], "profile@example.com")

    def test_retrieve_profile_with_documents(self):
        self.authenticate()
        self.client.patch(
            self.profile_url,
            {"documents": [{"name": "Document 1", "start_page": 1, "end_page": 5}]},
            format="json",
        )
        self.user.refresh_from_db()
        response = self.client.get(self.profile_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(len(response.data["documents"]), 1)

    def test_retrieve_profile_without_authentication(self):
        response = self.client.get(self.profile_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_success(self):
        self.authenticate()
        data = {
            "username": self.user.username,
            "first_name": "John",
            "last_name": "Doe",
            "email": "newemail@example.com",
        }
        response = self.client.put(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")

    def test_partial_update_profile_success(self):
        self.authenticate()
        data = {"first_name": "Jane"}
        response = self.client.patch(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jane")

    def test_partial_update_profile_with_document(self):
        self.authenticate()
        data = {"documents": [{"name": "Document 1", "start_page": 1, "end_page": 5}]}
        response = self.client.patch(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.documents.count(), 1)

    def test_partial_update_profile_with_several_documents(self):
        self.authenticate()
        data = {
            "documents": [
                {"name": "Document 1", "start_page": 1, "end_page": 5},
                {"name": "Document 2", "start_page": 6, "end_page": 10},
            ]
        }
        response = self.client.patch(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.documents.count(), 2)

    def test_partial_update_profile_with_documents_does_not_overwrite(self):
        self.authenticate()
        data = {
            "documents": [
                {"name": "Document 1", "start_page": 1, "end_page": 5},
            ]
        }
        response = self.client.patch(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.documents.count(), 1)

        self.authenticate()
        # Update with new document
        data = {"documents": [{"name": "Document 2", "start_page": 6, "end_page": 10}]}
        response = self.client.patch(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.documents.count(), 2)

    def test_access_profile_without_authentication(self):
        response = self.client.get(self.profile_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_invalid_data(self):
        self.authenticate()
        data = {"non-existing-field": "newemail@example.com"}
        response = self.client.put(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_profile_email_to_existing_email(self):
        User.objects.create_user(
            username="otheruser", email="existing@example.com", password="StrongP@ss1"
        )

        self.authenticate()
        data = {"username": self.user.username, "email": "existing@example.com"}
        response = self.client.put(self.profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_subscription_upgrade(self):
        # Create initial subscription
        basic = Subscription.objects.create(
            name="Basic", description="Basic plan", price=9.99, active=True
        )
        premium = Subscription.objects.create(
            name="Premium", description="Premium plan", price=19.99, active=True
        )

        # Register user with Basic subscription
        user = User.objects.create_user(
            username="upgradeuser",
            email="upgrade@example.com",
            password="StrongP@ss1",
            subscription=basic,
        )
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer " + str(refresh.access_token)
        )

        # Upgrade to Premium
        profile_url = reverse("profile")
        data = {
            "username": "upgradeuser",
            "email": "upgrade@example.com",
            "subscription_id": premium.id,
        }
        response = self.client.put(profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.subscription, premium)
