"""
User-Centric API URLs - Consolidated user profile and activity endpoints.
"""

from django.urls import path

from accounts.views import (
    UserActivityCreateView,
    UserActivityListView,
    UserFeedbackView,
    UserProfileView,
    UserStreakView,
)

app_name = "user"

urlpatterns = [
    # User profile endpoints
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/me/", UserProfileView.as_view(), name="user-profile-me"),
    # User activity endpoints
    path("activity/", UserActivityListView.as_view(), name="user-activity-list"),
    path(
        "activity/create/",
        UserActivityCreateView.as_view(),
        name="user-activity-create",
    ),
    # User streak endpoint
    path("streaks/", UserStreakView.as_view(), name="user-streak"),
    # User feedback endpoint
    path("feedback/", UserFeedbackView.as_view(), name="user-feedback"),
]
