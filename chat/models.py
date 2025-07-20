import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Chat(models.Model):
    """AI chat conversations with context management."""

    CHAT_TYPES = [
        ("general", "General Chat"),
        ("course_specific", "Course-Specific Chat"),
        ("document_based", "Document-Based Chat"),
        ("assessment_help", "Assessment Help"),
        ("study_planning", "Study Planning"),
        ("concept_explanation", "Concept Explanation"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("archived", "Archived"),
        ("deleted", "Deleted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_chats"
    )

    # Context relationships
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_chats",
        help_text="Course context for this chat",
    )
    section = models.ForeignKey(
        "courses.CourseSection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_chats",
        help_text="Section context for this chat",
    )

    # Chat metadata
    title = models.CharField(max_length=255, help_text="Chat title or topic")
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES, default="general")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Chat configuration
    system_prompt = models.TextField(
        blank=True, null=True, help_text="System prompt for AI behavior"
    )
    ai_model = models.CharField(
        max_length=100, default="gpt-4", help_text="AI model used for this chat"
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        help_text="AI temperature setting",
    )
    max_tokens = models.PositiveIntegerField(
        default=1000, help_text="Maximum tokens per response"
    )

    # Context and memory
    context_window_messages = models.PositiveIntegerField(
        default=10, help_text="Number of messages to keep in context"
    )
    use_course_context = models.BooleanField(
        default=True, help_text="Include course materials in context"
    )
    use_document_context = models.BooleanField(
        default=True, help_text="Include document content in context"
    )
    use_assessment_context = models.BooleanField(
        default=True, help_text="Include assessment history in context"
    )

    # Chat statistics
    message_count = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    average_response_time_ms = models.PositiveIntegerField(null=True, blank=True)

    # User engagement
    is_pinned = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    last_active_at = models.DateTimeField(null=True, blank=True)

    # Tutoring session tracking
    current_session = models.ForeignKey(
        "TutoringSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_chats",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_chats"
        ordering = ["-last_active_at", "-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["course", "status"]),
            models.Index(fields=["chat_type"]),
            models.Index(fields=["is_pinned", "is_favorite"]),
            models.Index(fields=["last_active_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Chat: {self.title} ({self.user.username})"

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_active_at = timezone.now()
        self.save(update_fields=["last_active_at"])

    def get_context_messages(self):
        """Get messages within context window."""
        return self.messages.filter(is_context_relevant=True).order_by("-created_at")[
            : self.context_window_messages
        ]

    def calculate_avg_response_time(self):
        """Calculate average response time for assistant messages."""
        assistant_messages = self.messages.filter(
            role="assistant", processing_time_ms__isnull=False
        )

        if assistant_messages.exists():
            avg_time = assistant_messages.aggregate(
                avg_time=models.Avg("processing_time_ms")
            )["avg_time"]
            self.average_response_time_ms = int(avg_time) if avg_time else None
            self.save(update_fields=["average_response_time_ms"])

    @property
    def context_summary(self):
        """Get a summary of the chat context."""
        context = {
            "course": self.course.name if self.course else None,
            "section": self.section.name if self.section else None,
            "type": self.chat_type,
            "message_count": self.message_count,
            "has_documents": self.context_documents.exists(),
            "has_assessments": self.context_assessments.exists(),
        }
        return context


class ChatMessage(models.Model):
    """Individual messages in AI chat conversations."""

    MESSAGE_ROLES = [
        ("user", "User"),
        ("assistant", "AI Assistant"),
        ("system", "System"),
        ("context", "Context Information"),
    ]

    MESSAGE_TYPES = [
        ("text", "Text Message"),
        ("image", "Image Message"),
        ("file", "File Message"),
        ("code", "Code Message"),
        ("math", "Math/Formula Message"),
        ("summary", "Summary Message"),
        ("feedback", "Feedback Message"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")

    # Message content
    role = models.CharField(max_length=10, choices=MESSAGE_ROLES)
    message_type = models.CharField(
        max_length=20, choices=MESSAGE_TYPES, default="text"
    )
    content = models.TextField()

    # Message metadata
    token_count = models.PositiveIntegerField(null=True, blank=True)
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)

    # AI model information (for assistant messages)
    ai_model_used = models.CharField(max_length=100, blank=True, null=True)
    temperature_used = models.FloatField(null=True, blank=True)
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)

    # Context and references
    context_used = models.TextField(
        blank=True, null=True, help_text="Context information used for AI response"
    )
    referenced_documents = models.ManyToManyField(
        "courses.Document",
        blank=True,
        related_name="chat_message_references",
        help_text="Documents referenced in this message",
    )
    referenced_assessments = models.ManyToManyField(
        "assessments.Flashcard",
        blank=True,
        related_name="chat_message_references",
        help_text="Assessments referenced in this message",
    )

    # Message threading
    parent_message = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    thread_depth = models.PositiveIntegerField(default=0)

    # User interaction
    is_helpful = models.BooleanField(null=True, blank=True)
    user_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User rating of AI response (1-5)",
    )
    user_feedback = models.TextField(blank=True, null=True)

    # Context relevance
    is_context_relevant = models.BooleanField(
        default=True, help_text="Whether this message should be included in context"
    )
    context_weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Weight of this message in context (0.0-1.0)",
    )

    # Message status
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    edit_history = models.JSONField(default=list, blank=True)

    # Attachments and media
    attachments = models.JSONField(default=list, help_text="List of file attachments")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_chat_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["chat", "created_at"]),
            models.Index(fields=["role", "created_at"]),
            models.Index(fields=["is_helpful"]),
            models.Index(fields=["user_rating"]),
            models.Index(fields=["is_context_relevant"]),
            models.Index(fields=["thread_depth"]),
        ]

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."

    def save(self, *args, **kwargs):
        """Override save to update chat statistics."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update chat message count
            self.chat.message_count = self.chat.messages.count()
            self.chat.save(update_fields=["message_count"])

            # Update chat activity
            self.chat.update_activity()

    def add_feedback(self, is_helpful=None, rating=None, feedback_text=None):
        """Add user feedback to this message."""
        if is_helpful is not None:
            self.is_helpful = is_helpful
        if rating is not None:
            self.user_rating = rating
        if feedback_text is not None:
            self.user_feedback = feedback_text
        self.save()

    def get_thread_messages(self):
        """Get all messages in this thread."""
        if self.parent_message:
            return self.parent_message.get_thread_messages()
        return ChatMessage.objects.filter(
            models.Q(pk=self.pk) | models.Q(parent_message=self)
        ).order_by("created_at")


class ChatContext(models.Model):
    """Context information for AI chat conversations."""

    CONTEXT_TYPES = [
        ("course_material", "Course Material"),
        ("document_content", "Document Content"),
        ("assessment_history", "Assessment History"),
        ("user_progress", "User Progress"),
        ("conversation_history", "Conversation History"),
        ("external_knowledge", "External Knowledge"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="context_items"
    )

    # Context metadata
    context_type = models.CharField(max_length=20, choices=CONTEXT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Context content
    content = models.TextField()
    content_hash = models.CharField(
        max_length=64, help_text="Hash of content for deduplication"
    )

    # Context relevance
    relevance_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Relevance score for this context item",
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this context is currently active"
    )

    # Source information
    source_type = models.CharField(max_length=50, blank=True, null=True)
    source_id = models.UUIDField(null=True, blank=True)
    source_metadata = models.JSONField(default=dict, blank=True)

    # Usage statistics
    usage_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Context relationships
    related_documents = models.ManyToManyField(
        "courses.Document", blank=True, related_name="chat_contexts"
    )
    related_assessments = models.ManyToManyField(
        "assessments.Flashcard", blank=True, related_name="chat_contexts"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_chat_contexts"
        ordering = ["-relevance_score", "-updated_at"]
        indexes = [
            models.Index(fields=["chat", "context_type"]),
            models.Index(fields=["relevance_score"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["content_hash"]),
            models.Index(fields=["last_used_at"]),
        ]
        unique_together = ["chat", "content_hash"]

    def __str__(self):
        return f"Context: {self.title} ({self.context_type})"

    def mark_used(self):
        """Mark this context as used."""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["usage_count", "last_used_at"])

    def calculate_relevance(self, query_text):
        """Calculate relevance score for a given query."""
        # This would implement semantic similarity calculation
        # For now, return a placeholder
        return 0.5


class TutoringSession(models.Model):
    """AI tutoring sessions with learning objectives and outcomes."""

    SESSION_TYPES = [
        ("concept_explanation", "Concept Explanation"),
        ("problem_solving", "Problem Solving"),
        ("exam_preparation", "Exam Preparation"),
        ("homework_help", "Homework Help"),
        ("study_planning", "Study Planning"),
        ("skill_practice", "Skill Practice"),
        ("review_session", "Review Session"),
    ]

    SESSION_STATUS = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

    LEARNING_STYLES = [
        ("visual", "Visual"),
        ("auditory", "Auditory"),
        ("kinesthetic", "Kinesthetic"),
        ("reading_writing", "Reading/Writing"),
        ("mixed", "Mixed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutoring_sessions",
    )

    # Session context
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tutoring_sessions",
    )
    section = models.ForeignKey(
        "courses.CourseSection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tutoring_sessions",
    )

    # Session metadata
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default="planned")

    # Learning objectives
    learning_objectives = models.JSONField(
        default=list, help_text="List of learning objectives for this session"
    )
    topics_covered = models.JSONField(
        default=list, help_text="Topics covered in this session"
    )
    skills_practiced = models.JSONField(
        default=list, help_text="Skills practiced in this session"
    )

    # Session configuration
    preferred_learning_style = models.CharField(
        max_length=20, choices=LEARNING_STYLES, default="mixed"
    )
    difficulty_level = models.CharField(
        max_length=15,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="intermediate",
    )

    # AI tutor configuration
    tutor_persona = models.CharField(
        max_length=100, default="helpful_teacher", help_text="AI tutor persona/style"
    )
    teaching_approach = models.CharField(
        max_length=100,
        default="socratic",
        help_text="Teaching approach (socratic, direct, guided_discovery, etc.)",
    )

    # Session timing
    planned_start_time = models.DateTimeField(null=True, blank=True)
    planned_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)

    # Session outcomes
    objectives_achieved = models.JSONField(
        default=list, help_text="Learning objectives that were achieved"
    )
    concepts_mastered = models.JSONField(
        default=list, help_text="Concepts that were mastered"
    )
    areas_for_improvement = models.JSONField(
        default=list, help_text="Areas identified for improvement"
    )

    # Session assessment
    user_satisfaction = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User satisfaction rating (1-5)",
    )
    learning_effectiveness = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Learning effectiveness rating (1-5)",
    )
    session_notes = models.TextField(blank=True, null=True)

    # Performance metrics
    total_interactions = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    average_response_time_ms = models.PositiveIntegerField(null=True, blank=True)

    # Follow-up planning
    next_session_topics = models.JSONField(
        default=list, help_text="Suggested topics for next session"
    )
    recommended_resources = models.JSONField(
        default=list, help_text="Recommended study resources"
    )
    homework_assignments = models.JSONField(
        default=list, help_text="Homework or practice assignments"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_tutoring_sessions"
        ordering = ["-planned_start_time", "-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["course", "status"]),
            models.Index(fields=["session_type"]),
            models.Index(fields=["planned_start_time"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Session: {self.title} ({self.user.username})"

    def start_session(self):
        """Start the tutoring session."""
        if self.status == "planned":
            self.status = "in_progress"
            self.actual_start_time = timezone.now()
            self.save(update_fields=["status", "actual_start_time"])

    def complete_session(self):
        """Complete the tutoring session."""
        if self.status == "in_progress":
            self.status = "completed"
            self.actual_end_time = timezone.now()
            self.save(update_fields=["status", "actual_end_time"])

    @property
    def duration_minutes(self):
        """Calculate actual session duration."""
        if self.actual_start_time and self.actual_end_time:
            duration = self.actual_end_time - self.actual_start_time
            return int(duration.total_seconds() / 60)
        return None

    @property
    def is_active(self):
        """Check if session is currently active."""
        return self.status == "in_progress"

    def get_session_summary(self):
        """Get a summary of the session."""
        summary = {
            "title": self.title,
            "type": self.session_type,
            "status": self.status,
            "duration_minutes": self.duration_minutes,
            "objectives_achieved": len(self.objectives_achieved),
            "total_objectives": len(self.learning_objectives),
            "concepts_mastered": len(self.concepts_mastered),
            "satisfaction": self.user_satisfaction,
            "effectiveness": self.learning_effectiveness,
            "total_interactions": self.total_interactions,
        }
        return summary

    def generate_follow_up_recommendations(self):
        """Generate recommendations for follow-up sessions."""
        recommendations = []

        # Check unmet objectives
        achieved_set = set(self.objectives_achieved)
        all_objectives = set(self.learning_objectives)
        unmet_objectives = all_objectives - achieved_set

        if unmet_objectives:
            recommendations.append(
                {
                    "type": "review_objectives",
                    "message": f"Review {len(unmet_objectives)} unmet learning objectives",
                    "priority": "high",
                    "objectives": list(unmet_objectives),
                }
            )

        # Check areas for improvement
        if self.areas_for_improvement:
            recommendations.append(
                {
                    "type": "improvement_focus",
                    "message": f"Focus on {len(self.areas_for_improvement)} areas for improvement",
                    "priority": "medium",
                    "areas": self.areas_for_improvement,
                }
            )

        # Check satisfaction and effectiveness
        if self.user_satisfaction and self.user_satisfaction < 3:
            recommendations.append(
                {
                    "type": "adjust_approach",
                    "message": "Consider adjusting teaching approach based on satisfaction feedback",
                    "priority": "high",
                }
            )

        return recommendations


class ChatAnalytics(models.Model):
    """Analytics and insights for chat conversations."""

    ANALYTICS_TYPES = [
        ("daily_summary", "Daily Summary"),
        ("weekly_summary", "Weekly Summary"),
        ("monthly_summary", "Monthly Summary"),
        ("topic_analysis", "Topic Analysis"),
        ("learning_progress", "Learning Progress"),
        ("engagement_metrics", "Engagement Metrics"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_analytics",
    )

    # Analytics metadata
    analytics_type = models.CharField(max_length=20, choices=ANALYTICS_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    # Metrics
    total_chats = models.PositiveIntegerField(default=0)
    total_messages = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    average_response_time_ms = models.PositiveIntegerField(null=True, blank=True)

    # Engagement metrics
    active_chat_days = models.PositiveIntegerField(default=0)
    average_messages_per_chat = models.FloatField(default=0.0)
    average_session_duration_minutes = models.FloatField(default=0.0)

    # Content analysis
    top_topics = models.JSONField(default=list)
    most_helpful_responses = models.JSONField(default=list)
    improvement_areas = models.JSONField(default=list)

    # Learning insights
    concepts_learned = models.JSONField(default=list)
    skills_developed = models.JSONField(default=list)
    knowledge_gaps = models.JSONField(default=list)

    # Detailed metrics
    metrics_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_chat_analytics"
        ordering = ["-period_end"]
        indexes = [
            models.Index(fields=["user", "analytics_type"]),
            models.Index(fields=["period_start", "period_end"]),
        ]
        unique_together = ["user", "analytics_type", "period_start", "period_end"]

    def __str__(self):
        return (
            f"Analytics: {self.get_analytics_type_display()} for {self.user.username}"
        )
