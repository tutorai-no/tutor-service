from django.db import models
from django.utils import timezone
from rest_framework import serializers
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


class FlashcardSerializer(serializers.ModelSerializer):
    mastery_level = serializers.CharField(read_only=True)
    is_due = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Flashcard
        fields = [
            'id', 'course', 'section', 'question', 'answer', 'explanation', 'difficulty_level',
            'tags', 'source_content', 'ease_factor', 'interval_days',
            'repetitions', 'next_review_date', 'total_reviews', 'total_correct',
            'success_rate', 'is_active', 'is_starred', 'generated_by_ai',
            'ai_model_used', 'generation_confidence', 'mastery_level', 'is_due',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'ease_factor', 'interval_days', 'repetitions', 'next_review_date',
            'total_reviews', 'total_correct', 'success_rate', 'generated_by_ai',
            'ai_model_used', 'generation_confidence', 'mastery_level', 'is_due',
            'created_at', 'updated_at'
        ]


class FlashcardReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashcardReview
        fields = [
            'id', 'flashcard', 'quality_response', 'response_time_seconds',
            'study_session_id', 'device_type', 'previous_interval_days',
            'new_interval_days', 'ease_factor_before', 'ease_factor_after',
            'created_at'
        ]
        read_only_fields = [
            'id', 'previous_interval_days', 'new_interval_days',
            'ease_factor_before', 'ease_factor_after', 'created_at'
        ]
    
    def create(self, validated_data):
        """Create review and update flashcard using spaced repetition."""
        flashcard = validated_data['flashcard']
        quality_response = validated_data['quality_response']
        
        # Store previous values
        validated_data['previous_interval_days'] = flashcard.interval_days
        validated_data['ease_factor_before'] = flashcard.ease_factor
        
        # Create review
        review = super().create(validated_data)
        
        # Update flashcard stats
        flashcard.total_reviews += 1
        if quality_response >= 3:
            flashcard.total_correct += 1
        flashcard.success_rate = flashcard.total_correct / flashcard.total_reviews
        
        # Calculate next review using spaced repetition
        flashcard.calculate_next_review(quality_response)
        
        # Store new values
        review.new_interval_days = flashcard.interval_days
        review.ease_factor_after = flashcard.ease_factor
        review.save()
        
        return review


class QuizQuestionSerializer(serializers.ModelSerializer):
    success_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'question_text', 'question_type', 'difficulty_level',
            'order', 'points', 'answer_options', 'correct_answers',
            'explanation', 'hint', 'tags', 'source_content',
            'total_attempts', 'correct_attempts', 'success_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_attempts', 'correct_attempts', 'success_rate',
            'created_at', 'updated_at'
        ]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'course', 'section', 'title', 'description', 'quiz_type', 'status',
            'time_limit_minutes', 'max_attempts', 'passing_score',
            'shuffle_questions', 'show_correct_answers', 'show_explanations',
            'allow_retakes', 'generated_by_ai', 'ai_model_used',
            'generation_prompt', 'source_content', 'total_questions',
            'total_attempts', 'average_score', 'questions', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_questions', 'total_attempts', 'average_score',
            'generated_by_ai', 'ai_model_used', 'questions', 'is_published',
            'created_at', 'updated_at'
        ]


class QuizResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResponse
        fields = [
            'id', 'question', 'user_answer', 'is_correct', 'points_earned',
            'time_taken_seconds', 'flagged_for_review', 'answered_at'
        ]
        read_only_fields = [
            'id', 'is_correct', 'points_earned', 'answered_at'
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    responses = QuizResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'status', 'attempt_number', 'score', 'max_score',
            'percentage_score', 'passed', 'time_taken_seconds', 'started_at',
            'completed_at', 'questions_order', 'device_type', 'ip_address',
            'user_agent', 'responses'
        ]
        read_only_fields = [
            'id', 'attempt_number', 'score', 'max_score', 'percentage_score',
            'passed', 'time_taken_seconds', 'started_at', 'completed_at',
            'responses'
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'assessment_type', 'status',
            'include_flashcards', 'include_quizzes', 'flashcard_count',
            'quiz_count', 'adaptive_difficulty', 'target_success_rate',
            'due_date', 'estimated_duration_minutes', 'completion_rate',
            'average_performance', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'completion_rate', 'average_performance', 'created_at', 'updated_at'
        ]


class StudyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyStreak
        fields = [
            'id', 'streak_type', 'current_streak', 'longest_streak',
            'streak_start_date', 'last_activity_date', 'milestones_achieved',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_streak', 'longest_streak', 'streak_start_date',
            'last_activity_date', 'milestones_achieved', 'created_at', 'updated_at'
        ]


# Specialized serializers for different use cases

class FlashcardReviewSessionSerializer(serializers.ModelSerializer):
    """Serializer for flashcard review sessions with minimal data."""
    
    class Meta:
        model = Flashcard
        fields = [
            'id', 'question', 'answer', 'explanation', 'difficulty_level',
            'is_starred', 'mastery_level'
        ]
        read_only_fields = ['id', 'mastery_level']


class QuizTakingSerializer(serializers.ModelSerializer):
    """Serializer for taking quizzes (excludes correct answers)."""
    
    questions = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'time_limit_minutes', 'passing_score',
            'shuffle_questions', 'questions'
        ]
        read_only_fields = ['id']
    
    def get_questions(self, obj):
        """Get questions without correct answers for quiz taking."""
        questions = obj.questions.all()
        return [
            {
                'id': q.id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'answer_options': q.answer_options,
                'hint': q.hint,
                'points': q.points,
                'order': q.order,
            }
            for q in questions
        ]


class QuizResultSerializer(serializers.ModelSerializer):
    """Serializer for quiz results with correct answers and explanations."""
    
    questions = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'passing_score', 'show_correct_answers',
            'show_explanations', 'questions'
        ]
        read_only_fields = ['id']
    
    def get_questions(self, obj):
        """Get questions with correct answers and explanations."""
        questions = obj.questions.all()
        return [
            {
                'id': q.id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'answer_options': q.answer_options,
                'correct_answers': q.correct_answers,
                'explanation': q.explanation,
                'points': q.points,
                'order': q.order,
            }
            for q in questions
        ]


class FlashcardStatsSerializer(serializers.ModelSerializer):
    """Serializer for flashcard statistics and analytics."""
    
    class Meta:
        model = Flashcard
        fields = [
            'id', 'question', 'difficulty_level', 'mastery_level',
            'total_reviews', 'total_correct', 'success_rate',
            'ease_factor', 'interval_days', 'repetitions',
            'next_review_date', 'created_at'
        ]
        read_only_fields = ['id']


class AssessmentStatsSerializer(serializers.ModelSerializer):
    """Serializer for assessment statistics and progress."""
    
    flashcard_stats = serializers.SerializerMethodField()
    quiz_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'assessment_type', 'completion_rate',
            'average_performance', 'flashcard_stats', 'quiz_stats',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id']
    
    def get_flashcard_stats(self, obj):
        """Get flashcard statistics for this assessment."""
        if not obj.include_flashcards:
            return None
        
        flashcards = Flashcard.objects.filter(
            course=obj.course,
            user=obj.user,
            is_active=True
        )
        
        return {
            'total_flashcards': flashcards.count(),
            'due_flashcards': flashcards.filter(next_review_date__lte=timezone.now()).count(),
            'mastered_flashcards': len([f for f in flashcards if f.mastery_level == 'mastered']),
            'average_success_rate': flashcards.aggregate(avg_rate=models.Avg('success_rate'))['avg_rate'] or 0,
        }
    
    def get_quiz_stats(self, obj):
        """Get quiz statistics for this assessment."""
        if not obj.include_quizzes:
            return None
        
        attempts = QuizAttempt.objects.filter(
            quiz__course=obj.course,
            user=obj.user,
            status='completed'
        )
        
        return {
            'total_attempts': attempts.count(),
            'passed_attempts': attempts.filter(passed=True).count(),
            'average_score': attempts.aggregate(avg_score=models.Avg('percentage_score'))['avg_score'] or 0,
            'best_score': attempts.aggregate(max_score=models.Max('percentage_score'))['max_score'] or 0,
        }