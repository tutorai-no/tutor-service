from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.core.validators import MaxValueValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.validators import UniqueValidator
from learning_materials.serializer import CardsetSerializer, QuizModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import Document, Feedback, Subscription, SubscriptionHistory


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        min_length=6,
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

    subscription = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = ("username", "email", "password",
                  "password_confirm", "subscription")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        subscription = validated_data.pop("subscription", None)

        user = User.objects.create_user(
            subscription=subscription, **validated_data)

        # Send welcome email
        send_mail(
            subject="Welcome to Our Site",
            message="Thank you for registering.",
            from_email="no-reply@example.com",
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
                raise AuthenticationFailed(
                    "User is inactive.", code="authorization")
            data = super().validate(
                {"username": user.username, "password": password})
            user.last_login = timezone.now()
            user.save()
            return data
        else:
            raise AuthenticationFailed(
                "Invalid credentials", code="authorization")


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
            raise serializers.ValidationError(
                {"token": "Invalid or expired token"})

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


class DocumentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(
        help_text="The ID of the document",
    )

    name = serializers.CharField(
        help_text="The name of the document",
        required=False,
    )

    subject = serializers.CharField(
        help_text="The subject of the quiz",
        required=False,
    )

    # The learning goals
    learning_goals = serializers.ListField(
        child=serializers.CharField(),
        help_text="The learning goals",
        required=False,
    )

    start_page = serializers.IntegerField(
        help_text="The start page of the document",
        required=False,
    )
    end_page = serializers.IntegerField(
        help_text="The end page of the document",
        required=False,
    )

    class Meta:
        model = Document
        fields = ["id", "name", "start_page",
                  "end_page", "subject", "learning_goals"]
        read_only_fields = ["id"]

    def validate(self, data: dict) -> dict:
        subject = data.get("subject")
        start_page = data.get("start_page")
        end_page = data.get("end_page")

        # Ensure at least one of subject or page range is provided
        if not subject and (start_page is None or end_page is None):
            raise serializers.ValidationError(
                "At least one of 'subject' or a valid 'start_page' and 'end_page' must be provided."
            )

        # If one page field is provided, both must be provided
        if (start_page is None) != (end_page is None):
            raise serializers.ValidationError(
                "Both 'start_page' and 'end_page' must be provided together."
            )

        # If both pages are provided, validate their relationship
        if start_page is not None and end_page is not None:
            if start_page > end_page:
                raise serializers.ValidationError(
                    "'start_page' must be less than or equal to 'end_page'."
                )

        return data


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

    subscription = SubscriptionSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(active=True),
        source="subscription",
        write_only=True,
        required=False,
        allow_null=True,
    )
    documents = DocumentSerializer(many=True, required=False)

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
            "documents",
            "cardsets",
            "quizzes",
        )

    def update(self, instance, validated_data):
        # Extract subscription_id and documents from validated_data
        subscription = validated_data.pop("subscription", None)
        documents_data = validated_data.pop("documents", None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update subscription if provided
        if subscription is not None:
            instance.subscription = subscription

        # Save the user instance
        instance.save()

        # Handle documents
        if documents_data:
            for doc_data in documents_data:
                Document.objects.create(user=instance, **doc_data)

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
