import logging

from datetime import datetime
from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator

from accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    UserApplicationSerializer,
    UserFeedbackSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserStreakSerializer,
    UserActivitySerializer,
)
from accounts.models import (
    UserFeedback,
    UserStreak,
    UserActivity,
    UserApplication,
    UserProfile,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class RequestAccessView(generics.CreateAPIView):
    """
    Endpoint for users to request access to Aksio.
    """

    serializer_class = UserApplicationSerializer
    permission_classes = [AllowAny]

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


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

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


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

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

    def get_object(self):
        return self.request.user


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserFeedbackView(generics.CreateAPIView):
    serializer_class = UserFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserStreakView(generics.RetrieveAPIView):
    serializer_class = UserStreakSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        streak, created = UserStreak.objects.get_or_create(user=self.request.user)
        return streak


class UserActivityCreateView(generics.CreateAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserActivityListView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user).order_by("-created_at")
