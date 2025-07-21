"""
Advanced API throttling and rate limiting configuration.

This module provides comprehensive rate limiting with different tiers for various
API endpoints and user types.
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

User = get_user_model()


class CustomBaseThrottle:
    """Base class for custom throttling with enhanced features."""

    def get_cache_key(self, request, view):
        """Generate cache key for throttling."""
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}

    def get_ident(self, request):
        """Get client identifier from request."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        remote_addr = request.META.get("REMOTE_ADDR")
        num_proxies = getattr(self, "num_proxies", None)

        if num_proxies is not None and xff:
            # Use the Nth IP from the right when behind proxies
            addrs = xff.split(",")
            client_addr = addrs[-min(num_proxies, len(addrs))]
            return client_addr.strip()

        return xff.split(",")[0].strip() if xff else remote_addr


class BurstRateThrottle(CustomBaseThrottle, UserRateThrottle):
    """Handle burst requests - short term high rate limit."""

    scope = "burst"
    rate = "60/min"  # 60 requests per minute


class SustainedRateThrottle(CustomBaseThrottle, UserRateThrottle):
    """Handle sustained requests - longer term moderate rate limit."""

    scope = "sustained"
    rate = "1000/hour"  # 1000 requests per hour


class LoginRateThrottle(CustomBaseThrottle, AnonRateThrottle):
    """Rate limit for login attempts to prevent brute force."""

    scope = "login"
    rate = "5/min"  # 5 login attempts per minute


class AnonBurstRateThrottle(CustomBaseThrottle, AnonRateThrottle):
    """Rate limit for anonymous users - more restrictive."""

    scope = "anon_burst"
    rate = "20/min"  # 20 requests per minute for anonymous users


class AnonSustainedRateThrottle(CustomBaseThrottle, AnonRateThrottle):
    """Sustained rate limit for anonymous users."""

    scope = "anon_sustained"
    rate = "100/hour"  # 100 requests per hour for anonymous users


class PremiumUserRateThrottle(CustomBaseThrottle, UserRateThrottle):
    """Higher rate limits for premium users."""

    scope = "premium"
    rate = "5000/hour"  # 5000 requests per hour for premium users

    def allow_request(self, request, view):
        """Check if user is premium and apply appropriate limits."""
        if request.user.is_authenticated and hasattr(request.user, "is_premium_user"):
            if request.user.is_premium_user:
                return super().allow_request(request, view)

        # Fall back to regular user throttling
        regular_throttle = SustainedRateThrottle()
        return regular_throttle.allow_request(request, view)


class AIServiceThrottle(CustomBaseThrottle, UserRateThrottle):
    """Special throttling for AI-intensive endpoints."""

    scope = "ai_service"
    rate = "100/hour"  # Limited AI requests due to cost

    def get_cache_key(self, request, view):
        """Use user-specific cache key for AI requests."""
        if request.user.is_authenticated:
            return f"throttle_ai_{request.user.pk}"
        return super().get_cache_key(request, view)


class DocumentProcessingThrottle(CustomBaseThrottle, UserRateThrottle):
    """Throttle document processing to prevent abuse."""

    scope = "document_processing"
    rate = "50/hour"  # 50 document uploads per hour

    def allow_request(self, request, view):
        """Enhanced validation for document processing."""
        # Check file size in request
        if hasattr(request, "FILES") and request.FILES:
            total_size = sum(f.size for f in request.FILES.values())
            # Block requests with total files > 100MB
            if total_size > 100 * 1024 * 1024:
                return False

        return super().allow_request(request, view)


class DynamicRateThrottle(CustomBaseThrottle, UserRateThrottle):
    """Dynamic rate limiting based on user behavior and system load."""

    def __init__(self):
        super().__init__()
        self.base_rate = 1000  # Base requests per hour

    def get_rate_limit(self, request):
        """Calculate dynamic rate limit based on user behavior."""
        if not request.user.is_authenticated:
            return "100/hour"  # Anonymous users get low limit

        user = request.user

        # Check user's recent behavior
        violations_key = f"rate_violations_{user.pk}"
        violations = cache.get(violations_key, 0)

        # Reduce rate limit for users with recent violations
        if violations > 5:
            rate = max(100, self.base_rate // 4)  # Quarter the limit
        elif violations > 2:
            rate = max(500, self.base_rate // 2)  # Half the limit
        else:
            rate = self.base_rate

        # Premium users get higher limits
        if hasattr(user, "is_premium_user") and user.is_premium_user:
            rate *= 5

        return f"{rate}/hour"

    def allow_request(self, request, view):
        """Dynamic rate limiting with violation tracking."""
        self.rate = self.get_rate_limit(request)

        allowed = super().allow_request(request, view)

        # Track violations for authenticated users
        if not allowed and request.user.is_authenticated:
            violations_key = f"rate_violations_{request.user.pk}"
            violations = cache.get(violations_key, 0)
            cache.set(violations_key, violations + 1, 3600)  # Store for 1 hour

        return allowed


class CustomThrottleInspector:
    """Utility class to inspect and manage throttling state."""

    @staticmethod
    def get_user_throttle_status(user) -> dict:
        """Get current throttle status for a user."""
        status = {}

        throttle_types = [
            "burst",
            "sustained",
            "ai_service",
            "document_processing",
            "premium",
        ]

        for throttle_type in throttle_types:
            cache_key = f"throttle_{throttle_type}_{user.pk}"
            throttle_data = cache.get(cache_key)

            if throttle_data:
                status[throttle_type] = {
                    "requests_made": throttle_data.get("requests", 0),
                    "reset_time": throttle_data.get("reset_time"),
                    "limit_exceeded": throttle_data.get("exceeded", False),
                }

        return status

    @staticmethod
    def reset_user_throttles(user):
        """Reset all throttles for a user (admin function)."""
        throttle_types = [
            "burst",
            "sustained",
            "ai_service",
            "document_processing",
            "premium",
        ]

        for throttle_type in throttle_types:
            cache_key = f"throttle_{throttle_type}_{user.pk}"
            cache.delete(cache_key)

        # Also reset violations
        violations_key = f"rate_violations_{user.pk}"
        cache.delete(violations_key)
