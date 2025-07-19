"""
Admin configuration for document processing models.
"""

from django.contrib import admin
from .models import DocumentUpload, DocumentChunk, URLUpload, URLChunk, ProcessingJob


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    """Admin interface for DocumentUpload model."""
    list_display = [
        'original_filename', 'user', 'status', 'processing_progress', 
        'total_nodes', 'total_edges', 'created_at'
    ]
    list_filter = ['status', 'content_type', 'created_at', 'course']
    search_fields = ['original_filename', 'user__email', 'file_hash']
    readonly_fields = [
        'id', 'file_hash', 'graph_id', 'processing_started_at', 
        'processing_completed_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'course']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'course', 'original_filename', 'file_size', 'content_type')
        }),
        ('Processing Status', {
            'fields': ('status', 'processing_started_at', 'processing_completed_at', 'error_message')
        }),
        ('Content Metadata', {
            'fields': ('total_chunks', 'processed_chunks', 'page_count')
        }),
        ('Knowledge Graph', {
            'fields': ('graph_id', 'total_nodes', 'total_edges')
        }),
        ('System Fields', {
            'fields': ('id', 'file_hash', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin interface for DocumentChunk model."""
    list_display = [
        'document', 'chunk_index', 'token_count', 'has_embedding', 
        'graph_extracted', 'nodes_count', 'edges_count'
    ]
    list_filter = ['has_embedding', 'graph_extracted', 'embedding_model']
    search_fields = ['document__original_filename', 'text_content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['document']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('document', 'chunk_index', 'text_content', 'token_count')
        }),
        ('Metadata', {
            'fields': ('page_numbers', 'metadata')
        }),
        ('Embedding', {
            'fields': ('has_embedding', 'embedding_model')
        }),
        ('Knowledge Graph', {
            'fields': ('graph_extracted', 'nodes_count', 'edges_count')
        }),
        ('System Fields', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(URLUpload)
class URLUploadAdmin(admin.ModelAdmin):
    """Admin interface for URLUpload model."""
    list_display = [
        'url', 'title', 'user', 'status', 'processing_progress',
        'total_nodes', 'total_edges', 'created_at'
    ]
    list_filter = ['status', 'domain', 'created_at', 'course']
    search_fields = ['url', 'title', 'user__email', 'domain']
    readonly_fields = [
        'id', 'graph_id', 'processing_started_at', 
        'processing_completed_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'course']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'course', 'url', 'title', 'domain')
        }),
        ('Processing Status', {
            'fields': ('status', 'processing_started_at', 'processing_completed_at', 'error_message')
        }),
        ('Content Metadata', {
            'fields': ('total_chunks', 'processed_chunks', 'content_length')
        }),
        ('Knowledge Graph', {
            'fields': ('graph_id', 'total_nodes', 'total_edges')
        }),
        ('System Fields', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(URLChunk)
class URLChunkAdmin(admin.ModelAdmin):
    """Admin interface for URLChunk model."""
    list_display = [
        'url_upload', 'chunk_index', 'token_count', 'has_embedding',
        'graph_extracted', 'nodes_count', 'edges_count'
    ]
    list_filter = ['has_embedding', 'graph_extracted', 'embedding_model']
    search_fields = ['url_upload__url', 'text_content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['url_upload']


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    """Admin interface for ProcessingJob model."""
    list_display = [
        'job_type', 'user', 'status', 'progress_percentage',
        'current_step_description', 'created_at'
    ]
    list_filter = ['job_type', 'status', 'created_at']
    search_fields = ['user__email', 'job_type', 'current_step_description']
    readonly_fields = [
        'id', 'started_at', 'completed_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user']
