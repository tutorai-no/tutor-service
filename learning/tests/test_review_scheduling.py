"""
Tests for ReviewSchedulingService.
"""

from unittest.mock import Mock, patch
from datetime import datetime, timedelta, date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from learning.services.review_scheduling import ReviewSchedulingService
from learning.models import LearningProgress
from assessments.models import Flashcard, FlashcardReview, Quiz, QuizAttempt
from courses.models import Course

User = get_user_model()


class TestReviewSchedulingService(TestCase):
    """Test cases for ReviewSchedulingService."""
    
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
        
        self.service = ReviewSchedulingService()
        
        # Create test flashcard
        self.flashcard = Flashcard.objects.create(
            user=self.user,
            course=self.course,
            front='What is Django?',
            back='A Python web framework'
        )
        
        # Create test learning progress
        self.progress = LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type='topic',
            identifier='Django Models',
            mastery_level=2,
            completion_percentage=60.0
        )
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        self.assertIsInstance(self.service, ReviewSchedulingService)
        self.assertEqual(self.service.base_intervals, [1, 3, 7, 14, 30, 90])
        self.assertEqual(self.service.max_interval, 365)
        self.assertEqual(self.service.min_interval, 1)
    
    def test_schedule_intelligent_reviews_success(self):
        """Test successful intelligent review scheduling."""
        result = self.service.schedule_intelligent_reviews(
            user=self.user,
            course=self.course,
            target_retention=0.85
        )
        
        self.assertTrue(result['success'])
        self.assertIn('review_schedule', result)
        self.assertIn('retention_analysis', result)
        self.assertIn('scheduling_stats', result)
        
        # Check scheduling stats
        stats = result['scheduling_stats']
        self.assertIn('total_items', stats)
        self.assertIn('reviews_today', stats)
        self.assertIn('reviews_this_week', stats)
        self.assertIn('target_retention', stats)
        self.assertEqual(stats['target_retention'], 0.85)
    
    def test_get_flashcards_for_review(self):
        """Test flashcard review item retrieval."""
        # Create a flashcard review to test different scenarios
        FlashcardReview.objects.create(
            user=self.user,
            flashcard=self.flashcard,
            difficulty='medium',
            response_time=5
        )
        
        items = self.service._get_flashcards_for_review(self.user, self.course)
        
        self.assertIsInstance(items, list)
        
        if items:  # If there are items to review
            item = items[0]
            self.assertIn('id', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('difficulty', item)
            self.assertIn('next_review_date', item)
            self.assertIn('priority', item)
            self.assertIn('estimated_time_minutes', item)
            self.assertEqual(item['type'], 'flashcard')
    
    def test_get_topics_for_review(self):
        """Test topic review item retrieval."""
        # Update progress to make it need review
        self.progress.updated_at = timezone.now() - timedelta(days=5)
        self.progress.save()
        
        items = self.service._get_topics_for_review(self.user, self.course)
        
        self.assertIsInstance(items, list)
        
        if items:  # If there are items to review
            item = items[0]
            self.assertIn('id', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('difficulty', item)
            self.assertEqual(item['type'], 'topic')
    
    def test_get_concepts_for_review(self):
        """Test concept review item retrieval."""
        # Create a quiz with low score
        quiz = Quiz.objects.create(
            title='Test Quiz',
            course=self.course,
            user=self.user
        )
        
        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=65,  # Below 75% threshold
            completed=True
        )
        
        items = self.service._get_concepts_for_review(self.user, self.course)
        
        self.assertIsInstance(items, list)
        
        if items:  # If there are items to review
            item = items[0]
            self.assertIn('id', item)
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertEqual(item['type'], 'concept')
    
    def test_update_review_schedule_realtime(self):
        """Test real-time review schedule updates."""
        performance = {
            'correct': True,
            'response_time': 3,
            'difficulty': 'easy',
            'confidence': 4
        }
        
        result = self.service.update_review_schedule_realtime(
            user=self.user,
            item_id=str(self.flashcard.id),
            item_type='flashcard',
            performance=performance
        )
        
        self.assertTrue(result['success'])
        self.assertIn('next_review_date', result)
        self.assertIn('updated_difficulty', result)
        self.assertIn('related_adjustments', result)
        self.assertIn('performance_impact', result)
        
        # Check that next review date is in the future
        next_review = datetime.fromisoformat(result['next_review_date'])
        self.assertGreater(next_review, timezone.now())
    
    def test_optimize_daily_review_load(self):
        """Test daily review load optimization."""
        result = self.service.optimize_daily_review_load(
            user=self.user,
            target_daily_reviews=50,
            max_daily_reviews=100
        )
        
        self.assertTrue(result['success'])
        self.assertIn('current_load_analysis', result)
        self.assertIn('optimized_schedule', result)
        self.assertIn('recommendations', result)
        self.assertIn('load_metrics', result)
        
        # Check load metrics structure
        load_metrics = result['load_metrics']
        self.assertIn('average_daily_reviews', load_metrics)
        self.assertIn('peak_load_day', load_metrics)
        self.assertIn('load_variance', load_metrics)
    
    def test_calculate_next_flashcard_review(self):
        """Test flashcard review date calculation."""
        # Create a recent review
        last_review = FlashcardReview.objects.create(
            user=self.user,
            flashcard=self.flashcard,
            difficulty='medium',
            response_time=5,
            created_at=timezone.now() - timedelta(days=1)
        )
        
        next_review_date = self.service._calculate_next_flashcard_review(
            self.flashcard, last_review
        )
        
        self.assertIsInstance(next_review_date, date)
        self.assertGreater(next_review_date, timezone.now().date())
    
    def test_calculate_flashcard_next_review_sm2(self):
        """Test SM-2 algorithm for flashcard review scheduling."""
        performance_data = {
            'difficulty': 'easy',
            'response_time': 2,
            'correct': True
        }
        
        next_review = self.service._calculate_flashcard_next_review(
            str(self.flashcard.id),
            performance_data['difficulty'],
            performance_data['response_time'],
            performance_data['correct'],
            self.user
        )
        
        self.assertIsInstance(next_review, datetime)
        self.assertGreater(next_review, timezone.now())
        
        # Test with different difficulties
        for difficulty in ['easy', 'medium', 'hard', 'again']:
            next_review = self.service._calculate_flashcard_next_review(
                str(self.flashcard.id),
                difficulty,
                5,
                True,
                self.user
            )
            self.assertIsInstance(next_review, datetime)
    
    def test_calculate_topic_next_review(self):
        """Test topic review date calculation."""
        performance = {
            'mastery_level': 3,
            'understanding_score': 75
        }
        
        next_review = self.service._calculate_topic_next_review(
            str(self.progress.id),
            performance,
            self.user
        )
        
        self.assertIsInstance(next_review, datetime)
        self.assertGreater(next_review, timezone.now())
    
    def test_update_item_difficulty(self):
        """Test item difficulty updates based on performance."""
        # Test difficulty increase for poor performance
        performance = {
            'current_difficulty': 'easy',
            'correct': False,
            'response_time': 15
        }
        
        new_difficulty = self.service._update_item_difficulty(
            str(self.flashcard.id),
            'flashcard',
            performance
        )
        
        self.assertEqual(new_difficulty, 'medium')  # Should increase difficulty
        
        # Test difficulty decrease for good performance
        performance = {
            'current_difficulty': 'hard',
            'correct': True,
            'response_time': 2
        }
        
        new_difficulty = self.service._update_item_difficulty(
            str(self.flashcard.id),
            'flashcard',
            performance
        )
        
        self.assertEqual(new_difficulty, 'medium')  # Should decrease difficulty
    
    def test_analyze_retention_patterns(self):
        """Test retention pattern analysis."""
        # Create some flashcard reviews
        FlashcardReview.objects.create(
            user=self.user,
            flashcard=self.flashcard,
            difficulty='easy',
            response_time=3
        )
        
        FlashcardReview.objects.create(
            user=self.user,
            flashcard=self.flashcard,
            difficulty='medium',
            response_time=5
        )
        
        patterns = self.service._analyze_retention_patterns(self.user, self.course)
        
        self.assertIn('average_retention', patterns)
        self.assertIn('retention_by_interval', patterns)
        self.assertIn('difficulty_patterns', patterns)
        self.assertIn('forgetting_curve', patterns)
        self.assertIn('optimal_intervals', patterns)
    
    def test_calculate_optimal_review_date(self):
        """Test optimal review date calculation."""
        item = {
            'difficulty': 'medium',
            'type': 'flashcard'
        }
        
        retention_analysis = {
            'average_retention': 0.75
        }
        
        optimal_date = self.service._calculate_optimal_review_date(
            item, retention_analysis, target_retention=0.85
        )
        
        self.assertIsInstance(optimal_date, date)
        self.assertGreater(optimal_date, timezone.now().date())
    
    def test_predict_retention(self):
        """Test retention prediction."""
        item = {
            'difficulty': 'medium',
            'type': 'flashcard'
        }
        
        review_date = timezone.now().date() + timedelta(days=7)
        
        retention = self.service._predict_retention(item, review_date)
        
        self.assertIsInstance(retention, float)
        self.assertGreaterEqual(retention, 0.1)
        self.assertLessEqual(retention, 1.0)
    
    def test_analyze_review_load_distribution(self):
        """Test review load distribution analysis."""
        upcoming_reviews = [
            {'date': '2024-01-01'},
            {'date': '2024-01-01'},
            {'date': '2024-01-02'},
            {'date': '2024-01-03'},
            {'date': '2024-01-03'},
            {'date': '2024-01-03'},
        ]
        
        analysis = self.service._analyze_review_load_distribution(upcoming_reviews)
        
        self.assertIn('average_daily_load', analysis)
        self.assertIn('peak_day', analysis)
        self.assertIn('load_variance', analysis)
        self.assertIn('overloaded_days', analysis)
        self.assertIn('daily_distribution', analysis)
        
        # Check calculations
        self.assertEqual(analysis['peak_day'], '2024-01-03')  # 3 reviews
        self.assertEqual(analysis['daily_distribution']['2024-01-01'], 2)
    
    def test_redistribute_review_load(self):
        """Test review load redistribution."""
        upcoming_reviews = [
            {'date': '2024-01-01', 'title': 'Review 1'},
            {'date': '2024-01-01', 'title': 'Review 2'},
            {'date': '2024-01-01', 'title': 'Review 3'},
            {'date': '2024-01-01', 'title': 'Review 4'},
            {'date': '2024-01-01', 'title': 'Review 5'},
        ]
        
        redistributed = self.service._redistribute_review_load(
            upcoming_reviews, target_daily_reviews=3, max_daily_reviews=4
        )
        
        self.assertIsInstance(redistributed, list)
        self.assertEqual(len(redistributed), 5)  # Same number of reviews
        
        # Check that some reviews were redistributed
        redistributed_count = sum(1 for r in redistributed if r.get('redistributed'))
        self.assertGreater(redistributed_count, 0)
    
    def test_find_available_date(self):
        """Test finding available dates for redistribution."""
        reviews_by_date = {
            '2024-01-01': [1, 2, 3, 4],  # Full day
            '2024-01-02': [1, 2],        # Available
            '2024-01-03': [1, 2, 3],     # Almost full
        }
        
        available_date = self.service._find_available_date(
            '2024-01-01', reviews_by_date, max_daily_reviews=4, offset=0
        )
        
        self.assertEqual(available_date, '2024-01-02')  # Should find day 2
    
    def test_calculate_review_priority(self):
        """Test review priority calculation."""
        # Create old review (overdue)
        old_review = FlashcardReview.objects.create(
            user=self.user,
            flashcard=self.flashcard,
            difficulty='medium',
            created_at=timezone.now() - timedelta(days=10)
        )
        
        priority = self.service._calculate_review_priority(old_review)
        
        self.assertIn(priority, ['high', 'medium', 'low'])
        # Old review should have high priority
        self.assertEqual(priority, 'high')
    
    def test_mastery_to_difficulty_conversion(self):
        """Test mastery level to difficulty conversion."""
        test_cases = [
            (1, 'hard'),
            (2, 'hard'),
            (3, 'medium'),
            (4, 'easy'),
            (5, 'easy')
        ]
        
        for mastery_level, expected_difficulty in test_cases:
            difficulty = self.service._mastery_to_difficulty(mastery_level)
            self.assertEqual(difficulty, expected_difficulty)
    
    def test_calculate_topic_priority(self):
        """Test topic priority calculation."""
        # Test different mastery levels
        high_priority_progress = LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            topic='Hard Topic',
            mastery_level=1
        )
        
        priority = self.service._calculate_topic_priority(high_priority_progress)
        self.assertEqual(priority, 'high')
        
        # Test medium priority
        medium_priority_progress = LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            topic='Medium Topic',
            mastery_level=3
        )
        
        priority = self.service._calculate_topic_priority(medium_priority_progress)
        self.assertEqual(priority, 'medium')
    
    def test_analyze_difficulty_patterns(self):
        """Test difficulty pattern analysis."""
        # Create reviews with different difficulties
        reviews = []
        for difficulty in ['easy', 'easy', 'medium', 'hard']:
            review = FlashcardReview.objects.create(
                user=self.user,
                flashcard=self.flashcard,
                difficulty=difficulty
            )
            reviews.append(review)
        
        # Convert to queryset
        from django.db.models import QuerySet
        reviews_qs = FlashcardReview.objects.filter(
            id__in=[r.id for r in reviews]
        )
        
        patterns = self.service._analyze_difficulty_patterns(reviews_qs)
        
        self.assertIn('distribution', patterns)
        self.assertIn('dominant_difficulty', patterns)
        
        # Check distribution calculations
        distribution = patterns['distribution']
        self.assertEqual(distribution['easy'], 0.5)    # 2/4
        self.assertEqual(distribution['medium'], 0.25) # 1/4
        self.assertEqual(distribution['hard'], 0.25)   # 1/4
    
    def test_is_this_week(self):
        """Test week checking functionality."""
        today = timezone.now().date()
        
        # Test current week dates
        self.assertTrue(self.service._is_this_week(today.isoformat()))
        
        # Test next week
        next_week = today + timedelta(days=8)
        self.assertFalse(self.service._is_this_week(next_week.isoformat()))
        
        # Test last week
        last_week = today - timedelta(days=8)
        self.assertFalse(self.service._is_this_week(last_week.isoformat()))
    
    def test_generate_load_balancing_recommendations(self):
        """Test load balancing recommendation generation."""
        load_analysis = {
            'load_variance': 150,  # High variance
            'overloaded_days': ['2024-01-01', '2024-01-02'],
            'average_daily_load': 85  # High load
        }
        
        optimized_schedule = []
        
        recommendations = self.service._generate_load_balancing_recommendations(
            load_analysis, optimized_schedule
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should recommend spreading reviews and addressing overloaded days
        rec_text = ' '.join(recommendations)
        self.assertIn('spreading', rec_text.lower())
    
    @patch('learning.services.review_scheduling.logger')
    def test_error_handling(self, mock_logger):
        """Test error handling and logging."""
        # Test with invalid user
        result = self.service.schedule_intelligent_reviews(
            user=None,
            course=self.course,
            target_retention=0.85
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        mock_logger.error.assert_called()
    
    def test_performance_impact_analysis(self):
        """Test performance impact analysis."""
        # Test good performance
        good_performance = {
            'correct': True,
            'response_time': 3,
            'confidence': 5
        }
        
        impact = self.service._analyze_performance_impact(good_performance)
        
        self.assertIn('learning_efficiency', impact)
        self.assertIn('retention_prediction', impact)
        self.assertIn('adjustment_needed', impact)
        
        self.assertEqual(impact['learning_efficiency'], 'high')
        self.assertEqual(impact['retention_prediction'], 'strong')
        self.assertFalse(impact['adjustment_needed'])
        
        # Test poor performance
        poor_performance = {
            'correct': False,
            'response_time': 15,
            'confidence': 1
        }
        
        impact = self.service._analyze_performance_impact(poor_performance)
        
        self.assertEqual(impact['learning_efficiency'], 'medium')
        self.assertEqual(impact['retention_prediction'], 'weak')
        self.assertTrue(impact['adjustment_needed'])
    
    def test_scheduling_confidence_calculation(self):
        """Test scheduling confidence calculation."""
        item = {'difficulty': 'medium'}
        retention_analysis = {
            'forgetting_curve': {'model_confidence': 0.8}
        }
        
        confidence = self.service._calculate_scheduling_confidence(
            item, retention_analysis
        )
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
    
    def test_different_target_retention_rates(self):
        """Test scheduling with different target retention rates."""
        for target_retention in [0.7, 0.8, 0.85, 0.9, 0.95]:
            result = self.service.schedule_intelligent_reviews(
                user=self.user,
                course=self.course,
                target_retention=target_retention
            )
            
            self.assertTrue(result['success'], f"Failed for retention rate {target_retention}")
            self.assertEqual(
                result['scheduling_stats']['target_retention'],
                target_retention
            )