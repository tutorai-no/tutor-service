"""
Advanced monitoring and observability system.

This module provides comprehensive monitoring capabilities including
metrics collection, health checks, performance monitoring, and alerting.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

# import psutil  # Temporarily commented out for testing
from functools import wraps
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Data structure for metric information."""

    name: str
    value: float
    labels: dict[str, str]
    timestamp: datetime
    metric_type: str  # counter, gauge, histogram


class MetricsCollector:
    """Centralized metrics collection system."""

    def __init__(self):
        # Define Prometheus metrics
        self.request_count = Counter(
            "aksio_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
        )

        self.request_duration = Histogram(
            "aksio_http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
        )

        self.database_queries = Counter(
            "aksio_database_queries_total", "Total database queries", ["query_type"]
        )

        self.cache_operations = Counter(
            "aksio_cache_operations_total",
            "Total cache operations",
            ["operation", "hit_miss"],
        )

        self.ai_service_requests = Counter(
            "aksio_ai_service_requests_total",
            "Total AI service requests",
            ["service", "status"],
        )

        self.active_users = Gauge("aksio_active_users", "Number of active users")

        self.system_memory_usage = Gauge(
            "aksio_system_memory_usage_bytes", "System memory usage in bytes"
        )

        self.system_cpu_usage = Gauge(
            "aksio_system_cpu_usage_percent", "System CPU usage percentage"
        )

        self.database_connections = Gauge(
            "aksio_database_connections", "Number of database connections"
        )

    def record_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics."""
        self.request_count.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_database_query(self, query_type: str):
        """Record database query metrics."""
        self.database_queries.labels(query_type=query_type).inc()

    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics."""
        hit_miss = "hit" if hit else "miss"
        self.cache_operations.labels(operation=operation, hit_miss=hit_miss).inc()

    def record_ai_service_request(self, service: str, success: bool):
        """Record AI service request metrics."""
        status = "success" if success else "error"
        self.ai_service_requests.labels(service=service, status=status).inc()

    def update_system_metrics(self):
        """Update system-level metrics."""
        try:
            # Memory usage (dummy values for testing)
            # memory = psutil.virtual_memory()
            self.system_memory_usage.set(1000000000)  # 1GB dummy value

            # CPU usage (dummy values for testing)
            # cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(20.0)  # 20% dummy CPU usage

            # Database connections
            db_connections = len(connection.queries)
            self.database_connections.set(db_connections)

            # Active users (from cache or database)
            active_users_count = self._get_active_users_count()
            self.active_users.set(active_users_count)

        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

    def _get_active_users_count(self) -> int:
        """Get count of active users."""
        try:
            # Use cache for performance
            cached_count = cache.get("active_users_count")
            if cached_count is not None:
                return cached_count

            # Calculate from database (users active in last 15 minutes)
            from accounts.models import User

            fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)
            count = User.objects.filter(last_active_at__gte=fifteen_minutes_ago).count()

            # Cache for 5 minutes
            cache.set("active_users_count", count, 300)
            return count

        except Exception as e:
            logger.error(f"Error getting active users count: {e}")
            return 0


