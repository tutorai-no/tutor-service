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
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication

from django_prometheus import urls as prometheus_urls  # Import Prometheus URLs
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework_simplejwt.authentication import JWTAuthentication

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
        - **Billing & Subscriptions**: Payment processing and plan management
        - **Document Processing**: Upload and process educational materials
        - **Learning Analytics**: Progress tracking and performance insights
        - **Monitoring & Health**: System health and performance metrics
        
        ## Authentication
        
        The API uses JWT (JSON Web Token) authentication. Include the token in the 
        Authorization header: `Authorization: Bearer <your-token>`
        
        ## Rate Limiting
        
        API endpoints are rate-limited to ensure fair usage:
        - **Authenticated users**: 60 requests/minute, 1000 requests/hour
        - **Anonymous users**: 20 requests/minute, 100 requests/hour
        - **Premium users**: 5000 requests/hour
        - **AI services**: 100 requests/hour (due to processing costs)
        
        ## Error Handling
        
        The API returns standard HTTP status codes with detailed error messages:
        - `400 Bad Request`: Invalid request data
        - `401 Unauthorized`: Authentication required
        - `403 Forbidden`: Insufficient permissions
        - `404 Not Found`: Resource not found
        - `429 Too Many Requests`: Rate limit exceeded
        - `500 Internal Server Error`: Server error
        """,
        terms_of_service="https://aksio.app/",
        contact=openapi.Contact(email="contact@aksio.app"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(SessionAuthentication, JWTAuthentication),
)

urlpatterns = [
    # Admin panel route
    path("admin/", admin.site.urls),
    # API routes
    path("api/", include("api.urls"), name="API"),
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
    # Prometheus metrics endpoint
    path("", include(prometheus_urls)),
]
