"""
Progress prediction service for forecasting learning outcomes and completion times.
"""

import logging
import statistics
from datetime import date, timedelta
from typing import Any

from django.db.models import Avg
from django.utils import timezone

from .base import AdaptiveLearningService, StudyMetrics

logger = logging.getLogger(__name__)


class ProgressPredictionService(AdaptiveLearningService):
    """
    Service for predicting learning progress and completion times.
    """

    def __init__(self):
        """Initialize the progress prediction service."""
        super().__init__()
        self.confidence_threshold = 0.7  # Minimum confidence for predictions
        self.prediction_horizon_days = 90  # Maximum days to predict ahead
        self.min_data_points = 5  # Minimum data points for reliable predictions

    def predict_course_completion(
        self, user, course, target_mastery_level: int = 4
    ) -> dict[str, Any]:
        """
        Predict when user will complete the course.

        Args:
            user: User object
            course: Course object
            target_mastery_level: Required mastery level for completion

        Returns:
            Course completion prediction
        """
        try:
            self.logger.info(
                f"Predicting course completion for user {user.id}, course {course.id}"
            )

            # Analyze current progress
            current_progress = self._analyze_current_progress(
                user, course, target_mastery_level
            )

            # Calculate learning velocity
            learning_velocity = self._calculate_learning_velocity(user, course)

            # Predict completion timeline
            completion_prediction = self._predict_completion_timeline(
                current_progress, learning_velocity, course
            )

            # Assess prediction confidence
            confidence = self._calculate_prediction_confidence(
                learning_velocity, current_progress
            )

            # Generate milestone predictions
            milestones = self._predict_milestones(
                current_progress, learning_velocity, course
            )

            return {
                "success": True,
                "completion_prediction": completion_prediction,
                "current_progress": current_progress,
                "learning_velocity": learning_velocity,
                "confidence": confidence,
                "milestones": milestones,
                "recommendations": self._generate_completion_recommendations(
                    completion_prediction, learning_velocity
                ),
            }

        except Exception as e:
            self.logger.error(f"Error predicting course completion: {str(e)}")
            return {"success": False, "error": str(e)}

    def predict_performance_trajectory(
        self, user, course=None, prediction_days: int = 30
    ) -> dict[str, Any]:
        """
        Predict performance trajectory over time.

        Args:
            user: User object
            course: Optional course filter
            prediction_days: Days ahead to predict

        Returns:
            Performance trajectory prediction
        """
        try:
            # Analyze historical performance trends
            performance_trends = self._analyze_performance_trends(user, course)

            # Model performance trajectory
            trajectory = self._model_performance_trajectory(
                performance_trends, prediction_days
            )

            # Identify potential issues
            risk_assessment = self._assess_trajectory_risks(trajectory)

            # Generate intervention recommendations
            interventions = self._recommend_trajectory_interventions(
                trajectory, risk_assessment
            )

            return {
                "success": True,
                "trajectory": trajectory,
                "risk_assessment": risk_assessment,
                "interventions": interventions,
                "confidence": self._calculate_trajectory_confidence(performance_trends),
            }

        except Exception as e:
            self.logger.error(f"Error predicting performance trajectory: {str(e)}")
            return {"success": False, "error": str(e)}

    def predict_study_plan_success(self, user, study_plan) -> dict[str, Any]:
        """
        Predict the likelihood of study plan success.

        Args:
            user: User object
            study_plan: StudyPlan object

        Returns:
            Success probability and factors
        """
        try:
            # Analyze user's historical performance
            historical_performance = self._analyze_historical_performance(user)

            # Assess plan difficulty
            plan_difficulty = self._assess_plan_difficulty(study_plan)

            # Calculate success probability
            success_probability = self._calculate_success_probability(
                historical_performance, plan_difficulty, study_plan
            )

            # Identify success factors
            success_factors = self._identify_success_factors(
                historical_performance, plan_difficulty
            )

            # Generate optimization recommendations
            optimizations = self._recommend_plan_optimizations(
                success_probability, success_factors, study_plan
            )

            return {
                "success": True,
                "success_probability": success_probability,
                "success_factors": success_factors,
                "plan_difficulty": plan_difficulty,
                "optimizations": optimizations,
                "confidence": self._calculate_success_prediction_confidence(
                    historical_performance, plan_difficulty
                ),
            }

        except Exception as e:
            self.logger.error(f"Error predicting study plan success: {str(e)}")
            return {"success": False, "error": str(e)}

    def predict_optimal_study_schedule(
        self, user, course, target_completion_date: date, weekly_hours_available: float
    ) -> dict[str, Any]:
        """
        Predict optimal study schedule to meet target completion date.

        Args:
            user: User object
            course: Course object
            target_completion_date: Desired completion date
            weekly_hours_available: Available study hours per week

        Returns:
            Optimal schedule prediction
        """
        try:
            # Calculate remaining work
            remaining_work = self._calculate_remaining_work(user, course)

            # Calculate time constraints
            time_constraints = self._calculate_time_constraints(
                target_completion_date, weekly_hours_available
            )

            # Predict optimal schedule
            optimal_schedule = self._predict_optimal_schedule(
                remaining_work, time_constraints, user
            )

            # Assess feasibility
            feasibility = self._assess_schedule_feasibility(
                optimal_schedule, time_constraints, user
            )

            return {
                "success": True,
                "optimal_schedule": optimal_schedule,
                "feasibility": feasibility,
                "remaining_work": remaining_work,
                "time_constraints": time_constraints,
                "recommendations": self._generate_schedule_recommendations(
                    optimal_schedule, feasibility
                ),
            }

        except Exception as e:
            self.logger.error(f"Error predicting optimal schedule: {str(e)}")
            return {"success": False, "error": str(e)}

    def _analyze_current_progress(
        self, user, course, target_mastery_level: int
    ) -> dict[str, Any]:
        """Analyze current learning progress."""
        from courses.models import Document
        from learning.models import LearningProgress

        # Get all course topics/documents
        total_documents = Document.objects.filter(course=course).count()

        # Get user's progress
        progress_entries = LearningProgress.objects.filter(user=user, course=course)

        total_progress_entries = progress_entries.count()
        mastered_entries = progress_entries.filter(
            mastery_level__gte=target_mastery_level
        ).count()

        # Calculate completion percentage
        if total_documents > 0:
            completion_percentage = (mastered_entries / total_documents) * 100
        else:
            completion_percentage = 0

        # Calculate average mastery level
        avg_mastery = progress_entries.aggregate(avg=Avg("mastery_level"))["avg"] or 0

        return {
            "total_topics": total_documents,
            "topics_started": total_progress_entries,
            "topics_mastered": mastered_entries,
            "completion_percentage": round(completion_percentage, 1),
            "average_mastery_level": round(avg_mastery, 1),
            "topics_remaining": total_documents - mastered_entries,
        }

    def _calculate_learning_velocity(self, user, course) -> dict[str, Any]:
        """Calculate user's learning velocity."""
        from learning.models import LearningProgress

        # Get progress over last 30 days
        recent_progress = LearningProgress.objects.filter(
            user=user,
            course=course,
            updated_at__gte=timezone.now() - timedelta(days=30),
        )

        if not recent_progress.exists():
            return {
                "topics_per_week": 0,
                "mastery_improvement_rate": 0,
                "velocity_trend": "insufficient_data",
                "consistency_score": 0,
            }

        # Calculate topics progressed per week
        days_of_data = 30
        topics_progressed = recent_progress.count()
        topics_per_week = (topics_progressed / days_of_data) * 7

        # Calculate mastery improvement rate
        mastery_improvements = recent_progress.filter(mastery_level__gte=3).count()
        mastery_improvement_rate = (mastery_improvements / days_of_data) * 7

        # Analyze velocity trend
        velocity_trend = self._analyze_velocity_trend(user, course)

        # Calculate consistency
        consistency_score = self._calculate_velocity_consistency(user, course)

        return {
            "topics_per_week": round(topics_per_week, 2),
            "mastery_improvement_rate": round(mastery_improvement_rate, 2),
            "velocity_trend": velocity_trend,
            "consistency_score": consistency_score,
        }

    def _predict_completion_timeline(
        self,
        current_progress: dict[str, Any],
        learning_velocity: dict[str, Any],
        course,
    ) -> dict[str, Any]:
        """Predict course completion timeline."""
        topics_remaining = current_progress["topics_remaining"]
        velocity = learning_velocity["topics_per_week"]

        if velocity <= 0:
            return {
                "estimated_completion_date": None,
                "weeks_remaining": float("inf"),
                "completion_probability": 0,
                "scenario_analysis": {},
            }

        # Calculate base estimate
        weeks_remaining = topics_remaining / velocity
        estimated_completion = timezone.now().date() + timedelta(weeks=weeks_remaining)

        # Calculate scenario analysis
        scenario_analysis = self._calculate_completion_scenarios(
            topics_remaining, velocity, learning_velocity["velocity_trend"]
        )

        # Calculate completion probability
        completion_probability = self._calculate_completion_probability(
            weeks_remaining, learning_velocity["consistency_score"]
        )

        return {
            "estimated_completion_date": estimated_completion.isoformat(),
            "weeks_remaining": round(weeks_remaining, 1),
            "completion_probability": completion_probability,
            "scenario_analysis": scenario_analysis,
        }

    def _calculate_prediction_confidence(
        self, learning_velocity: dict[str, Any], current_progress: dict[str, Any]
    ) -> float:
        """Calculate confidence in predictions."""
        factors = []

        # Data availability factor
        topics_started = current_progress["topics_started"]
        data_factor = min(1.0, topics_started / 10)  # Full confidence at 10+ topics
        factors.append(data_factor)

        # Velocity consistency factor
        consistency = learning_velocity["consistency_score"]
        factors.append(consistency / 100)  # Convert percentage to 0-1

        # Trend stability factor
        trend = learning_velocity["velocity_trend"]
        trend_factor = {
            "improving": 0.8,
            "stable": 0.9,
            "declining": 0.6,
            "insufficient_data": 0.3,
        }.get(trend, 0.5)
        factors.append(trend_factor)

        # Calculate weighted average
        confidence = sum(factors) / len(factors)

        return round(confidence, 2)

    def _predict_milestones(
        self,
        current_progress: dict[str, Any],
        learning_velocity: dict[str, Any],
        course,
    ) -> list[dict[str, Any]]:
        """Predict milestone completion dates."""
        milestones = []

        topics_remaining = current_progress["topics_remaining"]
        velocity = learning_velocity["topics_per_week"]

        if velocity <= 0:
            return milestones

        # Define milestones at 25%, 50%, 75%, 100%
        milestone_percentages = [0.25, 0.5, 0.75, 1.0]

        for percentage in milestone_percentages:
            topics_for_milestone = int(topics_remaining * percentage)
            weeks_to_milestone = topics_for_milestone / velocity
            milestone_date = timezone.now().date() + timedelta(weeks=weeks_to_milestone)

            milestones.append(
                {
                    "percentage": int(percentage * 100),
                    "topics_to_complete": topics_for_milestone,
                    "estimated_date": milestone_date.isoformat(),
                    "weeks_from_now": round(weeks_to_milestone, 1),
                    "confidence": max(
                        0.1, 0.9 - (weeks_to_milestone / 52)
                    ),  # Decrease confidence over time
                }
            )

        return milestones

    def _analyze_performance_trends(self, user, course) -> dict[str, Any]:
        """Analyze historical performance trends."""

        # Quiz performance trend
        quiz_trend = self._analyze_quiz_trend(user, course)

        # Study session trend
        session_trend = self._analyze_session_trend(user, course)

        # Overall engagement trend
        engagement_trend = self._analyze_engagement_trend(user, course)

        return {
            "quiz_performance": quiz_trend,
            "study_sessions": session_trend,
            "engagement": engagement_trend,
            "overall_trend": self._determine_overall_trend(
                [
                    quiz_trend["direction"],
                    session_trend["direction"],
                    engagement_trend["direction"],
                ]
            ),
        }

    def _model_performance_trajectory(
        self, performance_trends: dict[str, Any], prediction_days: int
    ) -> dict[str, Any]:
        """Model future performance trajectory."""
        overall_trend = performance_trends["overall_trend"]

        # Base trajectory based on current trend
        if overall_trend == "improving":
            trajectory_slope = 0.5  # Performance improves by 0.5% per day
        elif overall_trend == "declining":
            trajectory_slope = -0.3  # Performance declines by 0.3% per day
        else:
            trajectory_slope = 0.1  # Slight improvement for stable trend

        # Generate daily predictions
        daily_predictions = []
        current_performance = 75  # Assume 75% baseline performance

        for day in range(prediction_days):
            # Add some randomness to simulate real variations
            daily_variation = (day % 7) * 2 - 6  # Weekly pattern
            predicted_performance = (
                current_performance + (trajectory_slope * day) + daily_variation
            )

            # Ensure bounds
            predicted_performance = max(0, min(100, predicted_performance))

            prediction_date = timezone.now().date() + timedelta(days=day)
            daily_predictions.append(
                {
                    "date": prediction_date.isoformat(),
                    "predicted_performance": round(predicted_performance, 1),
                    "confidence": max(0.1, 0.9 - (day / prediction_days)),
                }
            )

        return {
            "daily_predictions": daily_predictions,
            "trajectory_slope": trajectory_slope,
            "trend_direction": overall_trend,
            "prediction_horizon_days": prediction_days,
        }

    def _assess_trajectory_risks(
        self, trajectory: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Assess risks in performance trajectory."""
        risks = []
        warnings = []

        trajectory_slope = trajectory["trajectory_slope"]
        daily_predictions = trajectory["daily_predictions"]

        # Check for declining performance
        if trajectory_slope < -0.2:
            risks.append("Performance declining rapidly")
        elif trajectory_slope < 0:
            warnings.append("Performance showing slight decline")

        # Check for low future performance
        future_performance = [
            p["predicted_performance"] for p in daily_predictions[-7:]
        ]
        if future_performance and min(future_performance) < 60:
            risks.append("Performance predicted to drop below 60%")

        # Check for high variability
        if len(daily_predictions) > 7:
            recent_predictions = [
                p["predicted_performance"] for p in daily_predictions[:7]
            ]
            if statistics.stdev(recent_predictions) > 15:
                warnings.append("High performance variability predicted")

        return {"high_risks": risks, "warnings": warnings}

    def _recommend_trajectory_interventions(
        self, trajectory: dict[str, Any], risk_assessment: dict[str, list[str]]
    ) -> list[dict[str, Any]]:
        """Recommend interventions for trajectory improvement."""
        interventions = []

        trajectory_slope = trajectory["trajectory_slope"]

        if trajectory_slope < -0.2:
            interventions.append(
                {
                    "type": "immediate",
                    "priority": "high",
                    "title": "Schedule Review Session",
                    "description": "Performance is declining rapidly - schedule immediate review",
                    "action_items": [
                        "Review recent topics",
                        "Reduce study intensity temporarily",
                        "Focus on fundamentals",
                    ],
                }
            )

        if "Performance declining rapidly" in risk_assessment["high_risks"]:
            interventions.append(
                {
                    "type": "study_strategy",
                    "priority": "high",
                    "title": "Adjust Study Strategy",
                    "description": "Change study approach to improve performance",
                    "action_items": [
                        "Try active recall techniques",
                        "Increase practice frequency",
                        "Get additional help or tutoring",
                    ],
                }
            )

        return interventions

    def _analyze_historical_performance(self, user) -> dict[str, Any]:
        """Analyze user's historical performance across all courses."""
        from assessments.models import QuizAttempt
        from learning.models import StudyPlan, StudySession

        # Get overall metrics
        all_attempts = QuizAttempt.objects.filter(user=user)
        all_sessions = StudySession.objects.filter(user=user)
        completed_plans = StudyPlan.objects.filter(user=user, status="completed")

        # Calculate historical success rate
        if all_attempts.exists():
            avg_quiz_score = all_attempts.aggregate(avg=Avg("score"))["avg"]
            quiz_success_rate = (
                len([a for a in all_attempts if a.score >= 75]) / all_attempts.count()
            )
        else:
            avg_quiz_score = 0
            quiz_success_rate = 0

        # Calculate plan completion rate
        total_plans = StudyPlan.objects.filter(user=user).count()
        plan_completion_rate = (
            completed_plans.count() / total_plans if total_plans > 0 else 0
        )

        # Calculate consistency metrics
        consistency_score = self._calculate_historical_consistency(user)

        return {
            "average_quiz_score": round(avg_quiz_score, 1),
            "quiz_success_rate": round(quiz_success_rate, 2),
            "plan_completion_rate": round(plan_completion_rate, 2),
            "consistency_score": consistency_score,
            "total_study_hours": sum(
                s.duration_hours for s in all_sessions if s.duration_hours
            ),
            "data_quality": self._assess_historical_data_quality(user),
        }

    def _assess_plan_difficulty(self, study_plan) -> dict[str, Any]:
        """Assess difficulty of study plan."""
        study_plan.plan_data

        # Calculate difficulty factors
        total_hours = study_plan.daily_study_hours * study_plan.study_days_per_week
        plan_duration_weeks = (study_plan.end_date - study_plan.start_date).days / 7

        # Assess intensity
        if total_hours > 20:
            intensity = "very_high"
        elif total_hours > 15:
            intensity = "high"
        elif total_hours > 10:
            intensity = "medium"
        else:
            intensity = "low"

        # Assess duration feasibility
        if plan_duration_weeks > 20:
            duration_difficulty = "high"
        elif plan_duration_weeks > 12:
            duration_difficulty = "medium"
        else:
            duration_difficulty = "low"

        return {
            "intensity": intensity,
            "duration_difficulty": duration_difficulty,
            "weekly_hours": total_hours,
            "duration_weeks": plan_duration_weeks,
            "overall_difficulty": self._calculate_overall_difficulty(
                intensity, duration_difficulty
            ),
        }

    def _calculate_success_probability(
        self,
        historical_performance: dict[str, Any],
        plan_difficulty: dict[str, Any],
        study_plan,
    ) -> float:
        """Calculate probability of study plan success."""
        # Base probability from historical performance
        base_probability = (
            historical_performance["quiz_success_rate"] * 0.4
            + historical_performance["plan_completion_rate"] * 0.4
            + historical_performance["consistency_score"] / 100 * 0.2
        )

        # Adjust for plan difficulty
        difficulty_multipliers = {
            "low": 1.1,
            "medium": 1.0,
            "high": 0.8,
            "very_high": 0.6,
        }

        overall_difficulty = plan_difficulty["overall_difficulty"]
        difficulty_multiplier = difficulty_multipliers.get(overall_difficulty, 1.0)

        # Calculate final probability
        success_probability = base_probability * difficulty_multiplier

        # Ensure bounds
        success_probability = max(0.1, min(0.95, success_probability))

        return round(success_probability, 2)

    def _identify_success_factors(
        self, historical_performance: dict[str, Any], plan_difficulty: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Identify factors that affect success probability."""
        positive_factors = []
        negative_factors = []

        # Historical performance factors
        if historical_performance["quiz_success_rate"] > 0.8:
            positive_factors.append("Strong quiz performance history")
        elif historical_performance["quiz_success_rate"] < 0.6:
            negative_factors.append("Weak quiz performance history")

        if historical_performance["plan_completion_rate"] > 0.8:
            positive_factors.append("High plan completion rate")
        elif historical_performance["plan_completion_rate"] < 0.6:
            negative_factors.append("Low plan completion rate")

        if historical_performance["consistency_score"] > 80:
            positive_factors.append("Consistent study habits")
        elif historical_performance["consistency_score"] < 60:
            negative_factors.append("Inconsistent study habits")

        # Plan difficulty factors
        if plan_difficulty["overall_difficulty"] == "low":
            positive_factors.append("Manageable plan difficulty")
        elif plan_difficulty["overall_difficulty"] in ["high", "very_high"]:
            negative_factors.append("Challenging plan difficulty")

        return {
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
        }

    def _recommend_plan_optimizations(
        self,
        success_probability: float,
        success_factors: dict[str, list[str]],
        study_plan,
    ) -> list[dict[str, Any]]:
        """Recommend optimizations to improve success probability."""
        optimizations = []

        if success_probability < 0.7:
            optimizations.append(
                {
                    "type": "difficulty_reduction",
                    "priority": "high",
                    "title": "Reduce Plan Difficulty",
                    "description": "Current plan may be too challenging",
                    "suggestions": [
                        "Reduce daily study hours by 25%",
                        "Extend plan duration",
                        "Focus on fewer topics initially",
                    ],
                }
            )

        if "Inconsistent study habits" in success_factors["negative_factors"]:
            optimizations.append(
                {
                    "type": "consistency_improvement",
                    "priority": "medium",
                    "title": "Improve Study Consistency",
                    "description": "Build more consistent study habits",
                    "suggestions": [
                        "Set fixed study times",
                        "Start with shorter sessions",
                        "Use habit tracking",
                    ],
                }
            )

        if "Weak quiz performance history" in success_factors["negative_factors"]:
            optimizations.append(
                {
                    "type": "assessment_strategy",
                    "priority": "medium",
                    "title": "Improve Assessment Performance",
                    "description": "Focus on better quiz preparation",
                    "suggestions": [
                        "Practice more before quizzes",
                        "Review mistakes thoroughly",
                        "Use active recall techniques",
                    ],
                }
            )

        return optimizations

    def _calculate_remaining_work(self, user, course) -> dict[str, Any]:
        """Calculate remaining work for course completion."""
        from courses.models import Document
        from learning.models import LearningProgress

        total_documents = Document.objects.filter(course=course).count()

        progress_entries = LearningProgress.objects.filter(user=user, course=course)

        mastered_topics = progress_entries.filter(mastery_level__gte=4).count()
        in_progress_topics = progress_entries.filter(mastery_level__in=[2, 3]).count()
        not_started_topics = total_documents - progress_entries.count()

        # Estimate hours needed
        hours_per_topic = {
            "not_started": 3,  # New topics need more time
            "in_progress": 1.5,  # Partially learned topics
            "review": 0.5,  # Quick review for mastered topics
        }

        estimated_hours = (
            not_started_topics * hours_per_topic["not_started"]
            + in_progress_topics * hours_per_topic["in_progress"]
            + mastered_topics * hours_per_topic["review"]
        )

        return {
            "total_topics": total_documents,
            "not_started_topics": not_started_topics,
            "in_progress_topics": in_progress_topics,
            "mastered_topics": mastered_topics,
            "estimated_hours_remaining": estimated_hours,
        }

    def _calculate_time_constraints(
        self, target_date: date, weekly_hours: float
    ) -> dict[str, Any]:
        """Calculate time constraints for schedule optimization."""
        days_available = (target_date - timezone.now().date()).days
        weeks_available = days_available / 7
        total_hours_available = weeks_available * weekly_hours

        return {
            "target_date": target_date.isoformat(),
            "days_available": days_available,
            "weeks_available": round(weeks_available, 1),
            "weekly_hours_available": weekly_hours,
            "total_hours_available": round(total_hours_available, 1),
            "daily_hours_needed": (
                round(weekly_hours / 7, 1) if weeks_available > 0 else 0
            ),
        }

    def _predict_optimal_schedule(
        self, remaining_work: dict[str, Any], time_constraints: dict[str, Any], user
    ) -> dict[str, Any]:
        """Predict optimal schedule to meet constraints."""
        hours_needed = remaining_work["estimated_hours_remaining"]
        hours_available = time_constraints["total_hours_available"]

        # Check if schedule is feasible
        if hours_needed > hours_available:
            # Need to prioritize
            schedule_type = "prioritized"
            feasibility_ratio = hours_available / hours_needed
        else:
            schedule_type = "comprehensive"
            feasibility_ratio = 1.0

        # Calculate optimal weekly distribution
        weekly_hours_needed = (
            hours_needed / time_constraints["weeks_available"]
            if time_constraints["weeks_available"] > 0
            else hours_needed
        )

        # Get user's optimal study times
        metrics = StudyMetrics(user)
        optimal_times = metrics.get_optimal_study_time()

        return {
            "schedule_type": schedule_type,
            "feasibility_ratio": round(feasibility_ratio, 2),
            "recommended_weekly_hours": round(weekly_hours_needed, 1),
            "recommended_daily_hours": round(weekly_hours_needed / 7, 1),
            "optimal_study_times": optimal_times["optimal_hours"],
            "session_length_recommendation": optimal_times[
                "recommended_session_length"
            ],
        }

    def _assess_schedule_feasibility(
        self, optimal_schedule: dict[str, Any], time_constraints: dict[str, Any], user
    ) -> dict[str, Any]:
        """Assess feasibility of optimal schedule."""
        feasibility_ratio = optimal_schedule["feasibility_ratio"]
        recommended_daily_hours = optimal_schedule["recommended_daily_hours"]

        # Assess overall feasibility
        if feasibility_ratio >= 1.0:
            overall_feasibility = "high"
        elif feasibility_ratio >= 0.8:
            overall_feasibility = "medium"
        elif feasibility_ratio >= 0.6:
            overall_feasibility = "low"
        else:
            overall_feasibility = "very_low"

        # Assess daily commitment feasibility
        if recommended_daily_hours <= 2:
            daily_feasibility = "high"
        elif recommended_daily_hours <= 4:
            daily_feasibility = "medium"
        elif recommended_daily_hours <= 6:
            daily_feasibility = "low"
        else:
            daily_feasibility = "very_low"

        # Calculate success probability
        success_probability = min(1.0, feasibility_ratio) * 0.8
        if daily_feasibility in ["low", "very_low"]:
            success_probability *= 0.7

        return {
            "overall_feasibility": overall_feasibility,
            "daily_feasibility": daily_feasibility,
            "success_probability": round(success_probability, 2),
            "risk_factors": self._identify_schedule_risks(
                optimal_schedule, time_constraints
            ),
        }

    def _generate_completion_recommendations(
        self, completion_prediction: dict[str, Any], learning_velocity: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations for course completion."""
        recommendations = []

        weeks_remaining = completion_prediction["weeks_remaining"]
        velocity_trend = learning_velocity["velocity_trend"]

        if weeks_remaining > 26:  # More than 6 months
            recommendations.append(
                "Consider increasing study intensity to complete sooner"
            )

        if velocity_trend == "declining":
            recommendations.append(
                "Your learning pace is slowing - consider reviewing study methods"
            )
        elif velocity_trend == "improving":
            recommendations.append(
                "Great progress! You might be able to complete ahead of schedule"
            )

        completion_probability = completion_prediction["completion_probability"]
        if completion_probability < 0.7:
            recommendations.append(
                "Consider adjusting your study plan to improve completion chances"
            )

        return recommendations

    def _generate_schedule_recommendations(
        self, optimal_schedule: dict[str, Any], feasibility: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations for schedule optimization."""
        recommendations = []

        if feasibility["overall_feasibility"] in ["low", "very_low"]:
            recommendations.append("Consider extending your target completion date")
            recommendations.append("Focus on high-priority topics first")

        if feasibility["daily_feasibility"] in ["low", "very_low"]:
            recommendations.append("Reduce daily study hours to maintain consistency")
            recommendations.append("Consider spreading study over more days")

        if optimal_schedule["schedule_type"] == "prioritized":
            recommendations.append(
                "Prioritize core concepts and skip optional material"
            )

        return recommendations

    # Helper methods for calculations and analysis
    def _analyze_velocity_trend(self, user, course) -> str:
        """Analyze trend in learning velocity."""
        # Simplified implementation
        return "stable"

    def _calculate_velocity_consistency(self, user, course) -> float:
        """Calculate consistency of learning velocity."""
        # Simplified implementation
        return 75.0

    def _calculate_completion_scenarios(
        self, topics_remaining: int, velocity: float, trend: str
    ) -> dict[str, Any]:
        """Calculate different completion scenarios."""
        return {
            "optimistic": {
                "weeks": max(1, topics_remaining / (velocity * 1.2)),
                "probability": 0.3,
            },
            "realistic": {
                "weeks": max(1, topics_remaining / velocity),
                "probability": 0.5,
            },
            "pessimistic": {
                "weeks": max(1, topics_remaining / (velocity * 0.8)),
                "probability": 0.2,
            },
        }

    def _calculate_completion_probability(
        self, weeks_remaining: float, consistency: float
    ) -> float:
        """Calculate probability of completing on schedule."""
        # Base probability decreases with time
        time_factor = max(0.3, 1.0 - (weeks_remaining / 52))  # Decrease over year

        # Consistency factor
        consistency_factor = consistency / 100

        probability = (time_factor + consistency_factor) / 2
        return round(probability, 2)

    def _analyze_quiz_trend(self, user, course) -> dict[str, str]:
        """Analyze quiz performance trend."""
        return {"direction": "stable", "strength": "moderate"}

    def _analyze_session_trend(self, user, course) -> dict[str, str]:
        """Analyze study session trend."""
        return {"direction": "stable", "strength": "moderate"}

    def _analyze_engagement_trend(self, user, course) -> dict[str, str]:
        """Analyze engagement trend."""
        return {"direction": "stable", "strength": "moderate"}

    def _determine_overall_trend(self, individual_trends: list[str]) -> str:
        """Determine overall trend from individual trends."""
        improving_count = individual_trends.count("improving")
        declining_count = individual_trends.count("declining")

        if improving_count > declining_count:
            return "improving"
        elif declining_count > improving_count:
            return "declining"
        else:
            return "stable"

    def _calculate_trajectory_confidence(
        self, performance_trends: dict[str, Any]
    ) -> float:
        """Calculate confidence in trajectory prediction."""
        return 0.75  # Simplified implementation

    def _calculate_historical_consistency(self, user) -> float:
        """Calculate historical consistency score."""
        return 75.0  # Simplified implementation

    def _assess_historical_data_quality(self, user) -> str:
        """Assess quality of historical data."""
        return "good"  # Simplified implementation

    def _calculate_overall_difficulty(
        self, intensity: str, duration_difficulty: str
    ) -> str:
        """Calculate overall plan difficulty."""
        difficulty_scores = {"low": 1, "medium": 2, "high": 3, "very_high": 4}

        intensity_score = difficulty_scores.get(intensity, 2)
        duration_score = difficulty_scores.get(duration_difficulty, 2)

        avg_score = (intensity_score + duration_score) / 2

        if avg_score <= 1.5:
            return "low"
        elif avg_score <= 2.5:
            return "medium"
        elif avg_score <= 3.5:
            return "high"
        else:
            return "very_high"

    def _calculate_success_prediction_confidence(
        self, historical_performance: dict[str, Any], plan_difficulty: dict[str, Any]
    ) -> float:
        """Calculate confidence in success prediction."""
        data_quality = historical_performance["data_quality"]

        quality_scores = {"excellent": 0.9, "good": 0.8, "fair": 0.6, "poor": 0.4}

        return quality_scores.get(data_quality, 0.6)

    def _identify_schedule_risks(
        self, optimal_schedule: dict[str, Any], time_constraints: dict[str, Any]
    ) -> list[str]:
        """Identify risks in schedule feasibility."""
        risks = []

        if optimal_schedule["feasibility_ratio"] < 0.8:
            risks.append("Insufficient time for comprehensive coverage")

        if optimal_schedule["recommended_daily_hours"] > 4:
            risks.append("High daily commitment may lead to burnout")

        if time_constraints["weeks_available"] < 4:
            risks.append("Very short timeframe increases risk of failure")

        return risks


# Global service instance
progress_prediction_service = ProgressPredictionService()


def get_progress_prediction_service() -> ProgressPredictionService:
    """Get the global progress prediction service instance."""
    return progress_prediction_service
