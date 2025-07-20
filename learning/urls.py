from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    StudyPlanViewSet,
    StudyGoalViewSet,
    StudySessionViewSet,
    LearningProgressViewSet,
    LearningAnalyticsViewSet,
    AdaptiveLearningViewSet,
)

app_name = 'learning'

# Create the main router
router = DefaultRouter()
router.register(r'study-plans', StudyPlanViewSet, basename='study-plan')
router.register(r'goals', StudyGoalViewSet, basename='study-goal')
router.register(r'study-sessions', StudySessionViewSet, basename='study-session')
router.register(r'progress', LearningProgressViewSet, basename='learning-progress')
router.register(r'analytics', LearningAnalyticsViewSet, basename='learning-analytics')
router.register(r'adaptive', AdaptiveLearningViewSet, basename='adaptive-learning')

urlpatterns = [
    path('', include(router.urls)),
]