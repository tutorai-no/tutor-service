from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer that provides common fields and functionality.
    """

    class Meta:
        abstract = True
        read_only_fields = ["id", "created_at", "updated_at"]


class TimestampedSerializer(serializers.ModelSerializer):
    """
    Serializer for models that include timestamp fields.
    """

    class Meta:
        abstract = True
        read_only_fields = ["created_at", "updated_at"]


# Monitoring and Health Check Serializers


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for public health check response."""

    status = serializers.CharField(
        help_text="Overall health status: healthy, degraded, or unhealthy"
    )
    timestamp = serializers.DateTimeField(help_text="Timestamp of the health check")
    uptime = serializers.CharField(help_text="System uptime in human-readable format")


class DetailedHealthCheckSerializer(serializers.Serializer):
    """Serializer for detailed health check response."""

    status = serializers.CharField(help_text="Overall health status")
    timestamp = serializers.DateTimeField(help_text="Timestamp of the health check")
    uptime = serializers.CharField(help_text="System uptime")
    version = serializers.CharField(help_text="Application version")
    checks = serializers.DictField(help_text="Individual health check results")


class PerformanceMetricsSerializer(serializers.Serializer):
    """Serializer for performance metrics response."""

    timestamp = serializers.DateTimeField(help_text="Timestamp of the analysis")
    status = serializers.CharField(
        help_text="Performance status: healthy, degraded, or unhealthy"
    )
    alerts = serializers.ListField(help_text="List of performance alerts")
    metrics = serializers.DictField(help_text="Performance metrics data")
    recommendations = serializers.ListField(
        help_text="Performance improvement recommendations"
    )


class CacheStatsSerializer(serializers.Serializer):
    """Serializer for cache statistics response."""

    redis_info = serializers.DictField(help_text="Redis server information")
    cache_performance = serializers.DictField(help_text="Cache performance metrics")
    cache_usage_by_type = serializers.DictField(
        help_text="Cache usage breakdown by type"
    )


class ThrottleStatusSerializer(serializers.Serializer):
    """Serializer for user throttle status response."""

    burst = serializers.DictField(required=False, help_text="Burst rate limit status")
    sustained = serializers.DictField(
        required=False, help_text="Sustained rate limit status"
    )
    ai_service = serializers.DictField(
        required=False, help_text="AI service rate limit status"
    )
    document_processing = serializers.DictField(
        required=False, help_text="Document processing rate limit status"
    )
    premium = serializers.DictField(
        required=False, help_text="Premium user rate limit status"
    )


class SystemInfoSerializer(serializers.Serializer):
    """Serializer for system information response."""

    platform = serializers.DictField(help_text="Platform information")
    python = serializers.DictField(help_text="Python version information")
    django = serializers.DictField(help_text="Django version information")
    database = serializers.DictField(help_text="Database information")
    environment = serializers.DictField(help_text="Environment configuration")


class ClearCacheRequestSerializer(serializers.Serializer):
    """Serializer for cache clearing request."""

    cache_type = serializers.ChoiceField(
        choices=["all", "user", "course", "api", "custom"],
        default="all",
        help_text="Type of cache to clear",
    )
    pattern = serializers.CharField(
        required=False,
        help_text="Cache key pattern to clear (required for 'custom' cache_type)",
    )

    def validate(self, data):
        if data.get("cache_type") == "custom" and not data.get("pattern"):
            raise serializers.ValidationError(
                "Pattern is required when cache_type is 'custom'"
            )
        return data


class ClearCacheResponseSerializer(serializers.Serializer):
    """Serializer for cache clearing response."""

    message = serializers.CharField(help_text="Success message")


class ResetThrottlesRequestSerializer(serializers.Serializer):
    """Serializer for throttle reset request."""

    user_id = serializers.CharField(
        help_text="ID of the user whose throttles should be reset"
    )


class ResetThrottlesResponseSerializer(serializers.Serializer):
    """Serializer for throttle reset response."""

    message = serializers.CharField(help_text="Success message")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    error = serializers.CharField(help_text="Error message")
    detail = serializers.CharField(required=False, help_text="Additional error details")


class MonitoringEndpointsSerializer(serializers.Serializer):
    """Serializer for monitoring endpoints list."""

    monitoring_endpoints = serializers.DictField(
        help_text="Available monitoring endpoints"
    )
    description = serializers.CharField(help_text="API description")
