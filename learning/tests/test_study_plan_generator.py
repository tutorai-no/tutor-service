"""
Tests for StudyPlanGeneratorService.
"""

from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from learning.services.study_plan_generator import StudyPlanGeneratorService
from learning.models import StudyPlan, StudyGoal, LearningProgress
from courses.models import Course

User = get_user_model()


class TestStudyPlanGeneratorService(TestCase):
    """Test cases for StudyPlanGeneratorService."""
    
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
        
        self.service = StudyPlanGeneratorService()
        
        # Create some test study goals
        self.goal = StudyGoal.objects.create(
            user=self.user,
            course=self.course,
            title='Master Django',
            description='Learn Django framework',
            goal_type='milestone',
            target_value=100,
            unit='percentage',
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=30)
        )
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        self.assertIsInstance(self.service, StudyPlanGeneratorService)
        self.assertEqual(self.service.max_daily_load, 85)
        self.assertEqual(self.service.optimal_session_gap, 2)
        self.assertEqual(self.service.min_session_duration, 15)
        self.assertEqual(self.service.max_session_duration, 120)
    
    def test_generate_adaptive_plan_success(self):
        """Test successful adaptive plan generation."""
        preferences = {
            'daily_hours': 2.0,
            'intensity_multiplier': 1.0,
            'prefer_short_sessions': False,
            'include_weekends': True
        }
        
        result = self.service.generate_adaptive_study_plan(
            user=self.user,
            course=self.course,
            plan_type='weekly',
            preferences=preferences
        )
        
        self.assertTrue(result['success'])
        self.assertIn('study_plan_id', result)
        self.assertIn('plan_data', result)
        self.assertIn('recommendations', result)
        
        # Check that plan was created in database
        study_plan = StudyPlan.objects.get(id=result['study_plan_id'])
        self.assertEqual(study_plan.user, self.user)
        self.assertEqual(study_plan.course, self.course)
    
    def test_generate_adaptive_plan_with_target_date(self):
        """Test plan generation with specific target date."""
        target_date = timezone.now().date() + timedelta(days=14)
        preferences = {'daily_hours': 1.5}
        
        result = self.service.generate_adaptive_study_plan(
            user=self.user,
            course=self.course,
            plan_type='exam_prep',
            target_date=target_date,
            preferences=preferences
        )
        
        self.assertTrue(result['success'])
        plan_data = result['plan_data']
        
        # Check that target date is respected
        completion_date = datetime.fromisoformat(plan_data['estimated_completion']).date()
        self.assertLessEqual(completion_date, target_date)
    
    def test_analyze_user_performance(self):
        """Test user performance analysis."""
        analysis = self.service._analyze_user_performance(self.user, self.course)
        
        self.assertIn('quiz_performance', analysis)
        self.assertIn('study_habits', analysis)
        self.assertIn('learning_velocity', analysis)
        self.assertIn('retention_patterns', analysis)
        
        # Check structure of quiz performance
        quiz_perf = analysis['quiz_performance']
        self.assertIn('average_score', quiz_perf)
        self.assertIn('improvement_trend', quiz_perf)
        self.assertIn('weak_topics', quiz_perf)
    
    def test_create_optimized_schedule(self):
        """Test schedule optimization."""
        preferences = {
            'daily_hours': 2.0,
            'prefer_short_sessions': True,
            'include_weekends': False
        }
        
        performance_analysis = {
            'study_habits': {
                'optimal_session_length': 45,
                'peak_productivity_hours': [9, 14, 19],
                'consistency_score': 0.8
            },
            'learning_velocity': {
                'topics_per_week': 3,
                'mastery_rate': 0.75
            }
        }
        
        topics = ['Django Models', 'Django Views', 'Django Templates']
        duration_weeks = 4
        
        schedule = self.service._create_optimized_schedule(
            topics, duration_weeks, preferences, performance_analysis
        )
        
        self.assertIsInstance(schedule, list)
        self.assertGreater(len(schedule), 0)
        
        # Check first session structure
        first_session = schedule[0]
        self.assertIn('date', first_session)
        self.assertIn('start_time', first_session)
        self.assertIn('duration_minutes', first_session)
        self.assertIn('content', first_session)
        self.assertIn('week', first_session)
    
    def test_adapt_to_performance_patterns(self):
        """Test performance-based adaptations."""
        base_schedule = [
            {
                'date': '2024-01-01',
                'start_time': '09:00',
                'duration_minutes': 60,
                'content': {'focus_topic': 'Django Models'},
                'week': 1
            }
        ]
        
        performance_analysis = {
            'study_habits': {
                'optimal_session_length': 45,
                'peak_productivity_hours': [14],  # Prefer afternoon
                'consistency_score': 0.6  # Low consistency
            },
            'quiz_performance': {
                'weak_topics': ['Django Models'],
                'strong_topics': []
            }
        }
        
        adapted_schedule, adaptations = self.service._adapt_to_performance_patterns(
            base_schedule, performance_analysis
        )
        
        self.assertIsInstance(adapted_schedule, list)
        self.assertIsInstance(adaptations, list)
        self.assertGreater(len(adaptations), 0)
        
        # Check that adaptations were made
        adaptation_types = [a['type'] for a in adaptations]
        self.assertIn('time_adjustment', adaptation_types)
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        plan_data = {
            'schedule': [
                {
                    'date': '2024-01-01',
                    'duration_minutes': 90,
                    'content': {'focus_topic': 'Django Models'}
                }
            ],
            'adaptations_made': ['Session duration reduced for better focus']
        }
        
        performance_analysis = {
            'study_habits': {'consistency_score': 0.5},
            'quiz_performance': {'average_score': 65}
        }
        
        recommendations = self.service._generate_recommendations(
            plan_data, performance_analysis
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check recommendation structure
        first_rec = recommendations[0]
        self.assertIn('title', first_rec)
        self.assertIn('description', first_rec)
        self.assertIn('priority', first_rec)
        self.assertIn('type', first_rec)
    
    def test_calculate_cognitive_load(self):
        """Test cognitive load calculation."""
        session_data = {
            'duration_minutes': 90,
            'content': {
                'focus_topic': 'Advanced Django',
                'tasks': [
                    {'title': 'Read documentation', 'type': 'reading'},
                    {'title': 'Code practice', 'type': 'coding'},
                    {'title': 'Take quiz', 'type': 'assessment'}
                ]
            }
        }
        
        user_performance = {
            'learning_velocity': {'mastery_rate': 0.7},
            'study_habits': {'optimal_session_length': 60}
        }
        
        cognitive_load = self.service._calculate_cognitive_load(
            session_data, user_performance
        )
        
        self.assertIsInstance(cognitive_load, float)
        self.assertGreater(cognitive_load, 0)
        self.assertLessEqual(cognitive_load, 10)  # Should be on 1-10 scale
    
    def test_distribute_topics_across_weeks(self):
        """Test topic distribution algorithm."""
        topics = ['Topic 1', 'Topic 2', 'Topic 3', 'Topic 4', 'Topic 5']
        weeks = 3
        
        distribution = self.service._distribute_topics_across_weeks(topics, weeks)
        
        self.assertIsInstance(distribution, dict)
        self.assertEqual(len(distribution), weeks)
        
        # Check all topics are distributed
        all_distributed_topics = []
        for week_topics in distribution.values():
            all_distributed_topics.extend(week_topics)
        
        self.assertEqual(len(all_distributed_topics), len(topics))
        self.assertEqual(set(all_distributed_topics), set(topics))
    
    def test_get_course_topics(self):
        """Test course topic extraction."""
        topics = self.service._get_course_topics(self.course)
        
        self.assertIsInstance(topics, list)
        # Should return default topics when no specific topics are available
        self.assertGreater(len(topics), 0)
    
    def test_invalid_preferences_handling(self):
        """Test handling of invalid preferences."""
        invalid_preferences = {
            'daily_hours': -1,  # Invalid negative hours
            'intensity_multiplier': 0,  # Invalid zero multiplier
        }
        
        result = self.service.generate_adaptive_study_plan(
            user=self.user,
            course=self.course,
            plan_type='weekly',
            preferences=invalid_preferences
        )
        
        # Should still succeed with corrected preferences
        self.assertTrue(result['success'])
    
    def test_plan_type_variations(self):
        """Test different plan types."""
        preferences = {'daily_hours': 2.0}
        
        for plan_type in ['weekly', 'monthly', 'exam_prep', 'custom']:
            result = self.service.generate_adaptive_study_plan(
                user=self.user,
                course=self.course,
                plan_type=plan_type,
                preferences=preferences
            )
            
            self.assertTrue(result['success'], f"Failed for plan_type: {plan_type}")
            self.assertIn('plan_data', result)
    
    @patch('learning.services.study_plan_generator.logger')
    def test_error_handling(self, mock_logger):
        """Test error handling and logging."""
        # Test with None user (should cause error)
        result = self.service.generate_adaptive_study_plan(
            user=None,
            course=self.course,
            plan_type='weekly',
            preferences={}
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        mock_logger.error.assert_called()
    
    def test_weekend_inclusion_preference(self):
        """Test weekend inclusion preference."""
        preferences_with_weekends = {
            'daily_hours': 2.0,
            'include_weekends': True
        }
        
        preferences_without_weekends = {
            'daily_hours': 2.0,
            'include_weekends': False
        }
        
        result_with = self.service.generate_adaptive_study_plan(
            user=self.user,
            course=self.course,
            plan_type='weekly',
            preferences=preferences_with_weekends
        )
        
        result_without = self.service.generate_adaptive_study_plan(
            user=self.user,
            course=self.course,
            plan_type='weekly',
            preferences=preferences_without_weekends
        )
        
        self.assertTrue(result_with['success'])
        self.assertTrue(result_without['success'])
        
        # Plans should be different based on weekend inclusion
        self.assertNotEqual(
            len(result_with['plan_data']['schedule']),
            len(result_without['plan_data']['schedule'])
        )
    
    def test_short_session_preference(self):
        """Test short session preference."""
        preferences = {
            'daily_hours': 2.0,
            'prefer_short_sessions': True
        }
        
        result = self.service.generate_adaptive_study_plan(
            user=self.user,
            course=self.course,
            plan_type='weekly',
            preferences=preferences
        )
        
        self.assertTrue(result['success'])
        
        # Check that sessions are indeed shorter
        schedule = result['plan_data']['schedule']
        if schedule:
            avg_duration = sum(s['duration_minutes'] for s in schedule) / len(schedule)
            self.assertLess(avg_duration, 60)  # Should be less than default 60 minutes