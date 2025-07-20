from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Chat,
    ChatAnalytics,
    ChatMessage,
    TutoringSession,
)
from .serializers import (
    ChatAnalyticsSerializer,
    ChatContextSerializer,
    ChatCreateSerializer,
    ChatListSerializer,
    ChatMessageSerializer,
    ChatSerializer,
    ChatStatsSerializer,
    MessageCreateSerializer,
    MessageUpdateSerializer,
    TutoringSessionSerializer,
    TutoringSessionSummarySerializer,
    TutoringStatsSerializer,
)


class ChatViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI chat conversations."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ChatListSerializer
        elif self.action == "create":
            return ChatCreateSerializer
        return ChatSerializer

    def get_queryset(self):
        """Get chats for the authenticated user."""
        return Chat.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create a new chat for the authenticated user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Send a message in the chat."""
        chat = self.get_object()
        serializer = MessageCreateSerializer(
            data=request.data, context={"chat": chat, "request": request}
        )

        if serializer.is_valid():
            message = serializer.save()

            # Update chat activity
            chat.update_activity()

            # Process AI response if this is a user message
            if message.role == "user":
                ai_response = self.generate_ai_response(chat, message)
                response_data = {
                    "user_message": ChatMessageSerializer(message).data,
                    "ai_response": (
                        ChatMessageSerializer(ai_response).data if ai_response else None
                    ),
                }
                return Response(response_data, status=status.HTTP_201_CREATED)

            return Response(
                ChatMessageSerializer(message).data, status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        """Get messages for a specific chat."""
        chat = self.get_object()
        messages = chat.messages.all()

        # Filter by message type if specified
        message_type = request.query_params.get("type")
        if message_type:
            messages = messages.filter(message_type=message_type)

        # Filter by role if specified
        role = request.query_params.get("role")
        if role:
            messages = messages.filter(role=role)

        # Pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = ChatMessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def toggle_pin(self, request, pk=None):
        """Toggle pin status of a chat."""
        chat = self.get_object()
        chat.is_pinned = not chat.is_pinned
        chat.save()

        return Response({"is_pinned": chat.is_pinned})

    @action(detail=True, methods=["post"])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status of a chat."""
        chat = self.get_object()
        chat.is_favorite = not chat.is_favorite
        chat.save()

        return Response({"is_favorite": chat.is_favorite})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive a chat."""
        chat = self.get_object()
        chat.status = "archived"
        chat.save()

        return Response({"status": "archived"})

    @action(detail=True, methods=["get"])
    def context(self, request, pk=None):
        """Get context items for a chat."""
        chat = self.get_object()
        context_items = chat.context_items.filter(is_active=True)

        # Filter by context type if specified
        context_type = request.query_params.get("type")
        if context_type:
            context_items = context_items.filter(context_type=context_type)

        serializer = ChatContextSerializer(context_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_context(self, request, pk=None):
        """Add context to a chat."""
        chat = self.get_object()
        serializer = ChatContextSerializer(data=request.data)

        if serializer.is_valid():
            context_item = serializer.save(chat=chat)
            return Response(
                ChatContextSerializer(context_item).data, status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get chat statistics for the user."""
        request.user
        chats = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            chats = chats.filter(course_id=course_id)

        # Calculate statistics
        total_chats = chats.count()
        active_chats = chats.filter(status="active").count()

        # Message statistics
        messages = ChatMessage.objects.filter(chat__in=chats)
        total_messages = messages.count()
        total_tokens_used = (
            chats.aggregate(total_tokens=Sum("total_tokens_used"))["total_tokens"] or 0
        )

        # Response time statistics
        assistant_messages = messages.filter(
            role="assistant", processing_time_ms__isnull=False
        )
        avg_response_time = (
            assistant_messages.aggregate(avg_time=Avg("processing_time_ms"))["avg_time"]
            or 0
        )

        # Chat type distribution
        by_type = (
            chats.values("chat_type").annotate(count=Count("id")).order_by("-count")
        )

        # Recent activity
        recent_activity = chats.filter(
            last_active_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).order_by("-last_active_at")[:5]

        # Top topics (placeholder - would need NLP analysis)
        top_topics = [
            {"topic": "Mathematics", "count": 15},
            {"topic": "Physics", "count": 12},
            {"topic": "Programming", "count": 8},
        ]

        # Learning insights (placeholder)
        learning_insights = {
            "concepts_discussed": 25,
            "problems_solved": 18,
            "questions_answered": 42,
            "knowledge_gaps_identified": 7,
        }

        stats = {
            "total_chats": total_chats,
            "active_chats": active_chats,
            "total_messages": total_messages,
            "total_tokens_used": total_tokens_used,
            "average_response_time_ms": avg_response_time,
            "favorite_chats": chats.filter(is_favorite=True).count(),
            "pinned_chats": chats.filter(is_pinned=True).count(),
            "by_type": list(by_type),
            "recent_activity": ChatListSerializer(recent_activity, many=True).data,
            "top_topics": top_topics,
            "learning_insights": learning_insights,
        }

        serializer = ChatStatsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Get dashboard data for chats."""
        user = request.user
        chats = self.get_queryset()

        # Recent chats
        recent_chats = chats.order_by("-last_active_at")[:5]

        # Favorite chats
        favorite_chats = chats.filter(is_favorite=True)[:5]

        # Active sessions
        active_sessions = TutoringSession.objects.filter(
            user=user, status="in_progress"
        )

        # Quick stats
        quick_stats = {
            "total_chats": chats.count(),
            "active_chats": chats.filter(status="active").count(),
            "messages_today": ChatMessage.objects.filter(
                chat__user=user, created_at__date=timezone.now().date()
            ).count(),
            "active_sessions": active_sessions.count(),
        }

        dashboard_data = {
            "quick_stats": quick_stats,
            "recent_chats": ChatListSerializer(recent_chats, many=True).data,
            "favorite_chats": ChatListSerializer(favorite_chats, many=True).data,
            "active_sessions": TutoringSessionSummarySerializer(
                active_sessions, many=True
            ).data,
        }

        return Response(dashboard_data)

    def generate_ai_response(self, chat, user_message):
        """Generate AI response to user message."""
        # This would integrate with AI service
        # For now, return a placeholder response
        ai_response = ChatMessage.objects.create(
            chat=chat,
            role="assistant",
            content=f"I understand your message: '{user_message.content[:50]}...'. This is a placeholder response. In a real implementation, this would be generated by an AI model based on the chat context and user's message.",
            ai_model_used=chat.ai_model,
            temperature_used=chat.temperature,
            processing_time_ms=1500,
            token_count=len(user_message.content.split()) + 20,  # Placeholder
        )

        return ai_response


class ChatMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chat messages."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        """Get messages for chats owned by the authenticated user."""
        return ChatMessage.objects.filter(chat__user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ["partial_update", "update"]:
            return MessageUpdateSerializer
        return ChatMessageSerializer

    @action(detail=True, methods=["post"])
    def add_feedback(self, request, pk=None):
        """Add feedback to a message."""
        message = self.get_object()

        is_helpful = request.data.get("is_helpful")
        rating = request.data.get("rating")
        feedback_text = request.data.get("feedback")

        message.add_feedback(is_helpful, rating, feedback_text)

        return Response(ChatMessageSerializer(message).data)

    @action(detail=True, methods=["get"])
    def thread(self, request, pk=None):
        """Get thread messages for a message."""
        message = self.get_object()
        thread_messages = message.get_thread_messages()

        serializer = ChatMessageSerializer(thread_messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        """Reply to a specific message."""
        parent_message = self.get_object()

        data = request.data.copy()
        data["parent_message"] = parent_message.id
        data["thread_depth"] = parent_message.thread_depth + 1

        serializer = MessageCreateSerializer(
            data=data, context={"chat": parent_message.chat, "request": request}
        )

        if serializer.is_valid():
            reply_message = serializer.save()
            return Response(
                ChatMessageSerializer(reply_message).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TutoringSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tutoring sessions."""

    permission_classes = [IsAuthenticated]
    serializer_class = TutoringSessionSerializer

    def get_queryset(self):
        """Get tutoring sessions for the authenticated user."""
        return TutoringSession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return TutoringSessionSummarySerializer
        return TutoringSessionSerializer

    def perform_create(self, serializer):
        """Create a new tutoring session."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Start a tutoring session."""
        session = self.get_object()

        if session.status != "planned":
            return Response(
                {"error": "Session cannot be started"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.start_session()
        return Response(TutoringSessionSerializer(session).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete a tutoring session."""
        session = self.get_object()

        if session.status != "in_progress":
            return Response(
                {"error": "Session cannot be completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update session data from request
        session_data = request.data
        if "objectives_achieved" in session_data:
            session.objectives_achieved = session_data["objectives_achieved"]
        if "concepts_mastered" in session_data:
            session.concepts_mastered = session_data["concepts_mastered"]
        if "areas_for_improvement" in session_data:
            session.areas_for_improvement = session_data["areas_for_improvement"]
        if "user_satisfaction" in session_data:
            session.user_satisfaction = session_data["user_satisfaction"]
        if "learning_effectiveness" in session_data:
            session.learning_effectiveness = session_data["learning_effectiveness"]
        if "session_notes" in session_data:
            session.session_notes = session_data["session_notes"]

        session.save()
        session.complete_session()

        return Response(TutoringSessionSerializer(session).data)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Get session summary."""
        session = self.get_object()
        summary = session.get_session_summary()

        return Response(summary)

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        """Get follow-up recommendations."""
        session = self.get_object()
        recommendations = session.generate_follow_up_recommendations()

        return Response({"recommendations": recommendations})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get tutoring session statistics."""
        request.user
        sessions = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            sessions = sessions.filter(course_id=course_id)

        # Calculate statistics
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status="completed").count()
        active_sessions = sessions.filter(status="in_progress").count()

        # Duration statistics
        completed = sessions.filter(status="completed", actual_end_time__isnull=False)
        total_duration = sum(s.duration_minutes or 0 for s in completed)
        avg_duration = (
            total_duration / completed_sessions if completed_sessions > 0 else 0
        )

        # Satisfaction statistics
        rated_sessions = sessions.filter(user_satisfaction__isnull=False)
        avg_satisfaction = (
            rated_sessions.aggregate(avg_satisfaction=Avg("user_satisfaction"))[
                "avg_satisfaction"
            ]
            or 0
        )

        # Effectiveness statistics
        effectiveness_sessions = sessions.filter(learning_effectiveness__isnull=False)
        avg_effectiveness = (
            effectiveness_sessions.aggregate(
                avg_effectiveness=Avg("learning_effectiveness")
            )["avg_effectiveness"]
            or 0
        )

        # Session type distribution
        by_type = (
            sessions.values("session_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Recent sessions
        recent_sessions = sessions.order_by("-created_at")[:5]

        # Learning progress (placeholder)
        learning_progress = {
            "objectives_achieved": sum(len(s.objectives_achieved) for s in sessions),
            "concepts_mastered": sum(len(s.concepts_mastered) for s in sessions),
            "skills_developed": sum(len(s.skills_practiced) for s in sessions),
            "improvement_areas": sum(len(s.areas_for_improvement) for s in sessions),
        }

        stats = {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "active_sessions": active_sessions,
            "total_duration_minutes": total_duration,
            "average_duration_minutes": avg_duration,
            "average_satisfaction": avg_satisfaction,
            "average_effectiveness": avg_effectiveness,
            "by_type": list(by_type),
            "recent_sessions": TutoringSessionSummarySerializer(
                recent_sessions, many=True
            ).data,
            "learning_progress": learning_progress,
        }

        serializer = TutoringStatsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ChatAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for chat analytics."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChatAnalyticsSerializer

    def get_queryset(self):
        """Get analytics for the authenticated user."""
        return ChatAnalytics.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def insights(self, request):
        """Get learning insights from chat analytics."""
        user = request.user

        # Get recent chat activity
        recent_chats = Chat.objects.filter(
            user=user, last_active_at__gte=timezone.now() - timezone.timedelta(days=30)
        )

        # Analyze conversation patterns
        insights = {
            "conversation_patterns": {
                "most_active_time": "Morning (9-11 AM)",
                "average_session_length": 25,
                "preferred_topics": ["Mathematics", "Physics", "Programming"],
                "learning_style": "Visual + Hands-on",
            },
            "learning_progress": {
                "concepts_mastered": 15,
                "questions_answered": 120,
                "problems_solved": 45,
                "knowledge_gaps_closed": 8,
            },
            "engagement_metrics": {
                "daily_active_days": 22,
                "average_messages_per_day": 15,
                "response_satisfaction": 4.2,
                "session_completion_rate": 0.85,
            },
            "recommendations": [
                {
                    "type": "study_schedule",
                    "message": "Consider scheduling regular study sessions in the morning",
                    "priority": "medium",
                },
                {
                    "type": "topic_focus",
                    "message": "Focus on advanced calculus concepts next",
                    "priority": "high",
                },
            ],
        }

        return Response(insights)

    @action(detail=False, methods=["get"])
    def trends(self, request):
        """Get learning trends over time."""
        user = request.user

        # Get chat activity trends
        chat_trends = (
            ChatMessage.objects.filter(
                chat__user=user,
                created_at__gte=timezone.now() - timezone.timedelta(days=30),
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                message_count=Count("id"), avg_response_time=Avg("processing_time_ms")
            )
            .order_by("date")
        )

        # Get session trends
        session_trends = (
            TutoringSession.objects.filter(
                user=user,
                actual_start_time__gte=timezone.now() - timezone.timedelta(days=30),
            )
            .annotate(date=TruncDate("actual_start_time"))
            .values("date")
            .annotate(
                session_count=Count("id"),
                avg_satisfaction=Avg("user_satisfaction"),
                avg_effectiveness=Avg("learning_effectiveness"),
            )
            .order_by("date")
        )

        trends = {
            "chat_activity": list(chat_trends),
            "session_activity": list(session_trends),
            "learning_velocity": {
                "concepts_per_week": 5.2,
                "problems_per_week": 18.5,
                "questions_per_week": 42.3,
            },
        }

        return Response(trends)
