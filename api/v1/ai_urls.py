"""
AI Services API URLs - Consolidated AI and chat-related endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat.views import ChatViewSet, TutoringSessionViewSet

# Create router for AI service endpoints
router = DefaultRouter()

# Chat and tutoring endpoints
router.register(r"chat", ChatViewSet, basename="ai-chat")
router.register(r"tutoring", TutoringSessionViewSet, basename="ai-tutoring")

app_name = "ai"

# Additional custom AI endpoints can be added here
urlpatterns = [
    path("", include(router.urls)),
    # Future AI endpoints:
    # path("generate/flashcards/", FlashcardGenerationView.as_view(), name="generate-flashcards"),
    # path("generate/quiz/", QuizGenerationView.as_view(), name="generate-quiz"),
    # path("analyze/performance/", PerformanceAnalysisView.as_view(), name="analyze-performance"),
    # path("recommend/content/", ContentRecommendationView.as_view(), name="recommend-content"),
]
