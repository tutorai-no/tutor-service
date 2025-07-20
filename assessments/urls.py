from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rest_framework_nested import routers

from .views import (
    AssessmentAnalyticsView,
    AssessmentViewSet,
    FlashcardReviewViewSet,
    FlashcardViewSet,
    QuizAttemptViewSet,
    QuizQuestionViewSet,
    QuizViewSet,
    StudyStreakViewSet,
)

app_name = "assessments"

# Create the main router
router = DefaultRouter()
router.register(r"flashcards", FlashcardViewSet, basename="flashcard")
router.register(
    r"flashcard-reviews", FlashcardReviewViewSet, basename="flashcard-review"
)
router.register(r"quizzes", QuizViewSet, basename="quiz")
router.register(r"quiz-attempts", QuizAttemptViewSet, basename="quiz-attempt")
router.register(r"", AssessmentViewSet, basename="assessment")
router.register(r"study-streaks", StudyStreakViewSet, basename="study-streak")
router.register(r"analytics", AssessmentAnalyticsView, basename="analytics")

# Create nested routers for quiz questions
quiz_router = routers.NestedDefaultRouter(router, r"quizzes", lookup="quiz")
quiz_router.register(r"questions", QuizQuestionViewSet, basename="quiz-question")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(quiz_router.urls)),
]
