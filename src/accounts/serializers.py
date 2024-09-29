# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import default_token_generator

class RegisterSerializer(serializers.ModelSerializer):
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
    email = serializers.EmailField(required=True)  # Explicitly required

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
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
        try:
            uid = int(attrs['uid'])  # Assuming UID is the raw primary key
            user = User.objects.get(pk=uid)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError({'uid': 'Invalid UID'})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': 'Invalid or expired token'})

        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['password'])
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        read_only_fields = ('email',)
