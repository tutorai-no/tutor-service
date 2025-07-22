"""
Views for the courses app.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for courses app.
    """
    return Response({
        'status': 'healthy',
        'app': 'courses',
        'message': 'Courses app is running',
        'implemented': False,
        'endpoints': [
            'GET /api/v1/courses/health/ - This health check'
        ]
    }, status=status.HTTP_200_OK)
