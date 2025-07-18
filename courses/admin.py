from django.contrib import admin
from .models import (
    Course, 
    CourseSection, 
    Document, 
    DocumentTag, 
    DocumentTagAssignment,
    Chat, 
    ChatMessage
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'course_code', 'university', 'language', 
        'is_active', 'is_favorite', 'created_at'
    ]
    list_filter = [
        'language', 'subject_area', 'difficulty_level', 'is_active', 
        'is_archived', 'is_favorite', 'created_at'
    ]
    search_fields = ['name', 'description', 'user__username', 'course_code', 'university']
    readonly_fields = [
        'id', 'total_documents', 'total_study_hours', 'completion_percentage',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'description')
        }),
        ('Academic Context', {
            'fields': ('university', 'course_code', 'semester', 'academic_year', 'credits')
        }),
        ('Course Metadata', {
            'fields': ('language', 'subject_area', 'difficulty_level', 'color', 'icon')
        }),
        ('Learning Configuration', {
            'fields': ('study_goals', 'preferred_study_methods')
        }),
        ('Important Dates', {
            'fields': ('start_date', 'end_date', 'exam_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_archived', 'is_favorite')
        }),
        ('Statistics', {
            'fields': ('total_documents', 'total_study_hours', 'completion_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'order', 'is_completed', 'created_at']
    list_filter = ['course', 'is_completed', 'created_at']
    search_fields = ['name', 'description', 'course__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Section Information', {
            'fields': ('course', 'name', 'description', 'order')
        }),
        ('Academic Context', {
            'fields': ('chapter_number', 'page_range_start', 'page_range_end')
        }),
        ('Content', {
            'fields': ('learning_objectives', 'key_concepts')
        }),
        ('Progress', {
            'fields': ('is_completed', 'completion_percentage', 'estimated_study_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'course', 'document_type', 'processing_status', 
        'is_favorite', 'created_at'
    ]
    list_filter = [
        'document_type', 'processing_status', 'is_favorite', 'is_archived', 
        'created_at'
    ]
    search_fields = ['name', 'description', 'user__username', 'course__name']
    readonly_fields = [
        'id', 'file_size_bytes', 'content_type', 'original_filename', 
        'page_count', 'word_count', 'language', 'processing_status',
        'processing_error', 'processed_at', 'storage_path', 'extracted_text',
        'summary', 'topics', 'view_count', 'last_accessed_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'course', 'section', 'name', 'description', 'document_type')
        }),
        ('File Details', {
            'fields': ('file_url', 'file_size_bytes', 'content_type', 'original_filename')
        }),
        ('URL/Media Details', {
            'fields': ('source_url', 'thumbnail_url', 'duration_seconds')
        }),
        ('Content Analysis', {
            'fields': ('page_count', 'word_count', 'language', 'extracted_text', 'summary', 'topics')
        }),
        ('Processing', {
            'fields': ('processing_status', 'processing_error', 'processed_at', 'storage_path')
        }),
        ('Usage Statistics', {
            'fields': ('view_count', 'last_accessed_at')
        }),
        ('Status', {
            'fields': ('is_favorite', 'is_archived')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'usage_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['id', 'usage_count', 'created_at', 'updated_at']


@admin.register(DocumentTagAssignment)
class DocumentTagAssignmentAdmin(admin.ModelAdmin):
    list_display = ['document', 'tag', 'assigned_at']
    list_filter = ['assigned_at']
    search_fields = ['document__name', 'tag__name']
    readonly_fields = ['assigned_at']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'course', 'message_count', 'is_pinned', 
        'is_archived', 'created_at'
    ]
    list_filter = ['is_pinned', 'is_archived', 'created_at']
    search_fields = ['title', 'user__username', 'course__name']
    readonly_fields = [
        'id', 'message_count', 'total_tokens_used', 'average_response_time_ms',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Chat Information', {
            'fields': ('user', 'course', 'title')
        }),
        ('Status', {
            'fields': ('is_pinned', 'is_archived')
        }),
        ('Statistics', {
            'fields': ('message_count', 'total_tokens_used', 'average_response_time_ms')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'chat', 'role', 'content_preview', 'token_count', 
        'is_helpful', 'user_rating', 'created_at'
    ]
    list_filter = ['role', 'is_helpful', 'user_rating', 'created_at']
    search_fields = ['chat__title', 'content']
    readonly_fields = [
        'id', 'token_count', 'processing_time_ms', 'model_used', 
        'temperature', 'context_used', 'created_at'
    ]
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content Preview"
    
    fieldsets = (
        ('Message', {
            'fields': ('chat', 'role', 'content')
        }),
        ('AI Model Information', {
            'fields': ('model_used', 'temperature', 'token_count', 'processing_time_ms')
        }),
        ('Context', {
            'fields': ('referenced_documents', 'context_used')
        }),
        ('User Feedback', {
            'fields': ('is_helpful', 'user_rating')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )