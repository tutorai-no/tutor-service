"""
Serializers for the accounts app.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        """
        Validate password confirmation.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def create(self, validated_data):
        """
        Create new user account.
        """
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(**validated_data)
        
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=False)
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True,
        required=False
    )
    
    def validate(self, attrs):
        """
        Validate user credentials.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError('Must include email and password.')
        
        # First, check if user exists and is active
        from accounts.models import User
        try:
            user_obj = User.objects.get(email=email)
            if not user_obj.is_active:
                raise serializers.ValidationError('User account is disabled.')
        except User.DoesNotExist:
            pass
        
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_verified', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'date_joined', 'last_login']


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for extended user profile information.
    """
    bio = serializers.CharField(source='profile.bio', allow_blank=True, required=False)
    timezone = serializers.CharField(source='profile.timezone', required=False)
    language = serializers.CharField(source='profile.language', required=False)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_verified', 'date_joined', 'last_login',
            'bio', 'timezone', 'language'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'date_joined', 'last_login']
    
    def update(self, instance, validated_data):
        """
        Update user and profile information.
        """
        profile_data = validated_data.pop('profile', {})
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance