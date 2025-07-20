from django.contrib import admin

from .models import (
    LearningProgress,
    StudyGoal,
    StudyPlan,
    StudyRecommendation,
    StudySession,
)


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "course",
        "plan_type",
        "status",
        "start_date",
        "end_date",
        "progress_percentage",
    ]
    list_filter = ["plan_type", "status", "start_date", "created_at"]
    search_fields = ["title", "user__username", "course__title"]
    readonly_fields = ["id", "created_at", "updated_at", "generated_at"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "course",
                    "title",
                    "description",
                    "plan_type",
                    "status",
                )
            },
        ),
        (
            "Schedule",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "target_exam_date",
                    "daily_study_hours",
                    "study_days_per_week",
                )
            },
        ),
        ("Progress", {"fields": ("total_tasks", "completed_tasks")}),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at", "generated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "course",
        "session_type",
        "status",
        "scheduled_start",
        "duration_actual",
    ]
    list_filter = ["session_type", "status", "scheduled_start", "created_at"]
    search_fields = ["title", "user__username", "course__title"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "duration_planned",
        "duration_actual",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "course",
                    "study_plan",
                    "title",
                    "description",
                    "session_type",
                    "status",
                )
            },
        ),
        (
            "Schedule",
            {
                "fields": (
                    "scheduled_start",
                    "scheduled_end",
                    "actual_start",
                    "actual_end",
                )
            },
        ),
        ("Content", {"fields": ("topics", "materials")}),
        (
            "Outcome",
            {
                "fields": (
                    "completion_notes",
                    "satisfaction_rating",
                    "productivity_rating",
                    "objectives_completed",
                    "total_objectives",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                    "duration_planned",
                    "duration_actual",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    list_display = [
        "identifier",
        "user",
        "course",
        "progress_type",
        "completion_percentage",
        "mastery_level",
        "last_studied",
    ]
    list_filter = ["progress_type", "mastery_level", "last_studied", "created_at"]
    search_fields = ["identifier", "user__username", "course__title"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "course", "progress_type", "identifier")},
        ),
        (
            "Progress Metrics",
            {"fields": ("completion_percentage", "mastery_level", "confidence_score")},
        ),
        ("Time Tracking", {"fields": ("total_study_time", "last_studied")}),
        ("Performance", {"fields": ("quiz_average", "flashcard_retention")}),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at", "metadata"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(StudyGoal)
class StudyGoalAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "course",
        "goal_type",
        "status",
        "progress_percentage",
        "target_date",
    ]
    list_filter = [
        "goal_type",
        "status",
        "target_date",
        "is_ai_suggested",
        "created_at",
    ]
    search_fields = ["title", "user__username", "course__title"]
    readonly_fields = ["id", "created_at", "updated_at", "progress_percentage"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "course",
                    "study_plan",
                    "title",
                    "description",
                    "goal_type",
                    "status",
                )
            },
        ),
        ("Goal Parameters", {"fields": ("target_value", "current_value", "unit")}),
        ("Timing", {"fields": ("start_date", "target_date", "completed_date")}),
        ("AI Assistance", {"fields": ("is_ai_suggested", "ai_rationale")}),
        ("Progress", {"fields": ("streak_count", "best_streak", "last_progress_date")}),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at", "progress_percentage"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(StudyRecommendation)
class StudyRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "course",
        "recommendation_type",
        "priority",
        "status",
        "created_at",
    ]
    list_filter = [
        "recommendation_type",
        "priority",
        "status",
        "created_at",
        "expires_at",
    ]
    search_fields = ["title", "user__username", "course__title"]
    readonly_fields = ["id", "created_at", "updated_at", "is_expired"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "course", "recommendation_type", "priority", "status")},
        ),
        ("Content", {"fields": ("title", "description", "rationale")}),
        ("Timing", {"fields": ("expires_at", "accepted_at", "dismissed_at")}),
        ("Feedback", {"fields": ("user_feedback", "effectiveness_rating")}),
        (
            "Metadata",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                    "is_expired",
                    "recommendation_data",
                ),
                "classes": ("collapse",),
            },
        ),
    )