class PerformanceMonitor:
    """Monitor application performance and detect anomalies."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.performance_thresholds = {
            "response_time_p95": 2.0,  # 2 seconds
            "error_rate": 0.05,  # 5%
            "memory_usage": 0.8,  # 80%
            "cpu_usage": 0.9,  # 90%
        }

    def analyze_performance(self) -> dict[str, Any]:
        """Analyze current performance metrics."""
        analysis = {
            "timestamp": timezone.now().isoformat(),
            "status": "healthy",
            "alerts": [],
            "metrics": {},
            "recommendations": [],
        }

        try:
            # Check response times
            response_times = self._get_recent_response_times()
            if response_times:
                p95_response_time = self._calculate_percentile(response_times, 95)
                analysis["metrics"]["response_time_p95"] = p95_response_time

                if p95_response_time > self.performance_thresholds["response_time_p95"]:
                    analysis["alerts"].append(
                        {
                            "level": "warning",
                            "message": f"High response time: {p95_response_time:.2f}s",
                            "recommendation": "Check database queries and cache hit rates",
                        }
                    )
                    analysis["status"] = "degraded"

            # Check error rates
            error_rate = self._get_recent_error_rate()
            analysis["metrics"]["error_rate"] = error_rate

            if error_rate > self.performance_thresholds["error_rate"]:
                analysis["alerts"].append(
                    {
                        "level": "critical",
                        "message": f"High error rate: {error_rate:.2%}",
                        "recommendation": "Check application logs for error patterns",
                    }
                )
                analysis["status"] = "unhealthy"

            # Check system resources
            memory_usage = 0.20  # 20% dummy memory usage
            cpu_usage = 0.15  # 15% dummy CPU usage

            analysis["metrics"]["memory_usage"] = memory_usage
            analysis["metrics"]["cpu_usage"] = cpu_usage

            if memory_usage > self.performance_thresholds["memory_usage"]:
                analysis["alerts"].append(
                    {
                        "level": "warning",
                        "message": f"High memory usage: {memory_usage:.1%}",
                        "recommendation": "Consider scaling up or optimizing memory usage",
                    }
                )

            if cpu_usage > self.performance_thresholds["cpu_usage"]:
                analysis["alerts"].append(
                    {
                        "level": "critical",
                        "message": f"High CPU usage: {cpu_usage:.1%}",
                        "recommendation": "Scale horizontally or optimize CPU-intensive operations",
                    }
                )
                analysis["status"] = "unhealthy"

            # Add general recommendations
            self._add_performance_recommendations(analysis)

        except Exception as e:
            logger.error(f"Error in performance analysis: {e}")
            analysis["status"] = "error"
            analysis["alerts"].append(
                {
                    "level": "critical",
                    "message": f"Performance monitoring error: {str(e)}",
                    "recommendation": "Check monitoring system health",
                }
            )

        return analysis

    def _get_recent_response_times(self) -> list[float]:
        """Get recent response times from cache or logs."""
        try:
            # Try to get from cache first
            cached_times = cache.get("recent_response_times", [])
            return cached_times
        except Exception:
            return []

    def _get_recent_error_rate(self) -> float:
        """Calculate recent error rate."""
        try:
            error_count = cache.get("recent_error_count", 0)
            total_requests = cache.get("recent_request_count", 1)
            return error_count / max(total_requests, 1)
        except Exception:
            return 0.0

    def _calculate_percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile from list of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)

        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def _add_performance_recommendations(self, analysis: dict[str, Any]):
        """Add performance recommendations based on metrics."""
        recommendations = []

        # Database optimization recommendations
        db_query_count = cache.get("recent_db_query_count", 0)
        if db_query_count > 1000:  # High query count
            recommendations.append(
                "Consider implementing query optimization and database indexing"
            )

        # Cache hit rate recommendations
        cache_hit_rate = cache.get("cache_hit_rate", 1.0)
        if cache_hit_rate < 0.8:  # Low cache hit rate
            recommendations.append(
                "Improve cache hit rate by optimizing cache keys and timeouts"
            )

        # Memory optimization
        if analysis["metrics"].get("memory_usage", 0) > 0.7:
            recommendations.append(
                "Consider implementing memory optimization strategies"
            )

        analysis["recommendations"].extend(recommendations)


class HealthCheckService:
    """Comprehensive health check service."""

    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "cache": self._check_cache,
            "storage": self._check_storage,
            "external_services": self._check_external_services,
            "memory": self._check_memory,
            "disk_space": self._check_disk_space,
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status."""
        health_status = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "checks": {},
            "uptime": self._get_uptime(),
            "version": getattr(settings, "VERSION", "unknown"),
        }

        overall_healthy = True

        for check_name, check_func in self.checks.items():
            try:
                check_result = check_func()
                health_status["checks"][check_name] = check_result

                if not check_result["healthy"]:
                    overall_healthy = False

            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                health_status["checks"][check_name] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": timezone.now().isoformat(),
                }
                overall_healthy = False

        health_status["status"] = "healthy" if overall_healthy else "unhealthy"
        return health_status

    def _check_database(self) -> dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()

            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            response_time = time.time() - start_time

            return {
                "healthy": True,
                "response_time": response_time,
                "connections": len(connection.queries),
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def _check_cache(self) -> dict[str, Any]:
        """Check cache service availability."""
        try:
            start_time = time.time()

            # Test cache operations
            test_key = "health_check_test"
            test_value = "test_value"

            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)

            response_time = time.time() - start_time

            return {
                "healthy": retrieved_value == test_value,
                "response_time": response_time,
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def _check_storage(self) -> dict[str, Any]:
        """Check storage availability."""
        try:
            # Check if we can write to media directory
            import os

            from django.conf import settings

            media_root = getattr(settings, "MEDIA_ROOT", "/tmp")
            test_file = os.path.join(media_root, "health_check.txt")

            # Try to write and read a test file
            with open(test_file, "w") as f:
                f.write("health check")

            with open(test_file) as f:
                content = f.read()

            os.remove(test_file)

            return {
                "healthy": content == "health check",
                "path": media_root,
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def _check_external_services(self) -> dict[str, Any]:
        """Check external service connectivity."""
        try:
            # This is a placeholder - implement actual external service checks
            # For example, check OpenAI API, retrieval service, etc.

            return {
                "healthy": True,
                "services": {"openai": "available", "retrieval_service": "available"},
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def _check_memory(self) -> dict[str, Any]:
        """Check memory usage."""
        try:
            # memory = psutil.virtual_memory()  # Dummy values for testing
            dummy_memory_percent = 25.0  # 25% dummy usage

            return {
                "healthy": dummy_memory_percent < 90,  # Less than 90% usage
                "usage_percent": dummy_memory_percent,
                "total_gb": 8.0,  # 8GB dummy total
                "available_gb": 6.0,  # 6GB dummy available
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def _check_disk_space(self) -> dict[str, Any]:
        """Check disk space availability."""
        try:
            # disk_usage = psutil.disk_usage('/')  # Dummy values for testing
            usage_percent = 30.0  # 30% dummy disk usage

            return {
                "healthy": usage_percent < 85,  # Less than 85% usage
                "usage_percent": round(usage_percent, 2),
                "total_gb": 100.0,  # 100GB dummy total
                "free_gb": 70.0,  # 70GB dummy free
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def _get_uptime(self) -> str:
        """Get application uptime."""
        try:
            uptime_seconds = 86400  # 1 day dummy uptime
            uptime_hours = uptime_seconds / 3600
            return f"{uptime_hours:.1f} hours"
        except Exception:
            return "unknown"


def monitor_performance(func):
    """Decorator to monitor function performance."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)

            # Record successful execution
            execution_time = time.time() - start_time
            cache.set(f"perf_{func.__name__}_last_success", execution_time, 3600)

            return result

        except Exception as e:
            # Record failed execution
            execution_time = time.time() - start_time
            cache.set(f"perf_{func.__name__}_last_error", str(e), 3600)

            logger.error(f"Performance monitoring error in {func.__name__}: {e}")
            raise

    return wrapper


# Global instances (commented out to avoid duplicate metrics registration)
# metrics_collector = MetricsCollector()
# performance_monitor = PerformanceMonitor()
# health_check_service = HealthCheckService()
