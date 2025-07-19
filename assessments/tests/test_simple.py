"""
Simple tests to verify basic functionality without external dependencies
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from assessments.services.ai_agents.base_agent import (
    GenerationContext,
    ContentAnalysis,
    AgentDecision,
    AgentRole
)
from assessments.services.spaced_repetition import SpacedRepetitionService
from assessments.tests.fixtures import UserFactory, CourseFactory, FlashcardFactory

User = get_user_model()


class TestDataModels(TestCase):
    """Test basic data model functionality"""
    
    def test_generation_context_creation(self):
        """Test creating a generation context"""
        context = GenerationContext(
            course_id=1,
            user_id=1,
            content="Test content",
            topic="Test Topic"
        )
        
        self.assertEqual(context.course_id, 1)
        self.assertEqual(context.user_id, 1)
        self.assertEqual(context.content, "Test content")
        self.assertEqual(context.topic, "Test Topic")
        self.assertEqual(context.difficulty_level, "medium")  # Default
        self.assertEqual(context.learning_objectives, [])  # Default
        self.assertEqual(context.constraints, {})  # Default
    
    def test_content_analysis_creation(self):
        """Test creating content analysis"""
        analysis = ContentAnalysis(
            complexity_level="moderate",
            key_concepts=["concept1", "concept2"],
            suitable_formats=["qa", "definition"],
            estimated_items=5,
            quality_indicators={"clarity": 0.8}
        )
        
        self.assertEqual(analysis.complexity_level, "moderate")
        self.assertEqual(len(analysis.key_concepts), 2)
        self.assertEqual(len(analysis.suitable_formats), 2)
        self.assertEqual(analysis.estimated_items, 5)
        self.assertEqual(analysis.quality_indicators["clarity"], 0.8)
    
    def test_agent_decision_creation(self):
        """Test creating agent decision"""
        decision = AgentDecision(
            action="generate_flashcards",
            reasoning="Content is suitable for flashcard generation",
            confidence=0.85,
            parameters={"count": 10, "difficulty": "medium"}
        )
        
        self.assertEqual(decision.action, "generate_flashcards")
        self.assertIn("suitable", decision.reasoning)
        self.assertEqual(decision.confidence, 0.85)
        self.assertEqual(decision.parameters["count"], 10)
        self.assertEqual(decision.fallback_actions, [])  # Default


class TestSpacedRepetitionService(TestCase):
    """Test spaced repetition algorithm"""
    
    def test_calculate_next_review_correct_response(self):
        """Test SM-2 algorithm with correct response"""
        ease_factor, interval, repetitions, next_date = SpacedRepetitionService.calculate_next_review(
            current_ease_factor=2.5,
            current_interval=1,
            repetitions=0,
            quality_response=4  # Good response
        )
        
        # First repetition should give interval of 1
        self.assertEqual(interval, 1)
        self.assertEqual(repetitions, 1)
        self.assertGreater(ease_factor, 2.5)  # Should increase with good response
        self.assertIsNotNone(next_date)
    
    def test_calculate_next_review_incorrect_response(self):
        """Test SM-2 algorithm with incorrect response"""
        ease_factor, interval, repetitions, next_date = SpacedRepetitionService.calculate_next_review(
            current_ease_factor=2.5,
            current_interval=6,
            repetitions=2,
            quality_response=1  # Poor response
        )
        
        # Should reset repetitions and interval
        self.assertEqual(repetitions, 0)
        self.assertEqual(interval, 1)
        self.assertLess(ease_factor, 2.5)  # Should decrease with poor response
        self.assertGreaterEqual(ease_factor, 1.3)  # Should not go below minimum
    
    def test_difficulty_multiplier(self):
        """Test difficulty multipliers"""
        easy_multiplier = SpacedRepetitionService.get_difficulty_multiplier('easy')
        medium_multiplier = SpacedRepetitionService.get_difficulty_multiplier('medium')
        hard_multiplier = SpacedRepetitionService.get_difficulty_multiplier('hard')
        unknown_multiplier = SpacedRepetitionService.get_difficulty_multiplier('unknown')
        
        self.assertEqual(easy_multiplier, 1.2)
        self.assertEqual(medium_multiplier, 1.0)
        self.assertEqual(hard_multiplier, 0.8)
        self.assertEqual(unknown_multiplier, 1.0)  # Default
    
    def test_adjust_for_difficulty(self):
        """Test interval adjustment for difficulty"""
        base_interval = 10
        
        easy_interval = SpacedRepetitionService.adjust_for_difficulty(base_interval, 'easy')
        hard_interval = SpacedRepetitionService.adjust_for_difficulty(base_interval, 'hard')
        
        self.assertEqual(easy_interval, 12)  # 10 * 1.2
        self.assertEqual(hard_interval, 8)   # 10 * 0.8
        
        # Test minimum interval
        short_interval = SpacedRepetitionService.adjust_for_difficulty(1, 'hard')
        self.assertEqual(short_interval, 1)  # Should not go below 1
    
    def test_get_optimal_batch_size(self):
        """Test optimal batch size calculation"""
        # Test normal case
        batch_size = SpacedRepetitionService.get_optimal_batch_size(
            total_due=100,
            available_time_minutes=30,
            avg_time_per_card=30  # 30 seconds
        )
        self.assertEqual(batch_size, 50)  # min(100, 60, 50) = 50
        
        # Test time-constrained case
        batch_size = SpacedRepetitionService.get_optimal_batch_size(
            total_due=100,
            available_time_minutes=10,
            avg_time_per_card=30
        )
        self.assertEqual(batch_size, 20)  # 10 * 60 / 30 = 20
        
        # Test minimum batch size
        batch_size = SpacedRepetitionService.get_optimal_batch_size(
            total_due=0,
            available_time_minutes=5,
            avg_time_per_card=60
        )
        self.assertEqual(batch_size, 1)  # Should not be less than 1


class TestModelFactories(TestCase):
    """Test that model factories work correctly"""
    
    def test_user_factory(self):
        """Test user factory"""
        user = UserFactory()
        
        self.assertIsNotNone(user.username)
        self.assertIsNotNone(user.email)
        self.assertTrue(user.is_active)
        self.assertIn("@test.com", user.email)
    
    def test_course_factory(self):
        """Test course factory"""
        course = CourseFactory()
        
        self.assertIsNotNone(course.name)
        self.assertIsNotNone(course.course_code)
        self.assertIsNotNone(course.user)
        self.assertEqual(course.semester, "Fall 2024")
    
    def test_flashcard_factory(self):
        """Test flashcard factory"""
        flashcard = FlashcardFactory()
        
        self.assertIsNotNone(flashcard.question)
        self.assertIsNotNone(flashcard.answer)
        self.assertIsNotNone(flashcard.user)
        self.assertIsNotNone(flashcard.course)
        self.assertTrue(flashcard.generated_by_ai)
        self.assertIn(flashcard.difficulty_level, ['easy', 'medium', 'hard'])


class TestAgentRoleEnum(TestCase):
    """Test AgentRole enum"""
    
    def test_agent_roles_exist(self):
        """Test that all required agent roles exist"""
        self.assertEqual(AgentRole.CONTENT_ANALYZER.value, "content_analyzer")
        self.assertEqual(AgentRole.FLASHCARD_GENERATOR.value, "flashcard_generator")
        self.assertEqual(AgentRole.QUIZ_GENERATOR.value, "quiz_generator")
        self.assertEqual(AgentRole.QUALITY_ASSESSOR.value, "quality_assessor")
        self.assertEqual(AgentRole.ORCHESTRATOR.value, "orchestrator")
    
    def test_agent_roles_unique(self):
        """Test that agent role values are unique"""
        roles = [role.value for role in AgentRole]
        self.assertEqual(len(roles), len(set(roles)))


class TestBasicImports(TestCase):
    """Test that all modules can be imported without errors"""
    
    def test_import_base_agent(self):
        """Test importing base agent module"""
        try:
            from assessments.services.ai_agents.base_agent import BaseAIAgent
            self.assertTrue(True)  # Import successful
        except ImportError as e:
            self.fail(f"Failed to import BaseAIAgent: {e}")
    
    def test_import_flashcard_agent(self):
        """Test importing flashcard agent module"""
        try:
            from assessments.services.ai_agents.flashcard_agent import FlashcardGenerationAgent
            self.assertTrue(True)  # Import successful
        except ImportError as e:
            self.fail(f"Failed to import FlashcardGenerationAgent: {e}")
    
    def test_import_quiz_agent(self):
        """Test importing quiz agent module"""
        try:
            from assessments.services.ai_agents.quiz_agent import QuizGenerationAgent
            self.assertTrue(True)  # Import successful
        except ImportError as e:
            self.fail(f"Failed to import QuizGenerationAgent: {e}")
    
    def test_import_generation_services(self):
        """Test importing generation services"""
        try:
            from assessments.services.generators.flashcard_service import FlashcardGenerationService
            from assessments.services.generators.quiz_service import QuizGenerationService
            self.assertTrue(True)  # Import successful
        except ImportError as e:
            self.fail(f"Failed to import generation services: {e}")
    
    def test_import_spaced_repetition(self):
        """Test importing spaced repetition service"""
        try:
            from assessments.services.spaced_repetition import SpacedRepetitionService
            self.assertTrue(True)  # Import successful
        except ImportError as e:
            self.fail(f"Failed to import SpacedRepetitionService: {e}")