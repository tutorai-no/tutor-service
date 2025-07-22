"""
URL configuration for the chat app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='chat_health'),
    
    # TODO: Add chat endpoints when implementing functionality
    # Example:
    # path('', views.chat_list, name='chat_list'),
    # path('<int:pk>/', views.chat_detail, name='chat_detail'),
]
