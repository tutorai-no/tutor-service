"""
URL configuration for the billing app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='billing_health'),
    
    # TODO: Add billing endpoints when implementing functionality
    # Example:
    # path('', views.billing_list, name='billing_list'),
    # path('<int:pk>/', views.billing_detail, name='billing_detail'),
]
