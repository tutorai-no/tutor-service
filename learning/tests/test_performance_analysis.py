"""
Tests for PerformanceAnalysisService.
"""

from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from learning.services.performance_analysis import PerformanceAnalysisService
from learning.models import StudySession, LearningProgress
from assessments.models import Quiz, QuizAttempt, Flashcard, FlashcardReview
from courses.models import Course

User = get_user_model()


class TestPerformanceAnalysisService(TestCase):
    """Test cases for PerformanceAnalysisService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.course = Course.objects.create(
            name='Test Course',
            description='A test course',
            user=self.user
        )
        
        self.service = PerformanceAnalysisService()
        
        # Create test learning progress
        self.progress = LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type='topic',
            identifier='Django Models',
            mastery_level=3,
            completion_percentage=75.0
        )
        
        # Create test study session
        self.study_session = StudySession.objects.create(
            user=self.user,
            course=self.course,
            title='Django Practice',
            duration_minutes=60,
            completed=True
        )
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        self.assertIsInstance(self.service, PerformanceAnalysisService)
    
    def test_analyze_adaptive_performance_success(self):
        """Test successful performance analysis."""
        result = self.service.analyze_adaptive_performance(
            user=self.user,
            course=self.course,
            days=30
        )
        
        self.assertTrue(result['success'])
        self.assertIn('overall_score', result)
        self.assertIn('performance_category', result)
        self.assertIn('detailed_analysis', result)
        self.assertIn('trends', result)
        self.assertIn('recommendations', result)
        
        # Check overall score is in valid range
        self.assertGreaterEqual(result['overall_score'], 0)
        self.assertLessEqual(result['overall_score'], 100)
        
        # Check performance category is valid
        valid_categories = ['Excellent', 'Good', 'Average', 'Needs Improvement', 'Poor']
        self.assertIn(result['performance_category'], valid_categories)
    
    def test_analyze_quiz_performance(self):
        """Test quiz performance analysis."""
        # Create test quiz and attempts
        quiz = Quiz.objects.create(
            title='Test Quiz',
            course=self.course,
            user=self.user
        )
        
        # Create quiz attempts with different scores
        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=85,
            time_taken=300,
            completed=True
        )
        
        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=92,
            time_taken=280,
            completed=True
        )
        
        analysis = self.service._analyze_quiz_performance(self.user, self.course, days=30)
        
        self.assertIn('average_score', analysis)
        self.assertIn('total_attempts', analysis)
        self.assertIn('completion_rate', analysis)
        self.assertIn('improvement_trend', analysis)
        self.assertIn('time_efficiency', analysis)
        
        # Check calculated values
        self.assertEqual(analysis['total_attempts'], 2)
        self.assertEqual(analysis['average_score'], 88.5)  # (85 + 92) / 2
        self.assertEqual(analysis['completion_rate'], 100.0)  # Both completed
    
    def test_analyze_study_sessions(self):
        """Test study session analysis."""
        # Create additional study sessions
        StudySession.objects.create(
            user=self.user,
            course=self.course,
            title='Django Views',
            duration_minutes=45,
            completed=True
        )
        
        StudySession.objects.create(
            user=self.user,
            course=self.course,
            title='Django Templates',
            duration_minutes=90,
            completed=False
        )
        
        analysis = self.service._analyze_study_sessions(self.user, self.course, days=30)
        
        self.assertIn('total_sessions', analysis)
        self.assertIn('completion_rate', analysis)
        self.assertIn('average_duration', analysis)
        self.assertIn('consistency_score', analysis)
        self.assertIn('total_study_time', analysis)
        
        # Check calculated values
        self.assertEqual(analysis['total_sessions'], 3)
        self.assertEqual(analysis['completion_rate'], 66.7)  # 2/3 completed
        self.assertEqual(analysis['total_study_time'], 195)  # 60 + 45 + 90
    
    def test_analyze_learning_progress(self):
        """Test learning progress analysis."""
        # Create additional progress entries
        LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type='topic',
            identifier='Django Views',
            mastery_level=4,
            completion_percentage=85.0
        )
        
        LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type='topic',
            identifier='Django Templates',
            mastery_level=2,
            completion_percentage=40.0
        )
        
        analysis = self.service._analyze_learning_progress(self.user, self.course)
        
        self.assertIn('topics_mastered', analysis)
        self.assertIn('average_mastery_level', analysis)
        self.assertIn('completion_percentage', analysis)
        self.assertIn('learning_velocity', analysis)
        
        # Check calculated values
        self.assertEqual(analysis['topics_mastered'], 1)  # Only level 4+ is mastered
        self.assertEqual(analysis['average_mastery_level'], 3.0)  # (3+4+2)/3
        self.assertEqual(analysis['completion_percentage'], 66.7)  # (75+85+40)/3
    
    def test_analyze_flashcard_retention(self):
        """Test flashcard retention analysis."""
        # Create test flashcard
        flashcard = Flashcard.objects.create(
            user=self.user,
            course=self.course,
            front='What is Django?',
            back='A Python web framework'
        )
        
        # Create flashcard reviews
        FlashcardReview.objects.create(
            user=self.user,
            flashcard=flashcard,
            difficulty='easy',
            response_time=3
        )
        
        FlashcardReview.objects.create(
            user=self.user,
            flashcard=flashcard,
            difficulty='medium',
            response_time=5
        )
        
        analysis = self.service._analyze_flashcard_retention(self.user, self.course, days=30)
        
        self.assertIn('total_reviews', analysis)
        self.assertIn('retention_rate', analysis)
        self.assertIn('average_response_time', analysis)
        self.assertIn('difficulty_distribution', analysis)
        
        # Check calculated values
        self.assertEqual(analysis['total_reviews'], 2)
        self.assertEqual(analysis['average_response_time'], 4.0)  # (3+5)/2
    
    def test_calculate_trends(self):
        """Test trend calculation."""
        # Create data points for trend analysis
        data_points = [
            {'date': '2024-01-01', 'score': 70},
            {'date': '2024-01-02', 'score': 75},
            {'date': '2024-01-03', 'score': 80},
            {'date': '2024-01-04', 'score': 85},
        ]
        
        trend = self.service._calculate_trend(data_points, 'score')
        
        self.assertIn('trend', trend)
        self.assertIn('slope', trend)
        self.assertIn('direction', trend)
        
        # Should detect upward trend
        self.assertEqual(trend['direction'], 'Improving')
        self.assertGreater(trend['slope'], 0)
    
    def test_generate_performance_recommendations(self):
        """Test performance recommendation generation."""
        performance_data = {
            'quiz_performance': {'average_score': 65, 'improvement_trend': 'Declining'},
            'study_sessions': {'completion_rate': 50, 'consistency_score': 0.3},
            'learning_progress': {'average_mastery_level': 2.5},
            'flashcard_retention': {'retention_rate': 60}
        }
        
        recommendations = self.service._generate_performance_recommendations(performance_data)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check recommendation structure
        first_rec = recommendations[0]
        self.assertIn('title', first_rec)
        self.assertIn('description', first_rec)
        self.assertIn('priority', first_rec)
        self.assertIn('type', first_rec)
        self.assertIn('action_items', first_rec)
    
    def test_categorize_performance(self):
        """Test performance categorization."""
        test_cases = [
            (95, 'Excellent'),
            (85, 'Good'),
            (75, 'Average'),
            (65, 'Needs Improvement'),
            (45, 'Poor')
        ]
        
        for score, expected_category in test_cases:
            category = self.service._categorize_performance(score)
            self.assertEqual(category, expected_category)
    
    def test_calculate_consistency_score(self):
        """Test consistency score calculation."""
        # Test with consistent study pattern
        consistent_sessions = [
            timezone.now() - timedelta(days=1),
            timezone.now() - timedelta(days=2),
            timezone.now() - timedelta(days=3),
            timezone.now() - timedelta(days=4),
        ]
        
        consistency = self.service._calculate_consistency_score(consistent_sessions)
        self.assertGreater(consistency, 0.8)  # Should be high consistency
        
        # Test with inconsistent pattern
        inconsistent_sessions = [
            timezone.now() - timedelta(days=1),
            timezone.now() - timedelta(days=10),
            timezone.now() - timedelta(days=25),
        ]
        
        consistency = self.service._calculate_consistency_score(inconsistent_sessions)
        self.assertLess(consistency, 0.5)  # Should be low consistency
    
    def test_analyze_time_efficiency(self):
        """Test time efficiency analysis."""
        attempts = [
            {'time_taken': 300, 'score': 85},
            {'time_taken': 250, 'score': 90},
            {'time_taken': 400, 'score': 75},
        ]
        
        efficiency = self.service._analyze_time_efficiency(attempts)
        
        self.assertIn('average_time', efficiency)
        self.assertIn('efficiency_score', efficiency)
        self.assertIn('time_vs_performance', efficiency)
        
        self.assertEqual(efficiency['average_time'], 316.7)  # (300+250+400)/3
    
    def test_performance_analysis_no_data(self):
        """Test performance analysis with no data."""
        # Create new user with no activity
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        result = self.service.analyze_adaptive_performance(
            user=new_user,
            course=self.course,
            days=30
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['overall_score'], 0)
        self.assertEqual(result['performance_category'], 'No Data')
    
    def test_performance_analysis_different_time_periods(self):
        """Test performance analysis for different time periods."""
        for days in [7, 14, 30, 90]:
            result = self.service.analyze_adaptive_performance(
                user=self.user,
                course=self.course,
                days=days
            )
            
            self.assertTrue(result['success'], f"Failed for {days} days")
            self.assertIn('overall_score', result)
    
    def test_real_time_adaptation_triggers(self):
        """Test identification of real-time adaptation triggers."""
        performance_data = {
            'quiz_performance': {'average_score': 45, 'improvement_trend': 'Declining'},
            'study_sessions': {'completion_rate': 30},
            'learning_progress': {'average_mastery_level': 1.5}
        }
        
        triggers = self.service._identify_adaptation_triggers(performance_data)
        
        self.assertIsInstance(triggers, list)
        self.assertGreater(len(triggers), 0)
        
        # Should identify poor performance triggers
        trigger_types = [t['type'] for t in triggers]
        self.assertIn('low_quiz_scores', trigger_types)
        self.assertIn('low_completion_rate', trigger_types)
    
    @patch('learning.services.performance_analysis.logger')
    def test_error_handling(self, mock_logger):
        """Test error handling and logging."""
        # Test with invalid course
        result = self.service.analyze_adaptive_performance(
            user=self.user,
            course=None,
            days=30
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        mock_logger.error.assert_called()
    
    def test_performance_score_calculation(self):
        """Test overall performance score calculation."""
        component_scores = {
            'quiz_performance': 85,
            'study_sessions': 75,
            'learning_progress': 80,
            'flashcard_retention': 70
        }
        
        overall_score = self.service._calculate_overall_score(component_scores)
        
        self.assertGreaterEqual(overall_score, 0)
        self.assertLessEqual(overall_score, 100)
        # Should be weighted average around 77.5
        self.assertAlmostEqual(overall_score, 77.5, delta=2)
    
    def test_learning_velocity_calculation(self):
        """Test learning velocity calculation."""
        progress_entries = [
            {'created_at': timezone.now() - timedelta(days=7), 'mastery_level': 2},
            {'created_at': timezone.now() - timedelta(days=14), 'mastery_level': 1},
            {'created_at': timezone.now() - timedelta(days=21), 'mastery_level': 1},
        ]
        
        velocity = self.service._calculate_learning_velocity(progress_entries)
        
        self.assertIn('topics_per_week', velocity)
        self.assertIn('mastery_improvement_rate', velocity)
        self.assertIn('velocity_trend', velocity)
        
        self.assertGreater(velocity['topics_per_week'], 0)
    
    def test_difficulty_distribution_analysis(self):
        """Test difficulty distribution analysis for flashcards."""
        reviews = [
            {'difficulty': 'easy'},
            {'difficulty': 'easy'},
            {'difficulty': 'medium'},
            {'difficulty': 'hard'},
        ]
        
        distribution = self.service._analyze_difficulty_distribution(reviews)
        
        self.assertIn('easy', distribution)
        self.assertIn('medium', distribution)
        self.assertIn('hard', distribution)
        
        # Check percentages
        self.assertEqual(distribution['easy'], 50.0)  # 2/4
        self.assertEqual(distribution['medium'], 25.0)  # 1/4
        self.assertEqual(distribution['hard'], 25.0)  # 1/4