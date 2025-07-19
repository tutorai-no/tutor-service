"""
Integration tests for end-to-end assessment workflows
"""
import pytest
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json

from assessments.models import Flashcard, Quiz, QuizQuestion, Assessment
from assessments.services.generators.flashcard_service import get_flashcard_service
from assessments.services.generators.quiz_service import get_quiz_service
from assessments.tests.fixtures import (
    UserFactory,
    CourseFactory,
    AssessmentFactory,
    create_mock_flashcard_data,
    create_mock_quiz_data
)

User = get_user_model()


class TestEndToEndFlashcardWorkflow(TransactionTestCase):
    """Test complete flashcard generation workflow"""
    
    def setUp(self):
        self.user = UserFactory()
        self.course = CourseFactory(user=self.user)
        
        # Mock external dependencies
        self.mock_llm_patcher = patch('assessments.services.ai_agents.base_agent.ChatOpenAI')
        self.mock_llm = self.mock_llm_patcher.start()
        
        self.mock_retrieval_patcher = patch('assessments.services.ai_agents.base_agent.get_retrieval_client')
        self.mock_retrieval = self.mock_retrieval_patcher.start()
        
        # Setup mock responses
        mock_retrieval_client = Mock()
        mock_retrieval_client.get_context.return_value = "Mock educational content about machine learning algorithms"
        self.mock_retrieval.return_value = mock_retrieval_client
        
        mock_llm_instance = Mock()
        mock_llm_instance.model_name = "gpt-4"
        mock_llm_instance.invoke.return_value = Mock(content="Mock AI response")
        self.mock_llm.return_value = mock_llm_instance
    
    def tearDown(self):
        self.mock_llm_patcher.stop()
        self.mock_retrieval_patcher.stop()
    
    @patch('assessments.services.ai_agents.flashcard_agent.PydanticOutputParser')
    def test_complete_flashcard_generation_workflow(self, mock_parser_class):
        """Test complete flashcard generation from request to database"""
        from assessments.services.ai_agents.flashcard_agent import FlashcardWrapper, FlashcardItem
        
        # Setup mock flashcards
        mock_flashcards = [
            FlashcardItem(
                question="What is supervised learning?",
                answer="Learning with labeled training data",
                explanation="Uses input-output pairs to train models",
                format_type="basic_qa",
                difficulty_level="medium",
                tags=["ml", "supervised"]
            ),
            FlashcardItem(
                question="Define neural network",
                answer="A computing system inspired by biological neural networks",
                explanation="Consists of interconnected nodes that process information",
                format_type="definition",
                difficulty_level="medium",
                tags=["ml", "neural_networks"]
            )
        ]
        
        mock_wrapper = FlashcardWrapper(flashcards=mock_flashcards)
        
        # Setup parser mock
        mock_parser = Mock()
        mock_parser.get_format_instructions.return_value = "Mock format instructions"
        mock_parser.parse.return_value = mock_wrapper
        mock_parser_class.return_value = mock_parser
        
        # Execute the workflow
        service = get_flashcard_service()
        result = service.generate_flashcards(
            user_id=self.user.id,
            course_id=self.course.id,
            topic="Machine Learning Basics",
            count=5,
            difficulty_level="medium",
            auto_save=True
        )
        
        # Verify successful generation
        self.assertTrue(result["success"])
        self.assertTrue(result["auto_saved"])
        self.assertEqual(result["count"], 2)
        
        # Verify database records
        flashcards = Flashcard.objects.filter(user=self.user, course=self.course)
        self.assertEqual(flashcards.count(), 2)
        
        # Verify flashcard content
        fc1 = flashcards.filter(question__icontains="supervised").first()
        self.assertIsNotNone(fc1)
        self.assertIn("labeled training data", fc1.answer)
        self.assertTrue(fc1.generated_by_ai)
        self.assertEqual(fc1.difficulty_level, "medium")
        self.assertIn("ml", fc1.tags)
        
        # Verify spaced repetition initialization
        self.assertEqual(fc1.ease_factor, 2.5)  # Default
        self.assertEqual(fc1.interval_days, 1)   # Default
        self.assertEqual(fc1.repetitions, 0)     # Default
        self.assertEqual(fc1.total_reviews, 0)   # Default
    
    def test_flashcard_generation_error_recovery(self):
        """Test error recovery in flashcard generation"""
        service = get_flashcard_service()
        
        # Test with invalid user
        result = service.generate_flashcards(
            user_id=999999,
            course_id=self.course.id,
            topic="Test Topic"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("User not found", result["error"])
        
        # Test with invalid course
        result = service.generate_flashcards(
            user_id=self.user.id,
            course_id=999999,
            topic="Test Topic"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("Course not found", result["error"])
        
        # Verify no flashcards were created
        self.assertEqual(Flashcard.objects.filter(user=self.user).count(), 0)


class TestEndToEndQuizWorkflow(TransactionTestCase):
    """Test complete quiz generation workflow"""
    
    def setUp(self):
        self.user = UserFactory()
        self.course = CourseFactory(user=self.user)
        
        # Mock external dependencies
        self.mock_llm_patcher = patch('assessments.services.ai_agents.base_agent.ChatOpenAI')
        self.mock_llm = self.mock_llm_patcher.start()
        
        mock_llm_instance = Mock()
        mock_llm_instance.model_name = "gpt-4"
        mock_llm_instance.invoke.return_value = Mock(content="Mock AI response")
        self.mock_llm.return_value = mock_llm_instance
    
    def tearDown(self):
        self.mock_llm_patcher.stop()
    
    @patch('assessments.services.ai_agents.quiz_agent.PydanticOutputParser')
    def test_complete_quiz_generation_workflow(self, mock_parser_class):
        """Test complete quiz generation from request to database"""
        from assessments.services.ai_agents.quiz_agent import QuizWrapper, QuizQuestion as QuizQuestionItem
        
        # Setup mock quiz questions
        mock_questions = [
            QuizQuestionItem(
                question_text="Which algorithm is used for classification?",
                question_type="multiple_choice",
                answer_options=["SVM", "K-means", "PCA", "DBSCAN"],
                correct_answers=["SVM"],
                explanation="SVM is a supervised learning algorithm used for classification",
                difficulty_level="medium",
                cognitive_domain="understand",
                points=1
            ),
            QuizQuestionItem(
                question_text="Explain the bias-variance tradeoff",
                question_type="short_answer",
                answer_options=[],
                correct_answers=["Balance between model complexity and generalization"],
                explanation="Higher bias = underfitting, higher variance = overfitting",
                difficulty_level="hard",
                cognitive_domain="analyze",
                points=2
            )
        ]
        
        mock_wrapper = QuizWrapper(questions=mock_questions)
        
        # Setup parser mock
        mock_parser = Mock()
        mock_parser.get_format_instructions.return_value = "Mock format instructions"
        mock_parser.parse.return_value = mock_wrapper
        mock_parser_class.return_value = mock_parser
        
        # Execute the workflow
        service = get_quiz_service()
        result = service.generate_quiz(
            user_id=self.user.id,
            course_id=self.course.id,
            title="Machine Learning Quiz",
            topic="ML Algorithms",
            question_count=5,
            difficulty_level="medium",
            auto_save=True
        )
        
        # Verify successful generation
        self.assertTrue(result["success"])
        self.assertTrue(result["auto_saved"])
        self.assertEqual(result["question_count"], 2)
        
        # Verify database records
        quizzes = Quiz.objects.filter(user=self.user, course=self.course)
        self.assertEqual(quizzes.count(), 1)
        
        quiz = quizzes.first()
        self.assertEqual(quiz.title, "Machine Learning Quiz")
        self.assertTrue(quiz.generated_by_ai)
        self.assertEqual(quiz.total_questions, 2)
        
        # Verify quiz questions
        questions = QuizQuestion.objects.filter(quiz=quiz)
        self.assertEqual(questions.count(), 2)
        
        mc_question = questions.filter(question_type="multiple_choice").first()
        self.assertIsNotNone(mc_question)
        self.assertIn("classification", mc_question.question_text)
        self.assertEqual(len(mc_question.answer_options), 4)
        self.assertEqual(mc_question.correct_answers, ["SVM"])
        self.assertEqual(mc_question.points, 1)
        
        sa_question = questions.filter(question_type="short_answer").first()
        self.assertIsNotNone(sa_question)
        self.assertIn("bias-variance", sa_question.question_text)
        self.assertEqual(sa_question.points, 2)


class TestAssessmentAPIIntegration(APITestCase):
    """Test assessment API endpoints with agentic AI integration"""
    
    def setUp(self):
        self.user = UserFactory()
        self.course = CourseFactory(user=self.user)
        self.assessment = AssessmentFactory(user=self.user, course=self.course)
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Mock external dependencies
        self.mock_llm_patcher = patch('assessments.services.ai_agents.base_agent.ChatOpenAI')
        self.mock_llm = self.mock_llm_patcher.start()
        
        mock_llm_instance = Mock()
        mock_llm_instance.model_name = "gpt-4"
        mock_llm_instance.invoke.return_value = Mock(content="Mock AI response")
        self.mock_llm.return_value = mock_llm_instance
    
    def tearDown(self):
        self.mock_llm_patcher.stop()
    
    @patch('assessments.services.generators.flashcard_service.FlashcardGenerationService.generate_flashcards')
    @patch('assessments.services.generators.quiz_service.QuizGenerationService.generate_quiz')
    def test_assessment_content_generation_api(self, mock_quiz_gen, mock_flashcard_gen):
        """Test assessment content generation API endpoint"""
        # Setup mock service responses
        mock_flashcard_gen.return_value = {
            "success": True,
            "count": 3,
            "flashcards": [
                {"id": "fc1", "question": "Test Q1", "answer": "Test A1"},
                {"id": "fc2", "question": "Test Q2", "answer": "Test A2"},
                {"id": "fc3", "question": "Test Q3", "answer": "Test A3"}
            ],
            "generation_metadata": {
                "confidence": 0.85,
                "workflow_steps": [{"step": "generation", "result": "success"}],
                "agents_used": ["flashcard_generator"]
            }
        }
        
        mock_quiz_gen.return_value = {
            "success": True,
            "question_count": 2,
            "quiz": {"id": 123, "title": "Generated Quiz", "questions": []},
            "questions": [
                {"id": 1, "question_text": "Quiz Q1", "question_type": "multiple_choice"},
                {"id": 2, "question_text": "Quiz Q2", "question_type": "short_answer"}
            ],
            "generation_metadata": {
                "confidence": 0.9,
                "workflow_steps": [{"step": "quiz_generation", "result": "success"}],
                "agents_used": ["quiz_generator"]
            }
        }
        
        # Make API request
        url = f'/api/assessments/{self.assessment.id}/generate_content/'
        data = {
            "topic": "Machine Learning",
            "content": "Sample educational content about ML algorithms",
            "use_adaptive": False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data["status"], "completed")
        self.assertIn("generated_content", response_data)
        self.assertIn("agent_metadata", response_data)
        
        # Verify flashcard generation
        flashcard_content = response_data["generated_content"]["flashcards"]
        self.assertEqual(flashcard_content["count"], 3)
        self.assertEqual(flashcard_content["confidence"], 0.85)
        
        # Verify quiz generation
        quiz_content = response_data["generated_content"]["quiz"]
        self.assertEqual(quiz_content["quiz_id"], 123)
        self.assertEqual(quiz_content["question_count"], 2)
        self.assertEqual(quiz_content["confidence"], 0.9)
        
        # Verify agent metadata
        self.assertIn("flashcard_generation", response_data["agent_metadata"])
        self.assertIn("quiz_generation", response_data["agent_metadata"])
    
    @patch('assessments.services.generators.quiz_service.QuizGenerationService.generate_adaptive_quiz')
    def test_adaptive_quiz_generation_api(self, mock_adaptive_quiz):
        """Test adaptive quiz generation through API"""
        # Setup mock adaptive response
        mock_adaptive_quiz.return_value = {
            "success": True,
            "question_count": 3,
            "quiz": {"id": 456, "title": "Adaptive Quiz"},
            "questions": [],
            "adaptive_metadata": {
                "starting_difficulty": "medium",
                "user_performance_level": 0.75,
                "adaptation_strategy": "difficulty_based"
            },
            "generation_metadata": {
                "confidence": 0.88,
                "agents_used": ["quiz_generator"]
            }
        }
        
        # Make API request with adaptive flag
        url = f'/api/assessments/{self.assessment.id}/generate_content/'
        data = {
            "topic": "Data Structures",
            "use_adaptive": True
        }
        
        response = self.client.post(url, data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        quiz_content = response_data["generated_content"]["quiz"]
        
        # Verify adaptive metadata is included
        self.assertIn("adaptive_metadata", quiz_content)
        adaptive_meta = quiz_content["adaptive_metadata"]
        self.assertEqual(adaptive_meta["starting_difficulty"], "medium")
        self.assertEqual(adaptive_meta["user_performance_level"], 0.75)
        self.assertEqual(adaptive_meta["adaptation_strategy"], "difficulty_based")
    
    def test_assessment_content_generation_error_handling(self):
        """Test API error handling for content generation"""
        # Test with missing assessment
        url = '/api/assessments/999999/generate_content/'
        data = {"topic": "Test Topic"}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test with authentication error
        self.client.force_authenticate(user=None)
        url = f'/api/assessments/{self.assessment.id}/generate_content/'
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSpacedRepetitionIntegration(TransactionTestCase):
    """Test spaced repetition integration with flashcard workflow"""
    
    def setUp(self):
        self.user = UserFactory()
        self.course = CourseFactory(user=self.user)
        self.flashcard = Flashcard.objects.create(
            user=self.user,
            course=self.course,
            question="What is machine learning?",
            answer="A subset of AI that learns from data",
            difficulty_level="medium"
        )
    
    def test_flashcard_review_updates_spaced_repetition(self):
        """Test that flashcard reviews update spaced repetition parameters"""
        # Initial state
        self.assertEqual(self.flashcard.total_reviews, 0)
        self.assertEqual(self.flashcard.repetitions, 0)
        self.assertEqual(self.flashcard.ease_factor, 2.5)
        self.assertEqual(self.flashcard.interval_days, 1)
        
        # Simulate successful review (quality 4)
        self.flashcard.calculate_next_review(quality_response=4)
        
        # Verify updates
        self.assertEqual(self.flashcard.total_reviews, 1)
        self.assertEqual(self.flashcard.total_correct, 1)
        self.assertEqual(self.flashcard.success_rate, 1.0)
        self.assertEqual(self.flashcard.repetitions, 1)
        self.assertGreater(self.flashcard.ease_factor, 2.5)  # Should increase with good response
        
        # Verify mastery level calculation
        mastery = self.flashcard.mastery_level
        self.assertIn(mastery, ['new', 'learning', 'difficult', 'mastered'])
    
    def test_multiple_review_progression(self):
        """Test flashcard progression through multiple reviews"""
        # First review (correct)
        self.flashcard.calculate_next_review(quality_response=4)
        first_interval = self.flashcard.interval_days
        first_ease = self.flashcard.ease_factor
        
        # Second review (correct)
        self.flashcard.calculate_next_review(quality_response=4)
        second_interval = self.flashcard.interval_days
        second_ease = self.flashcard.ease_factor
        
        # Verify progression
        self.assertGreater(second_interval, first_interval)
        self.assertGreaterEqual(second_ease, first_ease)
        self.assertEqual(self.flashcard.repetitions, 2)
        self.assertEqual(self.flashcard.total_reviews, 2)
        
        # Test incorrect review (resets progress)
        self.flashcard.calculate_next_review(quality_response=1)
        
        # Verify reset
        self.assertEqual(self.flashcard.repetitions, 0)
        self.assertEqual(self.flashcard.interval_days, 1)
        self.assertEqual(self.flashcard.total_reviews, 3)
        self.assertEqual(self.flashcard.total_correct, 2)
        self.assertAlmostEqual(self.flashcard.success_rate, 2/3, places=2)


if __name__ == '__main__':
    pytest.main([__file__])