import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
)

from accounts.models import (
    UserActivity,
    UserProfile,
    UserStreak,
)
from accounts.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UserActivitySerializer,
    UserApplicationSerializer,
    UserFeedbackSerializer,
    UserProfileSerializer,
    UserSerializer,
    UserStreakSerializer,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class RequestAccessView(generics.CreateAPIView):
    """
    Endpoint for users to request access to Aksio.
    """

    serializer_class = UserApplicationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        application = serializer.save()
        # Notify administrators about the new application
        self.notify_admin(application)

    def notify_admin(self, application):
        subject = f"New Access Request from {application.username}"
        message = (
            f"User '{application.username}' has requested access to Aksio.\n\n"
            f"Details:\n"
            f"Username: {application.username}\n"
            f"Email: {application.email}\n"
            f"Phone Number: {application.phone_number}\n"
            f"University: {application.university}\n"
            f"Study Level: {application.study_level}\n"
            f"Field of Study: {application.field_of_study}\n"
            f"Acquisition Source: {application.acquisition_source}\n"
        )
        if application.acquisition_source == "Other":
            message += f"Other Source: {application.acquisition_details}\n"
        message += f"Motivation: {application.motivation}\n\n"
        message += "Please review the application in the admin panel."

        admin_emails = [admin[1] for admin in settings.ADMINS]
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TokenError:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )


class TokenRefreshView(BaseTokenRefreshView):
    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()
        if user:
            uid = user.pk  # Using raw UID to match tests
            token = default_token_generator.make_token(user)
            base_url = "https://aksio.app"  # Replace with actual frontend URL
            reset_link = f"{base_url}/password-reset-confirm/?uid={uid}&token={token}"
            # Send password reset email
            send_mail(
                subject="Password Reset Request",
                message=f"Please click the link to reset your password: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(
                f"Password reset email sent to {user.email} with link {reset_link}"
            )

        # Always respond with 200 to prevent email enumeration
        return Response(
            {
                "detail": "If an account with that email exists, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @swagger_auto_schema(tags=["Accounts"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Accounts"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Accounts"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    @swagger_auto_schema(tags=["Accounts"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Accounts"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Accounts"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserFeedbackView(generics.CreateAPIView):
    serializer_class = UserFeedbackSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserStreakView(generics.RetrieveAPIView):
    serializer_class = UserStreakSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Accounts"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        # Fix race condition by using select_for_update to lock the row
        from django.db import transaction

        with transaction.atomic():
            try:
                streak = UserStreak.objects.select_for_update().get(
                    user=self.request.user
                )
            except UserStreak.DoesNotExist:
                streak, created = UserStreak.objects.get_or_create(
                    user=self.request.user
                )
        return streak


class UserActivityCreateView(generics.CreateAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserActivityListView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Accounts"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


class TokenValidationView(APIView):
    """
    Enhanced token validation and refresh endpoint for study sessions.

    Provides token validation, automatic refresh, and session management
    to prevent interruptions during long study sessions.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request):
        """
        Validate access token and optionally refresh if needed.

        Request body:
        {
            "access": "access_token",
            "refresh": "refresh_token" (optional for auto-refresh)
        }

        Response:
        {
            "valid": true/false,
            "access": "new_access_token" (if refreshed),
            "refresh": "new_refresh_token" (if rotated),
            "expires_in": seconds_until_expiry,
            "message": "status_message"
        }
        """
        access_token = request.data.get("access")
        refresh_token = request.data.get("refresh")

        if not access_token:
            return Response(
                {"valid": False, "message": "Access token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Try to validate the access token
            from rest_framework_simplejwt.tokens import AccessToken

            token = AccessToken(access_token)

            # Token is valid, calculate remaining time
            import time

            exp_timestamp = token.payload.get("exp")
            current_timestamp = time.time()
            expires_in = max(0, exp_timestamp - current_timestamp)

            return Response(
                {
                    "valid": True,
                    "expires_in": int(expires_in),
                    "message": "Token is valid",
                }
            )

        except TokenError:
            # Access token is invalid/expired, try to refresh if refresh token provided
            if refresh_token:
                try:
                    refresh = RefreshToken(refresh_token)
                    new_access = str(refresh.access_token)

                    # Check if we should rotate refresh token
                    new_refresh = (
                        str(refresh)
                        if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", True)
                        else refresh_token
                    )

                    # Calculate new token expiry
                    new_token = AccessToken(new_access)
                    exp_timestamp = new_token.payload.get("exp")
                    current_timestamp = time.time()
                    expires_in = max(0, exp_timestamp - current_timestamp)

                    response_data = {
                        "valid": True,
                        "access": new_access,
                        "expires_in": int(expires_in),
                        "message": "Token refreshed successfully",
                    }

                    if new_refresh != refresh_token:
                        response_data["refresh"] = new_refresh

                    return Response(response_data)

                except TokenError:
                    return Response(
                        {
                            "valid": False,
                            "message": "Both access and refresh tokens are invalid. Please login again.",
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            else:
                return Response(
                    {
                        "valid": False,
                        "message": "Access token expired and no refresh token provided",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )


class StudySessionTokenView(APIView):
    """
    Specialized token management for study sessions.

    Provides extended token validation specifically designed for
    long study sessions like quizzes and flashcard reviews.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Accounts"])
    def get(self, request):
        """
        Get current token status and remaining time.
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"message": "No valid authorization header"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = auth_header.split(" ")[1]

        try:
            import time

            from rest_framework_simplejwt.tokens import AccessToken

            token = AccessToken(access_token)
            exp_timestamp = token.payload.get("exp")
            current_timestamp = time.time()
            expires_in = max(0, exp_timestamp - current_timestamp)

            # Warning if token expires in less than 10 minutes
            needs_refresh = expires_in < 600  # 10 minutes

            return Response(
                {
                    "expires_in": int(expires_in),
                    "expires_in_minutes": round(expires_in / 60, 1),
                    "needs_refresh": needs_refresh,
                    "user_id": str(token.payload.get("user_id")),
                    "message": (
                        "Token expires soon" if needs_refresh else "Token is valid"
                    ),
                }
            )

        except TokenError:
            return Response(
                {"message": "Token is invalid or expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    @swagger_auto_schema(tags=["Accounts"])
    def post(self, request):
        """
        Proactively refresh token for study session continuity.

        Request body:
        {
            "refresh": "refresh_token"
        }
        """
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)

            # Calculate new token expiry
            import time

            from rest_framework_simplejwt.tokens import AccessToken

            new_token = AccessToken(new_access)
            exp_timestamp = new_token.payload.get("exp")
            current_timestamp = time.time()
            expires_in = max(0, exp_timestamp - current_timestamp)

            response_data = {
                "access": new_access,
                "expires_in": int(expires_in),
                "expires_in_minutes": round(expires_in / 60, 1),
                "message": "Token refreshed for study session",
            }

            # Include new refresh token if rotation is enabled
            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", True):
                response_data["refresh"] = str(refresh)

            return Response(response_data)

        except TokenError:
            return Response(
                {"message": "Invalid refresh token. Please login again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
