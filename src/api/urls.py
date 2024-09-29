from django.urls import path
from .views import health_check
from learning_materials.views import (
    FlashcardCreationView,
    RAGResponseView,
    QuizCreationView,
    QuizGradingView,
    CompendiumCreationView,
)


urlpatterns = [
    path("health-check/", health_check, name="health-check"),
    path(
        "flashcards/create/", FlashcardCreationView.as_view(), name="create-flashcards"
    ),
    path("search/", RAGResponseView.as_view(), name="create-rag-response"),
    path("quiz/create/", QuizCreationView.as_view(), name="create-quiz"),
    path("quiz/grade/", QuizGradingView.as_view(), name="grade-quiz"),
    path(
        "compendium/create/", CompendiumCreationView.as_view(), name="create-compendium"
    ),
]
