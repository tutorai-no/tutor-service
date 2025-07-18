from rest_framework import serializers
from .models import (
    Course, 
    CourseSection, 
    Document, 
    DocumentTag, 
    DocumentTagAssignment,
    Chat, 
    ChatMessage
)


class CourseSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    days_until_exam = serializers.IntegerField(read_only=True)
    is_exam_soon = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'description', 'university', 'course_code', 'semester',
            'academic_year', 'credits', 'language', 'subject_area', 'difficulty_level',
            'color', 'icon', 'study_goals', 'preferred_study_methods', 'start_date',
            'end_date', 'exam_date', 'is_active', 'is_archived', 'is_favorite',
            'total_documents', 'total_study_hours', 'completion_percentage',
            'display_name', 'days_until_exam', 'is_exam_soon', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_documents', 'total_study_hours', 'completion_percentage',
            'display_name', 'days_until_exam', 'is_exam_soon', 'created_at', 'updated_at'
        ]


class CourseSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSection
        fields = [
            'id', 'name', 'description', 'order', 'chapter_number', 'page_range_start',
            'page_range_end', 'learning_objectives', 'key_concepts', 'is_completed',
            'completion_percentage', 'estimated_study_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.FloatField(read_only=True)
    is_processed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'name', 'description', 'document_type', 'file_url', 'file_size_bytes',
            'content_type', 'original_filename', 'source_url', 'thumbnail_url',
            'duration_seconds', 'page_count', 'word_count', 'language', 'processing_status',
            'processing_error', 'processed_at', 'storage_path', 'extracted_text',
            'summary', 'topics', 'view_count', 'last_accessed_at', 'is_favorite',
            'is_archived', 'file_size_mb', 'is_processed', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size_bytes', 'content_type', 'original_filename', 'page_count',
            'word_count', 'language', 'processing_status', 'processing_error',
            'processed_at', 'storage_path', 'extracted_text', 'summary', 'topics',
            'view_count', 'last_accessed_at', 'file_size_mb', 'is_processed',
            'created_at', 'updated_at'
        ]


class DocumentTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTag
        fields = ['id', 'name', 'color', 'description', 'usage_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class DocumentTagAssignmentSerializer(serializers.ModelSerializer):
    tag = DocumentTagSerializer(read_only=True)
    tag_id = serializers.PrimaryKeyRelatedField(
        queryset=DocumentTag.objects.all(),
        source='tag',
        write_only=True
    )
    
    class Meta:
        model = DocumentTagAssignment
        fields = ['document', 'tag', 'tag_id', 'assigned_at']
        read_only_fields = ['assigned_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'role', 'content', 'token_count', 'processing_time_ms',
            'model_used', 'temperature', 'referenced_documents', 'context_used',
            'is_helpful', 'user_rating', 'created_at'
        ]
        read_only_fields = [
            'id', 'token_count', 'processing_time_ms', 'model_used', 'temperature',
            'context_used', 'created_at'
        ]


class ChatSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chat
        fields = [
            'id', 'title', 'is_pinned', 'is_archived', 'message_count',
            'total_tokens_used', 'average_response_time_ms', 'messages',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'message_count', 'total_tokens_used', 'average_response_time_ms',
            'messages', 'created_at', 'updated_at'
        ]