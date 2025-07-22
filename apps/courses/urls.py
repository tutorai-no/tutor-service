"""
URL configuration for the courses app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='courses_health'),
    
    # TODO: Add courses endpoints when implementing functionality
    # Example:
    # path('', views.courses_list, name='courses_list'),
    # path('<int:pk>/', views.courses_detail, name='courses_detail'),
]
