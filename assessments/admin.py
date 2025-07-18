from django.contrib import admin
from .models import (
    Flashcard,
    FlashcardReview,
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizResponse,
    Assessment,
    StudyStreak,
)


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = [
        'question_preview', 'user', 'course', 'difficulty_level', 
        'mastery_level', 'next_review_date', 'is_active'
    ]
    list_filter = [
        'difficulty_level', 'is_active', 'is_starred', 'generated_by_ai',
        'created_at', 'next_review_date'
    ]
    search_fields = ['question', 'answer', 'user__username', 'course__name']
    readonly_fields = [
        'id', 'total_reviews', 'total_correct', 'success_rate', 
        'mastery_level', 'created_at', 'updated_at'
    ]
    
    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = "Question Preview"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'course', 'section', 'question', 'answer', 'explanation')
        }),
        ('Configuration', {
            'fields': ('difficulty_level', 'tags', 'source_content')
        }),
        ('Spaced Repetition', {
            'fields': ('ease_factor', 'interval_days', 'repetitions', 'next_review_date')
        }),
        ('Performance', {
            'fields': ('total_reviews', 'total_correct', 'success_rate', 'mastery_level')
        }),
        ('Status', {
            'fields': ('is_active', 'is_starred')
        }),
        ('AI Generation', {
            'fields': ('generated_by_ai', 'ai_model_used', 'generation_confidence')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FlashcardReview)
class FlashcardReviewAdmin(admin.ModelAdmin):
    list_display = [
        'flashcard_preview', 'user', 'quality_response', 
        'response_time_seconds', 'created_at'
    ]
    list_filter = ['quality_response', 'created_at']
    search_fields = ['flashcard__question', 'user__username']
    readonly_fields = ['id', 'created_at']
    
    def flashcard_preview(self, obj):
        return obj.flashcard.question[:30] + "..." if len(obj.flashcard.question) > 30 else obj.flashcard.question
    flashcard_preview.short_description = "Flashcard"
    
    fieldsets = (
        ('Review Information', {
            'fields': ('flashcard', 'user', 'quality_response', 'response_time_seconds')
        }),
        ('Context', {
            'fields': ('study_session_id', 'device_type')
        }),
        ('Spaced Repetition Data', {
            'fields': (
                'previous_interval_days', 'new_interval_days', 
                'ease_factor_before', 'ease_factor_after'
            )
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'course', 'quiz_type', 'status', 
        'total_questions', 'average_score', 'created_at'
    ]
    list_filter = [
        'quiz_type', 'status', 'generated_by_ai', 'created_at'
    ]
    search_fields = ['title', 'description', 'user__username', 'course__name']
    readonly_fields = [
        'id', 'total_questions', 'total_attempts', 'average_score',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'course', 'section', 'title', 'description', 'quiz_type')
        }),
        ('Configuration', {
            'fields': (
                'time_limit_minutes', 'max_attempts', 'passing_score',
                'shuffle_questions', 'show_correct_answers', 'show_explanations', 'allow_retakes'
            )
        }),
        ('AI Generation', {
            'fields': ('generated_by_ai', 'ai_model_used', 'generation_prompt', 'source_content')
        }),
        ('Statistics', {
            'fields': ('total_questions', 'total_attempts', 'average_score')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'question_preview', 'quiz', 'question_type', 'difficulty_level',
        'points', 'success_rate', 'total_attempts'
    ]
    list_filter = ['question_type', 'difficulty_level', 'quiz__quiz_type']
    search_fields = ['question_text', 'quiz__title']
    readonly_fields = [
        'id', 'total_attempts', 'correct_attempts', 'success_rate',
        'created_at', 'updated_at'
    ]
    
    def question_preview(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_preview.short_description = "Question Preview"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('quiz', 'question_text', 'question_type', 'difficulty_level')
        }),
        ('Configuration', {
            'fields': ('order', 'points', 'answer_options', 'correct_answers')
        }),
        ('Additional Content', {
            'fields': ('explanation', 'hint', 'tags', 'source_content')
        }),
        ('Statistics', {
            'fields': ('total_attempts', 'correct_attempts', 'success_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'quiz', 'user', 'attempt_number', 'status', 'percentage_score',
        'passed', 'time_taken_seconds', 'started_at'
    ]
    list_filter = ['status', 'passed', 'started_at']
    search_fields = ['quiz__title', 'user__username']
    readonly_fields = [
        'id', 'score', 'max_score', 'percentage_score', 'passed',
        'time_taken_seconds', 'started_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('quiz', 'user', 'attempt_number', 'status')
        }),
        ('Scoring', {
            'fields': ('score', 'max_score', 'percentage_score', 'passed')
        }),
        ('Timing', {
            'fields': ('time_taken_seconds', 'started_at', 'completed_at')
        }),
        ('Configuration', {
            'fields': ('questions_order',)
        }),
        ('Context', {
            'fields': ('device_type', 'ip_address', 'user_agent')
        }),
    )


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = [
        'attempt', 'question_preview', 'is_correct', 'points_earned',
        'time_taken_seconds', 'answered_at'
    ]
    list_filter = ['is_correct', 'flagged_for_review', 'answered_at']
    search_fields = ['attempt__quiz__title', 'question__question_text']
    readonly_fields = ['id', 'answered_at']
    
    def question_preview(self, obj):
        return obj.question.question_text[:30] + "..." if len(obj.question.question_text) > 30 else obj.question.question_text
    question_preview.short_description = "Question"
    
    fieldsets = (
        ('Response Information', {
            'fields': ('attempt', 'question', 'user_answer', 'is_correct', 'points_earned')
        }),
        ('Timing', {
            'fields': ('time_taken_seconds', 'answered_at')
        }),
        ('Review', {
            'fields': ('flagged_for_review',)
        }),
    )


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'course', 'assessment_type', 'status',
        'completion_rate', 'average_performance', 'due_date'
    ]
    list_filter = ['assessment_type', 'status', 'created_at']
    search_fields = ['title', 'description', 'user__username', 'course__name']
    readonly_fields = [
        'id', 'completion_rate', 'average_performance', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'course', 'title', 'description', 'assessment_type')
        }),
        ('Configuration', {
            'fields': (
                'include_flashcards', 'include_quizzes', 'flashcard_count', 'quiz_count'
            )
        }),
        ('Adaptive Settings', {
            'fields': ('adaptive_difficulty', 'target_success_rate')
        }),
        ('Scheduling', {
            'fields': ('due_date', 'estimated_duration_minutes')
        }),
        ('Results', {
            'fields': ('completion_rate', 'average_performance')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudyStreak)
class StudyStreakAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'course', 'streak_type', 'current_streak', 
        'longest_streak', 'last_activity_date'
    ]
    list_filter = ['streak_type', 'last_activity_date']
    search_fields = ['user__username', 'course__name']
    readonly_fields = [
        'id', 'milestones_achieved', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Streak Information', {
            'fields': ('user', 'course', 'streak_type')
        }),
        ('Streak Data', {
            'fields': ('current_streak', 'longest_streak', 'streak_start_date', 'last_activity_date')
        }),
        ('Milestones', {
            'fields': ('milestones_achieved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )