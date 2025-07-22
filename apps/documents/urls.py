"""
URL configuration for the documents app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='documents_health'),
    
    # TODO: Add documents endpoints when implementing functionality
    # Example:
    # path('', views.documents_list, name='documents_list'),
    # path('<int:pk>/', views.documents_detail, name='documents_detail'),
]
