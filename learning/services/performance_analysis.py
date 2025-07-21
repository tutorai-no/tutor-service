"""
Performance analysis service for adaptive learning and study plan optimization.
"""

import logging
import statistics
from datetime import timedelta
from typing import Any

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone

from .base import AdaptiveLearningService, StudyMetrics

logger = logging.getLogger(__name__)


class PerformanceAnalysisService(AdaptiveLearningService):
    """
    Service for analyzing user performance and providing adaptive recommendations.
    """

    def __init__(self):
        """Initialize the performance analysis service."""
        super().__init__()
        self.analysis_window_days = 30  # Default analysis window
        self.trend_threshold = 10  # Percentage change to consider significant
        self.performance_categories = {
            "excellent": 90,
            "good": 80,
            "average": 70,
            "needs_improvement": 50,
            "poor": 0,
        }

    def analyze_comprehensive_performance(
        self, user, course=None, time_period_days: int = 30
    ) -> dict[str, Any]:
        """
        Perform comprehensive performance analysis for a user.

        Args:
            user: User object
            course: Optional course to filter analysis
            time_period_days: Number of days to analyze

        Returns:
            Comprehensive performance analysis
        """
        try:
            self.logger.info(f"Analyzing performance for user {user.id}")

            # Initialize metrics
            StudyMetrics(user, course, time_period_days)

            # Perform various analyses
            quiz_analysis = self._analyze_quiz_performance(
                user, course, time_period_days
            )
            session_analysis = self._analyze_study_sessions(
                user, course, time_period_days
            )
            progress_analysis = self._analyze_learning_progress(
                user, course, time_period_days
            )
            flashcard_analysis = self._analyze_flashcard_performance(
                user, course, time_period_days
            )
            engagement_analysis = self._analyze_engagement_patterns(
                user, course, time_period_days
            )

            # Calculate overall performance
            overall_score = self._calculate_overall_performance_score(
                {
                    "quiz": quiz_analysis,
                    "sessions": session_analysis,
                    "progress": progress_analysis,
                    "flashcards": flashcard_analysis,
                    "engagement": engagement_analysis,
                }
            )

            # Identify strengths and weaknesses
            strengths_weaknesses = self._identify_strengths_and_weaknesses(
                {
                    "quiz": quiz_analysis,
                    "sessions": session_analysis,
                    "progress": progress_analysis,
                    "flashcards": flashcard_analysis,
                }
            )

            # Generate adaptive recommendations
            recommendations = self._generate_adaptive_recommendations(
                overall_score,
                strengths_weaknesses,
                {
                    "quiz": quiz_analysis,
                    "sessions": session_analysis,
                    "progress": progress_analysis,
                    "flashcards": flashcard_analysis,
                    "engagement": engagement_analysis,
                },
            )

            # Performance trends
            trends = self._analyze_performance_trends(user, course, time_period_days)

            return {
                "overall_score": overall_score,
                "performance_category": self._categorize_performance(overall_score),
                "detailed_analysis": {
                    "quiz_performance": quiz_analysis,
                    "study_sessions": session_analysis,
                    "learning_progress": progress_analysis,
                    "flashcard_retention": flashcard_analysis,
                    "engagement_patterns": engagement_analysis,
                },
                "strengths_weaknesses": strengths_weaknesses,
                "trends": trends,
                "recommendations": recommendations,
                "analysis_period": {
                    "days": time_period_days,
                    "start_date": (timezone.now() - timedelta(days=time_period_days))
                    .date()
                    .isoformat(),
                    "end_date": timezone.now().date().isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"Error in comprehensive performance analysis: {str(e)}")
            return {
                "error": str(e),
                "overall_score": 0,
                "performance_category": "unknown",
            }

    def get_real_time_performance_update(
        self, user, recent_activity: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze recent activity and provide real-time performance update.

        Args:
            user: User object
            recent_activity: Recent quiz, session, or study activity

        Returns:
            Real-time performance analysis and recommendations
        """
        try:
            activity_type = recent_activity.get("type")

            if activity_type == "quiz_completion":
                return self._analyze_quiz_completion(user, recent_activity)
            elif activity_type == "study_session":
                return self._analyze_study_session_completion(user, recent_activity)
            elif activity_type == "flashcard_review":
                return self._analyze_flashcard_session(user, recent_activity)
            else:
                return {"status": "no_analysis", "message": "Unknown activity type"}

        except Exception as e:
            self.logger.error(f"Error in real-time performance update: {str(e)}")
            return {"error": str(e)}

    def predict_performance_trajectory(
        self, user, course=None, prediction_days: int = 30
    ) -> dict[str, Any]:
        """
        Predict future performance trajectory based on current trends.

        Args:
            user: User object
            course: Optional course filter
            prediction_days: Days into the future to predict

        Returns:
            Performance trajectory prediction
        """
        try:
            # Analyze current trends
            trends = self._analyze_performance_trends(user, course, 30)

            # Calculate trajectory
            trajectory = self._calculate_performance_trajectory(trends, prediction_days)

            # Risk assessment
            risk_factors = self._assess_performance_risks(user, course, trends)

            # Intervention recommendations
            interventions = self._recommend_interventions(trajectory, risk_factors)

            return {
                "current_trends": trends,
                "predicted_trajectory": trajectory,
                "risk_assessment": risk_factors,
                "recommended_interventions": interventions,
                "confidence_level": self._calculate_prediction_confidence(trends),
            }

        except Exception as e:
            self.logger.error(f"Error predicting performance trajectory: {str(e)}")
            return {"error": str(e)}

    def _analyze_quiz_performance(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Analyze quiz performance in detail."""
        from assessments.models import QuizAttempt

        attempts = QuizAttempt.objects.filter(
            user=user, created_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            attempts = attempts.filter(quiz__course=course)

        if not attempts.exists():
            return {
                "average_score": 0,
                "total_attempts": 0,
                "improvement_trend": "no_data",
                "consistency": 0,
                "time_efficiency": 0,
                "difficulty_performance": {},
                "weak_topics": [],
            }

        # Basic metrics
        scores = list(attempts.values_list("score", flat=True))
        avg_score = sum(scores) / len(scores)
        total_attempts = len(scores)

        # Improvement trend
        improvement_trend = self._calculate_trend(scores)

        # Consistency (inverse of standard deviation)
        consistency = self._calculate_consistency(scores)

        # Time efficiency
        time_efficiency = self._calculate_time_efficiency(attempts)

        # Performance by difficulty
        difficulty_performance = self._analyze_difficulty_performance(attempts)

        # Topic-wise performance
        topic_performance = self._analyze_topic_performance(attempts)

        # Identify weak topics based on low scores
        weak_topics = self._identify_weak_topics(topic_performance)

        return {
            "average_score": round(avg_score, 1),
            "total_attempts": total_attempts,
            "improvement_trend": improvement_trend,
            "consistency": consistency,
            "time_efficiency": time_efficiency,
            "difficulty_performance": difficulty_performance,
            "topic_performance": topic_performance,
            "recent_scores": scores[-5:],  # Last 5 scores
            "best_score": max(scores),
            "worst_score": min(scores),
            "weak_topics": weak_topics,
        }

    def _analyze_study_sessions(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Analyze study session patterns and effectiveness."""
        from learning.models import StudySession

        sessions = StudySession.objects.filter(
            user=user, created_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            sessions = sessions.filter(study_plan__course=course)

        if not sessions.exists():
            return {
                "total_sessions": 0,
                "total_hours": 0,
                "completion_rate": 0,
                "productivity_trend": "no_data",
                "optimal_session_length": 45,
            }

        # Basic metrics
        total_sessions = sessions.count()
        total_hours = sum(s.duration_hours for s in sessions if s.duration_hours)
        completed_sessions = sessions.filter(session_completed=True).count()
        completion_rate = (completed_sessions / total_sessions) * 100

        # Productivity analysis
        productivity_scores = list(
            sessions.filter(productivity_rating__isnull=False).values_list(
                "productivity_rating", flat=True
            )
        )

        avg_productivity = (
            sum(productivity_scores) / len(productivity_scores)
            if productivity_scores
            else 0
        )
        productivity_trend = self._calculate_trend(productivity_scores)

        # Session timing analysis
        timing_analysis = self._analyze_session_timing(sessions)

        # Optimal session length
        optimal_length = self._find_optimal_session_length(sessions)

        return {
            "total_sessions": total_sessions,
            "total_hours": round(total_hours, 1),
            "completion_rate": round(completion_rate, 1),
            "average_productivity": round(avg_productivity, 1),
            "productivity_trend": productivity_trend,
            "timing_analysis": timing_analysis,
            "optimal_session_length": optimal_length,
            "sessions_per_week": round((total_sessions * 7) / time_period_days, 1),
        }

    def _analyze_learning_progress(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Analyze learning progress and mastery levels."""
        from learning.models import LearningProgress

        progress_entries = LearningProgress.objects.filter(
            user=user, updated_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            progress_entries = progress_entries.filter(course=course)

        if not progress_entries.exists():
            return {
                "mastery_distribution": {},
                "learning_velocity": 0,
                "topics_mastered": 0,
                "improvement_rate": 0,
                "completion_percentage": 0,
            }

        # Mastery level distribution
        mastery_distribution = {}
        for level in range(1, 6):
            count = progress_entries.filter(mastery_level=level).count()
            mastery_distribution[f"level_{level}"] = count

        # Learning velocity (topics progressed per week)
        topics_progressed = progress_entries.count()
        learning_velocity = (topics_progressed * 7) / time_period_days

        # Topics mastered (level 4+)
        topics_mastered = progress_entries.filter(mastery_level__gte=4).count()

        # Improvement rate
        improvement_rate = self._calculate_improvement_rate(progress_entries)

        # Calculate average completion percentage
        avg_completion = (
            progress_entries.aggregate(avg_completion=Avg("completion_percentage"))[
                "avg_completion"
            ]
            or 0
        )

        return {
            "mastery_distribution": mastery_distribution,
            "learning_velocity": round(learning_velocity, 2),
            "topics_mastered": topics_mastered,
            "topics_in_progress": progress_entries.filter(
                mastery_level__in=[2, 3]
            ).count(),
            "improvement_rate": improvement_rate,
            "average_mastery_level": round(
                progress_entries.aggregate(avg=Avg("mastery_level"))["avg"] or 0, 1
            ),
            "completion_percentage": round(avg_completion, 1),
        }

    def _analyze_flashcard_retention(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Analyze flashcard retention performance."""
        return self._analyze_flashcard_performance(user, course, time_period_days)

    def _analyze_flashcard_performance(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Analyze flashcard review performance."""
        from assessments.models import FlashcardReview

        reviews = FlashcardReview.objects.filter(
            user=user, created_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            reviews = reviews.filter(flashcard__course=course)

        if not reviews.exists():
            return {
                "retention_rate": 0,
                "total_reviews": 0,
                "cards_mastered": 0,
                "review_efficiency": 0,
            }

        # Retention rate (quality_response >= 3 considered successful)
        successful_reviews = reviews.filter(quality_response__gte=3).count()
        total_reviews = reviews.count()
        retention_rate = (successful_reviews / total_reviews) * 100

        # Cards mastered (consistently easy responses)
        cards_mastered = self._count_mastered_cards(reviews)

        # Review efficiency
        review_efficiency = self._calculate_review_efficiency(reviews)

        # Quality distribution (mapped from quality_response)
        difficulty_dist = {
            "easy": reviews.filter(quality_response__gte=4).count(),  # 4-5: Easy
            "medium": reviews.filter(quality_response=3).count(),  # 3: Medium
            "hard": reviews.filter(quality_response__in=[1, 2]).count(),  # 1-2: Hard
            "again": reviews.filter(quality_response=0).count(),  # 0: Again
        }

        # Calculate average response time
        response_times = reviews.filter(
            response_time_seconds__isnull=False
        ).values_list("response_time_seconds", flat=True)
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        return {
            "retention_rate": round(retention_rate, 1),
            "total_reviews": total_reviews,
            "cards_mastered": cards_mastered,
            "review_efficiency": review_efficiency,
            "difficulty_distribution": difficulty_dist,
            "average_response_time": (
                round(avg_response_time, 1) if avg_response_time else 0
            ),
            "reviews_per_day": round(total_reviews / time_period_days, 1),
        }

    def _analyze_engagement_patterns(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Analyze user engagement patterns."""
        from learning.models import StudySession

        # Study frequency
        sessions = StudySession.objects.filter(
            user=user, created_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            sessions = sessions.filter(study_plan__course=course)

        # Daily activity pattern using Django ORM functions (safer than raw SQL)
        from django.db.models.functions import TruncDate

        daily_activity = (
            sessions.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(session_count=Count("id"), total_hours=Sum("duration_hours"))
            .order_by("day")
        )

        # Study streak
        study_streak = self._calculate_study_streak(user, course)

        # Peak activity times
        peak_times = self._analyze_peak_activity_times(sessions)

        # Engagement score
        engagement_score = self._calculate_engagement_score(
            sessions, study_streak, time_period_days
        )

        return {
            "study_streak": study_streak,
            "peak_activity_times": peak_times,
            "engagement_score": engagement_score,
            "daily_activity_pattern": list(daily_activity),
            "most_active_day": self._find_most_active_day(sessions),
            "consistency_score": self._calculate_consistency_score(daily_activity),
        }

    def _calculate_overall_performance_score(
        self, analyses: dict[str, dict[str, Any]]
    ) -> float:
        """Calculate weighted overall performance score."""
        weights = {
            "quiz": 0.3,
            "progress": 0.25,
            "flashcards": 0.2,
            "sessions": 0.15,
            "engagement": 0.1,
        }

        scores = {}

        # Normalize each component to 0-100 scale
        scores["quiz"] = analyses["quiz"].get("average_score", 0)
        scores["progress"] = (
            analyses["progress"].get("average_mastery_level", 0) / 5
        ) * 100
        scores["flashcards"] = analyses["flashcards"].get("retention_rate", 0)
        scores["sessions"] = analyses["sessions"].get("completion_rate", 0)
        scores["engagement"] = analyses["engagement"].get("engagement_score", 0)

        # Calculate weighted average
        weighted_score = sum(
            scores[component] * weights[component] for component in weights
        )

        return round(weighted_score, 1)

    def _identify_strengths_and_weaknesses(
        self, analyses: dict[str, dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Identify user's strengths and weaknesses."""
        strengths = []
        weaknesses = []

        # Quiz performance
        quiz_score = analyses["quiz"].get("average_score", 0)
        if quiz_score >= 80:
            strengths.append("Strong quiz performance")
        elif quiz_score < 60:
            weaknesses.append("Needs improvement in quiz performance")

        # Study consistency
        completion_rate = analyses["sessions"].get("completion_rate", 0)
        if completion_rate >= 80:
            strengths.append("Consistent study habits")
        elif completion_rate < 60:
            weaknesses.append("Inconsistent study completion")

        # Flashcard retention
        retention_rate = analyses["flashcards"].get("retention_rate", 0)
        if retention_rate >= 80:
            strengths.append("Excellent memory retention")
        elif retention_rate < 60:
            weaknesses.append("Memory retention needs work")

        # Learning progress
        mastery_level = analyses["progress"].get("average_mastery_level", 0)
        if mastery_level >= 4:
            strengths.append("Fast learning progression")
        elif mastery_level < 2.5:
            weaknesses.append("Slow learning progression")

        return {"strengths": strengths, "weaknesses": weaknesses}

    def _generate_adaptive_recommendations(
        self,
        overall_score: float,
        strengths_weaknesses: dict[str, list[str]],
        analyses: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate adaptive recommendations based on performance analysis."""
        recommendations = []

        # Overall performance recommendations
        if overall_score < 60:
            recommendations.append(
                {
                    "type": "study_strategy",
                    "priority": "high",
                    "title": "Adjust Study Strategy",
                    "description": "Consider reducing session length and increasing frequency",
                    "action_items": [
                        "Schedule shorter 25-30 minute sessions",
                        "Increase study frequency to daily",
                        "Focus on review and reinforcement",
                    ],
                }
            )
        elif overall_score > 85:
            recommendations.append(
                {
                    "type": "challenge",
                    "priority": "medium",
                    "title": "Increase Challenge Level",
                    "description": "You're performing excellently - time for advanced content",
                    "action_items": [
                        "Attempt harder practice problems",
                        "Explore advanced topics",
                        "Consider helping other students",
                    ],
                }
            )

        # Quiz-specific recommendations
        quiz_score = analyses["quiz"].get("average_score", 0)
        quiz_consistency = analyses["quiz"].get("consistency", 0)

        if quiz_score < 70:
            recommendations.append(
                {
                    "type": "quiz_improvement",
                    "priority": "high",
                    "title": "Improve Quiz Performance",
                    "description": "Focus on understanding concepts before testing",
                    "action_items": [
                        "Review material before taking quizzes",
                        "Take practice quizzes more frequently",
                        "Analyze incorrect answers to identify patterns",
                    ],
                }
            )

        if quiz_consistency < 70:
            recommendations.append(
                {
                    "type": "consistency",
                    "priority": "medium",
                    "title": "Improve Consistency",
                    "description": "Work on maintaining steady performance",
                    "action_items": [
                        "Establish a regular study routine",
                        "Review previous topics before moving forward",
                        "Practice stress management during assessments",
                    ],
                }
            )

        # Session-specific recommendations
        completion_rate = analyses["sessions"].get("completion_rate", 0)
        if completion_rate < 70:
            recommendations.append(
                {
                    "type": "session_completion",
                    "priority": "high",
                    "title": "Improve Session Completion",
                    "description": "Adjust session planning to improve completion rates",
                    "action_items": [
                        "Plan shorter sessions initially",
                        "Set clear, achievable goals for each session",
                        "Eliminate distractions during study time",
                    ],
                }
            )

        # Flashcard-specific recommendations
        retention_rate = analyses["flashcards"].get("retention_rate", 0)
        if retention_rate < 70:
            recommendations.append(
                {
                    "type": "memory_improvement",
                    "priority": "medium",
                    "title": "Enhance Memory Retention",
                    "description": "Implement better memory techniques",
                    "action_items": [
                        "Use spaced repetition more consistently",
                        "Create more memorable associations",
                        "Review cards more frequently initially",
                    ],
                }
            )

        return recommendations

    def _analyze_performance_trends(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Analyze performance trends over time."""
        # Get quiz score trends
        quiz_trends = self._get_quiz_score_trends(user, course, time_period_days)

        # Get study time trends
        study_time_trends = self._get_study_time_trends(user, course, time_period_days)

        # Get engagement trends
        engagement_trends = self._get_engagement_trends(user, course, time_period_days)

        return {
            "quiz_scores": quiz_trends,
            "study_time": study_time_trends,
            "engagement": engagement_trends,
            "overall_trend": self._determine_overall_trend(
                [
                    quiz_trends["trend"],
                    study_time_trends["trend"],
                    engagement_trends["trend"],
                ]
            ),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 3:
            return "insufficient_data"

        # Simple linear trend calculation
        x = list(range(len(values)))

        # Calculate correlation coefficient
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi**2 for xi in x)
        sum_y2 = sum(yi**2 for yi in values)

        denominator = (n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)
        if denominator <= 0:
            return "stable"

        correlation = (n * sum_xy - sum_x * sum_y) / (denominator**0.5)

        if correlation > 0.3:
            return "improving"
        elif correlation < -0.3:
            return "declining"
        else:
            return "stable"

    def _calculate_consistency(self, values: list[float]) -> float:
        """Calculate consistency score (0-100, higher is more consistent)."""
        if len(values) < 2:
            return 0

        std_dev = statistics.stdev(values)
        mean_val = statistics.mean(values)

        if mean_val == 0:
            return 0

        # Coefficient of variation (lower is more consistent)
        cv = std_dev / mean_val

        # Convert to consistency score (0-100)
        consistency = max(0, 100 - (cv * 100))

        return round(consistency, 1)

    def _calculate_time_efficiency(self, quiz_attempts) -> float:
        """Calculate quiz time efficiency."""
        attempts_with_time = quiz_attempts.filter(
            time_taken__isnull=False, time_taken__gt=0
        )

        if not attempts_with_time.exists():
            return 0

        # Calculate average time per question
        total_time = sum(attempt.time_taken for attempt in attempts_with_time)
        total_questions = sum(
            attempt.quiz.total_questions
            for attempt in attempts_with_time
            if hasattr(attempt.quiz, "total_questions")
        )

        if total_questions == 0:
            return 0

        avg_time_per_question = total_time / total_questions

        # Efficiency score (faster is better, but not too fast)
        # Optimal time: 30-60 seconds per question
        if 30 <= avg_time_per_question <= 60:
            return 100
        elif avg_time_per_question < 30:
            return max(50, 100 - (30 - avg_time_per_question) * 2)
        else:
            return max(0, 100 - (avg_time_per_question - 60))

    def _analyze_difficulty_performance(self, quiz_attempts) -> dict[str, float]:
        """Analyze performance by quiz difficulty."""
        difficulty_performance = {}

        for difficulty in ["easy", "medium", "hard"]:
            attempts = quiz_attempts.filter(quiz__difficulty=difficulty)
            if attempts.exists():
                avg_score = attempts.aggregate(avg=Avg("score"))["avg"]
                difficulty_performance[difficulty] = round(avg_score, 1)
            else:
                difficulty_performance[difficulty] = 0

        return difficulty_performance

    def _analyze_topic_performance(self, quiz_attempts) -> dict[str, float]:
        """Analyze performance by topic."""
        # This would require topic information in quiz model
        # For now, return empty dict
        return {}

    def _identify_weak_topics(self, topic_performance: dict[str, float]) -> list[str]:
        """Identify weak topics based on performance scores."""
        if not topic_performance:
            return []

        # Identify topics with scores below 70%
        weak_topics = [
            topic for topic, score in topic_performance.items() if score < 70.0
        ]

        # Sort by worst performance first
        weak_topics.sort(key=lambda t: topic_performance[t])

        # Return top 5 weakest topics
        return weak_topics[:5]

    def _analyze_session_timing(self, sessions) -> dict[str, Any]:
        """Analyze optimal timing for study sessions."""
        hourly_productivity = {}

        for session in sessions.filter(productivity_rating__isnull=False):
            hour = session.created_at.hour
            if hour not in hourly_productivity:
                hourly_productivity[hour] = []
            hourly_productivity[hour].append(session.productivity_rating)

        # Calculate averages
        hourly_averages = {
            hour: sum(ratings) / len(ratings)
            for hour, ratings in hourly_productivity.items()
        }

        # Find best time
        best_hour = (
            max(hourly_averages.items(), key=lambda x: x[1])[0]
            if hourly_averages
            else 9
        )

        return {
            "hourly_productivity": hourly_averages,
            "best_study_hour": best_hour,
            "productivity_variance": self._calculate_time_variance(hourly_averages),
        }

    def _find_optimal_session_length(self, sessions) -> int:
        """Find optimal session length based on productivity."""
        length_productivity = {}

        for session in sessions.filter(
            duration_minutes__isnull=False, productivity_rating__isnull=False
        ):
            length_range = self._categorize_session_length(session.duration_minutes)
            if length_range not in length_productivity:
                length_productivity[length_range] = []
            length_productivity[length_range].append(session.productivity_rating)

        # Find most productive length range
        best_range = None
        best_productivity = 0

        for length_range, ratings in length_productivity.items():
            avg_productivity = sum(ratings) / len(ratings)
            if avg_productivity > best_productivity:
                best_productivity = avg_productivity
                best_range = length_range

        # Convert to minutes
        range_minutes = {"short": 25, "medium": 45, "long": 90}

        return range_minutes.get(best_range, 45)

    def _categorize_session_length(self, minutes: int) -> str:
        """Categorize session length."""
        if minutes <= 30:
            return "short"
        elif minutes <= 60:
            return "medium"
        else:
            return "long"

    def _calculate_improvement_rate(self, progress_entries) -> float:
        """Calculate rate of improvement in learning progress."""
        if progress_entries.count() < 2:
            return 0

        # Group by week and calculate average mastery level
        weekly_progress = (
            progress_entries.annotate(week=TruncWeek("updated_at"))
            .values("week")
            .annotate(avg_mastery=Avg("mastery_level"))
            .order_by("week")
        )

        if len(weekly_progress) < 2:
            return 0

        # Calculate improvement rate
        first_week = weekly_progress[0]["avg_mastery"]
        last_week = weekly_progress[len(weekly_progress) - 1]["avg_mastery"]
        weeks_span = len(weekly_progress)

        improvement_rate = ((last_week - first_week) / weeks_span) * 100

        return round(improvement_rate, 2)

    def _count_mastered_cards(self, reviews) -> int:
        """Count flashcards that have been mastered."""
        # A card is considered mastered if last 3 reviews were 'easy'
        mastered_count = 0

        card_reviews = (
            reviews.values("flashcard")
            .annotate(last_reviews=Count("id"))
            .filter(last_reviews__gte=3)
        )

        for card_data in card_reviews:
            card_id = card_data["flashcard"]
            recent_reviews = reviews.filter(flashcard_id=card_id).order_by(
                "-created_at"
            )[:3]

            if all(review.quality_response >= 4 for review in recent_reviews):
                mastered_count += 1

        return mastered_count

    def _calculate_review_efficiency(self, reviews) -> float:
        """Calculate flashcard review efficiency."""
        if not reviews.exists():
            return 0

        # Efficiency is based on getting cards right quickly
        total_efficiency = 0
        count = 0

        for review in reviews.filter(response_time_seconds__isnull=False):
            # Optimal response time: 2-5 seconds
            response_time = review.response_time_seconds

            if review.quality_response >= 3:
                if 2 <= response_time <= 5:
                    efficiency = 100
                elif response_time < 2:
                    efficiency = 80  # Too fast, might be guessing
                else:
                    efficiency = max(0, 100 - (response_time - 5) * 10)
            else:
                efficiency = 0  # Wrong answer

            total_efficiency += efficiency
            count += 1

        return round(total_efficiency / count if count > 0 else 0, 1)

    def _calculate_study_streak(self, user, course) -> int:
        """Calculate current study streak."""
        from learning.models import StudySession

        sessions = StudySession.objects.filter(user=user)
        if course:
            sessions = sessions.filter(study_plan__course=course)

        # Check each day backwards from today
        current_date = timezone.now().date()
        streak = 0

        for i in range(365):  # Check up to a year
            check_date = current_date - timedelta(days=i)

            has_session = sessions.filter(created_at__date=check_date).exists()

            if has_session:
                streak += 1
            else:
                break

        return streak

    def _analyze_peak_activity_times(self, sessions) -> list[int]:
        """Find peak activity hours."""
        hourly_counts = {}

        for session in sessions:
            hour = session.created_at.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

        # Find top 3 hours
        sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)

        return [hour for hour, count in sorted_hours[:3]]

    def _calculate_engagement_score(
        self, sessions, study_streak: int, time_period_days: int
    ) -> float:
        """Calculate overall engagement score."""
        # Factors: session frequency, streak, completion rate
        session_frequency = sessions.count() / time_period_days
        completion_rate = sessions.filter(session_completed=True).count() / max(
            1, sessions.count()
        )

        # Normalize streak (max 30 days)
        streak_score = min(study_streak / 30, 1) * 100

        # Weight the factors
        engagement_score = (
            session_frequency * 30  # Max ~3 sessions per day
            + completion_rate * 40
            + streak_score * 30
        )

        return min(100, round(engagement_score, 1))

    def _find_most_active_day(self, sessions) -> str:
        """Find the most active day of the week."""
        day_counts = {}
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        for session in sessions:
            day = session.created_at.weekday()
            day_counts[day] = day_counts.get(day, 0) + 1

        if not day_counts:
            return "Unknown"

        most_active_day = max(day_counts.items(), key=lambda x: x[1])[0]
        return day_names[most_active_day]

    def _calculate_consistency_score(self, daily_activity) -> float:
        """Calculate consistency score based on daily activity."""
        if len(daily_activity) < 7:
            return 0

        activity_counts = [day["session_count"] for day in daily_activity]

        if not activity_counts:
            return 0

        # Calculate coefficient of variation
        mean_activity = sum(activity_counts) / len(activity_counts)

        if mean_activity == 0:
            return 0

        variance = sum((x - mean_activity) ** 2 for x in activity_counts) / len(
            activity_counts
        )
        std_dev = variance**0.5
        cv = std_dev / mean_activity

        # Convert to consistency score (lower CV = higher consistency)
        consistency = max(0, 100 - (cv * 100))

        return round(consistency, 1)

    def _categorize_performance(self, score: float) -> str:
        """Categorize performance level."""
        for category, threshold in self.performance_categories.items():
            if score >= threshold:
                # Capitalize first letter for consistency with tests
                if category == "needs_improvement":
                    return "Needs Improvement"
                return category.capitalize()
        return "Poor"

    def _get_quiz_score_trends(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Get quiz score trends over time."""
        from assessments.models import QuizAttempt

        attempts = QuizAttempt.objects.filter(
            user=user, created_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            attempts = attempts.filter(quiz__course=course)

        # Group by week
        weekly_scores = (
            attempts.annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(avg_score=Avg("score"), attempt_count=Count("id"))
            .order_by("week")
        )

        scores = [week["avg_score"] for week in weekly_scores]
        trend = self._calculate_trend(scores)

        return {
            "weekly_data": list(weekly_scores),
            "trend": trend,
            "latest_score": scores[-1] if scores else 0,
            "score_improvement": scores[-1] - scores[0] if len(scores) > 1 else 0,
        }

    def _get_study_time_trends(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Get study time trends over time."""
        from learning.models import StudySession

        sessions = StudySession.objects.filter(
            user=user, created_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            sessions = sessions.filter(study_plan__course=course)

        # Group by week
        weekly_time = (
            sessions.annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(total_hours=Sum("duration_hours"), session_count=Count("id"))
            .order_by("week")
        )

        hours = [week["total_hours"] or 0 for week in weekly_time]
        trend = self._calculate_trend(hours)

        return {
            "weekly_data": list(weekly_time),
            "trend": trend,
            "latest_hours": hours[-1] if hours else 0,
            "time_change": hours[-1] - hours[0] if len(hours) > 1 else 0,
        }

    def _get_engagement_trends(
        self, user, course, time_period_days: int
    ) -> dict[str, Any]:
        """Get engagement trends over time."""
        from learning.models import StudySession

        sessions = StudySession.objects.filter(
            user=user, created_at__gte=timezone.now() - timedelta(days=time_period_days)
        )

        if course:
            sessions = sessions.filter(study_plan__course=course)

        # Group by week and calculate engagement metrics
        weekly_engagement = (
            sessions.annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(
                session_count=Count("id"),
                avg_productivity=Avg("productivity_rating"),
                completion_rate=Avg("session_completed"),
            )
            .order_by("week")
        )

        # Calculate engagement scores for each week
        engagement_scores = []
        for week in weekly_engagement:
            score = (
                min(week["session_count"] / 7, 1) * 40  # Session frequency
                + (week["avg_productivity"] or 0) / 5 * 30  # Productivity
                + (week["completion_rate"] or 0) * 30  # Completion rate
            )
            engagement_scores.append(score)

        trend = self._calculate_trend(engagement_scores)

        return {
            "weekly_data": list(weekly_engagement),
            "trend": trend,
            "latest_engagement": engagement_scores[-1] if engagement_scores else 0,
            "engagement_change": (
                engagement_scores[-1] - engagement_scores[0]
                if len(engagement_scores) > 1
                else 0
            ),
        }

    def _determine_overall_trend(self, individual_trends: list[str]) -> str:
        """Determine overall trend from individual component trends."""
        improving_count = individual_trends.count("improving")
        declining_count = individual_trends.count("declining")

        if improving_count > declining_count:
            return "improving"
        elif declining_count > improving_count:
            return "declining"
        else:
            return "stable"

    def _calculate_time_variance(self, hourly_data: dict[int, float]) -> float:
        """Calculate variance in productivity across different times."""
        if len(hourly_data) < 2:
            return 0

        values = list(hourly_data.values())
        return round(statistics.variance(values), 2)

    def _analyze_quiz_completion(
        self, user, recent_activity: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze recent quiz completion for real-time feedback."""
        quiz_score = recent_activity.get("score", 0)
        recent_activity.get("time_taken", 0)

        # Get user's historical performance for comparison
        metrics = StudyMetrics(user, time_period_days=30)
        quiz_performance = metrics.get_quiz_performance()
        avg_score = quiz_performance["average_score"]

        # Performance comparison
        score_diff = quiz_score - avg_score

        feedback = {
            "performance_level": "good" if quiz_score >= avg_score else "below_average",
            "score_comparison": score_diff,
            "immediate_recommendations": [],
        }

        if score_diff < -10:
            feedback["immediate_recommendations"].append(
                "Review the topics covered in this quiz"
            )
            feedback["immediate_recommendations"].append(
                "Consider additional practice before the next quiz"
            )
        elif score_diff > 10:
            feedback["immediate_recommendations"].append(
                "Great improvement! Consider tackling more challenging content"
            )

        return feedback

    def _analyze_study_session_completion(
        self, user, recent_activity: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze recent study session for real-time feedback."""
        duration = recent_activity.get("duration_minutes", 0)
        productivity = recent_activity.get("productivity_rating", 0)
        completed = recent_activity.get("completed", False)

        feedback = {
            "session_quality": (
                "good" if productivity >= 3 and completed else "needs_improvement"
            ),
            "duration_feedback": self._evaluate_session_duration(duration),
            "immediate_recommendations": [],
        }

        if not completed:
            feedback["immediate_recommendations"].append(
                "Try shorter sessions to improve completion rate"
            )

        if productivity < 3:
            feedback["immediate_recommendations"].append(
                "Consider studying during your peak productivity hours"
            )
            feedback["immediate_recommendations"].append(
                "Eliminate distractions for better focus"
            )

        return feedback

    def _analyze_flashcard_session(
        self, user, recent_activity: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze recent flashcard session for real-time feedback."""
        cards_reviewed = recent_activity.get("cards_reviewed", 0)
        correct_rate = recent_activity.get("correct_rate", 0)

        feedback = {
            "retention_quality": "good" if correct_rate >= 0.8 else "needs_work",
            "volume_feedback": "sufficient" if cards_reviewed >= 10 else "low",
            "immediate_recommendations": [],
        }

        if correct_rate < 0.6:
            feedback["immediate_recommendations"].append(
                "Increase review frequency for these cards"
            )
            feedback["immediate_recommendations"].append(
                "Try creating memory associations"
            )

        return feedback

    def _evaluate_session_duration(self, duration_minutes: int) -> str:
        """Evaluate if session duration is optimal."""
        if duration_minutes < 15:
            return "too_short"
        elif duration_minutes > 120:
            return "too_long"
        elif 25 <= duration_minutes <= 90:
            return "optimal"
        else:
            return "acceptable"

    def _calculate_performance_trajectory(
        self, trends: dict[str, Any], prediction_days: int
    ) -> dict[str, Any]:
        """Calculate predicted performance trajectory."""
        # Simple linear projection based on current trends
        current_trends = [
            trends["quiz_scores"]["trend"],
            trends["study_time"]["trend"],
            trends["engagement"]["trend"],
        ]

        trajectory_direction = self._determine_overall_trend(current_trends)

        # Estimate trajectory strength
        if trajectory_direction == "improving":
            trajectory_strength = (
                "strong" if current_trends.count("improving") >= 2 else "moderate"
            )
        elif trajectory_direction == "declining":
            trajectory_strength = (
                "concerning" if current_trends.count("declining") >= 2 else "moderate"
            )
        else:
            trajectory_strength = "stable"

        return {
            "direction": trajectory_direction,
            "strength": trajectory_strength,
            "prediction_period_days": prediction_days,
            "confidence": self._calculate_prediction_confidence(trends),
        }

    def _assess_performance_risks(
        self, user, course, trends: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Assess risks to performance."""
        risks = []
        warnings = []

        # Check for declining trends
        if trends["quiz_scores"]["trend"] == "declining":
            risks.append("Quiz performance declining")

        if trends["engagement"]["trend"] == "declining":
            warnings.append("Engagement levels dropping")

        if trends["study_time"]["trend"] == "declining":
            warnings.append("Study time decreasing")

        return {"high_risks": risks, "warnings": warnings}

    def _recommend_interventions(
        self, trajectory: dict[str, Any], risks: dict[str, list[str]]
    ) -> list[dict[str, Any]]:
        """Recommend interventions based on trajectory and risks."""
        interventions = []

        if trajectory["direction"] == "declining":
            interventions.append(
                {
                    "type": "immediate",
                    "title": "Schedule Review Session",
                    "description": "Schedule an immediate review of recent topics",
                    "urgency": "high",
                }
            )

        if "Quiz performance declining" in risks["high_risks"]:
            interventions.append(
                {
                    "type": "learning_strategy",
                    "title": "Adjust Study Strategy",
                    "description": "Focus on active recall and practice testing",
                    "urgency": "high",
                }
            )

        if "Engagement levels dropping" in risks["warnings"]:
            interventions.append(
                {
                    "type": "motivation",
                    "title": "Re-engage with Material",
                    "description": "Try different study methods or set new goals",
                    "urgency": "medium",
                }
            )

        return interventions

    def _calculate_prediction_confidence(self, trends: dict[str, Any]) -> float:
        """Calculate confidence level in predictions."""
        # Based on data availability and trend consistency
        data_points = 0
        consistent_trends = 0

        for trend_type, trend_data in trends.items():
            if trend_data.get("weekly_data"):
                data_points += len(trend_data["weekly_data"])

            if trend_data.get("trend") in ["improving", "declining"]:
                consistent_trends += 1

        # Confidence based on data availability and trend clarity
        data_confidence = min(data_points / 12, 1.0)  # 12 weeks = high confidence
        trend_confidence = consistent_trends / len(trends)

        overall_confidence = (data_confidence + trend_confidence) / 2

        return round(overall_confidence * 100, 1)

    def _analyze_time_efficiency(self, attempts) -> dict[str, Any]:
        """Analyze time efficiency of quiz attempts."""
        if not attempts:
            return {
                "average_time": 0,
                "efficiency_score": 0,
                "time_vs_performance": "no_data",
            }

        total_time = 0
        total_score = 0
        count = 0

        for attempt in attempts:
            # Handle both dict and object attempts
            if isinstance(attempt, dict):
                time_taken = attempt.get("time_taken", 0)
                score = attempt.get("score", 0)
            else:
                time_taken = (
                    getattr(attempt, "time_taken", 0)
                    if hasattr(attempt, "time_taken")
                    else 0
                )
                score = getattr(attempt, "score", 0) if hasattr(attempt, "score") else 0

            if time_taken:
                total_time += time_taken
                total_score += score
                count += 1

        if count == 0:
            return {
                "average_time": 0,
                "efficiency_score": 0,
                "time_vs_performance": "no_data",
            }

        avg_time = round(total_time / count, 1)
        avg_score = round(total_score / count, 1)

        # Calculate efficiency score (higher score in less time = better)
        if avg_time > 0:
            efficiency = (avg_score / avg_time) * 100
        else:
            efficiency = 0

        # Determine time vs performance relationship
        if avg_score >= 80 and avg_time <= 300:  # Good score in reasonable time
            relationship = "optimal"
        elif avg_score >= 80 and avg_time > 300:  # Good score but slow
            relationship = "accurate_but_slow"
        elif avg_score < 80 and avg_time <= 300:  # Poor score despite quick time
            relationship = "rushed"
        else:
            relationship = "needs_improvement"

        return {
            "average_time": avg_time,
            "efficiency_score": round(efficiency, 1),
            "time_vs_performance": relationship,
        }

    def _analyze_difficulty_distribution(self, reviews) -> dict[str, float]:
        """Analyze difficulty distribution of flashcard reviews."""
        if not reviews:
            return {"easy": 0.0, "medium": 0.0, "hard": 0.0}

        total = len(reviews)
        easy_count = sum(1 for r in reviews if r.get("quality_response", 0) >= 4)
        medium_count = sum(1 for r in reviews if r.get("quality_response", 0) == 3)
        hard_count = sum(1 for r in reviews if r.get("quality_response", 0) in [1, 2])

        return {
            "easy": round((easy_count / total) * 100, 1) if total > 0 else 0.0,
            "medium": round((medium_count / total) * 100, 1) if total > 0 else 0.0,
            "hard": round((hard_count / total) * 100, 1) if total > 0 else 0.0,
        }

    def _identify_adaptation_triggers(
        self, performance_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Identify triggers for real-time adaptation."""
        triggers = []

        # Check quiz performance
        quiz_perf = performance_data.get("quiz_performance", {})
        if quiz_perf.get("average_score", 100) < 50:
            triggers.append(
                {
                    "type": "low_quiz_scores",
                    "severity": "high",
                    "recommendation": "Reduce difficulty or provide more practice",
                }
            )

        if quiz_perf.get("improvement_trend") == "Declining":
            triggers.append(
                {
                    "type": "declining_performance",
                    "severity": "medium",
                    "recommendation": "Review recent topics and adjust pacing",
                }
            )

        # Check study sessions
        study_sessions = performance_data.get("study_sessions", {})
        if study_sessions.get("completion_rate", 100) < 50:
            triggers.append(
                {
                    "type": "low_completion_rate",
                    "severity": "high",
                    "recommendation": "Shorten session duration or reduce workload",
                }
            )

        # Check learning progress
        learning_prog = performance_data.get("learning_progress", {})
        if learning_prog.get("average_mastery_level", 5) < 2:
            triggers.append(
                {
                    "type": "low_mastery",
                    "severity": "high",
                    "recommendation": "Focus on fundamentals and increase review",
                }
            )

        return triggers

    def _calculate_overall_score(self, component_scores: dict[str, float]) -> float:
        """Calculate overall performance score from components."""
        # Simple average of all component scores
        scores = list(component_scores.values())
        if not scores:
            return 0.0

        return round(sum(scores) / len(scores), 1)


# Global service instance
performance_analysis_service = PerformanceAnalysisService()


def get_performance_analysis_service() -> PerformanceAnalysisService:
    """Get the global performance analysis service instance."""
    return performance_analysis_service
