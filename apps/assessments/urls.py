"""
URL configuration for the assessments app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='assessments_health'),
    
    # TODO: Add assessments endpoints when implementing functionality
    # Example:
    # path('', views.assessments_list, name='assessments_list'),
    # path('<int:pk>/', views.assessments_detail, name='assessments_detail'),
]
