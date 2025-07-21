"""
Comprehensive testing utilities and base classes for Aksio backend tests.

This module provides advanced testing infrastructure including fixtures,
mocks, factories, and custom test cases for robust testing.
"""

import uuid
from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class BaseTestCase(TestCase):
    """
    Base test case with common utilities and setup.
    """

    def setUp(self):
        """Set up common test data."""
        super().setUp()
        self.client = APIClient()

        # Clear cache before each test
        cache.clear()

        # Create test users
        self.admin_user = self.create_admin_user()
        self.regular_user = self.create_regular_user()
        self.premium_user = self.create_premium_user()

    def create_admin_user(self) -> User:
        """Create an admin user for testing."""
        return User.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

    def create_regular_user(self) -> User:
        """Create a regular user for testing."""
        return User.objects.create_user(
            username="user_test", email="user@test.com", password="testpass123"
        )

    def create_premium_user(self) -> User:
        """Create a premium user for testing."""
        user = User.objects.create_user(
            username="premium_test", email="premium@test.com", password="testpass123"
        )
        # Mock premium status
        user.is_premium_user = True
        user.save()
        return user

    def authenticate_user(self, user: User):
        """Authenticate a user for API testing."""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def assert_error_response(
        self, response, status_code: int, error_message: str = None
    ):
        """Assert that response is an error with expected format."""
        self.assertEqual(response.status_code, status_code)
        self.assertIn("error", response.data)

        if error_message:
            self.assertIn(error_message, str(response.data["error"]))

    def assert_success_response(self, response, status_code: int = 200):
        """Assert that response is successful."""
        self.assertEqual(response.status_code, status_code)

        # Should not contain error field
        if hasattr(response, "data") and isinstance(response.data, dict):
            self.assertNotIn("error", response.data)


