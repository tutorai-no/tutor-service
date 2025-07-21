"""
Database optimization utilities for improved performance.

This module provides tools for database query optimization, indexing,
and performance monitoring.
"""

import logging
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.db import connection, models
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Data structure for query analysis results."""

    query: str
    execution_time: float
    rows_examined: int
    rows_returned: int
    index_usage: dict[str, Any]
    recommendations: list[str]


class DatabaseOptimizer:
    """
    Database optimization and analysis utilities.
    """

    def __init__(self):
        self.connection = connection

    def analyze_slow_queries(self, threshold_ms: float = 100.0) -> list[QueryAnalysis]:
        """
        Analyze slow queries and provide optimization recommendations.

        Args:
            threshold_ms: Query execution time threshold in milliseconds

        Returns:
            List of query analyses for slow queries
        """
        slow_queries = []

        if hasattr(connection, "queries_log"):
            for query_info in connection.queries_log:
                execution_time = (
                    float(query_info.get("time", 0)) * 1000
                )  # Convert to ms

                if execution_time > threshold_ms:
                    analysis = self._analyze_query(query_info["sql"], execution_time)
                    slow_queries.append(analysis)

        return slow_queries

    def _analyze_query(self, query: str, execution_time: float) -> QueryAnalysis:
        """Analyze individual query for optimization opportunities."""
        recommendations = []

        # Check for common performance issues
        query_lower = query.lower()

        # Check for SELECT *
        if "select *" in query_lower:
            recommendations.append("Avoid SELECT * - specify only needed columns")

        # Check for missing WHERE clauses on large tables
        if "where" not in query_lower and any(
            table in query_lower for table in ["users", "courses", "documents"]
        ):
            recommendations.append("Consider adding WHERE clause to limit results")

        # Check for N+1 queries
        if "in (" in query_lower and query_lower.count("select") == 1:
            recommendations.append(
                "Potential N+1 query - consider using select_related() or prefetch_related()"
            )

        # Check for LIKE queries
        if "like" in query_lower:
            recommendations.append(
                "LIKE queries can be slow - consider full-text search or indexed search"
            )

        # Check for ORDER BY without LIMIT
        if "order by" in query_lower and "limit" not in query_lower:
            recommendations.append(
                "ORDER BY without LIMIT can be expensive on large datasets"
            )

        return QueryAnalysis(
            query=query,
            execution_time=execution_time,
            rows_examined=0,  # Would need EXPLAIN output
            rows_returned=0,  # Would need query result info
            index_usage={},  # Would need EXPLAIN output
            recommendations=recommendations,
        )

    def suggest_indexes(self, model_class: models.Model) -> list[dict[str, Any]]:
        """
        Suggest database indexes for a model based on common query patterns.

        Args:
            model_class: Django model class

        Returns:
            List of index recommendations
        """
        recommendations = []
        model_name = model_class._meta.model_name

        # Analyze foreign key fields
        for field in model_class._meta.get_fields():
            if isinstance(field, models.ForeignKey):
                recommendations.append(
                    {
                        "type": "foreign_key_index",
                        "field": field.name,
                        "reason": "Foreign key fields should have indexes for JOIN performance",
                        "index_sql": f"CREATE INDEX IF NOT EXISTS idx_{model_name}_{field.name} ON {model_class._meta.db_table} ({field.column});",
                    }
                )

        # Analyze fields used in filters
        common_filter_fields = ["created_at", "updated_at", "is_active", "status"]
        for field_name in common_filter_fields:
            if hasattr(model_class, field_name):
                recommendations.append(
                    {
                        "type": "filter_field_index",
                        "field": field_name,
                        "reason": f"{field_name} is commonly used in filters",
                        "index_sql": f"CREATE INDEX IF NOT EXISTS idx_{model_name}_{field_name} ON {model_class._meta.db_table} ({field_name});",
                    }
                )

        # Suggest composite indexes for common query patterns
        if hasattr(model_class, "user") and hasattr(model_class, "created_at"):
            recommendations.append(
                {
                    "type": "composite_index",
                    "fields": ["user", "created_at"],
                    "reason": "Common pattern: filter by user and order by creation date",
                    "index_sql": f"CREATE INDEX IF NOT EXISTS idx_{model_name}_user_created ON {model_class._meta.db_table} (user_id, created_at);",
                }
            )

        return recommendations

    def check_missing_indexes(self) -> dict[str, list[dict[str, Any]]]:
        """Check for missing indexes across all models."""
        recommendations = {}

        # Get all Django models
        from django.apps import apps

        for model in apps.get_models():
            if model._meta.app_label in ["contenttypes", "auth", "sessions", "admin"]:
                continue  # Skip built-in Django models

            model_recommendations = self.suggest_indexes(model)
            if model_recommendations:
                recommendations[f"{model._meta.app_label}.{model._meta.model_name}"] = (
                    model_recommendations
                )

        return recommendations

    def optimize_queryset(self, queryset: models.QuerySet) -> models.QuerySet:
        """
        Optimize a QuerySet with select_related and prefetch_related.

        Args:
            queryset: Django QuerySet to optimize

        Returns:
            Optimized QuerySet
        """
        model = queryset.model

        # Auto-add select_related for foreign keys
        foreign_keys = []
        for field in model._meta.get_fields():
            if isinstance(field, models.ForeignKey):
                foreign_keys.append(field.name)

        if foreign_keys:
            queryset = queryset.select_related(*foreign_keys)

        # Auto-add prefetch_related for reverse foreign keys and many-to-many
        reverse_relations = []
        for field in model._meta.get_fields():
            if isinstance(field, (models.ManyToManyField, models.ManyToOneRel)):
                reverse_relations.append(field.name)

        if reverse_relations:
            queryset = queryset.prefetch_related(*reverse_relations)

        return queryset


class DatabaseMonitor:
    """Monitor database performance and health."""

    def __init__(self):
        self.connection = connection

    def get_database_stats(self) -> dict[str, Any]:
        """Get comprehensive database statistics."""
        stats = {
            "connection_info": self._get_connection_info(),
            "table_stats": self._get_table_stats(),
            "index_usage": self._get_index_usage(),
            "query_performance": self._get_query_performance(),
        }

        return stats

    def _get_connection_info(self) -> dict[str, Any]:
        """Get database connection information."""
        with self.connection.cursor() as cursor:
            # PostgreSQL specific queries
            if "postgresql" in settings.DATABASES["default"]["ENGINE"]:
                cursor.execute(
                    """
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """
                )

                result = cursor.fetchone()
                return {
                    "total_connections": result[0],
                    "active_connections": result[1],
                    "idle_connections": result[2],
                }

        return {"total_connections": "unknown", "active_connections": "unknown"}

    def _get_table_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for each table."""
        table_stats = {}

        with self.connection.cursor() as cursor:
            if "postgresql" in settings.DATABASES["default"]["ENGINE"]:
                cursor.execute(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_rows,
                        n_dead_tup as dead_rows
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """
                )

                for row in cursor.fetchall():
                    table_name = f"{row[0]}.{row[1]}"
                    table_stats[table_name] = {
                        "inserts": row[2],
                        "updates": row[3],
                        "deletes": row[4],
                        "live_rows": row[5],
                        "dead_rows": row[6],
                    }

        return table_stats

    def _get_index_usage(self) -> dict[str, dict[str, Any]]:
        """Get index usage statistics."""
        index_stats = {}

        with self.connection.cursor() as cursor:
            if "postgresql" in settings.DATABASES["default"]["ENGINE"]:
                cursor.execute(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_tup_read DESC
                """
                )

                for row in cursor.fetchall():
                    index_name = f"{row[0]}.{row[1]}.{row[2]}"
                    index_stats[index_name] = {
                        "reads": row[3],
                        "fetches": row[4],
                    }

        return index_stats

    def _get_query_performance(self) -> dict[str, Any]:
        """Get query performance metrics."""
        if hasattr(connection, "queries"):
            total_queries = len(connection.queries)
            if total_queries > 0:
                query_times = [float(q["time"]) for q in connection.queries]
                return {
                    "total_queries": total_queries,
                    "avg_query_time": sum(query_times) / len(query_times),
                    "max_query_time": max(query_times),
                    "min_query_time": min(query_times),
                }

        return {"total_queries": 0, "avg_query_time": 0}


