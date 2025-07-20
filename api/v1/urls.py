from django.urls import include, path

app_name = "api_v1"

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("learning/", include("learning.urls")),
    path("assessments/", include("assessments.urls")),
    path("chat/", include("chat.urls")),
    path("billing/", include("billing.urls")),
    path("documents/", include("document_processing.urls")),
]
