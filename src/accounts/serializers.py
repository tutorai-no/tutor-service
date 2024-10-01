from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import Subscription, SubscriptionHistory


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Username may contain only letters, numbers, and @/./+/-/_ characters.'
            ),
            UniqueValidator(queryset=User.objects.all())
        ]
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    email = serializers.EmailField(
        required=True, 
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ]
    )

    subscription = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(active=True),
        required=False,
        allow_null=True
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'subscription')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        subscription = validated_data.pop('subscription', None)

        user = User.objects.create_user(
            subscription=subscription,
            **validated_data
        )

        # Send welcome email
        send_mail(
            subject='Welcome to Our Site',
            message='Thank you for registering.',
            from_email='no-reply@example.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')

        # Allow login with username or email
        user = User.objects.filter(email=username_or_email).first() or User.objects.filter(username=username_or_email).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise AuthenticationFailed('User is inactive.', code='authorization')
            data = super().validate({'username': user.username, 'password': password})
            return data
        else:
            raise AuthenticationFailed('Invalid credentials', code='authorization')



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
        uid = attrs.get('uid')
        token = attrs.get('token')
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        try:
            user = User.objects.get(pk=uid)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError({'uid': 'Invalid UID'})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({'token': 'Invalid or expired token'})

        attrs['user'] = user
        return attrs


    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['password'])
        user.save()
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'name', 'description', 'price', 'active']


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = SubscriptionHistory
        fields = ['id', 'subscription', 'start_date', 'end_date']
        read_only_fields = ['id', 'subscription', 'start_date', 'end_date']


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Username may contain only letters, numbers, and @/./+/-/_ characters.'
            ),
            UniqueValidator(queryset=User.objects.all()),
        ]
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ]
    )

    subscription = SubscriptionSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(active=True),
        source='subscription',
        write_only=True,
        required=False,
        allow_null=True
    )


    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'subscription', 'subscription_id')


    def update(self, instance, validated_data):
        # Extract subscription_id from validated_data
        subscription_id = validated_data.pop('subscription_id', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update subscription if provided
        if subscription_id is not None:
            instance.subscription = subscription_id

        # Save the instance
        instance.save()
        return instance