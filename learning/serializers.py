"""
Serializers for learning management models.
"""

from rest_framework import serializers

from .models import (
    LearningProgress,
    StudyGoal,
    StudyPlan,
    StudyRecommendation,
    StudySession,
)


class StudyPlanSerializer(serializers.ModelSerializer):
    """Serializer for StudyPlan model."""

    progress_percentage = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = StudyPlan
        fields = [
            "id",
            "title",
            "description",
            "plan_type",
            "status",
            "start_date",
            "end_date",
            "target_exam_date",
            "daily_study_hours",
            "study_days_per_week",
            "plan_data",
            "total_tasks",
            "completed_tasks",
            "progress_percentage",
            "is_active",
            "generated_at",
            "last_updated",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user",
            "generated_at",
            "last_updated",
            "created_at",
            "updated_at",
        ]


class StudyPlanDetailSerializer(StudyPlanSerializer):
    """Detailed serializer for StudyPlan with related objects."""

    goals_count = serializers.SerializerMethodField()
    sessions_count = serializers.SerializerMethodField()

    class Meta(StudyPlanSerializer.Meta):
        fields = StudyPlanSerializer.Meta.fields + ["goals_count", "sessions_count"]

    def get_goals_count(self, obj):
        return obj.goals.count()

    def get_sessions_count(self, obj):
        return obj.sessions.count()


class StudyPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StudyPlan."""

    class Meta:
        model = StudyPlan
        fields = [
            "course",
            "title",
            "description",
            "plan_type",
            "start_date",
            "end_date",
            "target_exam_date",
            "daily_study_hours",
            "study_days_per_week",
        ]


class StudyGoalSerializer(serializers.ModelSerializer):
    """Serializer for StudyGoal model."""

    progress_percentage = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = StudyGoal
        fields = [
            "id",
            "title",
            "description",
            "goal_type",
            "status",
            "target_value",
            "current_value",
            "unit",
            "start_date",
            "target_date",
            "completed_date",
            "is_ai_suggested",
            "ai_rationale",
            "streak_count",
            "best_streak",
            "last_progress_date",
            "progress_percentage",
            "is_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user",
            "completed_date",
            "streak_count",
            "best_streak",
            "last_progress_date",
            "created_at",
            "updated_at",
        ]


class StudyGoalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StudyGoal."""

    class Meta:
        model = StudyGoal
        fields = [
            "course",
            "study_plan",
            "title",
            "description",
            "goal_type",
            "target_value",
            "unit",
            "start_date",
            "target_date",
            "is_ai_suggested",
            "ai_rationale",
        ]


class LearningProgressSerializer(serializers.ModelSerializer):
    """Serializer for LearningProgress model."""

    class Meta:
        model = LearningProgress
        fields = [
            "id",
            "progress_type",
            "identifier",
            "completion_percentage",
            "mastery_level",
            "confidence_score",
            "total_study_time",
            "last_studied",
            "quiz_average",
            "flashcard_retention",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "course", "created_at", "updated_at"]


class StudySessionSerializer(serializers.ModelSerializer):
    """Serializer for StudySession model."""

    duration_planned = serializers.ReadOnlyField()
    duration_actual = serializers.ReadOnlyField()

    class Meta:
        model = StudySession
        fields = [
            "id",
            "title",
            "description",
            "session_type",
            "status",
            "scheduled_start",
            "scheduled_end",
            "actual_start",
            "actual_end",
            "topics",
            "materials",
            "completion_notes",
            "satisfaction_rating",
            "productivity_rating",
            "objectives_completed",
            "total_objectives",
            "duration_planned",
            "duration_actual",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user",
            "actual_start",
            "actual_end",
            "created_at",
            "updated_at",
        ]


class StudySessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StudySession."""

    class Meta:
        model = StudySession
        fields = [
            "course",
            "study_plan",
            "title",
            "description",
            "session_type",
            "scheduled_start",
            "scheduled_end",
            "topics",
            "materials",
            "total_objectives",
        ]


class StudyRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for StudyRecommendation model."""

    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = StudyRecommendation
        fields = [
            "id",
            "recommendation_type",
            "priority",
            "status",
            "title",
            "description",
            "rationale",
            "recommendation_data",
            "expires_at",
            "accepted_at",
            "dismissed_at",
            "user_feedback",
            "effectiveness_rating",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user",
            "accepted_at",
            "dismissed_at",
            "created_at",
            "updated_at",
        ]


# Analytics serializers
class StudyAnalyticsSerializer(serializers.Serializer):
    """Serializer for study analytics data."""

    total_study_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_daily_hours = serializers.DecimalField(max_digits=5, decimal_places=2)
    goals_completed = serializers.IntegerField()
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()


class LearningPathAnalysisSerializer(serializers.Serializer):
    """Serializer for learning path analysis."""

    recommended_topics = serializers.ListField(child=serializers.CharField())
    difficulty_progression = serializers.DictField()
    estimated_completion_time = serializers.IntegerField()
    prerequisite_gaps = serializers.ListField(child=serializers.CharField())


class PerformanceTrendsSerializer(serializers.Serializer):
    """Serializer for performance trends data."""

    weekly_progress = serializers.ListField(child=serializers.DictField())
    monthly_trends = serializers.ListField(child=serializers.DictField())
    skill_development = serializers.DictField()
    learning_velocity = serializers.DecimalField(max_digits=5, decimal_places=2)


class LearningRecommendationSerializer(serializers.Serializer):
    """Serializer for AI-generated learning recommendations."""

    type = serializers.CharField()
    priority = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    action = serializers.CharField()
    metadata = serializers.DictField()
