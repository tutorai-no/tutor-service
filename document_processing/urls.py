"""
URL patterns for document processing endpoints.
"""

from django.urls import path
from .views import (
    DocumentUploadStreamView,
    URLUploadStreamView,
    DocumentStatusView,
    URLStatusView,
    KnowledgeGraphView,
    DocumentListView,
    URLListView,
    HealthCheckView
)

app_name = 'document_processing'

urlpatterns = [
    # Streaming upload endpoints
    path('upload/document/stream/', DocumentUploadStreamView.as_view(), name='document-upload-stream'),
    path('upload/url/stream/', URLUploadStreamView.as_view(), name='url-upload-stream'),
    
    # Status endpoints
    path('documents/<str:document_id>/status/', DocumentStatusView.as_view(), name='document-status'),
    path('urls/<str:url_upload_id>/status/', URLStatusView.as_view(), name='url-status'),
    
    # Knowledge graph endpoints
    path('graphs/<str:graph_id>/', KnowledgeGraphView.as_view(), name='knowledge-graph'),
    
    # List endpoints
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('urls/', URLListView.as_view(), name='url-list'),
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
]