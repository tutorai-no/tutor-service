"""
Views for the accounts app.
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import IsAuthenticatedOrError
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer, 
    UserProfileSerializer,
    UserProfileDetailSerializer
)


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """
        Create new user account and return JWT tokens.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Account created successfully',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    User login endpoint.
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """
        Authenticate user and return JWT tokens.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


@api_view(['POST'])
# Use default permission from settings  
def logout_view(request):
    """
    User logout endpoint - blacklist refresh token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile view - get and update profile information.
    """
    serializer_class = UserProfileDetailSerializer
    # Use default permission from settings
    
    def get_object(self):
        """
        Return the current user.
        """
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get user profile information.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'user': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """
        Update user profile information.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for accounts app.
    """
    return Response({
        'status': 'healthy',
        'app': 'accounts',
        'users_count': User.objects.count()
    })