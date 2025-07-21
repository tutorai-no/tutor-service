import uuid
from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Flashcard(models.Model):
    """AI-generated flashcards for spaced repetition learning."""

    DIFFICULTY_LEVELS = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="flashcards"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="flashcards"
    )
    section = models.ForeignKey(
        "courses.CourseSection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="flashcards",
    )

    # Flashcard content
    question = models.TextField(help_text="Front side of the flashcard")
    answer = models.TextField(help_text="Back side of the flashcard")
    explanation = models.TextField(
        blank=True, null=True, help_text="Additional explanation"
    )

    # Metadata
    difficulty_level = models.CharField(
        max_length=10, choices=DIFFICULTY_LEVELS, default="medium"
    )
    tags = models.JSONField(default=list, help_text="Tags for categorization")
    source_content = models.TextField(
        blank=True, null=True, help_text="Source text used to generate this flashcard"
    )

    # Spaced repetition data
    ease_factor = models.FloatField(
        default=2.5,
        validators=[MinValueValidator(1.3), MaxValueValidator(5.0)],
        help_text="Ease factor for spaced repetition algorithm",
    )
    interval_days = models.PositiveIntegerField(
        default=1, help_text="Current interval in days"
    )
    repetitions = models.PositiveIntegerField(
        default=0, help_text="Number of successful repetitions"
    )
    next_review_date = models.DateTimeField(
        default=timezone.now, help_text="Next scheduled review date"
    )

    # Performance tracking
    total_reviews = models.PositiveIntegerField(default=0)
    total_correct = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Success rate (0.0 to 1.0)",
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_starred = models.BooleanField(default=False)

    # AI generation metadata
    generated_by_ai = models.BooleanField(default=True)
    ai_model_used = models.CharField(max_length=100, blank=True, null=True)
    generation_confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "flashcards"
        ordering = ["next_review_date"]
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["next_review_date", "is_active"]),
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["is_starred"]),
        ]

    def __str__(self):
        return f"Flashcard: {self.question[:50]}..."

    @property
    def is_due(self):
        """Check if flashcard is due for review."""
        return self.next_review_date <= timezone.now()

    @property
    def mastery_level(self):
        """Calculate mastery level based on performance."""
        if self.total_reviews == 0:
            return "new"
        elif (
            self.repetitions >= 8
            and self.success_rate >= 0.9
            and self.ease_factor >= 2.5
        ):
            return "mastered"
        elif self.repetitions >= 3 and self.success_rate >= 0.7:
            return "learning"
        elif self.success_rate < 0.5 or self.ease_factor < 2.0:
            return "difficult"
        else:
            return "learning"

    def calculate_next_review(self, quality_response):
        """Calculate next review date based on spaced repetition algorithm."""
        from .services.spaced_repetition import SpacedRepetitionService

        # Use the existing spaced repetition service
        new_ease_factor, new_interval, new_repetitions, next_review_date = (
            SpacedRepetitionService.calculate_next_review(
                current_ease_factor=self.ease_factor,
                current_interval=self.interval_days,
                repetitions=self.repetitions,
                quality_response=quality_response,
            )
        )

        # Update flashcard with new parameters
        self.ease_factor = new_ease_factor
        self.interval_days = new_interval
        self.repetitions = new_repetitions
        self.next_review_date = next_review_date

        # Update performance tracking
        self.total_reviews += 1
        if quality_response >= 3:
            self.total_correct += 1

        # Calculate success rate
        self.success_rate = (
            self.total_correct / self.total_reviews if self.total_reviews > 0 else 0
        )

        self.save()


