from django.urls import path, include

app_name = 'api_v1'

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('assessments/', include('assessments.urls')),
    path('chat/', include('chat.urls')),
    path('billing/', include('billing.urls')),
]