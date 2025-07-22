#!/bin/bash
# Generate a template Django app with health check endpoint and basic structure

if [ -z "$1" ]; then
    echo "Usage: $0 <app_name>"
    echo "Example: $0 courses"
    exit 1
fi

APP_NAME=$1
APP_DIR="apps/$APP_NAME"

echo "🏗️  Creating template app: $APP_NAME"

# Create app directory if it doesn't exist
mkdir -p "$APP_DIR"

# Create __init__.py
cat > "$APP_DIR/__init__.py" << 'EOF'
# Empty init file for Python package
EOF

# Create apps.py
cat > "$APP_DIR/apps.py" << EOF
"""
App configuration for the ${APP_NAME} app.
"""

from django.apps import AppConfig


class ${APP_NAME^}Config(AppConfig):
    """
    Configuration for the ${APP_NAME} app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = '${APP_NAME}'
    verbose_name = '${APP_NAME^}'
EOF

# Create models.py
cat > "$APP_DIR/models.py" << EOF
"""
Models for the ${APP_NAME} app.
"""

from django.db import models

# This app is not yet implemented - no models defined
# TODO: Add ${APP_NAME} models when implementing functionality
EOF

# Create views.py
cat > "$APP_DIR/views.py" << EOF
"""
Views for the ${APP_NAME} app.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for ${APP_NAME} app.
    """
    return Response({
        'status': 'healthy',
        'app': '${APP_NAME}',
        'message': '${APP_NAME^} app is running',
        'implemented': False,
        'endpoints': [
            'GET /api/v1/${APP_NAME}/health/ - This health check'
        ]
    }, status=status.HTTP_200_OK)
EOF

# Create urls.py
cat > "$APP_DIR/urls.py" << EOF
"""
URL configuration for the ${APP_NAME} app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='${APP_NAME}_health'),
    
    # TODO: Add ${APP_NAME} endpoints when implementing functionality
    # Example:
    # path('', views.${APP_NAME}_list, name='${APP_NAME}_list'),
    # path('<int:pk>/', views.${APP_NAME}_detail, name='${APP_NAME}_detail'),
]
EOF

# Create admin.py
cat > "$APP_DIR/admin.py" << EOF
"""
Admin configuration for the ${APP_NAME} app.
"""

from django.contrib import admin

# This app is not yet implemented - no admin configurations
# TODO: Add ${APP_NAME} admin configurations when implementing functionality
EOF

# Create serializers.py
cat > "$APP_DIR/serializers.py" << EOF
"""
Serializers for the ${APP_NAME} app.
"""

from rest_framework import serializers

# This app is not yet implemented - no serializers defined
# TODO: Add ${APP_NAME} serializers when implementing functionality
EOF

# Create tests directory
mkdir -p "$APP_DIR/tests"

cat > "$APP_DIR/tests/__init__.py" << 'EOF'
# Test package for the app
EOF

# Create basic test file
cat > "$APP_DIR/tests/test_health.py" << EOF
"""
Health check tests for the ${APP_NAME} app.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class ${APP_NAME^}HealthCheckTestCase(APITestCase):
    """Test cases for ${APP_NAME} app health check."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        url = reverse('${APP_NAME}_health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('app', response.data)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['app'], '${APP_NAME}')
        self.assertFalse(response.data['implemented'])
EOF

echo "✅ Created template app structure for: $APP_NAME"
echo "📁 Files created:"
echo "   - $APP_DIR/__init__.py"
echo "   - $APP_DIR/apps.py"  
echo "   - $APP_DIR/models.py"
echo "   - $APP_DIR/views.py"
echo "   - $APP_DIR/urls.py"
echo "   - $APP_DIR/admin.py"
echo "   - $APP_DIR/serializers.py"
echo "   - $APP_DIR/tests/__init__.py"
echo "   - $APP_DIR/tests/test_health.py"
echo ""
echo "🔗 Health check URL: /api/v1/${APP_NAME}/health/"
echo "🧪 Test command: python manage.py test ${APP_NAME}.tests.test_health"