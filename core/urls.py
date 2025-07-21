"""
URLs for core application including monitoring and health check endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r"monitoring", views.MonitoringViewSet, basename="monitoring")

urlpatterns = [
    # Public health check for load balancers
    path("health/", views.health_check, name="health_check"),
    # Admin-only monitoring endpoints
    path(
        "monitoring/health-detailed/",
        views.detailed_health_check,
        name="detailed_health_check",
    ),
    path(
        "monitoring/performance/", views.performance_metrics, name="performance_metrics"
    ),
    path("monitoring/metrics/", views.prometheus_metrics, name="prometheus_metrics"),
    path("monitoring/cache-stats/", views.cache_stats, name="cache_stats"),
    path("monitoring/clear-cache/", views.clear_cache, name="clear_cache"),
    path(
        "monitoring/throttle-status/",
        views.user_throttle_status,
        name="throttle_status",
    ),
    path(
        "monitoring/reset-throttles/",
        views.reset_user_throttles,
        name="reset_throttles",
    ),
    path("monitoring/system-info/", views.system_info, name="system_info"),
    # Include router URLs
    path("", include(router.urls)),
]
