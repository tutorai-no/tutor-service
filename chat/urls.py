from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChatAnalyticsViewSet,
    ChatMessageViewSet,
    ChatViewSet,
    TutoringSessionViewSet,
)

router = DefaultRouter()
router.register(r"chats", ChatViewSet, basename="chat")
router.register(r"messages", ChatMessageViewSet, basename="chatmessage")
router.register(r"sessions", TutoringSessionViewSet, basename="tutoringsession")
router.register(r"analytics", ChatAnalyticsViewSet, basename="chatanalytics")

urlpatterns = [
    path("", include(router.urls)),
]
