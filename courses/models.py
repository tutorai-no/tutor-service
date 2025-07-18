import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Course(models.Model):
    """User courses/subjects."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="courses"
    )
    
    # Basic course information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Academic context
    university = models.CharField(max_length=200, blank=True, null=True)
    course_code = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="e.g., CS101, MATH201"
    )
    semester = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="e.g., Fall 2024, Spring 2025"
    )
    academic_year = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="e.g., 2024-2025"
    )
    credits = models.PositiveSmallIntegerField(null=True, blank=True)
    
    # Course metadata
    language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('no', 'Norwegian'),
        ('sv', 'Swedish'),
        ('da', 'Danish'),
    ])
    subject_area = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="e.g., Computer Science, Mathematics, Biology"
    )
    difficulty_level = models.PositiveSmallIntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Beginner, 5=Advanced"
    )
    
    # Visual customization
    color = models.CharField(
        max_length=7, default='#3B82F6', 
        help_text="Hex color for UI representation"
    )
    icon = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Icon name for UI representation"
    )
    
    # Learning configuration
    study_goals = models.JSONField(
        default=list, 
        help_text="List of learning objectives"
    )
    preferred_study_methods = models.JSONField(
        default=list, 
        help_text="Preferred learning tools (flashcards, quizzes, etc.)"
    )
    
    # Important dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    exam_date = models.DateTimeField(null=True, blank=True)
    
    # Course status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    # Statistics (computed fields)
    total_documents = models.PositiveIntegerField(default=0)
    total_study_hours = models.PositiveIntegerField(default=0, help_text="Minutes")
    completion_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['-is_favorite', 'name']
        unique_together = ['user', 'name', 'semester']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['course_code']),
            models.Index(fields=['subject_area']),
            models.Index(fields=['exam_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def display_name(self):
        """Get formatted course name with code."""
        if self.course_code:
            return f"{self.course_code} - {self.name}"
        return self.name

    @property
    def days_until_exam(self):
        """Calculate days until exam."""
        if not self.exam_date:
            return None
        
        from datetime import date
        exam_date = self.exam_date.date()
        today = date.today()
        return (exam_date - today).days

    @property
    def is_exam_soon(self):
        """Check if exam is within 2 weeks."""
        days = self.days_until_exam
        return days is not None and 0 <= days <= 14


class CourseSection(models.Model):
    """Course sections/chapters for better organization."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name="sections"
    )
    
    # Section information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Organization
    order = models.PositiveIntegerField(
        help_text="Display order within course"
    )
    
    # Academic context
    chapter_number = models.PositiveIntegerField(null=True, blank=True)
    page_range_start = models.PositiveIntegerField(null=True, blank=True)
    page_range_end = models.PositiveIntegerField(null=True, blank=True)
    
    # Section content
    learning_objectives = models.JSONField(
        default=list,
        help_text="List of learning objectives for this section"
    )
    key_concepts = models.JSONField(
        default=list,
        help_text="Key concepts covered in this section"
    )
    
    # Progress tracking
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    
    # Estimated study time (in minutes)
    estimated_study_time = models.PositiveIntegerField(
        default=60,
        help_text="Estimated study time in minutes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_sections'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        indexes = [
            models.Index(fields=['course', 'order']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Document(models.Model):
    """User uploaded documents (files, URLs, videos)."""
    
    DOCUMENT_TYPES = [
        ('file', 'File Upload'),
        ('url', 'URL/Link'),
        ('video', 'Video'),
        ('text', 'Text Input'),
        ('audio', 'Audio File'),
    ]
    
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="documents"
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name="documents"
    )
    section = models.ForeignKey(
        CourseSection, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="documents"
    )
    
    # Basic document information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    
    # File details (for file uploads)
    file_url = models.URLField(max_length=1024, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    
    # URL details (for links and videos)
    source_url = models.URLField(max_length=1024, blank=True)
    
    # Media details
    thumbnail_url = models.URLField(max_length=1024, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Content analysis
    page_count = models.PositiveIntegerField(null=True, blank=True)
    word_count = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, blank=True)
    
    # Processing status
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS, 
        default='pending'
    )
    processing_error = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # External storage
    storage_path = models.CharField(
        max_length=1024, blank=True, 
        help_text="Path in cloud storage"
    )
    
    # Content metadata
    extracted_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    topics = models.JSONField(
        default=list,
        help_text="Automatically extracted topics"
    )
    
    # Usage statistics
    view_count = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    # Document status
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['document_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_favorite', 'is_archived']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"

    @property
    def file_size_mb(self):
        """Get file size in MB."""
        if self.file_size_bytes:
            return round(self.file_size_bytes / (1024 * 1024), 2)
        return 0

    @property
    def is_processed(self):
        """Check if document processing is completed."""
        return self.processing_status == 'completed'


class DocumentTag(models.Model):
    """Tags for organizing documents."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="document_tags"
    )
    
    name = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7, default='#6B7280',
        help_text="Hex color for tag display"
    )
    description = models.TextField(blank=True, null=True)
    
    # Usage statistics
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_tags'
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class DocumentTagAssignment(models.Model):
    """Many-to-many relationship between documents and tags."""
    
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        related_name="tag_assignments"
    )
    tag = models.ForeignKey(
        DocumentTag, 
        on_delete=models.CASCADE, 
        related_name="document_assignments"
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_tag_assignments'
        unique_together = ['document', 'tag']

    def __str__(self):
        return f"{self.document.name} - {self.tag.name}"


class Chat(models.Model):
    """Chat conversations with AI tutor."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="chats"
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name="chats", 
        null=True, blank=True
    )
    
    # Chat information
    title = models.CharField(max_length=255)
    
    # Chat metadata
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    message_count = models.PositiveIntegerField(default=0)
    
    # Performance tracking
    total_tokens_used = models.PositiveIntegerField(default=0)
    average_response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chats'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['is_pinned', 'is_archived']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"Chat: {self.title} ({self.user.username})"


class ChatMessage(models.Model):
    """Individual messages in chat conversations."""
    
    MESSAGE_ROLES = [
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat, 
        on_delete=models.CASCADE, 
        related_name="messages"
    )
    
    # Message content
    role = models.CharField(max_length=10, choices=MESSAGE_ROLES)
    content = models.TextField()
    
    # Message metadata
    token_count = models.PositiveIntegerField(null=True, blank=True)
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # AI model information (for assistant messages)
    model_used = models.CharField(max_length=50, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    
    # References and context
    referenced_documents = models.ManyToManyField(
        Document, 
        blank=True, 
        related_name="chat_references"
    )
    context_used = models.TextField(
        blank=True,
        help_text="Context that was provided to the AI"
    )
    
    # User interaction
    is_helpful = models.BooleanField(null=True, blank=True)
    user_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['role']),
            models.Index(fields=['is_helpful']),
        ]

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."