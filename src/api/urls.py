from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import routers

from accounts.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    RequestAccessView,
    SubscriptionListView,
    SubscriptionHistoryView,
    UserFeedback,
    UserProfileView,
    StreakRetrieveView,
    ActivityCreateView,
    ActivityLogView,
)
from api.views import health_check
from learning_materials.views import (
    ChatResponseView,
    ChatListView,
    ChatView,
    CourseViewSet,
    FileUploadView,
    UserDocumentsListView,
    UserDocumentDetailView,
    CourseFilesView,
    CardsetExportView,
    CardsetViewSet,
    CompendiumCreationView,
    FlashcardGenerationView,
    FlashcardViewSet,
    QuizGenerationView,
    QuizGradingView,
    QuizViewSet,
    ReviewFlashcardView,
)

# Initialize the router and register the viewsets
router = routers.DefaultRouter()
router.register(r"cardsets", CardsetViewSet, basename="cardset")
router.register(r"flashcards", FlashcardViewSet, basename="flashcard")
router.register(r"quizzes", QuizViewSet, basename="quiz")
router.register(r"courses", CourseViewSet, basename="course")

urlpatterns = [
    # Health check
    path("health-check/", health_check, name="health-check"),
    # Authentication & Profile
    path("request-access/", RequestAccessView.as_view(), name="request_access"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    # Streaks
    path("streak/", StreakRetrieveView.as_view(), name="streak-retrieve"),
    # Activities
    path("activities/", ActivityCreateView.as_view(), name="activity-create"),
    path("activity-log/", ActivityLogView.as_view(), name="activity-log"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    # Subscriptions
    path("subscriptions/", SubscriptionListView.as_view(), name="subscriptions"),
    path(
        "subscription-history/",
        SubscriptionHistoryView.as_view(),
        name="subscription-history",
    ),
    # Courses
    path(
        "courses/<uuid:course_id>/files/",
        CourseFilesView.as_view(),
        name="course-files",
    ),
    # Files
    path("files/upload/", FileUploadView.as_view(), name="upload-file"),
    path("files/", UserDocumentsListView.as_view(), name="user-files"),
    path("files/<uuid:id>/", UserDocumentDetailView.as_view(), name="file-update"),
    # Chat
    path("chat/response/", ChatResponseView.as_view(), name="chat-response"),
    path("chat/history/", ChatListView.as_view(), name="chat-history-list"),
    path("chat/history/<uuid:chatId>/", ChatView.as_view(), name="chat-history"),
    # Flashcards
    path(
        "flashcards/create/",
        FlashcardGenerationView.as_view(),
        name="create-flashcards",
    ),
    path("flashcards/review/", ReviewFlashcardView.as_view(), name="review-flashcards"),
    path(
        "flashcards/export/<int:pk>/",
        CardsetExportView.as_view(),
        name="export-flashcards",
    ),
    # Quizzes
    path("quiz/create/", QuizGenerationView.as_view(), name="create-quiz"),
    path("quiz/grade/", QuizGradingView.as_view(), name="grade-quiz"),
    # Compendiums
    path(
        "compendium/create/", CompendiumCreationView.as_view(), name="create-compendium"
    ),
    # Feedback
    path("feedback/", UserFeedback.as_view(), name="feedback"),
    # Router URLs
    path("", include(router.urls)),
]
