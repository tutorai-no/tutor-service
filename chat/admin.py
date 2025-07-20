from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Chat,
    ChatAnalytics,
    ChatContext,
    ChatMessage,
    TutoringSession,
)


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "chat_type",
        "status",
        "course",
        "message_count",
        "is_pinned",
        "last_active_at",
        "created_at",
    ]
    list_filter = [
        "chat_type",
        "status",
        "is_pinned",
        "is_favorite",
        "use_course_context",
        "use_document_context",
        "created_at",
    ]
    search_fields = ["title", "user__username", "course__name"]
    readonly_fields = [
        "id",
        "message_count",
        "total_tokens_used",
        "average_response_time_ms",
        "last_active_at",
        "context_summary",
        "created_at",
        "updated_at",
    ]

    def context_summary(self, obj):
        """Display context summary."""
        summary = obj.context_summary
        return format_html(
            "<strong>Course:</strong> {}<br>"
            "<strong>Section:</strong> {}<br>"
            "<strong>Messages:</strong> {}<br>"
            "<strong>Documents:</strong> {}<br>"
            "<strong>Assessments:</strong> {}",
            summary.get("course", "None"),
            summary.get("section", "None"),
            summary.get("message_count", 0),
            "Yes" if summary.get("has_documents") else "No",
            "Yes" if summary.get("has_assessments") else "No",
        )

    context_summary.short_description = "Context Summary"

    fieldsets = (
        ("Basic Information", {"fields": ("user", "title", "chat_type", "status")}),
        ("Context", {"fields": ("course", "section", "current_session")}),
        (
            "AI Configuration",
            {
                "fields": (
                    "system_prompt",
                    "ai_model",
                    "temperature",
                    "max_tokens",
                    "context_window_messages",
                )
            },
        ),
        (
            "Context Settings",
            {
                "fields": (
                    "use_course_context",
                    "use_document_context",
                    "use_assessment_context",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "message_count",
                    "total_tokens_used",
                    "average_response_time_ms",
                )
            },
        ),
        (
            "User Preferences",
            {"fields": ("is_pinned", "is_favorite", "last_active_at")},
        ),
        ("Context Summary", {"fields": ("context_summary",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        "message_preview",
        "chat",
        "role",
        "message_type",
        "is_helpful",
        "user_rating",
        "created_at",
    ]
    list_filter = [
        "role",
        "message_type",
        "is_helpful",
        "user_rating",
        "is_context_relevant",
        "is_deleted",
        "created_at",
    ]
    search_fields = ["content", "chat__title", "user_feedback"]
    readonly_fields = [
        "id",
        "token_count",
        "processing_time_ms",
        "ai_model_used",
        "temperature_used",
        "prompt_tokens",
        "completion_tokens",
        "context_used",
        "thread_depth",
        "created_at",
        "updated_at",
    ]

    def message_preview(self, obj):
        """Display message preview."""
        preview = obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
        if obj.is_deleted:
            preview = f"[DELETED] {preview}"
        return preview

    message_preview.short_description = "Message Preview"

    fieldsets = (
        (
            "Message Information",
            {"fields": ("chat", "role", "message_type", "content")},
        ),
        ("Threading", {"fields": ("parent_message", "thread_depth")}),
        (
            "AI Information",
            {
                "fields": (
                    "ai_model_used",
                    "temperature_used",
                    "token_count",
                    "prompt_tokens",
                    "completion_tokens",
                    "processing_time_ms",
                )
            },
        ),
        (
            "Context & References",
            {
                "fields": (
                    "context_used",
                    "referenced_documents",
                    "referenced_assessments",
                )
            },
        ),
        ("User Feedback", {"fields": ("is_helpful", "user_rating", "user_feedback")}),
        ("Context Settings", {"fields": ("is_context_relevant", "context_weight")}),
        ("Status", {"fields": ("is_edited", "is_deleted", "edit_history")}),
        ("Attachments", {"fields": ("attachments",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ChatContext)
class ChatContextAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "chat",
        "context_type",
        "relevance_score",
        "is_active",
        "usage_count",
        "last_used_at",
    ]
    list_filter = ["context_type", "is_active", "source_type", "created_at"]
    search_fields = ["title", "description", "content", "chat__title"]
    readonly_fields = [
        "id",
        "content_hash",
        "usage_count",
        "last_used_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Context Information",
            {"fields": ("chat", "context_type", "title", "description")},
        ),
        ("Content", {"fields": ("content", "content_hash")}),
        ("Relevance", {"fields": ("relevance_score", "is_active")}),
        (
            "Source Information",
            {"fields": ("source_type", "source_id", "source_metadata")},
        ),
        ("Usage Statistics", {"fields": ("usage_count", "last_used_at")}),
        ("Relationships", {"fields": ("related_documents", "related_assessments")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(TutoringSession)
class TutoringSessionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "session_type",
        "status",
        "course",
        "duration_minutes",
        "user_satisfaction",
        "created_at",
    ]
    list_filter = [
        "session_type",
        "status",
        "difficulty_level",
        "preferred_learning_style",
        "user_satisfaction",
        "learning_effectiveness",
        "created_at",
    ]
    search_fields = ["title", "description", "user__username", "course__name"]
    readonly_fields = [
        "id",
        "duration_minutes",
        "is_active",
        "total_interactions",
        "total_tokens_used",
        "average_response_time_ms",
        "created_at",
        "updated_at",
    ]

    actions = ["start_sessions", "complete_sessions"]

    def start_sessions(self, request, queryset):
        """Start selected sessions."""
        updated = 0
        for session in queryset.filter(status="planned"):
            session.start_session()
            updated += 1

        self.message_user(
            request, f"Successfully started {updated} tutoring session(s)."
        )

    start_sessions.short_description = "Start selected sessions"

    def complete_sessions(self, request, queryset):
        """Complete selected sessions."""
        updated = 0
        for session in queryset.filter(status="in_progress"):
            session.complete_session()
            updated += 1

        self.message_user(
            request, f"Successfully completed {updated} tutoring session(s)."
        )

    complete_sessions.short_description = "Complete selected sessions"

    fieldsets = (
        (
            "Session Information",
            {"fields": ("user", "title", "description", "session_type", "status")},
        ),
        ("Context", {"fields": ("course", "section")}),
        (
            "Learning Objectives",
            {"fields": ("learning_objectives", "topics_covered", "skills_practiced")},
        ),
        (
            "Configuration",
            {
                "fields": (
                    "preferred_learning_style",
                    "difficulty_level",
                    "tutor_persona",
                    "teaching_approach",
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "planned_start_time",
                    "planned_duration_minutes",
                    "actual_start_time",
                    "actual_end_time",
                    "duration_minutes",
                )
            },
        ),
        (
            "Outcomes",
            {
                "fields": (
                    "objectives_achieved",
                    "concepts_mastered",
                    "areas_for_improvement",
                )
            },
        ),
        (
            "Assessment",
            {
                "fields": (
                    "user_satisfaction",
                    "learning_effectiveness",
                    "session_notes",
                )
            },
        ),
        (
            "Performance Metrics",
            {
                "fields": (
                    "total_interactions",
                    "total_tokens_used",
                    "average_response_time_ms",
                )
            },
        ),
        (
            "Follow-up",
            {
                "fields": (
                    "next_session_topics",
                    "recommended_resources",
                    "homework_assignments",
                )
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ChatAnalytics)
class ChatAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "analytics_type",
        "period_start",
        "period_end",
        "total_chats",
        "total_messages",
        "active_chat_days",
    ]
    list_filter = ["analytics_type", "period_start", "period_end", "created_at"]
    search_fields = ["user__username"]
    readonly_fields = [
        "id",
        "total_chats",
        "total_messages",
        "total_tokens_used",
        "average_response_time_ms",
        "active_chat_days",
        "average_messages_per_chat",
        "average_session_duration_minutes",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Analytics Information",
            {"fields": ("user", "analytics_type", "period_start", "period_end")},
        ),
        (
            "Basic Metrics",
            {
                "fields": (
                    "total_chats",
                    "total_messages",
                    "total_tokens_used",
                    "average_response_time_ms",
                )
            },
        ),
        (
            "Engagement Metrics",
            {
                "fields": (
                    "active_chat_days",
                    "average_messages_per_chat",
                    "average_session_duration_minutes",
                )
            },
        ),
        (
            "Content Analysis",
            {"fields": ("top_topics", "most_helpful_responses", "improvement_areas")},
        ),
        (
            "Learning Insights",
            {"fields": ("concepts_learned", "skills_developed", "knowledge_gaps")},
        ),
        ("Detailed Metrics", {"fields": ("metrics_data",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
