"""
Document processing models.
"""

import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ProcessingStatus(models.TextChoices):
    """Document processing status choices."""

    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"



class DocumentChunk(models.Model):
    """
    Model for storing document text chunks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        "courses.Document", on_delete=models.CASCADE, related_name="chunks"
    )

    # Chunk information
    chunk_index = models.PositiveIntegerField()  # Order within document
    text_content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)

    # Metadata
    page_numbers = models.JSONField(
        default=list, blank=True
    )  # Which pages this chunk spans
    metadata = models.JSONField(
        default=dict, blank=True
    )  # Additional metadata from extraction

    # Embedding information
    has_embedding = models.BooleanField(default=False)
    embedding_model = models.CharField(max_length=100, blank=True)

    # Knowledge graph processing
    graph_extracted = models.BooleanField(default=False)
    nodes_count = models.PositiveIntegerField(default=0)
    edges_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document_chunks"
        ordering = ["document", "chunk_index"]
        unique_together = [["document", "chunk_index"]]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
            models.Index(fields=["has_embedding"]),
            models.Index(fields=["graph_extracted"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.original_filename}"


class URLUpload(models.Model):
    """
    Model for tracking URL uploads and processing.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="url_uploads")
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="url_uploads",
        null=True,
        blank=True,
    )

    # URL information
    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=500, blank=True)
    domain = models.CharField(max_length=255, blank=True)

    # Processing information
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Extracted content metadata
    total_chunks = models.PositiveIntegerField(default=0)
    processed_chunks = models.PositiveIntegerField(default=0)
    content_length = models.PositiveIntegerField(default=0)

    # Knowledge graph information
    graph_id = models.CharField(max_length=100, db_index=True, blank=True)
    total_nodes = models.PositiveIntegerField(default=0)
    total_edges = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "url_uploads"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["course", "status"]),
            models.Index(fields=["graph_id"]),
            models.Index(fields=["domain"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.url} - {self.status}"

    @property
    def processing_progress(self) -> float:
        """Calculate processing progress percentage."""
        if self.total_chunks == 0:
            return 0.0
        return (self.processed_chunks / self.total_chunks) * 100


class URLChunk(models.Model):
    """
    Model for storing URL content chunks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url_upload = models.ForeignKey(
        URLUpload, on_delete=models.CASCADE, related_name="chunks"
    )

    # Chunk information
    chunk_index = models.PositiveIntegerField()  # Order within content
    text_content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)

    # Metadata
    metadata = models.JSONField(
        default=dict, blank=True
    )  # Additional metadata from scraping

    # Embedding information
    has_embedding = models.BooleanField(default=False)
    embedding_model = models.CharField(max_length=100, blank=True)

    # Knowledge graph processing
    graph_extracted = models.BooleanField(default=False)
    nodes_count = models.PositiveIntegerField(default=0)
    edges_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "url_chunks"
        ordering = ["url_upload", "chunk_index"]
        unique_together = [["url_upload", "chunk_index"]]
        indexes = [
            models.Index(fields=["url_upload", "chunk_index"]),
            models.Index(fields=["has_embedding"]),
            models.Index(fields=["graph_extracted"]),
        ]

    def __str__(self):
        return f"URL Chunk {self.chunk_index} of {self.url_upload.url}"


class ProcessingJob(models.Model):
    """
    Model for tracking background processing jobs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Job information
    job_type = models.CharField(max_length=50)  # 'document_upload', 'url_upload', etc.
    content_object_id = models.UUIDField()  # ID of the related object
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="processing_jobs"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Progress tracking
    total_steps = models.PositiveIntegerField(default=0)
    completed_steps = models.PositiveIntegerField(default=0)
    current_step_description = models.CharField(max_length=200, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "processing_jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["job_type", "status"]),
            models.Index(fields=["content_object_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.job_type} job - {self.status}"

    @property
    def progress_percentage(self) -> float:
        """Calculate job progress percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100
