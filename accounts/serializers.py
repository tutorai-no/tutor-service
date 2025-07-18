from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models import (
    User,
    UserProfile,
    UserActivity,
    UserStreak,
    UserFeedback,
    UserApplication,
)

User = get_user_model()


class UserApplicationSerializer(serializers.ModelSerializer):
    acquisition_source = serializers.CharField(required=True)
    acquisition_details = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = UserApplication
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "full_name",
            "university",
            "study_level",
            "field_of_study",
            "acquisition_source",
            "acquisition_details",
            "motivation",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "full_name", "created_at", "updated_at"]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        if UserApplication.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        if UserApplication.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate(self, attrs):
        if attrs["acquisition_source"] == "Other" and not attrs.get("acquisition_details"):
            raise serializers.ValidationError(
                {
                    "acquisition_details": "This field is required when 'Other' is selected."
                }
            )

        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message="Username may contain only letters, numbers, and @/./+/-/_ characters.",
            ),
            UniqueValidator(queryset=User.objects.all()),
        ],
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ],
    )

    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )

    phone_number = serializers.CharField(
        required=False,
        max_length=17,
        validators=[phone_regex],
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "phone_number",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        
        user = User.objects.create_user(**validated_data)
        
        # Send welcome email
        send_mail(
            subject="Welcome to Aksio",
            message="Thank you for registering at Aksio. We're excited to have you on board",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        # Allow login with username or email
        user = (
            User.objects.filter(email=username_or_email).first()
            or User.objects.filter(username=username_or_email).first()
        )
        if user and user.check_password(password):
            if not user.is_active:
                raise AuthenticationFailed("User is inactive.", code="authorization")
            data = super().validate({"username": user.username, "password": password})
            user.last_login = timezone.now()
            user.save()
            return data
        else:
            raise AuthenticationFailed("Invalid credentials", code="authorization")


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Optionally, prevent email enumeration by not indicating whether the email exists
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        try:
            user = User.objects.get(pk=uid)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid UID"})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid or expired token"})

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "id",
            "bio",
            "learning_goals",
            "study_style",
            "difficulty_preference",
            "email_notifications",
            "study_reminders",
            "progress_reports",
            "marketing_emails",
            "profile_public",
            "show_progress",
            "show_study_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStreak
        fields = [
            "id",
            "current_streak_days",
            "longest_streak_days",
            "current_streak_start",
            "last_activity_date",
            "total_study_days",
            "total_study_sessions",
            "streak_milestones_achieved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = [
            "id",
            "activity_type",
            "session_id",
            "resource_type",
            "resource_id",
            "duration_seconds",
            "metadata",
            "ip_address",
            "user_agent",
            "device_type",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "metadata": {"required": False},
        }


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message="Username may contain only letters, numbers, and @/./+/-/_ characters.",
            ),
            UniqueValidator(queryset=User.objects.all()),
        ],
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ],
    )
    
    profile = UserProfileSerializer(read_only=True)
    streak = UserStreakSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "university",
            "study_level",
            "study_year",
            "field_of_study",
            "timezone",
            "language",
            "preferred_study_time",
            "daily_study_goal_minutes",
            "acquisition_source",
            "acquisition_details",
            "is_verified",
            "last_active_at",
            "onboarding_completed",
            "stripe_customer_id",
            "profile",
            "streak",
            "created_at",
            "updated_at",
        )
        read_only_fields = [
            "id", 
            "is_verified", 
            "last_active_at", 
            "stripe_customer_id",
            "profile",
            "streak",
            "created_at", 
            "updated_at"
        ]


def validate_image_size(image):
    max_size_in_mb = 4
    max_size_in_bytes = max_size_in_mb * 1024 * 1024  # Convert MB to bytes
    if image.size > max_size_in_bytes:
        raise ValidationError(f"Image size should not exceed {max_size_in_mb} MB.")


class UserFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = [
            "id",
            "feedback_type",
            "title",
            "description",
            "screenshot",
            "page_url",
            "browser_info",
            "status",
            "priority",
            "admin_response",
            "resolved_at",
            "resolved_by",
            "satisfaction_rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "priority",
            "admin_response",
            "resolved_at",
            "resolved_by",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "screenshot": {
                "validators": [
                    FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"]),
                    validate_image_size,
                ],
            },
        }
