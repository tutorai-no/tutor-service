"""
Study Experience API URLs - Consolidated study-related endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from assessments.views import (
    FlashcardReviewViewSet,
    FlashcardViewSet,
    QuizViewSet,
    StudyStreakViewSet,
)
from learning.views import (
    LearningProgressViewSet,
    StudyPlanViewSet,
    StudySessionViewSet,
)

# Create router for study experience endpoints
router = DefaultRouter()

# Learning endpoints
router.register(r"plans", StudyPlanViewSet, basename="study-plan")
router.register(r"sessions", StudySessionViewSet, basename="study-session")
router.register(r"progress", LearningProgressViewSet, basename="progress")

# Assessment endpoints
router.register(r"flashcards", FlashcardViewSet, basename="flashcard")
router.register(
    r"flashcard-reviews", FlashcardReviewViewSet, basename="flashcard-review"
)
router.register(r"quizzes", QuizViewSet, basename="quiz")
router.register(r"streaks", StudyStreakViewSet, basename="study-streak")

app_name = "study"

urlpatterns = [
    path("", include(router.urls)),
]
