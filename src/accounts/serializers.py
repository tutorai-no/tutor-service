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
from learning_materials.serializer import (
    CardsetSerializer,
    QuizModelSerializer,
    UserFileSerializer,
    UserFile,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models import Feedback, Subscription, SubscriptionHistory, UserApplication, Streak


User = get_user_model()


class UserApplicationSerializer(serializers.ModelSerializer):
    heard_about_us = serializers.CharField(required=True)

    other_heard_about_us = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = UserApplication
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "heard_about_us",
            "other_heard_about_us",
            "inspiration",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

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
        if attrs["heard_about_us"] == "Other" and not attrs.get("other_heard_about_us"):
            raise serializers.ValidationError(
                {
                    "other_heard_about_us": "This field is required when 'Other' is selected."
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

    subscription = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "subscription",
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
        subscription = validated_data.pop("subscription", None)

        user = User.objects.create_user(subscription=subscription, **validated_data)

        # Send welcome email
        send_mail(
            subject="Welcome to TutorAI",
            message="Thank you for registering at TutorAI. We're excited to have you on board",
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


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["id", "name", "description", "price", "active"]


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = SubscriptionHistory
        fields = ["id", "subscription", "start_date", "end_date"]
        read_only_fields = ["id", "subscription", "start_date", "end_date"]

class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = ["start_date", "end_date", "current_streak", "longest_streak", "user"]

        
class UserProfileSerializer(serializers.ModelSerializer):
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

    uploaded_files = UserFileSerializer(many=True, required=False)

    subscription = SubscriptionSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(active=True),
        source="subscription",
        write_only=True,
        required=False,
        allow_null=True,
    )

    cardsets = CardsetSerializer(many=True, read_only=True)
    quizzes = QuizModelSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "subscription",
            "subscription_id",
            "uploaded_files",
            "cardsets",
            "quizzes",
        )

    def update(self, instance, validated_data):
        # Extract subscription_id and documents from validated_data
        subscription = validated_data.pop("subscription", None)
        documents_data = validated_data.pop("uploaded_files", None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update subscription if provided
        if subscription is not None:
            instance.subscription = subscription

        # Update uploaded_files if provided
        if documents_data is not None:
            # instance.uploaded_files.clear()  # Clear existing files if any
            for document_data in documents_data:
                # Assuming `document_data` contains enough data to create a UserFile instance
                document = UserFile.objects.create(user=instance, **document_data)
                instance.uploaded_files.add(document)

        # Save the user instance
        instance.save()

        return instance


def validate_image_size(image):
    max_size_in_mb = 4
    max_size_in_bytes = max_size_in_mb * 1024 * 1024  # Convert MB to bytes
    if image.size > max_size_in_bytes:
        raise ValidationError(f"Image size should not exceed { max_size_in_mb} MB.")


class UserFeedbackSerializer(serializers.Serializer):
    feedbackType = serializers.CharField(
        help_text="The type of feedback",
        required=True,
    )
    feedbackText = serializers.CharField(
        help_text="The feedback text",
        required=True,
    )
    feedbackScreenshot = serializers.ImageField(
        help_text="The feedback screenshot",
        allow_null=True,
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"]),
            validate_image_size,
        ],
    )

    class Meta:
        model = Feedback
        fields = ("feedbackType", "feedbackText", "feedbackScreenshot")