class QueryOptimizer:
    """Utilities for optimizing specific query patterns."""

    @staticmethod
    def optimize_user_content_queries():
        """Optimize common user content queries."""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Optimized user profile query with related data
        def get_user_with_profile(user_id):
            return User.objects.select_related("profile").get(pk=user_id)

        # Optimized user courses query
        def get_user_courses(user_id):
            from courses.models import Course

            return Course.objects.filter(user_id=user_id).select_related("user")

        # Optimized user flashcards query
        def get_user_flashcards_due(user_id):
            from assessments.models import Flashcard

            return (
                Flashcard.objects.filter(
                    user_id=user_id,
                    next_review_date__lte=timezone.now(),
                    is_active=True,
                )
                .select_related("course")
                .order_by("next_review_date")
            )

        return {
            "get_user_with_profile": get_user_with_profile,
            "get_user_courses": get_user_courses,
            "get_user_flashcards_due": get_user_flashcards_due,
        }

    @staticmethod
    def create_database_indexes():
        """Create recommended database indexes."""
        with connection.cursor() as cursor:
            # Common indexes for better performance
            indexes = [
                # User-related indexes
                "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users (last_active_at) WHERE last_active_at IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_users_email_active ON users (email) WHERE is_active = true;",
                # Course-related indexes
                "CREATE INDEX IF NOT EXISTS idx_courses_user_created ON courses (user_id, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_courses_visibility ON courses (visibility) WHERE visibility = 'public';",
                # Document-related indexes
                "CREATE INDEX IF NOT EXISTS idx_documents_course_status ON documents (course_id, processing_status);",
                "CREATE INDEX IF NOT EXISTS idx_documents_user_created ON documents (user_id, created_at);",
                # Flashcard-related indexes
                "CREATE INDEX IF NOT EXISTS idx_flashcards_user_active ON flashcards (user_id) WHERE is_active = true;",
                "CREATE INDEX IF NOT EXISTS idx_flashcards_due_date ON flashcards (next_review_date) WHERE is_active = true;",
                "CREATE INDEX IF NOT EXISTS idx_flashcards_course_user ON flashcards (course_id, user_id);",
                # Quiz-related indexes
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_status ON quiz_attempts (user_id, status);",
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_completed ON quiz_attempts (completed_at) WHERE status = 'completed';",
                # Chat-related indexes
                "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_created ON chat_sessions (user_id, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages (session_id, created_at);",
                # Activity tracking indexes
                "CREATE INDEX IF NOT EXISTS idx_user_activities_user_type ON user_activities (user_id, activity_type);",
                "CREATE INDEX IF NOT EXISTS idx_user_activities_created ON user_activities (created_at);",
            ]

            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {index_sql}, Error: {e}")


# Global instances
database_optimizer = DatabaseOptimizer()
database_monitor = DatabaseMonitor()
query_optimizer = QueryOptimizer()
