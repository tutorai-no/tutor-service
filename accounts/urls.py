from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    RequestAccessView,
    StudySessionTokenView,
    TokenRefreshView,
    TokenValidationView,
    UserActivityCreateView,
    UserActivityListView,
    UserFeedbackView,
    UserProfileDetailView,
    UserProfileView,
    UserStreakView,
)

# Create router for ViewSets (none in this case)
router = DefaultRouter()

urlpatterns = [
    # Authentication endpoints
    path("request-access/", RequestAccessView.as_view(), name="request-access"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token-refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token-validate/", TokenValidationView.as_view(), name="token-validate"),
    path(
        "study-session-token/",
        StudySessionTokenView.as_view(),
        name="study-session-token",
    ),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    # User profile endpoints
    path("profile/", UserProfileView.as_view(), name="profile"),
    path(
        "profile-detail/", UserProfileDetailView.as_view(), name="user-profile-detail"
    ),
    # User engagement endpoints
    path("feedback/", UserFeedbackView.as_view(), name="feedback"),
    path("streak/", UserStreakView.as_view(), name="user-streak"),
    path("activity/", UserActivityCreateView.as_view(), name="user-activity-create"),
    path("activity/list/", UserActivityListView.as_view(), name="user-activity-list"),
]

# Include router URLs
urlpatterns += router.urls
