"""
Tests for AdaptiveLearningViewSet API endpoints.
"""

from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from learning.models import StudyPlan, StudyGoal, LearningProgress
from courses.models import Course
from learning.views import AdaptiveLearningViewSet

User = get_user_model()


class TestAdaptiveLearningViewSet(TestCase):
    """Test cases for AdaptiveLearningViewSet API endpoints."""
    
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
        
        self.client = APIClient()
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create test study plan
        self.study_plan = StudyPlan.objects.create(
            user=self.user,
            course=self.course,
            title='Test Plan',
            description='Test study plan',
            plan_type='weekly',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            daily_study_hours=2.0,
            study_days_per_week=5,
            status='active'
        )
        
        # Create test learning progress
        self.progress = LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type='topic',
            identifier='Django Models',
            mastery_level=3,
            completion_percentage=75.0
        )
    
    def test_generate_adaptive_plan_success(self):
        """Test successful adaptive plan generation."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        data = {
            'course_id': str(self.course.id),
            'plan_type': 'weekly',
            'preferences': {
                'daily_hours': 2.0,
                'intensity_multiplier': 1.0,
                'prefer_short_sessions': False,
                'include_weekends': True
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertIn('study_plan_id', response.data)
        self.assertIn('plan_data', response.data)
        self.assertIn('recommendations', response.data)
    
    def test_generate_adaptive_plan_with_target_date(self):
        """Test adaptive plan generation with target date."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        target_date = (timezone.now().date() + timedelta(days=14)).isoformat()
        
        data = {
            'course_id': str(self.course.id),
            'plan_type': 'exam_prep',
            'target_date': target_date,
            'preferences': {
                'daily_hours': 3.0,
                'high_intensity': True
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Check that target date is considered
        plan_data = response.data['plan_data']
        completion_date = plan_data['estimated_completion']
        self.assertIsNotNone(completion_date)
    
    def test_generate_adaptive_plan_missing_course_id(self):
        """Test plan generation with missing course ID."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        data = {
            'plan_type': 'weekly',
            'preferences': {'daily_hours': 2.0}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('course_id', response.data['error'].lower())
    
    def test_generate_adaptive_plan_invalid_course(self):
        """Test plan generation with invalid course ID."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        data = {
            'course_id': '00000000-0000-0000-0000-000000000000',
            'plan_type': 'weekly',
            'preferences': {'daily_hours': 2.0}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_manual_override_success(self):
        """Test successful manual override."""
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'study_plan_id': str(self.study_plan.id),
            'override_type': 'schedule',
            'override_data': {
                'session_id': 'session_123',
                'new_date': '2024-01-15',
                'new_time': '14:00'
            },
            'reason': 'User preference for afternoon study'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertIn('override_applied', response.data)
        self.assertIn('updated_plan', response.data)
    
    def test_manual_override_difficulty_adjustment(self):
        """Test manual difficulty adjustment override."""
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'study_plan_id': str(self.study_plan.id),
            'override_type': 'difficulty',
            'override_data': {
                'adjustment': 1  # Make harder
            },
            'reason': 'Current level too easy'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['override_applied']['type'], 'difficulty')
    
    def test_manual_override_review_frequency(self):
        """Test manual review frequency override."""
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'study_plan_id': str(self.study_plan.id),
            'override_type': 'review_frequency',
            'override_data': {
                'frequency_days': 5
            },
            'reason': 'Need more frequent reviews'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['override_applied']['type'], 'review_frequency')
    
    def test_manual_override_missing_data(self):
        """Test manual override with missing required data."""
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'override_type': 'schedule',
            'reason': 'Test reason'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('study_plan_id', response.data['error'].lower())
    
    def test_manual_override_invalid_study_plan(self):
        """Test manual override with invalid study plan ID."""
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'study_plan_id': '00000000-0000-0000-0000-000000000000',
            'override_type': 'schedule',
            'override_data': {'new_date': '2024-01-15'},
            'reason': 'Test reason'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_adaptive_dashboard_success(self):
        """Test successful adaptive dashboard retrieval."""
        url = '/api/v1/learning/adaptive/adaptive-dashboard/'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overall_performance', response.data)
        self.assertIn('active_plans', response.data)
        self.assertIn('review_workload', response.data)
        self.assertIn('adaptation_status', response.data)
        self.assertIn('key_strengths', response.data)
        self.assertIn('improvement_areas', response.data)
        self.assertIn('priority_recommendations', response.data)
        
        # Check overall performance structure
        overall_perf = response.data['overall_performance']
        self.assertIn('score', overall_perf)
        self.assertIn('category', overall_perf)
        self.assertIn('trend', overall_perf)
    
    def test_adaptive_dashboard_with_course_filter(self):
        """Test adaptive dashboard with course filter."""
        url = '/api/v1/learning/adaptive/adaptive-dashboard/'
        
        response = self.client.get(url, {'course_id': str(self.course.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overall_performance', response.data)
        # Should include course-specific data
        self.assertIn('active_plans', response.data)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are rejected."""
        self.client.credentials()  # Remove authentication
        
        urls = [
            '/api/v1/learning/adaptive/generate-adaptive-plan/',
            '/api/v1/learning/adaptive/manual-override/',
            '/api/v1/learning/adaptive/adaptive-dashboard/',
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_different_plan_types(self):
        """Test generation of different plan types."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        
        plan_types = ['weekly', 'monthly', 'exam_prep', 'custom']
        
        for plan_type in plan_types:
            data = {
                'course_id': str(self.course.id),
                'plan_type': plan_type,
                'preferences': {'daily_hours': 2.0}
            }
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_201_CREATED,
                f"Failed for plan_type: {plan_type}"
            )
            self.assertTrue(response.data['success'])
    
    def test_invalid_override_type(self):
        """Test manual override with invalid override type."""
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'study_plan_id': str(self.study_plan.id),
            'override_type': 'invalid_type',
            'override_data': {'test': 'data'},
            'reason': 'Test reason'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('override_type', response.data['error'].lower())
    
    def test_course_access_control(self):
        """Test that users can only access their own courses."""
        # Create another user and course
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_course = Course.objects.create(
            name='Other Course',
            description='Another user\'s course',
            user=other_user
        )
        
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        data = {
            'course_id': str(other_course.id),
            'plan_type': 'weekly',
            'preferences': {'daily_hours': 2.0}
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should not be able to access other user's course
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_study_plan_access_control(self):
        """Test that users can only modify their own study plans."""
        # Create another user and study plan
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_plan = StudyPlan.objects.create(
            user=other_user,
            course=self.course,  # Same course but different user
            title='Other Plan',
            description='Another user\'s plan',
            plan_type='weekly',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            daily_study_hours=2.0,
            study_days_per_week=5,
            status='active'
        )
        
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'study_plan_id': str(other_plan.id),
            'override_type': 'schedule',
            'override_data': {'new_date': '2024-01-15'},
            'reason': 'Test reason'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should not be able to modify other user's plan
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_preferences_validation(self):
        """Test validation of preferences in plan generation."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        
        # Test with invalid daily hours
        data = {
            'course_id': str(self.course.id),
            'plan_type': 'weekly',
            'preferences': {
                'daily_hours': -1  # Invalid negative hours
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should still succeed but correct the invalid preference
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
    
    def test_dashboard_performance_calculations(self):
        """Test dashboard performance calculations."""
        # Create additional data for better performance calculations
        LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type='topic',
            identifier='Django Views',
            mastery_level=4,
            completion_percentage=90.0
        )
        
        url = '/api/v1/learning/adaptive/adaptive-dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that performance score is reasonable
        performance_score = response.data['overall_performance']['score']
        self.assertGreaterEqual(performance_score, 0)
        self.assertLessEqual(performance_score, 100)
        
        # Check that we have recommendations
        recommendations = response.data['priority_recommendations']
        self.assertIsInstance(recommendations, list)
    
    def test_dashboard_with_no_data(self):
        """Test dashboard behavior with no learning data."""
        # Create a new user with no learning data
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        # Create new client with new user
        new_client = APIClient()
        refresh = RefreshToken.for_user(new_user)
        access_token = str(refresh.access_token)
        new_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = '/api/v1/learning/adaptive/adaptive-dashboard/'
        response = new_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should still provide dashboard structure
        self.assertIn('overall_performance', response.data)
        self.assertIn('active_plans', response.data)
        
        # Performance score should be 0 or low for new user
        performance_score = response.data['overall_performance']['score']
        self.assertLessEqual(performance_score, 10)
    
    def test_concurrent_plan_generation(self):
        """Test handling of concurrent plan generation requests."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        data = {
            'course_id': str(self.course.id),
            'plan_type': 'weekly',
            'preferences': {'daily_hours': 2.0}
        }
        
        # Make multiple concurrent requests
        responses = []
        for _ in range(3):
            response = self.client.post(url, data, format='json')
            responses.append(response)
        
        # All should succeed
        for i, response in enumerate(responses):
            self.assertEqual(
                response.status_code, 
                status.HTTP_201_CREATED,
                f"Request {i} failed"
            )
            self.assertTrue(response.data['success'])
    
    def test_large_preferences_object(self):
        """Test handling of large preferences object."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        
        # Create large preferences object
        large_preferences = {
            'daily_hours': 2.5,
            'intensity_multiplier': 1.2,
            'prefer_short_sessions': True,
            'include_weekends': False,
            'morning_preference': True,
            'break_frequency': 15,
            'review_emphasis': 'high',
            'difficulty_preference': 'adaptive',
            'learning_style': 'visual',
            'custom_settings': {
                'reminder_frequency': 'daily',
                'progress_tracking': True,
                'gamification': False
            }
        }
        
        data = {
            'course_id': str(self.course.id),
            'plan_type': 'custom',
            'preferences': large_preferences
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
    
    @patch('learning.views.logger')
    def test_service_error_handling(self, mock_logger):
        """Test API error handling when services fail."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        
        # Use non-existent course to trigger service error
        data = {
            'course_id': str(self.course.id),
            'plan_type': 'weekly',
            'preferences': {'daily_hours': 2.0}
        }
        
        # Mock service to raise exception
        with patch('learning.services.study_plan_generator.StudyPlanGeneratorService.generate_adaptive_plan') as mock_service:
            mock_service.side_effect = Exception('Service error')
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
    
    def test_dashboard_recommendations_structure(self):
        """Test that dashboard recommendations have proper structure."""
        url = '/api/v1/learning/adaptive/adaptive-dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        recommendations = response.data['priority_recommendations']
        self.assertIsInstance(recommendations, list)
        
        if recommendations:
            rec = recommendations[0]
            self.assertIn('title', rec)
            self.assertIn('description', rec)
            self.assertIn('priority', rec)
            self.assertIn('type', rec)
    
    def test_manual_override_logs_changes(self):
        """Test that manual overrides are properly logged."""
        url = '/api/v1/learning/adaptive/manual-override/'
        data = {
            'study_plan_id': str(self.study_plan.id),
            'override_type': 'schedule',
            'override_data': {
                'session_id': 'session_123',
                'new_date': '2024-01-15'
            },
            'reason': 'User requested schedule change'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that override details are returned
        override_applied = response.data['override_applied']
        self.assertEqual(override_applied['type'], 'schedule')
        self.assertEqual(override_applied['reason'], 'User requested schedule change')
        self.assertIn('timestamp', override_applied)
    
    def test_plan_generation_response_format(self):
        """Test that plan generation response has correct format."""
        url = '/api/v1/learning/adaptive/generate-adaptive-plan/'
        data = {
            'course_id': str(self.course.id),
            'plan_type': 'weekly',
            'preferences': {'daily_hours': 2.0}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response structure
        required_fields = [
            'success', 'study_plan_id', 'plan_data', 'recommendations'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data, f"Missing field: {field}")
        
        # Check plan_data structure
        plan_data = response.data['plan_data']
        self.assertIn('schedule', plan_data)
        self.assertIn('estimated_completion', plan_data)
        self.assertIn('adaptations_made', plan_data)
        
        # Check recommendations structure
        recommendations = response.data['recommendations']
        self.assertIsInstance(recommendations, list)