from django.utils import timezone
from rest_framework import serializers

from .models import (
    Chat,
    ChatAnalytics,
    ChatContext,
    ChatMessage,
    TutoringSession,
)


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "role",
            "message_type",
            "content",
            "token_count",
            "processing_time_ms",
            "ai_model_used",
            "temperature_used",
            "prompt_tokens",
            "completion_tokens",
            "context_used",
            "referenced_documents",
            "referenced_assessments",
            "parent_message",
            "thread_depth",
            "is_helpful",
            "user_rating",
            "user_feedback",
            "is_context_relevant",
            "context_weight",
            "is_edited",
            "is_deleted",
            "edit_history",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "token_count",
            "processing_time_ms",
            "ai_model_used",
            "temperature_used",
            "prompt_tokens",
            "completion_tokens",
            "context_used",
            "thread_depth",
            "is_edited",
            "edit_history",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Create a new chat message."""
        # Handle referenced documents and assessments
        referenced_documents = validated_data.pop("referenced_documents", [])
        referenced_assessments = validated_data.pop("referenced_assessments", [])

        message = super().create(validated_data)

        # Set many-to-many relationships
        if referenced_documents:
            message.referenced_documents.set(referenced_documents)
        if referenced_assessments:
            message.referenced_assessments.set(referenced_assessments)

        return message


class ChatContextSerializer(serializers.ModelSerializer):
    """Serializer for chat context items."""

    class Meta:
        model = ChatContext
        fields = [
            "id",
            "context_type",
            "title",
            "description",
            "content",
            "content_hash",
            "relevance_score",
            "is_active",
            "source_type",
            "source_id",
            "source_metadata",
            "usage_count",
            "last_used_at",
            "related_documents",
            "related_assessments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "content_hash",
            "usage_count",
            "last_used_at",
            "created_at",
            "updated_at",
        ]


class ChatSerializer(serializers.ModelSerializer):
    """Serializer for chat conversations."""

    messages = ChatMessageSerializer(many=True, read_only=True)
    context_items = ChatContextSerializer(many=True, read_only=True)
    context_summary = serializers.ReadOnlyField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "title",
            "chat_type",
            "status",
            "course",
            "section",
            "system_prompt",
            "ai_model",
            "temperature",
            "max_tokens",
            "context_window_messages",
            "use_course_context",
            "use_document_context",
            "use_assessment_context",
            "message_count",
            "total_tokens_used",
            "average_response_time_ms",
            "is_pinned",
            "is_favorite",
            "last_active_at",
            "current_session",
            "messages",
            "context_items",
            "context_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "message_count",
            "total_tokens_used",
            "average_response_time_ms",
            "last_active_at",
            "messages",
            "context_items",
            "context_summary",
            "created_at",
            "updated_at",
        ]


class TutoringSessionSerializer(serializers.ModelSerializer):
    """Serializer for tutoring sessions."""

    duration_minutes = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = TutoringSession
        fields = [
            "id",
            "title",
            "description",
            "session_type",
            "status",
            "course",
            "section",
            "learning_objectives",
            "topics_covered",
            "skills_practiced",
            "preferred_learning_style",
            "difficulty_level",
            "tutor_persona",
            "teaching_approach",
            "planned_start_time",
            "planned_duration_minutes",
            "actual_start_time",
            "actual_end_time",
            "duration_minutes",
            "objectives_achieved",
            "concepts_mastered",
            "areas_for_improvement",
            "user_satisfaction",
            "learning_effectiveness",
            "session_notes",
            "total_interactions",
            "total_tokens_used",
            "average_response_time_ms",
            "next_session_topics",
            "recommended_resources",
            "homework_assignments",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "actual_start_time",
            "actual_end_time",
            "duration_minutes",
            "total_interactions",
            "total_tokens_used",
            "average_response_time_ms",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ChatAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for chat analytics."""

    class Meta:
        model = ChatAnalytics
        fields = [
            "id",
            "analytics_type",
            "period_start",
            "period_end",
            "total_chats",
            "total_messages",
            "total_tokens_used",
            "average_response_time_ms",
            "active_chat_days",
            "average_messages_per_chat",
            "average_session_duration_minutes",
            "top_topics",
            "most_helpful_responses",
            "improvement_areas",
            "concepts_learned",
            "skills_developed",
            "knowledge_gaps",
            "metrics_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
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


# Specialized serializers for different use cases


class ChatListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for chat lists."""

    context_summary = serializers.ReadOnlyField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "title",
            "chat_type",
            "status",
            "course",
            "section",
            "message_count",
            "is_pinned",
            "is_favorite",
            "last_active_at",
            "context_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "message_count",
            "last_active_at",
            "context_summary",
            "created_at",
            "updated_at",
        ]


class ChatCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new chats."""

    class Meta:
        model = Chat
        fields = [
            "id",
            "title",
            "chat_type",
            "course",
            "section",
            "system_prompt",
            "ai_model",
            "temperature",
            "max_tokens",
            "context_window_messages",
            "use_course_context",
            "use_document_context",
            "use_assessment_context",
        ]
        read_only_fields = ["id"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make course field optional since it's nullable in the model
        self.fields['course'].required = False
        self.fields['section'].required = False

    def create(self, validated_data):
        """Create a new chat with user context."""
        # User is already passed from perform_create
        chat = Chat.objects.create(**validated_data)
        return chat


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages."""

    class Meta:
        model = ChatMessage
        fields = [
            "role",
            "message_type",
            "content",
            "parent_message",
            "referenced_documents",
            "referenced_assessments",
            "attachments",
        ]

    def create(self, validated_data):
        """Create a new message and update chat activity."""
        chat = self.context["chat"]

        # Handle referenced documents and assessments
        referenced_documents = validated_data.pop("referenced_documents", [])
        referenced_assessments = validated_data.pop("referenced_assessments", [])

        message = ChatMessage.objects.create(chat=chat, **validated_data)

        # Set many-to-many relationships
        if referenced_documents:
            message.referenced_documents.set(referenced_documents)
        if referenced_assessments:
            message.referenced_assessments.set(referenced_assessments)

        return message


class MessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating messages (feedback, ratings)."""

    class Meta:
        model = ChatMessage
        fields = ["is_helpful", "user_rating", "user_feedback"]

    def update(self, instance, validated_data):
        """Update message and track edit history."""
        # Store original values in edit history
        if not instance.edit_history:
            instance.edit_history = []

        edit_entry = {"timestamp": timezone.now().isoformat(), "changes": {}}

        for field, new_value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != new_value:
                edit_entry["changes"][field] = {"old": old_value, "new": new_value}

        if edit_entry["changes"]:
            instance.edit_history.append(edit_entry)
            instance.is_edited = True

        return super().update(instance, validated_data)


class TutoringSessionSummarySerializer(serializers.ModelSerializer):
    """Serializer for tutoring session summaries."""

    duration_minutes = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    session_summary = serializers.SerializerMethodField()

    class Meta:
        model = TutoringSession
        fields = [
            "id",
            "title",
            "session_type",
            "status",
            "course",
            "planned_start_time",
            "duration_minutes",
            "user_satisfaction",
            "learning_effectiveness",
            "is_active",
            "session_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "duration_minutes",
            "is_active",
            "session_summary",
            "created_at",
            "updated_at",
        ]

    def get_session_summary(self, obj):
        """Get session summary."""
        return obj.get_session_summary()


class ChatStatsSerializer(serializers.Serializer):
    """Serializer for chat statistics."""

    total_chats = serializers.IntegerField()
    active_chats = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    total_tokens_used = serializers.IntegerField()
    average_response_time_ms = serializers.FloatField()
    favorite_chats = serializers.IntegerField()
    pinned_chats = serializers.IntegerField()
    by_type = serializers.ListField()
    recent_activity = serializers.ListField()
    top_topics = serializers.ListField()
    learning_insights = serializers.DictField()


class TutoringStatsSerializer(serializers.Serializer):
    """Serializer for tutoring statistics."""

    total_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    total_duration_minutes = serializers.IntegerField()
    average_duration_minutes = serializers.FloatField()
    average_satisfaction = serializers.FloatField()
    average_effectiveness = serializers.FloatField()
    by_type = serializers.ListField()
    recent_sessions = serializers.ListField()
    learning_progress = serializers.DictField()


class ConversationAnalysisSerializer(serializers.Serializer):
    """Serializer for conversation analysis."""

    conversation_id = serializers.UUIDField()
    analysis_type = serializers.CharField()
    insights = serializers.DictField()
    recommendations = serializers.ListField()
    learning_outcomes = serializers.ListField()
    areas_for_improvement = serializers.ListField()
    confidence_score = serializers.FloatField()
    generated_at = serializers.DateTimeField()


class ContextRecommendationSerializer(serializers.Serializer):
    """Serializer for context recommendations."""

    context_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    relevance_score = serializers.FloatField()
    source_type = serializers.CharField()
    source_id = serializers.UUIDField()
    recommended_action = serializers.CharField()
    reasoning = serializers.CharField()


class LearningPathSerializer(serializers.Serializer):
    """Serializer for learning path recommendations."""

    path_id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    difficulty_level = serializers.CharField()
    estimated_duration_hours = serializers.IntegerField()
    prerequisites = serializers.ListField()
    learning_objectives = serializers.ListField()
    recommended_resources = serializers.ListField()
    assessment_checkpoints = serializers.ListField()
    confidence_score = serializers.FloatField()
