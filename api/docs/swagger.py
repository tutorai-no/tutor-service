from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework_simplejwt.authentication import JWTAuthentication

# Swagger schema view configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Aksio API",
        default_version="v1",
        description="""
        Aksio is an intelligent learning platform that transforms how higher education 
        students master their curriculum through AI-powered study planning and 
        personalized learning exercises.
        
        ## Features
        - **User Management**: Secure authentication and user profiles
        - **Course Management**: Course creation, document upload, and organization
        - **Learning Tools**: AI-powered study planning and session scheduling
        - **Assessments**: Interactive flashcards and quizzes with adaptive learning
        - **Tutoring Sessions**: Context-aware AI conversations for learning support
        - **Progress Tracking**: Comprehensive analytics and learning insights
        
        ## Authentication
        This API uses JWT (JSON Web Tokens) for authentication. To authenticate:
        1. Obtain a token by logging in via `/api/v1/accounts/auth/login/`
        2. Include the token in the Authorization header: `Bearer <token>`
        
        ## Rate Limiting
        API requests are rate-limited to prevent abuse. Current limits:
        - 100 requests per minute for authenticated users
        - 20 requests per minute for unauthenticated users
        
        ## Pagination
        List endpoints support pagination with the following parameters:
        - `page`: Page number (default: 1)
        - `page_size`: Number of items per page (default: 20, max: 100)
        
        ## Error Handling
        All errors follow a consistent format:
        ```json
        {
            "error": true,
            "message": "Error description",
            "details": "Additional error details"
        }
        ```
        """,
        terms_of_service="https://aksio.app/terms/",
        contact=openapi.Contact(email="support@aksio.app"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[SessionAuthentication, JWTAuthentication],
)
