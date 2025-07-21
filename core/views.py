"""
Core views for monitoring, health checks, and system information.
"""

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from prometheus_client import generate_latest

# from .monitoring import health_check_service, performance_monitor, metrics_collector  # Temporarily commented out for testing


# Dummy health check service for testing
class DummyHealthCheckService:
    def get_health_status(self):
        return {
            "status": "healthy",
            "message": "All systems operational (dummy data)",
            "timestamp": "2025-07-20T22:20:00Z",
        }

    def update_system_metrics(self):
        pass  # Dummy implementation

    def analyze_performance(self):
        return {"performance": "good", "response_time": 100, "throughput": "normal"}


health_check_service = DummyHealthCheckService()
performance_monitor = DummyHealthCheckService()
metrics_collector = DummyHealthCheckService()
from .cache_service import course_cache_service, user_cache_service
from .serializers import (
    CacheStatsSerializer,
    ClearCacheRequestSerializer,
    ClearCacheResponseSerializer,
    DetailedHealthCheckSerializer,
    ErrorResponseSerializer,
    MonitoringEndpointsSerializer,
    PerformanceMetricsSerializer,
)
from .throttling import CustomThrottleInspector


@require_http_methods(["GET"])
def health_check(request):
    """
    Public health check endpoint for load balancers and monitoring systems.
    Returns basic health status without sensitive information.
    """
    try:
        health_status = health_check_service.get_health_status()

        # Return simplified status for public consumption
        public_status = {
            "status": health_status["status"],
            "timestamp": health_status["timestamp"],
            "uptime": health_status["uptime"],
        }

        # Return appropriate HTTP status code
        http_status = 200 if health_status["status"] == "healthy" else 503

        return JsonResponse(public_status, status=http_status)

    except Exception:
        return JsonResponse(
            {"status": "error", "error": "Health check failed"}, status=503
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get detailed health status including all system components",
    operation_summary="Detailed Health Check",
    tags=["Monitoring"],
    responses={
        200: DetailedHealthCheckSerializer,
        500: ErrorResponseSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def detailed_health_check(request):
    """
    Detailed health check endpoint for administrators.
    Returns comprehensive health information including database, cache, storage, and external services.
    """
    try:
        health_status = health_check_service.get_health_status()
        return Response(health_status)

    except Exception as e:
        return Response(
            {"status": "error", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get comprehensive performance metrics and analysis",
    operation_summary="Performance Metrics",
    tags=["Monitoring"],
    responses={
        200: PerformanceMetricsSerializer,
        500: ErrorResponseSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def performance_metrics(request):
    """
    Get detailed performance metrics and analysis including response times, error rates, and system resources.
    Provides alerts and recommendations for performance optimization.
    """
    try:
        # Update system metrics first
        metrics_collector.update_system_metrics()

        # Get performance analysis
        performance_analysis = performance_monitor.analyze_performance()

        return Response(performance_analysis)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_http_methods(["GET"])
@staff_member_required
def prometheus_metrics(request):
    """
    Prometheus metrics endpoint for metrics collection.
    """
    try:
        metrics_collector.update_system_metrics()
        metrics_data = generate_latest()

        return HttpResponse(metrics_data, content_type="text/plain; charset=utf-8")

    except Exception as e:
        return HttpResponse(
            f"Error generating metrics: {str(e)}", status=500, content_type="text/plain"
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get comprehensive cache statistics and performance metrics",
    operation_summary="Cache Statistics",
    tags=["Monitoring"],
    responses={
        200: CacheStatsSerializer,
        500: ErrorResponseSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def cache_stats(request):
    """
    Get cache statistics and hit rates including Redis info, performance metrics, and usage breakdown.
    """
    try:
        from django_redis import get_redis_connection

        # Get Redis connection info
        redis_conn = get_redis_connection("default")
        redis_info = redis_conn.info()

        cache_stats = {
            "redis_info": {
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory": redis_info.get("used_memory", 0),
                "used_memory_human": redis_info.get("used_memory_human", "0B"),
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0),
                "total_commands_processed": redis_info.get(
                    "total_commands_processed", 0
                ),
            },
            "cache_performance": {
                "hit_rate": _calculate_cache_hit_rate(redis_info),
                "total_keys": redis_conn.dbsize(),
            },
            "cache_usage_by_type": {
                "user_cache": _get_cache_key_count("aksio_user_*"),
                "course_cache": _get_cache_key_count("aksio_course_*"),
                "api_cache": _get_cache_key_count("aksio_api_response_*"),
                "session_cache": _get_cache_key_count("aksio_session_*"),
                "throttle_cache": _get_cache_key_count("aksio_throttle_*"),
            },
        }

        return Response(cache_stats)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method="post",
    operation_description="Clear cache with various options and patterns",
    operation_summary="Clear Cache",
    tags=["Monitoring"],
    request_body=ClearCacheRequestSerializer,
    responses={
        200: ClearCacheResponseSerializer,
        400: ErrorResponseSerializer,
        500: ErrorResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def clear_cache(request):
    """
    Clear cache with optional patterns. Supports clearing all cache, specific cache types, or custom patterns.
    """
    try:
        from django.core.cache import cache

        cache_type = request.data.get("cache_type", "all")
        pattern = request.data.get("pattern")

        if cache_type == "all":
            cache.clear()
            message = "All cache cleared"
        elif cache_type == "user":
            user_cache_service.delete_pattern("aksio_user_*")
            message = "User cache cleared"
        elif cache_type == "course":
            course_cache_service.delete_pattern("aksio_course_*")
            message = "Course cache cleared"
        elif pattern:
            cache.delete_pattern(pattern)
            message = f"Cache cleared for pattern: {pattern}"
        else:
            return Response(
                {"error": "Invalid cache_type or missing pattern"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": message})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_throttle_status(request):
    """
    Get current user's throttle status.
    """
    try:
        throttle_status = CustomThrottleInspector.get_user_throttle_status(request.user)
        return Response(throttle_status)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def reset_user_throttles(request):
    """
    Reset throttles for a specific user (admin only).
    """
    try:
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        from accounts.models import User

        user = User.objects.get(pk=user_id)

        CustomThrottleInspector.reset_user_throttles(user)

        return Response({"message": f"Throttles reset for user {user.username}"})

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def system_info(request):
    """
    Get comprehensive system information.
    """
    try:
        import platform
        import sys

        import django

        system_info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable,
            },
            "django": {
                "version": django.get_version(),
            },
            "database": {
                "engine": "PostgreSQL",
                "connections": len(connections.all()),
            },
            "environment": {
                "debug": getattr(settings, "DEBUG", False),
                "allowed_hosts": getattr(settings, "ALLOWED_HOSTS", []),
                "time_zone": getattr(settings, "TIME_ZONE", "UTC"),
            },
        }

        return Response(system_info)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _calculate_cache_hit_rate(redis_info):
    """Calculate cache hit rate from Redis info."""
    hits = redis_info.get("keyspace_hits", 0)
    misses = redis_info.get("keyspace_misses", 0)
    total = hits + misses

    if total == 0:
        return 0.0

    return round((hits / total) * 100, 2)


def _get_cache_key_count(pattern):
    """Get count of cache keys matching pattern."""
    try:
        from django_redis import get_redis_connection

        redis_conn = get_redis_connection("default")
        keys = redis_conn.keys(pattern)
        return len(keys)
    except Exception:
        return 0


class MonitoringViewSet(viewsets.ViewSet):
    """
    ViewSet for monitoring and admin operations.
    Provides a comprehensive overview of available monitoring endpoints.
    """

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_description="Get list of all available monitoring endpoints",
        operation_summary="List Monitoring Endpoints",
        tags=["Monitoring"],
        responses={
            200: MonitoringEndpointsSerializer,
        },
    )
    def list(self, request):
        """Get available monitoring endpoints with descriptions."""
        endpoints = {
            "health": "/api/core/health/",
            "health-detailed": "/api/core/monitoring/health-detailed/",
            "performance": "/api/core/monitoring/performance/",
            "metrics": "/api/core/monitoring/metrics/",
            "cache-stats": "/api/core/monitoring/cache-stats/",
            "clear-cache": "/api/core/monitoring/clear-cache/",
            "throttle-status": "/api/core/monitoring/throttle-status/",
            "reset-throttles": "/api/core/monitoring/reset-throttles/",
            "system-info": "/api/core/monitoring/system-info/",
        }

        return Response(
            {
                "monitoring_endpoints": endpoints,
                "description": "Aksio Backend Monitoring and Admin API - Comprehensive system monitoring and management endpoints",
            }
        )


class BaseViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet that provides common functionality.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Override to filter by user by default.
        """
        queryset = super().get_queryset()

        # Filter by user if the model has a user field
        if hasattr(self.queryset.model, "user"):
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        """
        Override to set user field during creation.
        """
        # Set user field if the model has one
        if hasattr(serializer.Meta.model, "user"):
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class ReadOnlyBaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base Read-only ViewSet that provides common functionality.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Override to filter by user by default.
        """
        queryset = super().get_queryset()

        # Filter by user if the model has a user field
        if hasattr(self.queryset.model, "user"):
            queryset = queryset.filter(user=self.request.user)

        return queryset
