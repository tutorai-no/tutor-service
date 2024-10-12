from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import CustomTokenObtainPairView, LogoutView, PasswordResetConfirmView, PasswordResetView, RegisterView, SubscriptionListView, UserProfileView, SubscriptionHistoryView
from api.views import health_check
from learning_materials.views import (
    FlashcardCreationView,
    RAGResponseView,
    QuizCreationView,
    QuizGradingView,
    CompendiumCreationView,
    ReviewFlashcardView
)


urlpatterns = [
    path("health-check/", health_check, name="health-check"),
    path(
        "flashcards/create/", FlashcardCreationView.as_view(), name="create-flashcards"
    ),
    path("flashcards/review/", ReviewFlashcardView.as_view(),
         name="review-flashcards"),
    path("search/", RAGResponseView.as_view(), name="create-rag-response"),
    path("quiz/create/", QuizCreationView.as_view(), name="create-quiz"),
    path("quiz/grade/", QuizGradingView.as_view(), name="grade-quiz"),
    path(
        "compendium/create/", CompendiumCreationView.as_view(), name="create-compendium"
    ),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    path('subscriptions/', SubscriptionListView.as_view(), name='subscriptions'),
    path('subscription-history/', SubscriptionHistoryView.as_view(),
         name='subscription_history'),



]
