"""
Learning models for study planning and progress tracking.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel
import uuid

User = get_user_model()


class StudyPlan(BaseModel):
    """
    AI-generated study plan for a user's course.
    """
    
    PLAN_TYPES = [
        ('weekly', 'Weekly Plan'),
        ('monthly', 'Monthly Plan'),
        ('exam_prep', 'Exam Preparation'),
        ('custom', 'Custom Plan'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='study_plans')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Plan scheduling
    start_date = models.DateField()
    end_date = models.DateField()
    target_exam_date = models.DateField(null=True, blank=True)
    
    # Plan configuration
    daily_study_hours = models.DecimalField(
        max_digits=3, decimal_places=1, 
        validators=[MinValueValidator(0.5), MaxValueValidator(12.0)]
    )
    study_days_per_week = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    
    # AI-generated plan data
    plan_data = models.JSONField(
        default=dict,
        help_text="AI-generated plan structure with tasks and schedules"
    )
    
    # Progress tracking
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'study_plans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @property
    def progress_percentage(self):
        """Calculate completion percentage."""
        if self.total_tasks == 0:
            return 0
        return (self.completed_tasks / self.total_tasks) * 100

    @property
    def is_active(self):
        """Check if plan is currently active."""
        return (
            self.status == 'active' and
            self.start_date <= timezone.now().date() <= self.end_date
        )


class StudySession(BaseModel):
    """
    Individual study session tracked by user.
    """
    
    SESSION_TYPES = [
        ('planned', 'Planned Session'),
        ('spontaneous', 'Spontaneous Study'),
        ('review', 'Review Session'),
        ('practice', 'Practice Session'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='study_sessions')
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Session scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Session content
    topics = models.JSONField(
        default=list,
        help_text="List of topics to cover in this session"
    )
    materials = models.JSONField(
        default=list,
        help_text="List of materials/documents for this session"
    )
    
    # Session outcome
    completion_notes = models.TextField(blank=True)
    satisfaction_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    productivity_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Progress tracking
    objectives_completed = models.PositiveIntegerField(default=0)
    total_objectives = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'study_sessions'
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_start']),
            models.Index(fields=['study_plan']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.scheduled_start.date()})"

    @property
    def duration_planned(self):
        """Planned duration in minutes."""
        if self.scheduled_end and self.scheduled_start:
            return int((self.scheduled_end - self.scheduled_start).total_seconds() / 60)
        return 0

    @property
    def duration_actual(self):
        """Actual duration in minutes."""
        if self.actual_end and self.actual_start:
            return int((self.actual_end - self.actual_start).total_seconds() / 60)
        return 0

    def start_session(self):
        """Mark session as started."""
        self.status = 'in_progress'
        self.actual_start = timezone.now()
        self.save()

    def complete_session(self, notes="", satisfaction=None, productivity=None):
        """Mark session as completed."""
        self.status = 'completed'
        self.actual_end = timezone.now()
        if notes:
            self.completion_notes = notes
        if satisfaction:
            self.satisfaction_rating = satisfaction
        if productivity:
            self.productivity_rating = productivity
        self.save()


class LearningProgress(BaseModel):
    """
    Track learning progress for a user across different dimensions.
    """
    
    PROGRESS_TYPES = [
        ('course', 'Course Progress'),
        ('topic', 'Topic Progress'),
        ('skill', 'Skill Progress'),
        ('objective', 'Learning Objective Progress'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_progress')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='learning_progress')
    
    progress_type = models.CharField(max_length=20, choices=PROGRESS_TYPES)
    identifier = models.CharField(max_length=200, help_text="Topic name, skill identifier, etc.")
    
    # Progress metrics
    completion_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    mastery_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
        help_text="1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert"
    )
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    # Time tracking
    total_study_time = models.DurationField(default=timezone.timedelta)
    last_studied = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    quiz_average = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    flashcard_retention = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional progress data and analytics"
    )

    class Meta:
        db_table = 'learning_progress'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['progress_type']),
            models.Index(fields=['completion_percentage']),
            models.Index(fields=['mastery_level']),
        ]
        unique_together = [['user', 'course', 'progress_type', 'identifier']]

    def __str__(self):
        return f"{self.user.username} - {self.identifier} ({self.completion_percentage}%)"

    def update_progress(self, completion_delta=0, time_spent=None, performance_data=None):
        """Update progress metrics."""
        if completion_delta:
            self.completion_percentage = min(100, self.completion_percentage + completion_delta)
        
        if time_spent:
            self.total_study_time += time_spent
            self.last_studied = timezone.now()
        
        if performance_data:
            self.metadata.update(performance_data)
        
        self.save()


class StudyGoal(BaseModel):
    """
    User-defined or AI-suggested study goals.
    """
    
    GOAL_TYPES = [
        ('daily', 'Daily Goal'),
        ('weekly', 'Weekly Goal'),
        ('monthly', 'Monthly Goal'),
        ('milestone', 'Milestone Goal'),
        ('exam', 'Exam Goal'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_goals')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='learning_goals', null=True, blank=True)
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='goals', null=True, blank=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Goal parameters
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=50, help_text="minutes, pages, flashcards, etc.")
    
    # Goal timing
    start_date = models.DateField()
    target_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # AI assistance
    is_ai_suggested = models.BooleanField(default=False)
    ai_rationale = models.TextField(blank=True, help_text="AI explanation for suggested goal")
    
    # Progress tracking
    streak_count = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    last_progress_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'study_goals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['status']),
            models.Index(fields=['goal_type']),
            models.Index(fields=['target_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @property
    def progress_percentage(self):
        """Calculate goal completion percentage."""
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)

    @property
    def is_overdue(self):
        """Check if goal is overdue."""
        return (
            self.status == 'active' and
            self.target_date < timezone.now().date() and
            self.current_value < self.target_value
        )

    def update_progress(self, value_delta):
        """Update goal progress."""
        self.current_value += value_delta
        
        # Update streak
        today = timezone.now().date()
        if self.last_progress_date != today:
            if self.last_progress_date == today - timezone.timedelta(days=1):
                self.streak_count += 1
            else:
                self.streak_count = 1
            self.best_streak = max(self.best_streak, self.streak_count)
            self.last_progress_date = today
        
        # Check if goal is completed
        if self.current_value >= self.target_value and self.status == 'active':
            self.status = 'completed'
            self.completed_date = today
        
        self.save()


class StudyRecommendation(BaseModel):
    """
    AI-generated study recommendations for users.
    """
    
    RECOMMENDATION_TYPES = [
        ('study_plan', 'Study Plan Recommendation'),
        ('session_schedule', 'Session Schedule Recommendation'),
        ('material_priority', 'Material Priority Recommendation'),
        ('review_timing', 'Review Timing Recommendation'),
        ('goal_adjustment', 'Goal Adjustment Recommendation'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('dismissed', 'Dismissed'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_recommendations')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='study_recommendations', null=True, blank=True)
    
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    rationale = models.TextField(help_text="AI explanation for this recommendation")
    
    # Recommendation data
    recommendation_data = models.JSONField(
        default=dict,
        help_text="Structured data for the recommendation"
    )
    
    # Timing
    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback
    user_feedback = models.TextField(blank=True)
    effectiveness_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        db_table = 'study_recommendations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['recommendation_type']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def accept(self):
        """Accept the recommendation."""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()

    def dismiss(self, feedback=""):
        """Dismiss the recommendation."""
        self.status = 'dismissed'
        self.dismissed_at = timezone.now()
        if feedback:
            self.user_feedback = feedback
        self.save()

    @property
    def is_expired(self):
        """Check if recommendation has expired."""
        return (
            self.expires_at and
            self.expires_at < timezone.now() and
            self.status == 'pending'
        )