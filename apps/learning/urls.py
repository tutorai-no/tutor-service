"""
URL configuration for the learning app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='learning_health'),
    
    # TODO: Add learning endpoints when implementing functionality
    # Example:
    # path('', views.learning_list, name='learning_list'),
    # path('<int:pk>/', views.learning_detail, name='learning_detail'),
]
