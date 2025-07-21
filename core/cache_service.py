"""
Advanced caching service with intelligent cache management.

This module provides a comprehensive caching layer with various strategies
for different types of data and use cases.
"""

import hashlib
import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.conf import settings
from django.core.cache import caches

logger = logging.getLogger(__name__)


class CacheService:
    """
    Centralized cache service with intelligent cache management.
    """

    def __init__(self, cache_alias: str = "default"):
        self.cache = caches[cache_alias]
        self.default_timeout = getattr(settings, "CACHE_DEFAULT_TIMEOUT", 300)

    def get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key."""
        # Create a hash of the arguments to ensure consistent key generation
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        if kwargs:
            key_data += f":{json.dumps(kwargs, sort_keys=True)}"

        # Hash long keys to avoid Redis key length limits
        if len(key_data) > 250:
            key_data = f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

        return key_data

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with error handling."""
        try:
            return self.cache.get(key, default)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    def set(self, key: str, value: Any, timeout: int | None = None) -> bool:
        """Set value in cache with error handling."""
        try:
            timeout = timeout or self.default_timeout
            self.cache.set(key, value, timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            if hasattr(self.cache, "delete_pattern"):
                return self.cache.delete_pattern(pattern)
            else:
                # Fallback for caches that don't support pattern deletion
                keys = self.cache.keys(pattern)
                if keys:
                    self.cache.delete_many(keys)
                    return len(keys)
                return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
            return 0

    def get_or_set(
        self, key: str, callable_func: Callable, timeout: int | None = None
    ) -> Any:
        """Get value from cache or set it using the callable."""
        value = self.get(key)
        if value is None:
            value = callable_func()
            self.set(key, value, timeout)
        return value


class UserCacheService(CacheService):
    """Cache service specifically for user-related data."""

    def __init__(self):
        super().__init__()
        self.prefix = "user"

    def get_user_profile_cache_key(self, user_id: str) -> str:
        """Get cache key for user profile."""
        return self.get_cache_key(f"{self.prefix}_profile", user_id)

    def get_user_permissions_cache_key(self, user_id: str) -> str:
        """Get cache key for user permissions."""
        return self.get_cache_key(f"{self.prefix}_permissions", user_id)

    def cache_user_profile(self, user_id: str, profile_data: dict, timeout: int = 1800):
        """Cache user profile data for 30 minutes."""
        key = self.get_user_profile_cache_key(user_id)
        self.set(key, profile_data, timeout)

    def get_user_profile(self, user_id: str) -> dict | None:
        """Get cached user profile."""
        key = self.get_user_profile_cache_key(user_id)
        return self.get(key)

    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user."""
        pattern = f"{self.prefix}_*_{user_id}"
        self.delete_pattern(pattern)


class CourseCacheService(CacheService):
    """Cache service for course-related data."""

    def __init__(self):
        super().__init__()
        self.prefix = "course"

    def get_course_cache_key(self, course_id: str, user_id: str = None) -> str:
        """Get cache key for course data."""
        if user_id:
            return self.get_cache_key(f"{self.prefix}", course_id, user_id)
        return self.get_cache_key(f"{self.prefix}", course_id)

    def get_course_stats_cache_key(self, course_id: str) -> str:
        """Get cache key for course statistics."""
        return self.get_cache_key(f"{self.prefix}_stats", course_id)

    def cache_course_data(self, course_id: str, course_data: dict, timeout: int = 900):
        """Cache course data for 15 minutes."""
        key = self.get_course_cache_key(course_id)
        self.set(key, course_data, timeout)

    def cache_course_stats(self, course_id: str, stats_data: dict, timeout: int = 1800):
        """Cache course statistics for 30 minutes."""
        key = self.get_course_stats_cache_key(course_id)
        self.set(key, stats_data, timeout)

    def invalidate_course_cache(self, course_id: str):
        """Invalidate all cache entries for a course."""
        pattern = f"{self.prefix}_*_{course_id}"
        self.delete_pattern(pattern)


class APIResponseCacheService(CacheService):
    """Cache service for API responses."""

    def __init__(self):
        super().__init__()
        self.prefix = "api_response"

    def get_api_cache_key(
        self, endpoint: str, user_id: str, query_params: dict = None
    ) -> str:
        """Get cache key for API response."""
        params = query_params or {}
        return self.get_cache_key(f"{self.prefix}", endpoint, user_id, **params)

    def cache_api_response(
        self,
        endpoint: str,
        user_id: str,
        response_data: dict,
        query_params: dict = None,
        timeout: int = 300,
    ):
        """Cache API response for 5 minutes by default."""
        key = self.get_api_cache_key(endpoint, user_id, query_params)
        self.set(key, response_data, timeout)

    def get_cached_api_response(
        self, endpoint: str, user_id: str, query_params: dict = None
    ):
        """Get cached API response."""
        key = self.get_api_cache_key(endpoint, user_id, query_params)
        return self.get(key)


def cached_method(timeout: int = 300, key_prefix: str = None):
    """
    Decorator for caching method results.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Optional prefix for cache key
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            class_name = self.__class__.__name__
            method_name = func.__name__
            prefix = key_prefix or f"{class_name}_{method_name}"

            cache_service = CacheService()
            cache_key = cache_service.get_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Calculate result and cache it
            result = func(self, *args, **kwargs)
            cache_service.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def cached_function(timeout: int = 300, key_prefix: str = None):
    """
    Decorator for caching function results.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Optional prefix for cache key
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__

            cache_service = CacheService()
            cache_key = cache_service.get_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Calculate result and cache it
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


class CacheWarmupService:
    """Service for warming up frequently accessed cache entries."""

    def __init__(self):
        self.user_cache = UserCacheService()
        self.course_cache = CourseCacheService()
        self.api_cache = APIResponseCacheService()

    def warmup_user_data(self, user_ids: list[str]):
        """Warm up cache for multiple users."""
        from accounts.models import User

        for user_id in user_ids:
            try:
                user = User.objects.select_related("profile").get(pk=user_id)
                profile_data = {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_premium": user.is_premium_user,
                }

                self.user_cache.cache_user_profile(user_id, profile_data)
                logger.info(f"Warmed up cache for user {user_id}")

            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found during cache warmup")

    def warmup_popular_courses(self, course_ids: list[str]):
        """Warm up cache for popular courses."""
        from courses.models import Course

        for course_id in course_ids:
            try:
                course = Course.objects.select_related("user").get(pk=course_id)
                course_data = {
                    "id": str(course.id),
                    "name": course.name,
                    "description": course.description,
                    "created_at": course.created_at.isoformat(),
                }

                self.course_cache.cache_course_data(course_id, course_data)
                logger.info(f"Warmed up cache for course {course_id}")

            except Course.DoesNotExist:
                logger.warning(f"Course {course_id} not found during cache warmup")


# Global cache service instances
user_cache_service = UserCacheService()
course_cache_service = CourseCacheService()
api_cache_service = APIResponseCacheService()
cache_warmup_service = CacheWarmupService()
