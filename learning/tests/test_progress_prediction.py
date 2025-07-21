"""
Tests for ProgressPredictionService.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from courses.models import Course
from learning.models import LearningProgress, StudyPlan, StudySession
from learning.services.progress_prediction import ProgressPredictionService

User = get_user_model()


class TestProgressPredictionService(TestCase):
    """Test cases for ProgressPredictionService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.course = Course.objects.create(
            name="Test Course", description="A test course", user=self.user
        )

        self.service = ProgressPredictionService()

        # Create test study plan
        self.study_plan = StudyPlan.objects.create(
            user=self.user,
            course=self.course,
            title="Test Plan",
            description="Test study plan",
            plan_type="weekly",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            daily_study_hours=2.0,
            study_days_per_week=5,
            status="active",
        )

        # Create test learning progress
        self.progress = LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type="topic",
            identifier="Django Models",
            mastery_level=3,
            completion_percentage=75.0,
        )

        # Create test study sessions
        self.study_session = StudySession.objects.create(
            user=self.user,
            course=self.course,
            title="Django Practice",
            session_type="practice",
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            status="completed",
        )

    def test_service_initialization(self):
        """Test service initializes correctly."""
        self.assertIsInstance(self.service, ProgressPredictionService)

    def test_predict_completion_success(self):
        """Test successful completion prediction."""
        result = self.service.predict_completion(
            study_plan=self.study_plan, target_mastery_level=4
        )

        self.assertTrue(result["success"])
        self.assertIn("completion_prediction", result)
        self.assertIn("current_progress", result)
        self.assertIn("milestones", result)
        self.assertIn("learning_velocity", result)
        self.assertIn("confidence", result)
        self.assertIn("recommendations", result)

        # Check completion prediction structure
        completion = result["completion_prediction"]
        self.assertIn("estimated_completion_date", completion)
        self.assertIn("weeks_remaining", completion)
        self.assertIn("completion_probability", completion)

        # Check confidence is in valid range
        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 1)

    def test_analyze_current_progress(self):
        """Test current progress analysis."""
        progress = self.service._analyze_current_progress(self.study_plan)

        self.assertIn("topics_mastered", progress)
        self.assertIn("total_topics", progress)
        self.assertIn("completion_percentage", progress)
        self.assertIn("average_mastery_level", progress)
        self.assertIn("study_sessions_completed", progress)
        self.assertIn("total_study_time", progress)

        # Check calculated values
        self.assertGreaterEqual(progress["topics_mastered"], 0)
        self.assertGreaterEqual(progress["total_topics"], 0)
        self.assertGreaterEqual(progress["completion_percentage"], 0)
        self.assertLessEqual(progress["completion_percentage"], 100)

    def test_calculate_learning_velocity(self):
        """Test learning velocity calculation."""
        # Create additional progress entries with different dates
        LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type="topic",
            identifier="Django Views",
            mastery_level=4,
            completion_percentage=90.0,
            updated_at=timezone.now() - timedelta(days=7),
        )

        LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type="topic",
            identifier="Django Templates",
            mastery_level=2,
            completion_percentage=50.0,
            updated_at=timezone.now() - timedelta(days=14),
        )

        velocity = self.service._calculate_learning_velocity(self.study_plan)

        self.assertIn("topics_per_week", velocity)
        self.assertIn("mastery_points_per_week", velocity)
        self.assertIn("velocity_trend", velocity)
        self.assertIn("consistency_score", velocity)

        # Check velocity values are reasonable
        self.assertGreaterEqual(velocity["topics_per_week"], 0)
        self.assertGreaterEqual(velocity["mastery_points_per_week"], 0)
        self.assertIn(
            velocity["velocity_trend"], ["Accelerating", "Stable", "Declining"]
        )

    def test_predict_completion_date(self):
        """Test completion date prediction."""
        current_progress = {
            "completion_percentage": 60,
            "topics_mastered": 3,
            "total_topics": 10,
        }

        learning_velocity = {"topics_per_week": 2, "mastery_points_per_week": 5}

        completion_data = self.service._predict_completion_date(
            current_progress, learning_velocity, target_mastery_level=4
        )

        self.assertIn("estimated_completion_date", completion_data)
        self.assertIn("weeks_remaining", completion_data)
        self.assertIn("completion_probability", completion_data)

        # Check that completion date is in the future
        completion_date = datetime.strptime(
            completion_data["estimated_completion_date"], "%Y-%m-%d"
        ).date()
        self.assertGreater(completion_date, timezone.now().date())

        # Check probability is in valid range
        self.assertGreaterEqual(completion_data["completion_probability"], 0)
        self.assertLessEqual(completion_data["completion_probability"], 1)

    def test_generate_milestones(self):
        """Test milestone generation."""
        completion_data = {
            "weeks_remaining": 8,
            "estimated_completion_date": "2024-03-01",
        }

        milestones = self.service._generate_milestones(completion_data)

        self.assertIsInstance(milestones, list)
        self.assertGreater(len(milestones), 0)

        # Check milestone structure
        first_milestone = milestones[0]
        self.assertIn("percentage", first_milestone)
        self.assertIn("estimated_date", first_milestone)
        self.assertIn("weeks_from_now", first_milestone)
        self.assertIn("description", first_milestone)

        # Check milestones are in order
        percentages = [m["percentage"] for m in milestones]
        self.assertEqual(percentages, sorted(percentages))

    def test_calculate_prediction_confidence(self):
        """Test prediction confidence calculation."""
        learning_velocity = {"consistency_score": 0.8, "velocity_trend": "Stable"}

        current_progress = {"study_sessions_completed": 10, "total_study_time": 600}

        confidence = self.service._calculate_prediction_confidence(
            learning_velocity, current_progress
        )

        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)

        # High consistency and stable trend should give high confidence
        self.assertGreater(confidence, 0.5)

    def test_generate_prediction_recommendations(self):
        """Test prediction recommendation generation."""
        prediction_data = {
            "completion_prediction": {
                "weeks_remaining": 12,
                "completion_probability": 0.6,
            },
            "learning_velocity": {
                "velocity_trend": "Declining",
                "consistency_score": 0.4,
            },
            "current_progress": {"completion_percentage": 40},
        }

        recommendations = self.service._generate_prediction_recommendations(
            prediction_data
        )

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Should include recommendations for declining velocity and low consistency
        rec_text = " ".join(recommendations)
        self.assertIn(
            "velocity" in rec_text.lower() or "consistency" in rec_text.lower(), True
        )

    def test_analyze_study_patterns(self):
        """Test study pattern analysis."""
        # Create study sessions over different days
        for i in range(5):
            StudySession.objects.create(
                user=self.user,
                course=self.course,
                title=f"Session {i}",
                session_type="practice",
                scheduled_start=timezone.now() - timedelta(days=i),
                scheduled_end=timezone.now()
                - timedelta(days=i)
                + timedelta(minutes=45 + i * 15),
                status="completed",
                created_at=timezone.now() - timedelta(days=i),
            )

        patterns = self.service._analyze_study_patterns(self.study_plan)

        self.assertIn("average_session_duration", patterns)
        self.assertIn("sessions_per_week", patterns)
        self.assertIn("completion_rate", patterns)
        self.assertIn("study_streak", patterns)

        # Check calculated values are reasonable
        self.assertGreater(patterns["average_session_duration"], 0)
        self.assertGreaterEqual(patterns["sessions_per_week"], 0)
        self.assertGreaterEqual(patterns["completion_rate"], 0)
        self.assertLessEqual(patterns["completion_rate"], 100)

    def test_calculate_mastery_projection(self):
        """Test mastery level projection."""
        current_progress = {
            "average_mastery_level": 2.5,
            "topics_mastered": 2,
            "total_topics": 8,
        }

        learning_velocity = {"mastery_points_per_week": 3, "topics_per_week": 1.5}

        projection = self.service._calculate_mastery_projection(
            current_progress, learning_velocity, target_mastery_level=4
        )

        self.assertIn("weeks_to_target", projection)
        self.assertIn("projected_mastery_date", projection)
        self.assertIn("confidence_level", projection)

        # Check that projection is reasonable
        self.assertGreater(projection["weeks_to_target"], 0)
        self.assertGreaterEqual(projection["confidence_level"], 0)
        self.assertLessEqual(projection["confidence_level"], 1)

    def test_identify_learning_bottlenecks(self):
        """Test learning bottleneck identification."""
        # Create progress with some struggling topics
        LearningProgress.objects.create(
            user=self.user,
            course=self.course,
            progress_type="topic",
            identifier="Difficult Topic",
            mastery_level=1,
            completion_percentage=25.0,
            updated_at=timezone.now() - timedelta(days=20),  # Old, no progress
        )

        bottlenecks = self.service._identify_learning_bottlenecks(self.study_plan)

        self.assertIsInstance(bottlenecks, list)

        if bottlenecks:
            bottleneck = bottlenecks[0]
            self.assertIn("topic", bottleneck)
            self.assertIn("issue", bottleneck)
            self.assertIn("severity", bottleneck)
            self.assertIn("recommendation", bottleneck)

    def test_calculate_completion_probability(self):
        """Test completion probability calculation."""
        weeks_remaining = 8
        learning_velocity = {"consistency_score": 0.7, "velocity_trend": "Stable"}

        current_progress = {"completion_percentage": 60}

        probability = self.service._calculate_completion_probability(
            weeks_remaining, learning_velocity, current_progress
        )

        self.assertIsInstance(probability, float)
        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 1)

    def test_project_future_performance(self):
        """Test future performance projection."""
        learning_velocity = {
            "topics_per_week": 2,
            "mastery_points_per_week": 6,
            "velocity_trend": "Accelerating",
        }

        weeks_ahead = 4

        projection = self.service._project_future_performance(
            learning_velocity, weeks_ahead
        )

        self.assertIn("projected_topics_completed", projection)
        self.assertIn("projected_mastery_gain", projection)
        self.assertIn("confidence", projection)

        # Check projections are reasonable
        self.assertGreater(projection["projected_topics_completed"], 0)
        self.assertGreater(projection["projected_mastery_gain"], 0)

    def test_different_target_mastery_levels(self):
        """Test predictions with different target mastery levels."""
        for target_level in [3, 4, 5]:
            result = self.service.predict_completion(
                study_plan=self.study_plan, target_mastery_level=target_level
            )

            self.assertTrue(
                result["success"], f"Failed for mastery level {target_level}"
            )

            # Higher mastery levels should generally take longer
            weeks_remaining = result["completion_prediction"]["weeks_remaining"]
            self.assertGreater(weeks_remaining, 0)

    def test_velocity_trend_calculation(self):
        """Test velocity trend calculation."""
        # Test accelerating trend
        velocity_data = [
            {"week": 1, "topics": 1},
            {"week": 2, "topics": 2},
            {"week": 3, "topics": 3},
            {"week": 4, "topics": 4},
        ]

        trend = self.service._calculate_velocity_trend(velocity_data)
        self.assertEqual(trend, "Accelerating")

        # Test declining trend
        velocity_data = [
            {"week": 1, "topics": 4},
            {"week": 2, "topics": 3},
            {"week": 3, "topics": 2},
            {"week": 4, "topics": 1},
        ]

        trend = self.service._calculate_velocity_trend(velocity_data)
        self.assertEqual(trend, "Declining")

        # Test stable trend
        velocity_data = [
            {"week": 1, "topics": 2},
            {"week": 2, "topics": 2},
            {"week": 3, "topics": 2},
            {"week": 4, "topics": 2},
        ]

        trend = self.service._calculate_velocity_trend(velocity_data)
        self.assertEqual(trend, "Stable")

    def test_study_plan_without_progress(self):
        """Test prediction with study plan that has no progress."""
        # Create new study plan with no progress
        new_plan = StudyPlan.objects.create(
            user=self.user,
            course=self.course,
            title="New Plan",
            description="New study plan with no progress",
            plan_type="monthly",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=60),
            daily_study_hours=2.0,
            study_days_per_week=5,
            status="active",
        )

        # Remove existing progress
        LearningProgress.objects.filter(user=self.user, course=self.course).delete()
        StudySession.objects.filter(user=self.user, course=self.course).delete()

        result = self.service.predict_completion(
            study_plan=new_plan, target_mastery_level=4
        )

        self.assertTrue(result["success"])
        # Should still provide predictions based on defaults
        self.assertIn("completion_prediction", result)
        self.assertLower(result["confidence"], 0.5)  # Should have low confidence

    def test_consistency_score_calculation(self):
        """Test consistency score calculation for study sessions."""
        # Create consistent study pattern
        consistent_dates = []
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            consistent_dates.append(date)
            StudySession.objects.create(
                user=self.user,
                course=self.course,
                title=f"Daily Session {i}",
                session_type="practice",
                scheduled_start=date,
                scheduled_end=date + timedelta(hours=1),
                status="completed",
                created_at=date,
            )

        consistency = self.service._calculate_consistency_score(consistent_dates)
        self.assertGreater(consistency, 0.8)  # Should be high consistency

    def test_milestone_descriptions(self):
        """Test milestone description generation."""
        milestone_25 = self.service._generate_milestone_description(25)
        milestone_50 = self.service._generate_milestone_description(50)
        milestone_75 = self.service._generate_milestone_description(75)
        milestone_100 = self.service._generate_milestone_description(100)

        self.assertIn("quarter", milestone_25.lower())
        self.assertIn("half", milestone_50.lower())
        self.assertIn("three-quarters", milestone_75.lower())
        self.assertIn("completion", milestone_100.lower())

    @patch("learning.services.progress_prediction.logger")
    def test_error_handling(self, mock_logger):
        """Test error handling and logging."""
        # Test with None study plan
        result = self.service.predict_completion(
            study_plan=None, target_mastery_level=4
        )

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        mock_logger.error.assert_called()

    def test_realistic_completion_scenarios(self):
        """Test realistic completion scenarios."""
        # Scenario 1: Fast learner
        fast_velocity = {
            "topics_per_week": 3,
            "mastery_points_per_week": 10,
            "consistency_score": 0.9,
            "velocity_trend": "Accelerating",
        }

        current_progress = {
            "completion_percentage": 50,
            "topics_mastered": 5,
            "total_topics": 10,
        }

        completion = self.service._predict_completion_date(
            current_progress, fast_velocity, target_mastery_level=4
        )

        self.assertLess(completion["weeks_remaining"], 5)  # Should finish quickly
        self.assertGreater(
            completion["completion_probability"], 0.8
        )  # High probability

        # Scenario 2: Struggling learner
        slow_velocity = {
            "topics_per_week": 0.5,
            "mastery_points_per_week": 2,
            "consistency_score": 0.3,
            "velocity_trend": "Declining",
        }

        completion = self.service._predict_completion_date(
            current_progress, slow_velocity, target_mastery_level=5
        )

        self.assertGreater(completion["weeks_remaining"], 10)  # Should take longer
        self.assertLess(completion["completion_probability"], 0.6)  # Lower probability

    def test_adaptive_milestone_spacing(self):
        """Test adaptive milestone spacing based on timeline."""
        # Short timeline
        short_completion = {"weeks_remaining": 4}
        short_milestones = self.service._generate_milestones(short_completion)

        # Long timeline
        long_completion = {"weeks_remaining": 20}
        long_milestones = self.service._generate_milestones(long_completion)

        # Long timeline should have more milestones
        self.assertGreaterEqual(len(long_milestones), len(short_milestones))

    def assertLower(self, value, threshold):
        """Custom assertion to check if value is lower than threshold."""
        self.assertLess(value, threshold)
