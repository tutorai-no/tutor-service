import logging

from django.db.models import Avg, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

from .models import (
    Assessment,
    Flashcard,
    FlashcardReview,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    StudyStreak,
)
from .serializers import (
    AssessmentSerializer,
    AssessmentStatsSerializer,
    FlashcardReviewSerializer,
    FlashcardReviewSessionSerializer,
    FlashcardSerializer,
    QuizAttemptSerializer,
    QuizQuestionSerializer,
    QuizResponseSerializer,
    QuizResultSerializer,
    QuizSerializer,
    QuizTakingSerializer,
    StudyStreakSerializer,
)


class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def due(self, request):
        """Get flashcards due for review."""
        due_flashcards = (
            self.get_queryset()
            .filter(next_review_date__lte=timezone.now(), is_active=True)
            .order_by("next_review_date")
        )

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            due_flashcards = due_flashcards.filter(course_id=course_id)

        serializer = FlashcardReviewSessionSerializer(due_flashcards, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get flashcard statistics."""
        queryset = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        stats = {
            "total_flashcards": queryset.count(),
            "active_flashcards": queryset.filter(is_active=True).count(),
            "due_flashcards": queryset.filter(
                next_review_date__lte=timezone.now(), is_active=True
            ).count(),
            "mastered_flashcards": len(
                [f for f in queryset if f.mastery_level == "mastered"]
            ),
            "average_success_rate": queryset.aggregate(avg_rate=Avg("success_rate"))[
                "avg_rate"
            ]
            or 0,
            "by_difficulty": queryset.values("difficulty_level").annotate(
                count=Count("id")
            ),
            "by_mastery": [
                {
                    "level": level,
                    "count": len([f for f in queryset if f.mastery_level == level]),
                }
                for level in ["new", "learning", "difficult", "mastered"]
            ],
        }

        return Response(stats)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """Submit a review for a flashcard."""
        flashcard = self.get_object()
        serializer = FlashcardReviewSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(flashcard=flashcard, user=request.user)

            # Update study streak
            self.update_study_streak(request.user, flashcard.course, "flashcard")

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def toggle_star(self, request, pk=None):
        """Toggle star status of a flashcard."""
        flashcard = self.get_object()
        flashcard.is_starred = not flashcard.is_starred
        flashcard.save()

        return Response({"is_starred": flashcard.is_starred})

    def update_study_streak(self, user, course, streak_type):
        """Update user's study streak."""
        streak, created = StudyStreak.objects.get_or_create(
            user=user, course=course, streak_type=streak_type
        )
        streak.update_streak()


class FlashcardReviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FlashcardReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FlashcardReview.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get review statistics."""
        queryset = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(flashcard__course_id=course_id)

        stats = {
            "total_reviews": queryset.count(),
            "average_quality": queryset.aggregate(avg_quality=Avg("quality_response"))[
                "avg_quality"
            ]
            or 0,
            "by_quality": queryset.values("quality_response")
            .annotate(count=Count("id"))
            .order_by("quality_response"),
            "recent_reviews": queryset.order_by("-created_at")[:10].values(
                "flashcard__question", "quality_response", "created_at"
            ),
        }

        return Response(stats)


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Validate that the course belongs to the user
        course = serializer.validated_data.get("course")
        if course and course.user != self.request.user:
            from rest_framework import serializers as rest_serializers

            raise rest_serializers.ValidationError(
                "Course must belong to the authenticated user"
            )
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def take(self, request, pk=None):
        """Get quiz for taking (without correct answers)."""
        quiz = self.get_object()

        if not quiz.can_user_attempt(request.user):
            return Response(
                {"error": "You cannot attempt this quiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = QuizTakingSerializer(quiz)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def start_attempt(self, request, pk=None):
        """Start a new quiz attempt."""
        quiz = self.get_object()

        if not quiz.can_user_attempt(request.user):
            return Response(
                {"error": "You cannot attempt this quiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create new attempt
        attempt_number = quiz.get_user_attempts(request.user) + 1
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user,
            attempt_number=attempt_number,
            questions_order=list(quiz.questions.values_list("id", flat=True)),
        )

        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        """Get quiz results with correct answers."""
        quiz = self.get_object()
        serializer = QuizResultSerializer(quiz)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get quiz statistics."""
        queryset = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        stats = {
            "total_quizzes": queryset.count(),
            "published_quizzes": queryset.filter(status="published").count(),
            "draft_quizzes": queryset.filter(status="draft").count(),
            "by_type": queryset.values("quiz_type").annotate(count=Count("id")),
            "average_score": queryset.aggregate(avg_score=Avg("average_score"))[
                "avg_score"
            ]
            or 0,
        }

        return Response(stats)


class QuizQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuizQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.kwargs.get("quiz_pk")
        return QuizQuestion.objects.filter(
            quiz_id=quiz_id, quiz__user=self.request.user
        )

    def perform_create(self, serializer):
        quiz_id = self.kwargs.get("quiz_pk")
        quiz = get_object_or_404(Quiz, id=quiz_id, user=self.request.user)
        serializer.save(quiz=quiz)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def submit_response(self, request, pk=None):
        """Submit a response to a quiz question."""
        attempt = self.get_object()

        if attempt.status != "in_progress":
            return Response(
                {"error": "Cannot submit response to completed attempt"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = QuizResponseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(attempt=attempt)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete the quiz attempt."""
        attempt = self.get_object()

        if attempt.status != "in_progress":
            return Response(
                {"error": "Attempt is not in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt.complete_attempt()

        # Update study streak
        self.update_study_streak(request.user, attempt.quiz.course, "quiz")

        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get quiz attempt statistics."""
        queryset = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(quiz__course_id=course_id)

        stats = {
            "total_attempts": queryset.count(),
            "completed_attempts": queryset.filter(status="completed").count(),
            "passed_attempts": queryset.filter(passed=True).count(),
            "average_score": queryset.filter(status="completed").aggregate(
                avg_score=Avg("percentage_score")
            )["avg_score"]
            or 0,
            "best_score": queryset.filter(status="completed").aggregate(
                max_score=Max("percentage_score")
            )["max_score"]
            or 0,
            "by_status": queryset.values("status").annotate(count=Count("id")),
        }

        return Response(stats)

    def update_study_streak(self, user, course, streak_type):
        """Update user's study streak."""
        streak, created = StudyStreak.objects.get_or_create(
            user=user, course=course, streak_type=streak_type
        )
        streak.update_streak()


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Assessment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def generate_content(self, request, pk=None):
        """Generate flashcards and quizzes for the assessment using agentic AI."""
        assessment = self.get_object()

        try:
            # Get parameters from request
            topic = request.data.get("topic", assessment.title or "")
            content = request.data.get("content", "")
            document_ids = request.data.get("document_ids", [])
            use_adaptive = request.data.get("use_adaptive", False)

            results = {
                "message": "Content generation completed",
                "assessment_id": assessment.id,
                "status": "completed",
                "generated_content": {},
                "agent_metadata": {},
            }

            # Generate flashcards if requested
            if assessment.include_flashcards:
                try:
                    from .services.generators.flashcard_service import (
                        get_flashcard_service,
                    )

                    flashcard_service = get_flashcard_service()
                    flashcard_result = flashcard_service.generate_flashcards(
                        user_id=request.user.id,
                        course_id=assessment.course.id,
                        content=content,
                        topic=topic,
                        document_ids=document_ids,
                        count=assessment.flashcard_count,
                        difficulty_level=getattr(
                            assessment, "difficulty_level", "medium"
                        ),
                        auto_save=True,
                    )

                    if flashcard_result.get("success"):
                        results["generated_content"]["flashcards"] = {
                            "count": flashcard_result.get("count", 0),
                            "flashcards": flashcard_result.get("flashcards", []),
                            "confidence": flashcard_result.get(
                                "generation_metadata", {}
                            ).get("confidence", 0.0),
                        }
                        results["agent_metadata"]["flashcard_generation"] = (
                            flashcard_result.get("generation_metadata", {})
                        )
                    else:
                        results["generated_content"]["flashcards"] = {
                            "error": flashcard_result.get("error", "Unknown error")
                        }

                except Exception as e:
                    logger.error(f"Error generating flashcards: {str(e)}")
                    results["generated_content"]["flashcards"] = {"error": str(e)}

            # Generate quiz questions if requested
            if assessment.include_quizzes:
                try:
                    from .services.generators.quiz_service import get_quiz_service

                    quiz_service = get_quiz_service()

                    if use_adaptive:
                        # Get user performance history for adaptive generation
                        user_performance = self._get_user_performance_stats(
                            request.user, assessment.course
                        )
                        quiz_result = quiz_service.generate_adaptive_quiz(
                            user_id=request.user.id,
                            course_id=assessment.course.id,
                            topic=topic,
                            target_duration_minutes=assessment.estimated_duration_minutes
                            or 20,
                            adaptive_difficulty=True,
                            performance_history=user_performance,
                        )
                    else:
                        quiz_result = quiz_service.generate_quiz(
                            user_id=request.user.id,
                            course_id=assessment.course.id,
                            title=f"Quiz for {assessment.title}",
                            content=content,
                            topic=topic,
                            document_ids=document_ids,
                            question_count=assessment.quiz_count,
                            difficulty_level=getattr(
                                assessment, "difficulty_level", "medium"
                            ),
                            quiz_type="assessment",
                            auto_save=True,
                        )

                    if quiz_result.get("success"):
                        quiz_data = quiz_result.get("quiz", {})
                        results["generated_content"]["quiz"] = {
                            "quiz_id": quiz_data.get("id"),
                            "title": quiz_data.get("title"),
                            "question_count": quiz_result.get("question_count", 0),
                            "questions": quiz_result.get("questions", []),
                            "confidence": quiz_result.get(
                                "generation_metadata", {}
                            ).get("confidence", 0.0),
                        }
                        results["agent_metadata"]["quiz_generation"] = quiz_result.get(
                            "generation_metadata", {}
                        )

                        if use_adaptive:
                            results["generated_content"]["quiz"][
                                "adaptive_metadata"
                            ] = quiz_result.get("adaptive_metadata", {})
                    else:
                        results["generated_content"]["quiz"] = {
                            "error": quiz_result.get("error", "Unknown error")
                        }

                except Exception as e:
                    logger.error(f"Error generating quiz questions: {str(e)}")
                    results["generated_content"]["quiz"] = {"error": str(e)}

            return Response(results)

        except Exception as e:
            logger.error(f"Error in content generation: {str(e)}")
            return Response(
                {
                    "message": "Content generation failed",
                    "assessment_id": assessment.id,
                    "status": "failed",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_user_performance_stats(self, user, course):
        """Get user performance statistics for adaptive generation."""
        try:
            # Get recent quiz attempts
            recent_attempts = QuizAttempt.objects.filter(
                user=user, quiz__course=course, status="completed"
            ).order_by("-completed_at")[:10]

            if recent_attempts:
                scores = [attempt.percentage_score for attempt in recent_attempts]
                return {
                    "average_score": sum(scores)
                    / len(scores)
                    / 100.0,  # Convert to 0-1 scale
                    "recent_attempts": len(recent_attempts),
                    "improvement_trend": self._calculate_trend(scores),
                }

            return None

        except Exception as e:
            logger.error(f"Error getting user performance stats: {str(e)}")
            return None

    def _calculate_trend(self, scores):
        """Calculate performance trend from recent scores."""
        if len(scores) < 3:
            return "insufficient_data"

        recent_avg = sum(scores[-3:]) / 3
        earlier_avg = (
            sum(scores[:-3]) / len(scores[:-3])
            if len(scores) > 3
            else sum(scores[:3]) / 3
        )

        if recent_avg > earlier_avg + 5:
            return "improving"
        elif recent_avg < earlier_avg - 5:
            return "declining"
        else:
            return "stable"

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get detailed assessment statistics."""
        assessment = self.get_object()
        serializer = AssessmentStatsSerializer(assessment)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Get assessment dashboard data."""
        queryset = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        # Get upcoming assessments
        upcoming = queryset.filter(
            due_date__gte=timezone.now(), status="published"
        ).order_by("due_date")[:5]

        # Get recent assessments
        recent = queryset.order_by("-created_at")[:5]

        # Overall stats
        stats = {
            "total_assessments": queryset.count(),
            "active_assessments": queryset.filter(status="published").count(),
            "average_performance": queryset.aggregate(
                avg_performance=Avg("average_performance")
            )["avg_performance"]
            or 0,
            "upcoming_assessments": AssessmentSerializer(upcoming, many=True).data,
            "recent_assessments": AssessmentSerializer(recent, many=True).data,
        }

        return Response(stats)


class StudyStreakViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudyStreakSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudyStreak.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get study streak summary."""
        queryset = self.get_queryset()

        # Filter by course if specified
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        summary = {
            "total_streaks": queryset.count(),
            "active_streaks": queryset.filter(current_streak__gt=0).count(),
            "longest_overall_streak": queryset.aggregate(
                max_streak=Max("longest_streak")
            )["max_streak"]
            or 0,
            "by_type": queryset.values("streak_type").annotate(
                count=Count("id"),
                avg_current=Avg("current_streak"),
                max_longest=Max("longest_streak"),
            ),
            "recent_milestones": self.get_recent_milestones(queryset),
        }

        return Response(summary)

    def get_recent_milestones(self, queryset):
        """Get recently achieved milestones."""
        milestones = []
        for streak in queryset:
            if streak.milestones_achieved:
                for milestone in streak.milestones_achieved[-3:]:  # Last 3 milestones
                    milestones.append(
                        {
                            "streak_type": streak.streak_type,
                            "course": (
                                streak.course.name if streak.course else "All Courses"
                            ),
                            "milestone": milestone,
                            "achieved_at": streak.updated_at,
                        }
                    )

        return sorted(milestones, key=lambda x: x["achieved_at"], reverse=True)[:10]


# Additional utility views


class AssessmentAnalyticsView(viewsets.ReadOnlyModelViewSet):
    """Advanced analytics for assessments."""

    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Assessment.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def performance_trends(self, request):
        """Get performance trends over time."""
        user = request.user
        course_id = request.query_params.get("course")

        # Get flashcard review trends
        flashcard_reviews = FlashcardReview.objects.filter(user=user)
        if course_id:
            flashcard_reviews = flashcard_reviews.filter(flashcard__course_id=course_id)

        # Get quiz attempt trends
        quiz_attempts = QuizAttempt.objects.filter(user=user, status="completed")
        if course_id:
            quiz_attempts = quiz_attempts.filter(quiz__course_id=course_id)

        # Group by date and calculate averages
        from django.db.models import Avg
        from django.db.models.functions import TruncDate

        flashcard_trends = (
            flashcard_reviews.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(avg_quality=Avg("quality_response"), count=Count("id"))
            .order_by("date")
        )

        quiz_trends = (
            quiz_attempts.annotate(date=TruncDate("completed_at"))
            .values("date")
            .annotate(avg_score=Avg("percentage_score"), count=Count("id"))
            .order_by("date")
        )

        return Response(
            {
                "flashcard_trends": list(flashcard_trends),
                "quiz_trends": list(quiz_trends),
            }
        )

    @action(detail=False, methods=["get"])
    def learning_insights(self, request):
        """Get learning insights and recommendations."""
        user = request.user
        course_id = request.query_params.get("course")

        # Get user's performance data
        flashcards = Flashcard.objects.filter(user=user)
        quizzes = Quiz.objects.filter(user=user)

        if course_id:
            flashcards = flashcards.filter(course_id=course_id)
            quizzes = quizzes.filter(course_id=course_id)

        # Analyze difficult areas
        difficult_flashcards = flashcards.filter(
            success_rate__lt=0.7, total_reviews__gte=3
        ).order_by("success_rate")

        # Analyze time patterns
        reviews = FlashcardReview.objects.filter(user=user)
        if course_id:
            reviews = reviews.filter(flashcard__course_id=course_id)

        # Get peak performance times
        from django.db.models.functions import Extract

        time_performance = (
            reviews.annotate(hour=Extract("created_at", "hour"))
            .values("hour")
            .annotate(avg_quality=Avg("quality_response"), count=Count("id"))
            .order_by("-avg_quality")
        )

        insights = {
            "difficult_areas": [
                {
                    "question": fc.question[:100],
                    "success_rate": fc.success_rate,
                    "reviews": fc.total_reviews,
                    "difficulty": fc.difficulty_level,
                }
                for fc in difficult_flashcards[:10]
            ],
            "best_study_times": list(time_performance[:5]),
            "recommendations": self.generate_recommendations(user, course_id),
        }

        return Response(insights)

    def generate_recommendations(self, user, course_id):
        """Generate personalized learning recommendations."""
        recommendations = []

        # Check for due flashcards
        due_count = Flashcard.objects.filter(
            user=user, next_review_date__lte=timezone.now(), is_active=True
        ).count()

        if due_count > 0:
            recommendations.append(
                {
                    "type": "review_due",
                    "message": f"You have {due_count} flashcards due for review",
                    "action": "review_flashcards",
                    "priority": "high",
                }
            )

        # Check for long streaks
        streaks = StudyStreak.objects.filter(user=user)
        if course_id:
            streaks = streaks.filter(course_id=course_id)

        for streak in streaks:
            if streak.current_streak == 0 and streak.longest_streak > 7:
                recommendations.append(
                    {
                        "type": "broken_streak",
                        "message": f"Your {streak.streak_type} streak has been broken. Start a new one today!",
                        "action": "start_study_session",
                        "priority": "medium",
                    }
                )

        return recommendations
