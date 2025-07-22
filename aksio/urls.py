"""
URL configuration for aksio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path, re_path
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework_simplejwt.authentication import JWTAuthentication


def health_check(request):
    """Simple health check endpoint for monitoring and Cloud Run"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'aksio-backend',
        'version': '1.0.0'
    })


def root_view(request):
    """Root endpoint with API information"""
    return JsonResponse({
        'service': 'Aksio Backend API',
        'version': '1.0.0',
        'status': 'running',
        'documentation': {
            'swagger': '/swagger/',
            'redoc': '/redoc/'
        },
        'endpoints': {
            'health': '/health/',
            'api': '/api/v1/',
            'admin': '/admin/'
        }
    })


# Swagger schema view configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Aksio Backend API",
        default_version="v1",
        description="""
        Aksio is an advanced educational platform that combines AI-powered learning tools 
        with modern web architecture. This API provides comprehensive endpoints for:
        
        - **User Management**: Authentication, profiles, and activity tracking
        - **Course Management**: Create, manage, and organize learning content
        - **Assessment System**: Flashcards, quizzes with spaced repetition
        - **AI-Powered Chat**: Intelligent learning assistance
        - **Document Processing**: Upload and process educational materials
        - **Learning Analytics**: Progress tracking and performance insights
        
        ## Authentication
        
        The API uses JWT (JSON Web Token) authentication. Include the token in the 
        Authorization header: `Authorization: Bearer <your-token>`
        
        ## Rate Limiting
        
        API endpoints are rate-limited to ensure fair usage:
        - **Authenticated users**: 1000 requests/hour
        - **Anonymous users**: 100 requests/hour
        
        ## Error Handling
        
        The API returns standard HTTP status codes with detailed error messages:
        - `400 Bad Request`: Invalid request data
        - `401 Unauthorized`: Authentication required
        - `403 Forbidden`: Insufficient permissions
        - `404 Not Found`: Resource not found
        - `429 Too Many Requests`: Rate limit exceeded
        - `500 Internal Server Error`: Server error
        """,
        terms_of_service="https://aksio.app/terms/",
        contact=openapi.Contact(email="contact@aksio.app"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(SessionAuthentication, JWTAuthentication),
)

urlpatterns = [
    # Root endpoint
    path("", root_view, name="root"),
    
    # Health check endpoint (for monitoring and Cloud Run)
    path("health/", health_check, name="health_check"),
    
    # Admin panel route
    path("admin/", admin.site.urls),
    
    # API routes - organized by app
    path("api/v1/accounts/", include("accounts.urls")),
    # Note: Uncomment these as you implement each app
    # path("api/v1/assessments/", include("assessments.urls")),
    # path("api/v1/billing/", include("billing.urls")),
    # path("api/v1/chat/", include("chat.urls")),
    # path("api/v1/courses/", include("courses.urls")),
    # path("api/v1/documents/", include("documents.urls")),
    # path("api/v1/learning/", include("learning.urls")),
    
    # Core utilities
    path("api/v1/", include("core.urls")),
    
    # API Documentation routes
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]

# Customize admin site
admin.site.site_header = "Aksio Administration"
admin.site.site_title = "Aksio Admin"
admin.site.index_title = "Welcome to Aksio Administration"