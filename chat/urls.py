from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ChatViewSet,
    ChatMessageViewSet,
    TutoringSessionViewSet,
    ChatAnalyticsViewSet,
)

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'messages', ChatMessageViewSet, basename='chatmessage')
router.register(r'sessions', TutoringSessionViewSet, basename='tutoringsession')
router.register(r'analytics', ChatAnalyticsViewSet, basename='chatanalytics')

urlpatterns = [
    path('', include(router.urls)),
]