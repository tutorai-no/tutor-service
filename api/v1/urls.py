from django.urls import include, path

app_name = "api_v1"

urlpatterns = [
    # Original app-based endpoints (maintained for backward compatibility)
    path("accounts/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("learning/", include("learning.urls")),
    path("assessments/", include("assessments.urls")),
    path("chat/", include("chat.urls")),
    path("billing/", include("billing.urls")),
    path("documents/", include("document_processing.urls")),
    # Grouped endpoints for better organization
    path("analytics/", include("api.v1.analytics_urls")),
    path("study/", include("api.v1.study_urls")),
    path("ai/", include("api.v1.ai_urls")),
    path("user/", include("api.v1.user_urls")),
]
