from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

class BaseAPIView(APIView):
    """Base API view with common functionality."""
    
    def handle_exception(self, exc):
        """Custom exception handling."""
        # Add common exception handling logic
        return super().handle_exception(exc)

class HealthCheckView(APIView):
    """Health check endpoint."""
    permission_classes = []
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'aksio-backend'
        }, status=status.HTTP_200_OK)