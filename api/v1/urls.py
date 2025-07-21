from django.urls import include, path

from .routers import router

app_name = "api_v1"

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("assessments/", include("assessments.urls")),
    path("billing/", include("billing.urls")),
    path("chat/", include("chat.urls")),
    path("courses/", include("courses.urls")),
    path("documents/", include("document_processing.urls")),
    path("learning/", include("learning.urls")),
] + router.urls
