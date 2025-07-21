"""
Analytics API URLs - Consolidated analytics endpoints from different apps.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from assessments.views import AssessmentAnalyticsView
from chat.views import ChatAnalyticsViewSet
from learning.views import LearningAnalyticsViewSet

# Create router for analytics endpoints
router = DefaultRouter()

# Register analytics viewsets from different apps
router.register(r"learning", LearningAnalyticsViewSet, basename="learning-analytics")
router.register(r"chat", ChatAnalyticsViewSet, basename="chat-analytics")
router.register(
    r"assessments", AssessmentAnalyticsView, basename="assessment-analytics"
)

app_name = "analytics"

urlpatterns = [
    path("", include(router.urls)),
]
