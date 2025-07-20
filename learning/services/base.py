"""
Base classes and utilities for adaptive learning services.
"""

import logging
from abc import ABC
from datetime import time, timedelta
from typing import Any

from django.db.models import Avg, QuerySet
from django.utils import timezone

logger = logging.getLogger(__name__)


class AdaptiveLearningService(ABC):
    """
    Base class for all adaptive learning services.
    Provides common functionality and utilities.
    """

    def __init__(self):
        """Initialize the adaptive learning service."""
        self.logger = logger.getChild(self.__class__.__name__)

    def log_adaptation(
        self, user_id: str, adaptation_type: str, details: dict[str, Any]
    ) -> None:
        """
        Log an adaptation decision for tracking and analysis.

        Args:
            user_id: ID of the user
            adaptation_type: Type of adaptation made
            details: Details about the adaptation
        """
        self.logger.info(
            f"Adaptation made for user {user_id}: {adaptation_type}",
            extra={
                "user_id": user_id,
                "adaptation_type": adaptation_type,
                "details": details,
            },
        )


class StudyMetrics:
    """
    Container for study performance metrics and calculations.
    """

    def __init__(self, user, course=None, time_period_days: int = 30):
        """
        Initialize study metrics for a user.

        Args:
            user: User object
            course: Optional course to filter metrics
            time_period_days: Number of days to look back for metrics
        """
        self.user = user
        self.course = course
        self.time_period_days = time_period_days
        self.start_date = timezone.now() - timedelta(days=time_period_days)
        self._cache = {}

    def get_quiz_performance(self) -> dict[str, float]:
        """Get quiz performance metrics."""
        if "quiz_performance" not in self._cache:
            from assessments.models import QuizAttempt

            attempts = QuizAttempt.objects.filter(
                user=self.user, started_at__gte=self.start_date
            )

            if self.course:
                attempts = attempts.filter(quiz__course=self.course)

            avg_score = attempts.aggregate(avg_score=Avg("score"))["avg_score"] or 0
            total_attempts = attempts.count()
            recent_trend = self._calculate_performance_trend(attempts)

            self._cache["quiz_performance"] = {
                "average_score": float(avg_score),
                "total_attempts": total_attempts,
                "improvement_trend": recent_trend,
                "consistency": self._calculate_consistency(attempts),
                "weak_topics": [],  # TODO: Implement topic analysis when quiz model has topic data
            }

        return self._cache["quiz_performance"]

    def get_study_session_metrics(self) -> dict[str, Any]:
        """Get study session metrics."""
        if "session_metrics" not in self._cache:
            from learning.models import StudySession

            sessions = StudySession.objects.filter(
                user=self.user, created_at__gte=self.start_date
            )

            if self.course:
                sessions = sessions.filter(course=self.course)

            total_sessions = sessions.count()
            total_hours = sum(
                session.duration_actual.total_seconds() / 3600
                for session in sessions
                if session.duration_actual
            )
            avg_productivity = (
                sessions.aggregate(avg_prod=Avg("productivity_rating"))["avg_prod"] or 0
            )

            completion_rate = self._calculate_completion_rate(sessions)

            self._cache["session_metrics"] = {
                "total_sessions": total_sessions,
                "total_hours": float(total_hours),
                "average_productivity": float(avg_productivity),
                "completion_rate": completion_rate,
                "sessions_per_week": total_sessions * 7 / self.time_period_days,
            }

        return self._cache["session_metrics"]

    def get_flashcard_retention(self) -> dict[str, float]:
        """Get flashcard retention metrics."""
        if "flashcard_retention" not in self._cache:
            from assessments.models import FlashcardReview

            reviews = FlashcardReview.objects.filter(
                user=self.user, created_at__gte=self.start_date
            )

            if self.course:
                reviews = reviews.filter(flashcard__course=self.course)

            total_reviews = reviews.count()
            correct_reviews = reviews.filter(quality_response__gte=3).count()
            retention_rate = (
                (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0
            )

            self._cache["flashcard_retention"] = {
                "retention_rate": retention_rate,
                "total_reviews": total_reviews,
                "mastery_trend": self._calculate_flashcard_trend(reviews),
            }

        return self._cache["flashcard_retention"]

    def get_learning_velocity(self) -> float:
        """
        Calculate learning velocity (topics mastered per week).

        Returns:
            Learning velocity as topics per week
        """
        from learning.models import LearningProgress

        progress_entries = LearningProgress.objects.filter(
            user=self.user,
            updated_at__gte=self.start_date,
            mastery_level__gte=4,  # Consider mastery level 4+ as "mastered"
        )

        if self.course:
            progress_entries = progress_entries.filter(course=self.course)

        mastered_topics = progress_entries.count()
        weeks = self.time_period_days / 7

        return mastered_topics / weeks if weeks > 0 else 0

    def get_optimal_study_time(self) -> dict[str, Any]:
        """
        Analyze when user performs best and recommend optimal study times.

        Returns:
            Dictionary with optimal study time recommendations
        """
        from learning.models import StudySession

        sessions = StudySession.objects.filter(
            user=self.user,
            created_at__gte=self.start_date,
            productivity_rating__isnull=False,
        )

        if self.course:
            sessions = sessions.filter(course=self.course)

        # Group by hour of day and calculate average productivity
        hourly_productivity = {}
        for session in sessions:
            hour = session.created_at.hour
            if hour not in hourly_productivity:
                hourly_productivity[hour] = []
            hourly_productivity[hour].append(session.productivity_rating)

        # Calculate averages
        hourly_averages = {
            hour: sum(ratings) / len(ratings)
            for hour, ratings in hourly_productivity.items()
        }

        # Find optimal time slots
        optimal_hours = sorted(
            hourly_averages.items(), key=lambda x: x[1], reverse=True
        )[
            :3
        ]  # Top 3 most productive hours

        return {
            "optimal_hours": [hour for hour, _ in optimal_hours],
            "peak_productivity_hour": optimal_hours[0][0] if optimal_hours else 9,
            "hourly_productivity": hourly_averages,
            "recommended_session_length": self._calculate_optimal_session_length(),
        }

    def _calculate_performance_trend(self, attempts: QuerySet) -> str:
        """Calculate if performance is improving, declining, or stable."""
        if attempts.count() < 3:
            return "insufficient_data"

        recent_scores = list(
            attempts.order_by("-started_at")[:5].values_list("score", flat=True)
        )
        older_scores = list(
            attempts.order_by("-started_at")[5:10].values_list("score", flat=True)
        )

        if not older_scores:
            return "insufficient_data"

        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)

        diff = recent_avg - older_avg

        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"

    def _calculate_consistency(self, attempts: QuerySet) -> float:
        """Calculate performance consistency (lower standard deviation = more consistent)."""
        scores = list(attempts.values_list("score", flat=True))

        if len(scores) < 2:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        std_dev = variance**0.5

        # Convert to consistency score (0-100, higher is more consistent)
        consistency = max(0, 100 - std_dev)
        return consistency

    def _calculate_completion_rate(self, sessions: QuerySet) -> float:
        """Calculate session completion rate."""
        if not sessions.exists():
            return 0.0

        completed_sessions = sessions.filter(status="completed").count()
        total_sessions = sessions.count()

        return (completed_sessions / total_sessions) * 100

    def _calculate_flashcard_trend(self, reviews: QuerySet) -> str:
        """Calculate flashcard mastery trend."""
        if reviews.count() < 10:
            return "insufficient_data"

        recent_correct = (
            reviews.order_by("-created_at")[:20].filter(quality_response__gte=3).count()
        )
        older_correct = (
            reviews.order_by("-created_at")[20:40]
            .filter(quality_response__gte=3)
            .count()
        )

        recent_rate = recent_correct / 20 if recent_correct else 0
        older_rate = older_correct / 20 if older_correct else 0

        if recent_rate > older_rate + 0.1:
            return "improving"
        elif recent_rate < older_rate - 0.1:
            return "declining"
        else:
            return "stable"

    def _calculate_optimal_session_length(self) -> int:
        """Calculate optimal study session length in minutes."""
        from learning.models import StudySession

        sessions = StudySession.objects.filter(
            user=self.user,
            created_at__gte=self.start_date,
            actual_start__isnull=False,
            actual_end__isnull=False,
            productivity_rating__isnull=False,
        )

        # Group sessions by duration ranges and find most productive range
        duration_productivity = {}

        for session in sessions:
            duration_minutes = (
                session.duration_actual.total_seconds() / 60
                if session.duration_actual
                else 0
            )
            duration_range = self._get_duration_range(int(duration_minutes))
            if duration_range not in duration_productivity:
                duration_productivity[duration_range] = []
            duration_productivity[duration_range].append(session.productivity_rating)

        # Find range with highest average productivity
        best_range = None
        best_productivity = 0

        for duration_range, ratings in duration_productivity.items():
            avg_productivity = sum(ratings) / len(ratings)
            if avg_productivity > best_productivity:
                best_productivity = avg_productivity
                best_range = duration_range

        # Convert range to recommended minutes
        range_to_minutes = {
            "short": 25,  # 15-30 minutes
            "medium": 45,  # 31-60 minutes
            "long": 90,  # 61+ minutes
        }

        return range_to_minutes.get(best_range, 45)  # Default to 45 minutes

    def _get_duration_range(self, minutes: int) -> str:
        """Categorize session duration into ranges."""
        if minutes <= 30:
            return "short"
        elif minutes <= 60:
            return "medium"
        else:
            return "long"