class FlashcardReview(models.Model):
    """Individual review sessions for flashcards."""

    QUALITY_CHOICES = [
        (0, "Complete blackout"),
        (1, "Incorrect but remembered"),
        (2, "Incorrect but easy"),
        (3, "Correct with difficulty"),
        (4, "Correct with hesitation"),
        (5, "Perfect recall"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flashcard = models.ForeignKey(
        Flashcard, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flashcard_reviews",
    )

    # Review data
    quality_response = models.PositiveSmallIntegerField(
        choices=QUALITY_CHOICES, help_text="Quality of recall (0-5)"
    )
    response_time_seconds = models.PositiveIntegerField(
        null=True, blank=True, help_text="Time taken to respond in seconds"
    )

    # Context
    study_session_id = models.UUIDField(null=True, blank=True)
    device_type = models.CharField(max_length=20, blank=True, null=True)

    # Metadata
    previous_interval_days = models.PositiveIntegerField(null=True, blank=True)
    new_interval_days = models.PositiveIntegerField(null=True, blank=True)
    ease_factor_before = models.FloatField(null=True, blank=True)
    ease_factor_after = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "flashcard_reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["flashcard", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["study_session_id"]),
        ]

    def __str__(self):
        return f"Review: {self.flashcard.question[:30]}... - Quality: {self.quality_response}"


class Quiz(models.Model):
    """AI-generated quizzes for assessment and practice."""

    QUIZ_TYPES = [
        ("practice", "Practice Quiz"),
        ("assessment", "Assessment Quiz"),
        ("review", "Review Quiz"),
        ("diagnostic", "Diagnostic Quiz"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="quizzes"
    )
    section = models.ForeignKey(
        "courses.CourseSection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quizzes",
    )

    # Quiz metadata
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, default="practice")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Configuration
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(default=3)
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Passing score percentage",
    )

    # Settings
    shuffle_questions = models.BooleanField(default=True)
    show_correct_answers = models.BooleanField(default=True)
    show_explanations = models.BooleanField(default=True)
    allow_retakes = models.BooleanField(default=True)

    # AI generation
    generated_by_ai = models.BooleanField(default=True)
    ai_model_used = models.CharField(max_length=100, blank=True, null=True)
    generation_prompt = models.TextField(blank=True, null=True)
    source_content = models.TextField(blank=True, null=True)

    # Statistics
    total_questions = models.PositiveIntegerField(default=0)
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quizzes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["quiz_type", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Quiz: {self.title}"

    @property
    def is_published(self):
        return self.status == "published"

    def get_user_attempts(self, user):
        """Get number of attempts by a specific user."""
        return self.attempts.filter(user=user).count()

    def can_user_attempt(self, user):
        """Check if user can attempt this quiz."""
        if not self.is_published:
            return False
        if not self.allow_retakes and self.get_user_attempts(user) > 0:
            return False
        return self.get_user_attempts(user) < self.max_attempts


class QuizQuestion(models.Model):
    """Individual questions within a quiz."""

    QUESTION_TYPES = [
        ("multiple_choice", "Multiple Choice"),
        ("true_false", "True/False"),
        ("short_answer", "Short Answer"),
        ("essay", "Essay"),
        ("fill_blank", "Fill in the Blank"),
    ]

    DIFFICULTY_LEVELS = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")

    # Question content
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    difficulty_level = models.CharField(
        max_length=10, choices=DIFFICULTY_LEVELS, default="medium"
    )

    # Question configuration
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)

    # Answer options (for multiple choice)
    answer_options = models.JSONField(
        default=list, help_text="List of answer options for multiple choice questions"
    )
    correct_answers = models.JSONField(
        default=list,
        help_text="List of correct answers (indices for MC, text for others)",
    )

    # Additional content
    explanation = models.TextField(blank=True, null=True)
    hint = models.TextField(blank=True, null=True)

    # Metadata
    tags = models.JSONField(default=list)
    source_content = models.TextField(blank=True, null=True)

    # Statistics
    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quiz_questions"
        ordering = ["quiz", "order"]
        indexes = [
            models.Index(fields=["quiz", "order"]),
            models.Index(fields=["question_type", "difficulty_level"]),
        ]

    def __str__(self):
        return f"Question: {self.question_text[:50]}..."

    @property
    def success_rate(self):
        """Calculate success rate for this question."""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_attempts / self.total_attempts

    def is_correct_answer(self, user_answer):
        """Check if user answer is correct."""
        if self.question_type == "multiple_choice":
            return user_answer in self.correct_answers
        elif self.question_type == "true_false":
            return str(user_answer).lower() == str(self.correct_answers[0]).lower()
        elif self.question_type in ["short_answer", "fill_blank"]:
            # Simple text comparison (could be enhanced with NLP)
            user_text = str(user_answer).strip().lower()
            for correct in self.correct_answers:
                if user_text == str(correct).strip().lower():
                    return True
            return False
        else:
            # Essay questions require manual grading
            return None


