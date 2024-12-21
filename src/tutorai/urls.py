"""
URL configuration for tutorai project.

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
from django.urls import path, re_path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_prometheus import urls as prometheus_urls  # Import Prometheus URLs

# Swagger schema view configuration
schema_view = get_schema_view(
    openapi.Info(
        title="TutorAI API",
        default_version="v1",
        description="Your API description",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(SessionAuthentication, JWTAuthentication),
    # Define the security schemes
)

urlpatterns = [
    # Admin panel route
    path("admin/", admin.site.urls),
    # Authentication URLs (using Django's built-in auth views)
    path(
        "accounts/", include("django.contrib.auth.urls")
    ),  # Includes login/logout views
    # API routes
    path("api/", include("api.urls"), name="api"),
    # Swagger routes
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
    path("", include(prometheus_urls)),
]