class APITestCase(BaseTestCase, APITestCase):
    """
    Enhanced API test case with authentication and common assertions.
    """

    def setUp(self):
        """Set up API test case."""
        super().setUp()

        # Default authentication
        self.authenticate_user(self.regular_user)

    def assert_paginated_response(self, response, expected_count: int = None):
        """Assert that response is properly paginated."""
        self.assert_success_response(response)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)

        if expected_count is not None:
            self.assertEqual(response.data["count"], expected_count)

    def assert_throttled_response(self, response):
        """Assert that response indicates throttling."""
        self.assertEqual(response.status_code, 429)
        self.assertIn("detail", response.data)
        self.assertIn("throttled", str(response.data["detail"]).lower())


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    username = Faker("user_name")
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to handle password hashing."""
        password = kwargs.pop("password", "testpass123")
        user = model_class._default_manager.create_user(*args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class CourseFactory(DjangoModelFactory):
    """Factory for creating Course instances."""

    class Meta:
        model = "courses.Course"

    name = Faker("sentence", nb_words=3)
    description = Faker("text", max_nb_chars=500)
    user = SubFactory(UserFactory)
    visibility = "private"

    created_at = LazyAttribute(lambda obj: timezone.now())
    updated_at = LazyAttribute(lambda obj: timezone.now())


class DocumentFactory(DjangoModelFactory):
    """Factory for creating Document instances."""

    class Meta:
        model = "courses.Document"

    title = Faker("sentence", nb_words=4)
    content = Faker("text", max_nb_chars=2000)
    user = SubFactory(UserFactory)
    course = SubFactory(CourseFactory)

    file_type = "pdf"
    file_size = 1024000  # 1MB
    processing_status = "completed"


class FlashcardFactory(DjangoModelFactory):
    """Factory for creating Flashcard instances."""

    class Meta:
        model = "assessments.Flashcard"

    question = Faker("sentence", nb_words=8)
    answer = Faker("text", max_nb_chars=300)
    user = SubFactory(UserFactory)
    course = SubFactory(CourseFactory)

    difficulty_level = "medium"
    is_active = True
    ease_factor = 2.5
    interval_days = 1
    repetitions = 0


class MockServiceMixin:
    """Mixin providing mocks for external services."""

    def setUp(self):
        """Set up service mocks."""
        super().setUp()
        self.setup_ai_service_mock()
        self.setup_retrieval_service_mock()
        self.setup_cache_mock()

    def setup_ai_service_mock(self):
        """Mock AI service responses."""
        self.ai_service_mock = Mock()
        self.ai_service_mock.generate_completion.return_value = {
            "error": None,
            "content": "Mock AI response",
            "usage": {"total_tokens": 100},
        }

        self.ai_service_patcher = patch(
            "core.services.ai_service.OpenAIService", return_value=self.ai_service_mock
        )
        self.ai_service_patcher.start()

    def setup_retrieval_service_mock(self):
        """Mock retrieval service responses."""
        self.retrieval_mock = Mock()
        self.retrieval_mock.search.return_value = {
            "success": True,
            "results": [
                {
                    "content": "Mock retrieval content",
                    "score": 0.95,
                    "metadata": {"source": "test"},
                }
            ],
        }

        self.retrieval_patcher = patch(
            "core.services.retrieval_client.RetrievalServiceClient",
            return_value=self.retrieval_mock,
        )
        self.retrieval_patcher.start()

    def setup_cache_mock(self):
        """Mock cache for consistent testing."""
        self.cache_mock = Mock()
        self.cache_mock.get.return_value = None
        self.cache_mock.set.return_value = True
        self.cache_mock.delete.return_value = True

        self.cache_patcher = patch("django.core.cache.cache", self.cache_mock)
        self.cache_patcher.start()

    def tearDown(self):
        """Clean up mocks."""
        super().tearDown()
        self.ai_service_patcher.stop()
        self.retrieval_patcher.stop()
        self.cache_patcher.stop()


class PerformanceTestCase(BaseTestCase):
    """Test case for performance testing."""

    def setUp(self):
        """Set up performance testing."""
        super().setUp()
        self.performance_data = {}

    def time_operation(self, operation_name: str, func, *args, **kwargs):
        """Time an operation and store results."""
        start_time = timezone.now()
        result = func(*args, **kwargs)
        end_time = timezone.now()

        duration = (end_time - start_time).total_seconds()
        self.performance_data[operation_name] = duration

        return result

    def assert_performance_threshold(
        self, operation_name: str, threshold_seconds: float
    ):
        """Assert that operation completed within threshold."""
        self.assertIn(operation_name, self.performance_data)
        actual_time = self.performance_data[operation_name]

        self.assertLessEqual(
            actual_time,
            threshold_seconds,
            f"{operation_name} took {actual_time}s, expected <= {threshold_seconds}s",
        )


class CacheTestMixin:
    """Mixin for testing cache functionality."""

    def assert_cached(self, cache_key: str, expected_value: Any = None):
        """Assert that a value is cached."""
        cached_value = cache.get(cache_key)
        self.assertIsNotNone(cached_value, f"Key {cache_key} not found in cache")

        if expected_value is not None:
            self.assertEqual(cached_value, expected_value)

    def assert_not_cached(self, cache_key: str):
        """Assert that a value is not cached."""
        cached_value = cache.get(cache_key)
        self.assertIsNone(cached_value, f"Key {cache_key} unexpectedly found in cache")

    def clear_cache_pattern(self, pattern: str):
        """Clear cache keys matching pattern."""
        try:
            cache.delete_pattern(pattern)
        except AttributeError:
            # If cache doesn't support pattern deletion, clear all
            cache.clear()


class SecurityTestMixin:
    """Mixin for security testing."""

    def test_authentication_required(self, url: str, method: str = "GET"):
        """Test that endpoint requires authentication."""
        self.client.credentials()  # Remove authentication

        response = getattr(self.client, method.lower())(url)
        self.assertIn(response.status_code, [401, 403])

    def test_permission_required(
        self, url: str, required_permission: str, method: str = "GET"
    ):
        """Test that endpoint requires specific permission."""
        # Create user without permission
        user_without_permission = UserFactory()
        self.authenticate_user(user_without_permission)

        response = getattr(self.client, method.lower())(url)
        self.assertEqual(response.status_code, 403)

    def test_input_validation(
        self, url: str, invalid_data: dict[str, Any], method: str = "POST"
    ):
        """Test input validation with invalid data."""
        response = getattr(self.client, method.lower())(url, data=invalid_data)
        self.assertIn(response.status_code, [400, 422])


class DatabaseTestMixin:
    """Mixin for database testing utilities."""

    def assert_db_queries_count(self, expected_count: int):
        """Context manager to assert database query count."""
        from django.db import connection

        class QueryCountAssertion:
            def __enter__(self):
                self.initial_queries = len(connection.queries)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                final_queries = len(connection.queries)
                actual_count = final_queries - self.initial_queries

                if actual_count != expected_count:
                    raise AssertionError(
                        f"Expected {expected_count} database queries, got {actual_count}"
                    )

        return QueryCountAssertion()


class IntegrationTestCase(BaseTestCase, MockServiceMixin):
    """
    Integration test case with service mocks and full workflow testing.
    """

    def setUp(self):
        """Set up integration testing."""
        super().setUp()

        # Create test data
        self.test_course = CourseFactory(user=self.regular_user)
        self.test_document = DocumentFactory(
            user=self.regular_user, course=self.test_course
        )
        self.test_flashcards = FlashcardFactory.create_batch(
            5, user=self.regular_user, course=self.test_course
        )

    def simulate_user_workflow(self, workflow_steps: list[dict[str, Any]]) -> list[Any]:
        """Simulate a complete user workflow."""
        results = []

        for step in workflow_steps:
            method = step.get("method", "GET")
            url = step["url"]
            data = step.get("data", {})
            expected_status = step.get("expected_status", 200)

            response = getattr(self.client, method.lower())(url, data=data)
            self.assertEqual(response.status_code, expected_status)

            results.append(response)

        return results


# Test data generators
def generate_test_user_data() -> dict[str, str]:
    """Generate test user data."""
    return {
        "username": f"test_user_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
    }


def generate_test_course_data() -> dict[str, str]:
    """Generate test course data."""
    return {
        "name": f"Test Course {uuid.uuid4().hex[:8]}",
        "description": "A test course for automated testing",
        "visibility": "private",
    }


def generate_test_flashcard_data() -> dict[str, str]:
    """Generate test flashcard data."""
    return {
        "question": f"Test question {uuid.uuid4().hex[:8]}?",
        "answer": "Test answer for the question.",
        "difficulty_level": "medium",
    }


# Custom assertions
def assert_valid_uuid(test_case: TestCase, value: str):
    """Assert that value is a valid UUID."""
    try:
        uuid.UUID(value)
    except (ValueError, TypeError):
        test_case.fail(f"'{value}' is not a valid UUID")


def assert_valid_timestamp(test_case: TestCase, timestamp_str: str):
    """Assert that string is a valid ISO timestamp."""
    try:
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        test_case.fail(f"'{timestamp_str}' is not a valid ISO timestamp")


def assert_response_schema(
    test_case: TestCase, response_data: dict[str, Any], expected_fields: list[str]
):
    """Assert that response contains expected fields."""
    for field in expected_fields:
        test_case.assertIn(
            field, response_data, f"Response missing required field: {field}"
        )


# Performance testing utilities
class PerformanceBenchmark:
    """Utility for performance benchmarking."""

    def __init__(self, name: str):
        self.name = name
        self.results = []

    def time_function(self, func, *args, **kwargs):
        """Time function execution."""
        start_time = timezone.now()
        result = func(*args, **kwargs)
        end_time = timezone.now()

        duration = (end_time - start_time).total_seconds()
        self.results.append(duration)

        return result

    def get_average_time(self) -> float:
        """Get average execution time."""
        return sum(self.results) / len(self.results) if self.results else 0.0

    def get_percentile(self, percentile: float) -> float:
        """Get execution time percentile."""
        if not self.results:
            return 0.0

        sorted_results = sorted(self.results)
        index = int(len(sorted_results) * (percentile / 100))
        return sorted_results[min(index, len(sorted_results) - 1)]
