import logging

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

from config import Config
from accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    SubscriptionHistorySerializer,
    SubscriptionSerializer,
    UserApplicationSerializer,
    UserFeedbackSerializer,
    UserProfileSerializer,
    StreakSerializer,
    ActivitySerializer,
    ActivityLogSerializer,
)
from accounts.models import Feedback, Subscription, Streak, Activity


logger = logging.getLogger(__name__)

User = get_user_model()


class RequestAccessView(generics.CreateAPIView):
    """
    Endpoint for users to request access to TutorAI.
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
            f"User '{application.username}' has requested access to TutorAI.\n\n"
            f"Details:\n"
            f"Username: {application.username}\n"
            f"Email: {application.email}\n"
            f"Phone Number: {application.phone_number}\n"
            f"Heard About Us: {application.heard_about_us}\n"
        )
        if application.heard_about_us == "Other":
            message += f"Other Source: {application.other_heard_about_us}\n"
        message += f"Inspiration: {application.inspiration}\n\n"
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
            base_url = Config().BASE_URL_FRONTEND
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
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class SubscriptionListView(generics.ListAPIView):
    """
    View to list available subscriptions.
    """

    queryset = Subscription.objects.filter(active=True)
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]


class SubscriptionHistoryView(generics.ListAPIView):
    serializer_class = SubscriptionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.subscription_history.all()


class UserFeedback(generics.GenericAPIView):
    serializer_class = UserFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            feedback_type = serializer.validated_data["feedbackType"]
            feedback_text = serializer.validated_data["feedbackText"]

            # optional field
            feedback_screenshot = serializer.validated_data.get("feedbackScreenshot")
            # Save feedback to database
            Feedback.objects.create(
                user=request.user,
                feedback_type=feedback_type,
                feedback_text=feedback_text,
                feedback_screenshot=feedback_screenshot,
            )
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StreakRetrieveView(generics.RetrieveAPIView):
    serializer_class = StreakSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        streak, created = Streak.objects.get_or_create(user=self.request.user)
        return streak


class ActivityCreateView(generics.CreateAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer: ActivitySerializer):
        activity_type = serializer.validated_data.get("activity_type")
        user = self.request.user

        # Create Activity record
        activity = serializer.save(user=user)

        # Update Streak
        streak, created = Streak.objects.get_or_create(user=user)
        streak.increment_streak()


class ActivityLogView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user).order_by("-timestamp")