class TimeSlotOptimizer:
    """
    Utility class for optimizing study time slots based on user preferences and performance.
    """

    def __init__(self, user, preferences: dict[str, Any] = None):
        """
        Initialize time slot optimizer.

        Args:
            user: User object
            preferences: User preferences for study times
        """
        self.user = user
        self.preferences = preferences or {}
        self.metrics = StudyMetrics(user)

    def get_optimal_time_slots(
        self, hours_needed: float, days_available: list[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get optimal time slots for studying.

        Args:
            hours_needed: Total hours needed to schedule
            days_available: Days available for studying

        Returns:
            List of optimal time slots
        """
        if days_available is None:
            days_available = ["monday", "tuesday", "wednesday", "thursday", "friday"]

        optimal_times = self.metrics.get_optimal_study_time()
        session_length = optimal_times["recommended_session_length"]

        # Convert hours to sessions
        sessions_needed = max(1, int((hours_needed * 60) / session_length))

        # Generate time slots
        time_slots = []
        preferred_hours = self.preferences.get(
            "preferred_hours", optimal_times["optimal_hours"]
        )

        sessions_per_day = max(1, sessions_needed // len(days_available))

        for day in days_available:
            for i in range(sessions_per_day):
                if len(time_slots) >= sessions_needed:
                    break

                # Pick optimal hour for this session
                hour = (
                    preferred_hours[i % len(preferred_hours)] if preferred_hours else 9
                )

                time_slots.append(
                    {
                        "day": day,
                        "start_time": time(hour, 0),
                        "duration_minutes": session_length,
                        "productivity_score": optimal_times["hourly_productivity"].get(
                            hour, 3.0
                        ),
                    }
                )

        return time_slots[:sessions_needed]


def calculate_cognitive_load(tasks: list[dict[str, Any]]) -> float:
    """
    Calculate cognitive load for a set of study tasks.

    Args:
        tasks: List of study tasks with difficulty and duration

    Returns:
        Cognitive load score (0-100)
    """
    if not tasks:
        return 0.0

    total_load = 0.0

    for task in tasks:
        # Base load from duration
        duration_load = task.get("duration_minutes", 30) / 60  # Hours

        # Difficulty multiplier
        difficulty_multipliers = {"easy": 0.8, "medium": 1.0, "hard": 1.3}
        difficulty = task.get("difficulty", "medium")
        difficulty_mult = difficulty_multipliers.get(difficulty, 1.0)

        # Task type multiplier
        type_multipliers = {
            "reading": 0.9,
            "practice": 1.1,
            "quiz": 1.2,
            "project": 1.4,
        }
        task_type = task.get("type", "reading")
        type_mult = type_multipliers.get(task_type, 1.0)

        task_load = duration_load * difficulty_mult * type_mult
        total_load += task_load

    # Normalize to 0-100 scale (assume 3 hours = 100% load)
    normalized_load = min(100, (total_load / 3.0) * 100)

    return normalized_load
