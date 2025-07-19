"""
Unit tests for BaseAIAgent and ContentGenerationOrchestrator
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from assessments.services.ai_agents.base_agent import (
    BaseAIAgent, 
    ContentGenerationOrchestrator,
    AgentRole,
    GenerationContext,
    ContentAnalysis,
    AgentDecision
)
from assessments.tests.fixtures import (
    BaseTestCase,
    MockLLM,
    MockRetrievalClient,
    MockPydanticParser,
    create_mock_generation_context,
    create_mock_content_analysis
)


class TestGenerationContext(TestCase):
    """Test GenerationContext data class"""
    
    def test_context_creation(self):
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
    
    def test_context_with_all_fields(self):
        """Test creating context with all fields"""
        context = GenerationContext(
            course_id=2,
            user_id=3,
            content="Advanced content",
            topic="Machine Learning",
            difficulty_level="hard",
            learning_objectives=["Understand concepts", "Apply knowledge"],
            target_audience="graduate",
            document_ids=[1, 2, 3],
            constraints={"count": 10, "time_limit": 30}
        )
        
        self.assertEqual(context.course_id, 2)
        self.assertEqual(context.difficulty_level, "hard")
        self.assertEqual(len(context.learning_objectives), 2)
        self.assertEqual(context.target_audience, "graduate")
        self.assertEqual(len(context.document_ids), 3)
        self.assertEqual(context.constraints["count"], 10)


class TestContentAnalysis(TestCase):
    """Test ContentAnalysis model"""
    
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


class TestAgentDecision(TestCase):
    """Test AgentDecision model"""
    
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


class ConcreteAgent(BaseAIAgent):
    """Concrete implementation of BaseAIAgent for testing"""
    
    def execute_task(self, context, decision):
        """Mock implementation"""
        return [{"test": "result"}]


class TestBaseAIAgent(BaseTestCase):
    """Test BaseAIAgent functionality"""
    
    def setUp(self):
        super().setUp()
        self.agent = ConcreteAgent(AgentRole.CONTENT_ANALYZER)
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.agent.role, AgentRole.CONTENT_ANALYZER)
        self.assertIsNotNone(self.agent.llm)
        self.assertIsNotNone(self.agent.retrieval_client)
        self.assertEqual(len(self.agent.conversation_history), 0)
    
    @patch('assessments.services.ai_agents.base_agent.PydanticOutputParser')
    def test_analyze_content(self, mock_parser_class):
        """Test content analysis"""
        # Setup mock parser
        mock_analysis = create_mock_content_analysis()
        mock_parser = MockPydanticParser(mock_analysis)
        mock_parser_class.return_value = mock_parser
        
        # Setup mock chain
        with patch.object(self.agent.llm, 'invoke', return_value=Mock(content="mock response")):
            context = create_mock_generation_context()
            result = self.agent.analyze_content(context)
            
            self.assertIsInstance(result, ContentAnalysis)
            self.assertEqual(result.complexity_level, "moderate")
            self.assertEqual(len(result.key_concepts), 3)
    
    @patch('assessments.services.ai_agents.base_agent.PydanticOutputParser')
    def test_make_decision(self, mock_parser_class):
        """Test decision making"""
        # Setup mock decision
        mock_decision = AgentDecision(
            action="test_action",
            reasoning="Test reasoning",
            confidence=0.8,
            parameters={"test": "param"}
        )
        mock_parser = MockPydanticParser(mock_decision)
        mock_parser_class.return_value = mock_parser
        
        # Test decision making
        context = create_mock_generation_context()
        analysis = create_mock_content_analysis()
        
        with patch.object(self.agent.llm, 'invoke', return_value=Mock(content="mock response")):
            result = self.agent.make_decision(context, analysis)
            
            self.assertIsInstance(result, AgentDecision)
            self.assertEqual(result.action, "test_action")
            self.assertEqual(result.confidence, 0.8)
    
    def test_enhance_with_retrieval(self):
        """Test retrieval enhancement"""
        context = create_mock_generation_context()
        query = "test query"
        
        enhanced_content = self.agent.enhance_with_retrieval(context, query)
        
        self.assertIn(context.content, enhanced_content)
        self.assertIn("Mock context", enhanced_content)
        self.assertIn("Additional Context", enhanced_content)
    
    def test_reflect_on_results(self):
        """Test result reflection"""
        generated_items = [{"question": "Test?", "answer": "Test answer"}]
        context = create_mock_generation_context()
        
        with patch.object(self.agent.llm, 'invoke', return_value=Mock(content="Reflection response")):
            reflection = self.agent.reflect_on_results(generated_items, context)
            
            self.assertIsInstance(reflection, dict)
            self.assertIn("quality_score", reflection)
            self.assertIn("strengths", reflection)
            self.assertIn("improvements", reflection)
            self.assertIn("recommendation", reflection)
    
    def test_update_conversation_history(self):
        """Test conversation history management"""
        self.agent.update_conversation_history("user", "Test message 1")
        self.agent.update_conversation_history("assistant", "Test response 1")
        
        self.assertEqual(len(self.agent.conversation_history), 2)
        self.assertEqual(self.agent.conversation_history[0]["role"], "user")
        self.assertEqual(self.agent.conversation_history[1]["role"], "assistant")
        
        # Test history truncation (add 10 more messages)
        for i in range(10):
            self.agent.update_conversation_history("user", f"Message {i}")
        
        # Should keep only last 10 messages
        self.assertEqual(len(self.agent.conversation_history), 10)
    
    def test_error_handling_in_analysis(self):
        """Test error handling in content analysis"""
        context = create_mock_generation_context()
        
        # Mock an exception in the LLM call
        with patch.object(self.agent.llm, 'invoke', side_effect=Exception("AI Error")):
            result = self.agent.analyze_content(context)
            
            # Should return fallback analysis
            self.assertIsInstance(result, ContentAnalysis)
            self.assertEqual(result.complexity_level, "moderate")
            self.assertEqual(result.quality_indicators["confidence"], 0.5)
    
    def test_error_handling_in_decision(self):
        """Test error handling in decision making"""
        context = create_mock_generation_context()
        analysis = create_mock_content_analysis()
        
        # Mock an exception in the LLM call
        with patch.object(self.agent.llm, 'invoke', side_effect=Exception("AI Error")):
            result = self.agent.make_decision(context, analysis)
            
            # Should return fallback decision
            self.assertIsInstance(result, AgentDecision)
            self.assertEqual(result.action, "standard_generation")
            self.assertEqual(result.confidence, 0.5)


class TestContentGenerationOrchestrator(BaseTestCase):
    """Test ContentGenerationOrchestrator"""
    
    def setUp(self):
        super().setUp()
        self.orchestrator = ContentGenerationOrchestrator()
        self.test_agent = ConcreteAgent(AgentRole.FLASHCARD_GENERATOR)
        self.orchestrator.register_agent(self.test_agent)
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = ContentGenerationOrchestrator()
        self.assertEqual(len(orchestrator.agents), 0)
        self.assertEqual(len(orchestrator.workflow_history), 0)
    
    def test_register_agent(self):
        """Test agent registration"""
        orchestrator = ContentGenerationOrchestrator()
        agent = ConcreteAgent(AgentRole.QUIZ_GENERATOR)
        
        orchestrator.register_agent(agent)
        
        self.assertEqual(len(orchestrator.agents), 1)
        self.assertIn(AgentRole.QUIZ_GENERATOR, orchestrator.agents)
        self.assertEqual(orchestrator.agents[AgentRole.QUIZ_GENERATOR], agent)
    
    @patch('assessments.services.ai_agents.base_agent.PydanticOutputParser')
    def test_orchestrate_generation_success(self, mock_parser_class):
        """Test successful orchestrated generation"""
        # Setup mocks
        mock_analysis = create_mock_content_analysis()
        mock_decision = AgentDecision(
            action="generate_content",
            reasoning="Test reasoning",
            confidence=0.85,
            parameters={"count": 5}
        )
        
        mock_parser = Mock()
        mock_parser.get_format_instructions.return_value = "Mock instructions"
        mock_parser_class.return_value = mock_parser
        
        # Mock the chain operations
        with patch.object(self.test_agent.llm, 'invoke') as mock_invoke:
            # First call returns analysis, second returns decision
            mock_invoke.side_effect = [
                Mock(content="analysis"),
                Mock(content="decision")
            ]
            
            # Mock the parser to return our mock objects
            def parse_side_effect(content):
                if "analysis" in str(content):
                    return mock_analysis
                else:
                    return mock_decision
            
            mock_parser.parse = Mock(side_effect=parse_side_effect)
            
            # Test orchestration
            context = create_mock_generation_context()
            results = self.orchestrator.orchestrate_generation(
                context=context,
                primary_agent_role=AgentRole.FLASHCARD_GENERATOR,
                use_quality_assessment=False
            )
            
            self.assertIn("generated_content", results)
            self.assertIn("workflow_steps", results)
            self.assertIn("agents_used", results)
            self.assertEqual(results["total_confidence"], 0.85)
    
    def test_orchestrate_generation_missing_agent(self):
        """Test orchestration with missing agent"""
        context = create_mock_generation_context()
        
        results = self.orchestrator.orchestrate_generation(
            context=context,
            primary_agent_role=AgentRole.QUALITY_ASSESSOR,  # Not registered
            use_quality_assessment=False
        )
        
        self.assertIn("error", results)
        self.assertIn("not registered", results["error"])
    
    def test_get_agent_recommendations(self):
        """Test agent recommendations"""
        # Test with simple content
        simple_context = GenerationContext(
            course_id=1,
            user_id=1,
            content="Short content",
            topic="Simple topic"
        )
        
        recommendations = self.orchestrator.get_agent_recommendations(simple_context)
        
        self.assertEqual(recommendations["complexity"], "simple")
        self.assertEqual(recommendations["suggested_workflow"], "basic_generation")
        self.assertIn("agents", recommendations)
        
        # Test with complex content
        complex_context = GenerationContext(
            course_id=1,
            user_id=1,
            content="A" * 3000,  # Long content
            topic="Complex topic",
            learning_objectives=["Objective 1", "Objective 2"]
        )
        
        recommendations = self.orchestrator.get_agent_recommendations(complex_context)
        
        self.assertEqual(recommendations["complexity"], "high")
        self.assertEqual(recommendations["suggested_workflow"], "full_agent_collaboration")
        self.assertGreater(len(recommendations["agents"]), 2)
    
    def test_workflow_history_tracking(self):
        """Test workflow history tracking"""
        initial_history_length = len(self.orchestrator.workflow_history)
        
        context = create_mock_generation_context()
        
        # Mock successful generation
        with patch.object(self.test_agent, 'analyze_content', return_value=create_mock_content_analysis()):
            with patch.object(self.test_agent, 'make_decision', return_value=AgentDecision(
                action="test", reasoning="test", confidence=0.8
            )):
                with patch.object(self.test_agent, 'execute_task', return_value=[{"test": "result"}]):
                    self.orchestrator.orchestrate_generation(
                        context=context,
                        primary_agent_role=AgentRole.FLASHCARD_GENERATOR
                    )
        
        # Verify history was recorded
        self.assertEqual(len(self.orchestrator.workflow_history), initial_history_length + 1)
        latest_entry = self.orchestrator.workflow_history[-1]
        self.assertIn("context_summary", latest_entry)
        self.assertIn("results", latest_entry)


if __name__ == '__main__':
    pytest.main([__file__])