class QuizAttempt(models.Model):
    """Individual attempts at taking a quiz."""

    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
        ("timed_out", "Timed Out"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )

    # Attempt data
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_progress"
    )
    attempt_number = models.PositiveIntegerField(default=1)

    # Scoring
    score = models.FloatField(null=True, blank=True)
    max_score = models.FloatField(null=True, blank=True)
    percentage_score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)

    # Timing
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Configuration snapshot
    questions_order = models.JSONField(
        default=list, help_text="Order of questions for this attempt"
    )

    # Context
    device_type = models.CharField(max_length=20, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "quiz_attempts"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["quiz", "user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self):
        return (
            f"Attempt {self.attempt_number}: {self.quiz.title} by {self.user.username}"
        )

    def calculate_score(self):
        """Calculate the final score for this attempt."""
        if self.status != "completed":
            return

        total_points = 0
        earned_points = 0

        # Fix N+1 query by prefetching the related question objects
        for response in self.responses.select_related("question").all():
            total_points += response.question.points
            if response.is_correct:
                earned_points += response.question.points

        self.score = earned_points
        self.max_score = total_points
        self.percentage_score = (
            (earned_points / total_points * 100) if total_points > 0 else 0
        )
        self.passed = self.percentage_score >= self.quiz.passing_score
        self.save()

    def complete_attempt(self):
        """Mark attempt as completed and calculate score."""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.time_taken_seconds = int(
            (self.completed_at - self.started_at).total_seconds()
        )
        self.calculate_score()


class QuizResponse(models.Model):
    """Individual responses to quiz questions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="responses"
    )
    question = models.ForeignKey(
        QuizQuestion, on_delete=models.CASCADE, related_name="responses"
    )

    # Response data
    user_answer = models.JSONField(
        help_text="User's answer (format depends on question type)"
    )
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.FloatField(default=0.0)

    # Timing
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    # Review data
    flagged_for_review = models.BooleanField(default=False)

    class Meta:
        db_table = "quiz_responses"
        unique_together = ["attempt", "question"]
        indexes = [
            models.Index(fields=["attempt", "question"]),
            models.Index(fields=["is_correct"]),
        ]

    def __str__(self):
        return f"Response to {self.question.question_text[:30]}..."

    def save(self, *args, **kwargs):
        """Auto-calculate correctness and points on save."""
        if self.is_correct is None:
            self.is_correct = self.question.is_correct_answer(self.user_answer)

        if self.is_correct:
            self.points_earned = self.question.points
        else:
            self.points_earned = 0.0

        super().save(*args, **kwargs)


class Assessment(models.Model):
    """Comprehensive assessments combining multiple evaluation methods."""

    ASSESSMENT_TYPES = [
        ("diagnostic", "Diagnostic Assessment"),
        ("formative", "Formative Assessment"),
        ("summative", "Summative Assessment"),
        ("self_assessment", "Self Assessment"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assessments"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="assessments"
    )

    # Assessment metadata
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Configuration
    include_flashcards = models.BooleanField(default=True)
    include_quizzes = models.BooleanField(default=True)
    flashcard_count = models.PositiveIntegerField(default=10)
    quiz_count = models.PositiveIntegerField(default=1)

    # Adaptive settings
    adaptive_difficulty = models.BooleanField(default=True)
    target_success_rate = models.FloatField(
        default=0.8, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    # Scheduling
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    # Results
    completion_rate = models.FloatField(default=0.0)
    average_performance = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["assessment_type", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"Assessment: {self.title}"

    def generate_content(self):
        """Generate flashcards and quizzes for this assessment."""
        # This would integrate with AI services to generate content
        # For now, this is a placeholder

    def calculate_performance(self):
        """Calculate overall performance metrics."""
        # Aggregate performance from flashcards and quizzes
        flashcard_performance = 0.0
        quiz_performance = 0.0

        # Get related flashcard reviews
        flashcard_reviews = FlashcardReview.objects.filter(
            flashcard__course=self.course, user=self.user
        )

        if flashcard_reviews.exists():
            flashcard_performance = (
                flashcard_reviews.aggregate(avg_quality=models.Avg("quality_response"))[
                    "avg_quality"
                ]
                / 5.0
            )  # Normalize to 0-1

        # Get related quiz attempts
        quiz_attempts = QuizAttempt.objects.filter(
            quiz__course=self.course, user=self.user, status="completed"
        )

        if quiz_attempts.exists():
            quiz_performance = (
                quiz_attempts.aggregate(avg_score=models.Avg("percentage_score"))[
                    "avg_score"
                ]
                / 100.0
            )  # Normalize to 0-1

        # Calculate weighted average
        if self.include_flashcards and self.include_quizzes:
            self.average_performance = (flashcard_performance + quiz_performance) / 2
        elif self.include_flashcards:
            self.average_performance = flashcard_performance
        elif self.include_quizzes:
            self.average_performance = quiz_performance

        self.save()


class StudyStreak(models.Model):
    """Track study streaks for different assessment types."""

    STREAK_TYPES = [
        ("flashcard", "Flashcard Streak"),
        ("quiz", "Quiz Streak"),
        ("assessment", "Assessment Streak"),
        ("overall", "Overall Study Streak"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_streaks"
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="study_streaks",
        null=True,
        blank=True,
    )

    # Streak data
    streak_type = models.CharField(max_length=20, choices=STREAK_TYPES)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)

    # Dates
    streak_start_date = models.DateField(null=True, blank=True)
    last_activity_date = models.DateField(null=True, blank=True)

    # Milestones
    milestones_achieved = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "study_streaks"
        unique_together = ["user", "course", "streak_type"]
        indexes = [
            models.Index(fields=["user", "streak_type"]),
            models.Index(fields=["current_streak"]),
        ]

    def __str__(self):
        course_name = self.course.name if self.course else "All Courses"
        return (
            f"{self.user.username} - {self.get_streak_type_display()} - {course_name}"
        )

    def update_streak(self, activity_date=None):
        """Update streak based on activity."""
        if activity_date is None:
            activity_date = timezone.now().date()

        if self.last_activity_date is None:
            # First activity
            self.current_streak = 1
            self.streak_start_date = activity_date
        elif activity_date == self.last_activity_date:
            # Same day activity, no change
            pass
        elif activity_date == self.last_activity_date + timedelta(days=1):
            # Consecutive day
            self.current_streak += 1
        else:
            # Streak broken
            self.current_streak = 1
            self.streak_start_date = activity_date

        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_activity_date = activity_date
        self.save()

        # Check for milestones
        self.check_milestones()

    def check_milestones(self):
        """Check and record milestone achievements."""
        milestone_levels = [7, 14, 30, 50, 100, 200, 365]

        for level in milestone_levels:
            if self.current_streak >= level and level not in self.milestones_achieved:
                self.milestones_achieved.append(level)

        self.save()
