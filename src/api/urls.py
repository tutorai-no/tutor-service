from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import routers

from accounts.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    SubscriptionListView,
    SubscriptionHistoryView,
    UserFeedback,
    UserProfileView,
)
from api.views import health_check
from learning_materials.views import (
    FileUploadView,
    CourseFilesView,
    CardsetExportView,
    CardsetViewSet,
    CompendiumCreationView,
    FlashcardCreationView,
    FlashcardViewSet,
    QuizCreationView,
    QuizGradingView,
    ReviewFlashcardView,
    ChatHistoryListView,
    ChatHistoryView,
    RAGResponseView,
)

# Initialize the router and register the viewsets
router = routers.DefaultRouter()
router.register(r"cardsets", CardsetViewSet, basename="cardset")
router.register(r"flashcards", FlashcardViewSet, basename="flashcard")

urlpatterns = [
    path("health-check/", health_check, name="health-check"),
    path("files/upload/", FileUploadView.as_view(), name="upload-file"),
    path("courses/<uuid:course_id>/files/", CourseFilesView.as_view(), name="course-files"),
    path(
        "flashcards/create/", FlashcardCreationView.as_view(), name="create-flashcards"
    ),
    path("flashcards/review/", ReviewFlashcardView.as_view(), name="review-flashcards"),
    path(
        "flashcards/export/<int:pk>/",
        CardsetExportView.as_view(),
        name="export-flashcards",
    ),
    path("search/", RAGResponseView.as_view(), name="create-rag-response"),
    path("quiz/create/", QuizCreationView.as_view(), name="create-quiz"),
    path("quiz/grade/", QuizGradingView.as_view(), name="grade-quiz"),
    path(
        "compendium/create/", CompendiumCreationView.as_view(), name="create-compendium"
    ),
    path("chat/", RAGResponseView.as_view(), name="chat"),
    path("chat/history/", ChatHistoryListView.as_view(), name="chat-history-list"),
    path("chat/history/<str:chatId>/", ChatHistoryView.as_view(), name="chat-history"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("subscriptions/", SubscriptionListView.as_view(), name="subscriptions"),
    path(
        "subscription-history/",
        SubscriptionHistoryView.as_view(),
        name="subscription_history",
    ),
    path("feedback/", UserFeedback.as_view(), name="feedback"),
    path("", include(router.urls)),
]
