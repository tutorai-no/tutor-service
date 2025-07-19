"""
Unit tests for FlashcardGenerationAgent
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from assessments.services.ai_agents.flashcard_agent import (
    FlashcardGenerationAgent,
    FlashcardItem,
    FlashcardGenerationPlan,
    FlashcardBatch,
    create_flashcard_agent
)
from assessments.services.ai_agents.base_agent import (
    AgentRole,
    GenerationContext,
    AgentDecision
)
from assessments.tests.fixtures import (
    BaseTestCase,
    MockLLM,
    MockPydanticParser,
    create_mock_generation_context,
    create_mock_content_analysis
)


class TestFlashcardItem(TestCase):
    """Test FlashcardItem model"""
    
    def test_flashcard_item_creation(self):
        """Test creating a flashcard item"""
        item = FlashcardItem(
            question="What is Python?",
            answer="A programming language",
            explanation="Python is a high-level programming language",
            format_type="basic_qa",
            difficulty_level="easy",
            cognitive_level="remember",
            tags=["python", "programming"],
            learning_objective="Understand Python basics"
        )
        
        self.assertEqual(item.question, "What is Python?")
        self.assertEqual(item.answer, "A programming language")
        self.assertEqual(item.format_type, "basic_qa")
        self.assertEqual(item.difficulty_level, "easy")
        self.assertEqual(item.cognitive_level, "remember")
        self.assertEqual(len(item.tags), 2)
        self.assertEqual(item.estimated_time_seconds, 30)  # Default



class TestFlashcardGenerationPlan(TestCase):
    """Test FlashcardGenerationPlan model"""
    
    def test_generation_plan_creation(self):
        """Test creating a generation plan"""
        plan = FlashcardGenerationPlan(
            strategy="comprehensive_coverage",
            total_cards=10,
            format_distribution={"basic_qa": 6, "definition": 4},
            difficulty_distribution={"easy": 3, "medium": 5, "hard": 2},
            cognitive_levels=["remember", "understand", "apply"],
            sequencing_approach="difficulty_progression",
            quality_checkpoints=["clarity", "accuracy", "relevance"]
        )
        
        self.assertEqual(plan.strategy, "comprehensive_coverage")
        self.assertEqual(plan.total_cards, 10)
        self.assertEqual(plan.format_distribution["basic_qa"], 6)
        self.assertEqual(len(plan.cognitive_levels), 3)
        self.assertEqual(len(plan.quality_checkpoints), 3)


class TestFlashcardBatch(TestCase):
    """Test FlashcardBatch model"""
    
    def test_batch_creation(self):
        """Test creating a flashcard batch"""
        flashcards = [
            FlashcardItem(
                question="Batch question",
                answer="Batch answer",
                format_type="basic_qa",
                difficulty_level="medium"
            )
        ]
        
        batch = FlashcardBatch(
            flashcards=flashcards,
            generation_metadata={"batch_number": 1},
            quality_scores={"clarity": 0.8, "relevance": 0.9}
        )
        
        self.assertEqual(len(batch.flashcards), 1)
        self.assertEqual(batch.generation_metadata["batch_number"], 1)
        self.assertEqual(batch.quality_scores["clarity"], 0.8)


class TestFlashcardGenerationAgent(BaseTestCase):
    """Test FlashcardGenerationAgent functionality"""
    
    def setUp(self):
        super().setUp()
        self.agent = FlashcardGenerationAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.agent.role, AgentRole.FLASHCARD_GENERATOR)
        self.assertIsNotNone(self.agent.llm)
        self.assertGreater(len(self.agent.supported_formats), 5)
        self.assertGreater(len(self.agent.generation_strategies), 3)
    
    @patch('assessments.services.ai_agents.flashcard_agent.PydanticOutputParser')
    def test_create_generation_plan(self, mock_parser_class):
        """Test generation plan creation"""
        # Setup mock plan
        mock_plan = FlashcardGenerationPlan(
            strategy="comprehensive_coverage",
            total_cards=8,
            format_distribution={"basic_qa": 5, "definition": 3},
            difficulty_distribution={"easy": 2, "medium": 4, "hard": 2},
            cognitive_levels=["remember", "understand", "apply"],
            sequencing_approach="difficulty_progression",
            quality_checkpoints=["clarity", "accuracy"]
        )
        
        mock_parser = MockPydanticParser(mock_plan)
        mock_parser_class.return_value = mock_parser
        
        # Test plan creation
        context = create_mock_generation_context()
        analysis = create_mock_content_analysis()
        
        with patch.object(self.agent.llm, 'invoke', return_value=Mock(content="mock plan")):
            plan = self.agent.create_generation_plan(context, analysis)
            
            self.assertIsInstance(plan, FlashcardGenerationPlan)
            self.assertEqual(plan.strategy, "comprehensive_coverage")
            self.assertEqual(plan.total_cards, 8)
            self.assertIn("basic_qa", plan.format_distribution)
    
    def test_get_batch_focus(self):
        """Test batch focus determination"""
        plan = FlashcardGenerationPlan(
            strategy="comprehensive_coverage",
            total_cards=12,
            format_distribution={"basic_qa": 8, "definition": 4},
            difficulty_distribution={"easy": 4, "medium": 6, "hard": 2},
            cognitive_levels=["remember", "understand", "apply"],
            sequencing_approach="difficulty_progression",
            quality_checkpoints=["clarity"]
        )
        
        # Test first batch focus
        focus_1 = self.agent._get_batch_focus(plan, 1, 4)
        self.assertEqual(focus_1["emphasis"], "foundational_concepts")
        self.assertEqual(focus_1["difficulty_bias"], "easy_to_medium")
        self.assertIn("remember", focus_1["cognitive_levels"])
        
        # Test middle batch focus
        focus_2 = self.agent._get_batch_focus(plan, 2, 4)
        self.assertEqual(focus_2["emphasis"], "concept_connections")
        self.assertEqual(focus_2["difficulty_bias"], "medium")
        
        # Test last batch focus
        focus_3 = self.agent._get_batch_focus(plan, 3, 4)
        self.assertEqual(focus_3["emphasis"], "synthesis_and_application")
        self.assertEqual(focus_3["difficulty_bias"], "medium_to_hard")
        self.assertIn("analyze", focus_3["cognitive_levels"])
    
    @patch('assessments.services.ai_agents.flashcard_agent.PydanticOutputParser')
    def test_generate_flashcard_batch(self, mock_parser_class):
        """Test flashcard batch generation"""
        # Setup mock batch
        mock_flashcards = [
            FlashcardItem(
                question="What is machine learning?",
                answer="A subset of AI",
                format_type="basic_qa",
                difficulty_level="medium"
            ),
            FlashcardItem(
                question="Define algorithm",
                answer="A set of rules or instructions",
                format_type="definition",
                difficulty_level="easy"
            )
        ]
        
        mock_batch = FlashcardBatch(flashcards=mock_flashcards)
        mock_parser = MockPydanticParser(mock_batch)
        mock_parser_class.return_value = mock_parser
        
        # Test batch generation
        context = create_mock_generation_context()
        plan = FlashcardGenerationPlan(
            strategy="comprehensive_coverage",
            total_cards=5,
            format_distribution={"basic_qa": 3, "definition": 2},
            difficulty_distribution={"easy": 2, "medium": 3},
            cognitive_levels=["remember", "understand"],
            sequencing_approach="difficulty_progression",
            quality_checkpoints=["clarity"]
        )
        
        with patch.object(self.agent.llm, 'invoke', return_value=Mock(content="mock batch")):
            batch = self.agent._generate_flashcard_batch(context, plan, 2, 1)
            
            self.assertIsInstance(batch, FlashcardBatch)
            self.assertEqual(len(batch.flashcards), 2)
            self.assertEqual(batch.flashcards[0].question, "What is machine learning?")
    
    def test_enhance_batch_quality(self):
        """Test batch quality enhancement"""
        # Create a batch with basic flashcards
        flashcards = [
            FlashcardItem(
                question="Short?",  # Too short
                answer="Yes",      # Too short
                format_type="basic_qa",
                difficulty_level="medium",
                tags=[]           # No tags
            )
        ]
        
        batch = FlashcardBatch(flashcards=flashcards)
        context = create_mock_generation_context()
        
        # Test enhancement
        enhanced_batch = self.agent._enhance_batch_quality(batch, context)
        
        self.assertIsInstance(enhanced_batch, FlashcardBatch)
        # Question should be enhanced (longer)
        self.assertGreater(len(enhanced_batch.flashcards[0].question), 10)
        # Answer should be enhanced
        self.assertGreater(len(enhanced_batch.flashcards[0].answer), 5)
        # Tags should be added
        self.assertGreater(len(enhanced_batch.flashcards[0].tags), 0)
        # Quality scores should be present
        self.assertIn("clarity", enhanced_batch.quality_scores)
    
    @patch('assessments.services.ai_agents.flashcard_agent.PydanticOutputParser')
    def test_execute_task_success(self, mock_parser_class):
        """Test successful task execution"""
        # Setup mocks for the entire workflow
        mock_analysis = create_mock_content_analysis()
        
        mock_plan = FlashcardGenerationPlan(
            strategy="comprehensive_coverage",
            total_cards=3,
            format_distribution={"basic_qa": 2, "definition": 1},
            difficulty_distribution={"easy": 1, "medium": 2},
            cognitive_levels=["remember", "understand"],
            sequencing_approach="difficulty_progression",
            quality_checkpoints=["clarity"]
        )
        
        mock_flashcards = [
            FlashcardItem(
                question="What is AI?",
                answer="Artificial Intelligence",
                format_type="basic_qa",
                difficulty_level="medium"
            )
        ]
        
        mock_batch = FlashcardBatch(flashcards=mock_flashcards)
        
        # Setup parser to return different objects based on context
        def parser_side_effect(pydantic_object):
            if pydantic_object.__name__ == 'ContentAnalysis':
                return MockPydanticParser(mock_analysis)
            elif pydantic_object.__name__ == 'FlashcardGenerationPlan':
                return MockPydanticParser(mock_plan)
            elif pydantic_object.__name__ == 'FlashcardBatch':
                return MockPydanticParser(mock_batch)
            else:
                return MockPydanticParser(mock_analysis)
        
        mock_parser_class.side_effect = parser_side_effect
        
        # Test execution
        context = create_mock_generation_context()
        decision = AgentDecision(
            action="generate_flashcards",
            reasoning="Content is suitable",
            confidence=0.85,
            parameters={"count": 3}
        )
        
        with patch.object(self.agent.llm, 'invoke', return_value=Mock(content="mock response")):
            results = self.agent.execute_task(context, decision)
            
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            
            # Check result structure
            result = results[0]
            self.assertIn("question", result)
            self.assertIn("answer", result)
            self.assertIn("difficulty_level", result)
            self.assertIn("generated_by_ai", result)
            self.assertEqual(result["generated_by_ai"], True)
            self.assertEqual(result["generation_confidence"], 0.85)
    
    def test_execute_task_fallback(self):
        """Test task execution with fallback"""
        context = create_mock_generation_context()
        decision = AgentDecision(
            action="generate_flashcards",
            reasoning="Fallback test",
            confidence=0.5,
            parameters={"count": 3}
        )
        
        # Mock all method calls to raise exceptions to trigger fallback
        with patch.object(self.agent, 'analyze_content', side_effect=Exception("Analysis failed")):
            results = self.agent.execute_task(context, decision)
            
            # Should return fallback results
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 3)  # Based on decision parameters
            
            # Check fallback structure
            result = results[0]
            self.assertIn("question", result)
            self.assertIn("answer", result)
            self.assertEqual(result["ai_model_used"], "fallback")
            self.assertEqual(result["generation_confidence"], 0.5)
    
    def test_fallback_generation(self):
        """Test fallback generation method"""
        context = create_mock_generation_context()
        decision = AgentDecision(
            action="fallback",
            reasoning="Testing fallback",
            confidence=0.5,
            parameters={"count": 2}
        )
        
        results = self.agent._fallback_generation(context, decision)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        
        # Check fallback content
        for i, result in enumerate(results):
            self.assertIn(f"Question {i+1}", result["question"])
            self.assertIn(context.topic, result["question"])
            self.assertEqual(result["difficulty_level"], context.difficulty_level)
            self.assertEqual(result["generation_confidence"], 0.5)
    
    def test_error_handling_in_plan_creation(self):
        """Test error handling in plan creation"""
        context = create_mock_generation_context()
        analysis = create_mock_content_analysis()
        
        # Mock LLM to raise an exception
        with patch.object(self.agent.llm, 'invoke', side_effect=Exception("Plan creation failed")):
            plan = self.agent.create_generation_plan(context, analysis)
            
            # Should return fallback plan
            self.assertIsInstance(plan, FlashcardGenerationPlan)
            self.assertEqual(plan.strategy, "comprehensive_coverage")
            self.assertEqual(plan.total_cards, 10)
            self.assertIn("basic_qa", plan.format_distribution)


class TestFlashcardAgentFactory(TestCase):
    """Test flashcard agent factory function"""
    
    @patch('assessments.services.ai_agents.flashcard_agent.ChatOpenAI')
    def test_create_flashcard_agent(self, mock_llm_class):
        """Test factory function"""
        mock_llm_class.return_value = MockLLM()
        
        agent = create_flashcard_agent()
        
        self.assertIsInstance(agent, FlashcardGenerationAgent)
        self.assertEqual(agent.role, AgentRole.FLASHCARD_GENERATOR)
    
    @patch('assessments.services.ai_agents.flashcard_agent.ChatOpenAI')
    def test_create_flashcard_agent_with_model(self, mock_llm_class):
        """Test factory function with custom model"""
        mock_llm_class.return_value = MockLLM()
        
        agent = create_flashcard_agent(model_name="gpt-4")
        
        self.assertIsInstance(agent, FlashcardGenerationAgent)
        mock_llm_class.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])