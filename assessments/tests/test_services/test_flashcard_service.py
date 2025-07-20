"""
Unit tests for FlashcardGenerationService
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from assessments.models import Flashcard
from assessments.services.ai_agents.base_agent import AgentRole
from assessments.services.generators.flashcard_service import (
    FlashcardGenerationService,
    get_flashcard_service,
)
from assessments.tests.fixtures import (
    BaseTestCase,
    CourseFactory,
    UserFactory,
    create_mock_flashcard_data,
)

User = get_user_model()


class TestFlashcardGenerationService(BaseTestCase):
    """Test FlashcardGenerationService functionality"""

    def setUp(self):
        super().setUp()
        self.service = FlashcardGenerationService()
        self.user = UserFactory.create()
        self.course = CourseFactory.create(user=self.user)

    def test_service_initialization(self):
        """Test service initialization"""
        service = FlashcardGenerationService()

        self.assertIsNotNone(service.orchestrator)
        self.assertIn(AgentRole.FLASHCARD_GENERATOR, service.orchestrator.agents)

    @patch(
        "assessments.services.generators.flashcard_service.ContentGenerationOrchestrator"
    )
    def test_setup_agents_success(self, mock_orchestrator_class):
        """Test successful agent setup"""
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        with patch(
            "assessments.services.generators.flashcard_service.create_flashcard_agent"
        ) as mock_create_agent:
            mock_agent = Mock()
            mock_create_agent.return_value = mock_agent

            FlashcardGenerationService()

            mock_create_agent.assert_called_once()
            mock_orchestrator.register_agent.assert_called_once_with(mock_agent)

    @patch(
        "assessments.services.generators.flashcard_service.ContentGenerationOrchestrator"
    )
    def test_setup_agents_failure(self, mock_orchestrator_class):
        """Test agent setup with failure"""
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        with patch(
            "assessments.services.generators.flashcard_service.create_flashcard_agent",
            side_effect=Exception("Agent creation failed"),
        ):
            # Should not raise exception, just log error
            service = FlashcardGenerationService()
            self.assertIsNotNone(service.orchestrator)

    def test_generate_flashcards_success(self):
        """Test successful flashcard generation"""
        # Mock orchestrator results
        mock_results = {
            "generated_content": create_mock_flashcard_data(),
            "workflow_steps": [{"step": "generation", "result": "success"}],
            "agents_used": ["flashcard_generator"],
            "total_confidence": 0.85,
            "quality_assessment": {"quality_score": 0.8},
        }

        with patch.object(
            self.service.orchestrator,
            "orchestrate_generation",
            return_value=mock_results,
        ):
            result = self.service.generate_flashcards(
                user_id=self.user.id,
                course_id=self.course.id,
                topic="Machine Learning",
                count=5,
                auto_save=False,
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["count"], 2)  # Based on mock data
            self.assertFalse(result["auto_saved"])
            self.assertEqual(result["generation_metadata"]["confidence"], 0.85)
            self.assertIn("workflow_steps", result["generation_metadata"])

    def test_generate_flashcards_with_content(self):
        """Test flashcard generation with direct content"""
        mock_results = {
            "generated_content": create_mock_flashcard_data(),
            "workflow_steps": [],
            "agents_used": ["flashcard_generator"],
            "total_confidence": 0.9,
        }

        with patch.object(
            self.service.orchestrator,
            "orchestrate_generation",
            return_value=mock_results,
        ):
            result = self.service.generate_flashcards(
                user_id=self.user.id,
                course_id=self.course.id,
                content="Direct content for flashcard generation",
                count=3,
                difficulty_level="hard",
                auto_save=False,
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["count"], 2)

            # Verify the context passed to orchestrator
            call_args = self.service.orchestrator.orchestrate_generation.call_args[1]
            context = call_args["context"]
            self.assertEqual(context.content, "Direct content for flashcard generation")
            self.assertEqual(context.difficulty_level, "hard")
            self.assertEqual(context.constraints["count"], 3)

    def test_generate_flashcards_with_auto_save(self):
        """Test flashcard generation with auto-save enabled"""
        mock_results = {
            "generated_content": create_mock_flashcard_data(),
            "workflow_steps": [],
            "agents_used": ["flashcard_generator"],
            "total_confidence": 0.8,
        }

        with patch.object(
            self.service.orchestrator,
            "orchestrate_generation",
            return_value=mock_results,
        ):
            with patch.object(self.service, "_save_flashcards_to_db") as mock_save:
                mock_save.return_value = [
                    {"id": "123", "question": "Test?", "answer": "Test."}
                ]

                result = self.service.generate_flashcards(
                    user_id=self.user.id,
                    course_id=self.course.id,
                    topic="Test Topic",
                    auto_save=True,
                )

                self.assertTrue(result["success"])
                self.assertTrue(result["auto_saved"])
                mock_save.assert_called_once()

                # Should return saved flashcards, not generated ones
                self.assertEqual(len(result["flashcards"]), 1)
                self.assertEqual(result["flashcards"][0]["id"], "123")

    def test_generate_flashcards_validation_errors(self):
        """Test flashcard generation with validation errors"""
        # Test missing user
        result = self.service.generate_flashcards(
            user_id=999999,  # Non-existent user
            course_id=self.course.id,
            topic="Test Topic",
        )

        self.assertFalse(result["success"])
        self.assertIn("User not found", result["error"])
        self.assertEqual(result["flashcards"], [])

        # Test missing course
        result = self.service.generate_flashcards(
            user_id=self.user.id,
            course_id=999999,  # Non-existent course
            topic="Test Topic",
        )

        self.assertFalse(result["success"])
        self.assertIn("Course not found", result["error"])

        # Test missing content and topic
        result = self.service.generate_flashcards(
            user_id=self.user.id,
            course_id=self.course.id,
            # No content or topic provided
        )

        self.assertFalse(result["success"])
        self.assertIn("Either content or topic must be provided", result["error"])

    def test_generate_flashcards_orchestrator_error(self):
        """Test flashcard generation with orchestrator error"""
        mock_results = {
            "error": "AI service unavailable",
            "generated_content": [],
            "workflow_steps": [],
        }

        with patch.object(
            self.service.orchestrator,
            "orchestrate_generation",
            return_value=mock_results,
        ):
            result = self.service.generate_flashcards(
                user_id=self.user.id, course_id=self.course.id, topic="Test Topic"
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "AI service unavailable")
            self.assertEqual(result["flashcards"], [])

    def test_save_flashcards_to_db_success(self):
        """Test successful flashcard saving to database"""
        flashcard_data = create_mock_flashcard_data()
        additional_tags = ["test_tag"]

        saved_flashcards = self.service._save_flashcards_to_db(
            self.user, self.course, flashcard_data, additional_tags
        )

        self.assertEqual(len(saved_flashcards), 2)

        # Verify database records were created
        db_flashcards = Flashcard.objects.filter(user=self.user, course=self.course)
        self.assertEqual(db_flashcards.count(), 2)

        # Check saved flashcard structure
        saved_fc = saved_flashcards[0]
        self.assertIn("id", saved_fc)
        self.assertIn("question", saved_fc)
        self.assertIn("answer", saved_fc)
        self.assertIn("created_at", saved_fc)
        self.assertIn("mastery_level", saved_fc)

        # Check tags were merged
        db_fc = db_flashcards.first()
        self.assertIn("test_tag", db_fc.tags)
        self.assertIn("ml", db_fc.tags)  # From original data

    def test_save_flashcards_to_db_error(self):
        """Test flashcard saving with database error"""
        flashcard_data = [{"invalid": "data"}]  # Missing required fields

        # This should handle the error gracefully by creating with defaults
        saved_flashcards = self.service._save_flashcards_to_db(
            self.user, self.course, flashcard_data
        )

        # Should create flashcard with empty values for missing fields
        self.assertEqual(len(saved_flashcards), 1)
        self.assertEqual(saved_flashcards[0]["question"], "")
        self.assertEqual(saved_flashcards[0]["answer"], "")
        self.assertEqual(saved_flashcards[0]["difficulty_level"], "medium")

        # One flashcard should be created in database
        self.assertEqual(Flashcard.objects.filter(user=self.user).count(), 1)

    def test_bulk_generate_from_documents(self):
        """Test bulk generation from multiple documents"""
        document_ids = [1, 2, 3]

        # Mock retrieval client
        with patch(
            "core.services.retrieval_client.get_retrieval_client"
        ) as mock_client_factory:
            mock_client = Mock()
            mock_client.get_page_range.side_effect = [
                "Content from document 1",
                "Content from document 2",
                "Content from document 3",
            ]
            mock_client_factory.return_value = mock_client

            # Mock individual generation calls
            with patch.object(self.service, "generate_flashcards") as mock_generate:
                mock_generate.side_effect = [
                    {"success": True, "count": 5, "flashcards": []},
                    {"success": True, "count": 4, "flashcards": []},
                    {"success": False, "error": "Generation failed", "flashcards": []},
                ]

                result = self.service.bulk_generate_from_documents(
                    user_id=self.user.id,
                    course_id=self.course.id,
                    document_ids=document_ids,
                    cards_per_document=5,
                )

                self.assertTrue(result["success"])
                self.assertEqual(result["total_flashcards"], 9)  # 5 + 4 + 0
                self.assertEqual(result["documents_processed"], 3)
                self.assertEqual(len(result["results_per_document"]), 3)

                # Check summary
                self.assertEqual(result["summary"]["successful_documents"], 2)
                self.assertEqual(result["summary"]["failed_documents"], 1)
                self.assertEqual(result["summary"]["average_cards_per_document"], 3.0)

    def test_bulk_generate_error_handling(self):
        """Test bulk generation with error handling"""
        with patch(
            "core.services.retrieval_client.get_retrieval_client",
            side_effect=Exception("Retrieval service error"),
        ):
            result = self.service.bulk_generate_from_documents(
                user_id=self.user.id, course_id=self.course.id, document_ids=[1, 2]
            )

            self.assertFalse(result["success"])
            self.assertIn("Retrieval service error", result["error"])
            self.assertEqual(result["total_flashcards"], 0)

    def test_get_generation_recommendations_no_content(self):
        """Test recommendations with no content sample"""
        result = self.service.get_generation_recommendations(
            user_id=self.user.id, course_id=self.course.id
        )

        self.assertIn("recommendations", result)
        recommendations = result["recommendations"]
        self.assertEqual(recommendations["suggested_count"], 10)
        self.assertEqual(recommendations["difficulty_level"], "medium")
        self.assertIn("basic_qa", recommendations["formats"])
        self.assertEqual(recommendations["estimated_time_minutes"], 15)

    def test_get_generation_recommendations_with_content(self):
        """Test recommendations with content analysis"""
        # Test short content
        short_content = "Short sample content"

        with patch.object(
            self.service.orchestrator, "get_agent_recommendations"
        ) as mock_recommendations:
            mock_recommendations.return_value = {
                "suggested_workflow": "basic_generation",
                "complexity": "simple",
            }

            result = self.service.get_generation_recommendations(
                user_id=self.user.id,
                course_id=self.course.id,
                content_sample=short_content,
            )

            recommendations = result["recommendations"]
            self.assertEqual(recommendations["suggested_count"], 3)  # Short content
            self.assertEqual(recommendations["estimated_time_minutes"], 5)
            self.assertEqual(recommendations["agent_workflow"], "basic_generation")
            self.assertEqual(recommendations["complexity_assessment"], "simple")

            content_analysis = result["content_analysis"]
            self.assertEqual(content_analysis["length"], len(short_content))
            self.assertGreater(content_analysis["estimated_concepts"], 0)

        # Test long content
        long_content = "A" * 2500  # Long content

        result = self.service.get_generation_recommendations(
            user_id=self.user.id, course_id=self.course.id, content_sample=long_content
        )

        recommendations = result["recommendations"]
        self.assertEqual(recommendations["suggested_count"], 15)  # Long content
        self.assertEqual(recommendations["estimated_time_minutes"], 20)

    def test_get_generation_recommendations_error(self):
        """Test recommendations with error handling"""
        with patch.object(
            self.service.orchestrator,
            "get_agent_recommendations",
            side_effect=Exception("Analysis error"),
        ):
            result = self.service.get_generation_recommendations(
                user_id=self.user.id,
                course_id=self.course.id,
                content_sample="test content",
            )

            # Should return fallback recommendations
            self.assertIn("recommendations", result)
            self.assertIn("error", result)
            self.assertEqual(result["recommendations"]["suggested_count"], 5)


class TestFlashcardServiceFactory(TestCase):
    """Test flashcard service factory function"""

    @patch(
        "assessments.services.generators.flashcard_service.FlashcardGenerationService"
    )
    def test_get_flashcard_service(self, mock_service_class):
        """Test factory function"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        service = get_flashcard_service()

        self.assertEqual(service, mock_service)
        mock_service_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
