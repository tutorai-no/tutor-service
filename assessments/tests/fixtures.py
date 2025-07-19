"""
Test fixtures and mock objects for assessments tests
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any
from django.contrib.auth import get_user_model
from django.test import TestCase
import factory
from factory.django import DjangoModelFactory

from courses.models import Course
from assessments.models import Flashcard, Quiz, QuizQuestion, Assessment
from assessments.services.ai_agents.base_agent import GenerationContext, ContentAnalysis

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating test users"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class CourseFactory(DjangoModelFactory):
    """Factory for creating test courses"""
    
    class Meta:
        model = Course
    
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text')
    course_code = factory.Sequence(lambda n: f"COURSE{n:03d}")
    semester = "Fall 2024"
    user = factory.SubFactory(UserFactory)


class FlashcardFactory(DjangoModelFactory):
    """Factory for creating test flashcards"""
    
    class Meta:
        model = Flashcard
    
    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    question = factory.Faker('sentence', nb_words=8)
    answer = factory.Faker('text', max_nb_chars=200)
    explanation = factory.Faker('text', max_nb_chars=150)
    difficulty_level = factory.Iterator(['easy', 'medium', 'hard'])
    tags = factory.LazyFunction(lambda: ['test', 'generated'])
    generated_by_ai = True


class QuizFactory(DjangoModelFactory):
    """Factory for creating test quizzes"""
    
    class Meta:
        model = Quiz
    
    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text')
    quiz_type = factory.Iterator(['practice', 'assessment', 'exam'])
    time_limit_minutes = 30
    max_attempts = 3
    passing_score = 70.0


class QuizQuestionFactory(DjangoModelFactory):
    """Factory for creating test quiz questions"""
    
    class Meta:
        model = QuizQuestion
    
    quiz = factory.SubFactory(QuizFactory)
    question_text = factory.Faker('sentence', nb_words=10)
    question_type = factory.Iterator(['multiple_choice', 'short_answer', 'true_false'])
    difficulty_level = factory.Iterator(['easy', 'medium', 'hard'])
    order = factory.Sequence(lambda n: n + 1)
    points = 1
    answer_options = factory.LazyFunction(lambda: ['Option A', 'Option B', 'Option C', 'Option D'])
    correct_answers = factory.LazyFunction(lambda: ['Option A'])
    explanation = factory.Faker('text', max_nb_chars=100)


class AssessmentFactory(DjangoModelFactory):
    """Factory for creating test assessments"""
    
    class Meta:
        model = Assessment
    
    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text')
    assessment_type = factory.Iterator(['formative', 'summative'])
    include_flashcards = True
    include_quizzes = True
    flashcard_count = 10
    quiz_count = 5


class MockAIResponse:
    """Mock AI response for testing"""
    
    def __init__(self, content: str):
        self.content = content


class MockLLM:
    """Mock LangChain LLM for testing"""
    
    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["Mock AI response"]
        self.call_count = 0
        self.model_name = "mock-gpt-4"
        self.api_key = "mock-key"
    
    def invoke(self, prompt_or_messages):
        """Mock invoke method"""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = self.responses[-1] if self.responses else "Default mock response"
        
        self.call_count += 1
        return MockAIResponse(response)


class MockRetrievalClient:
    """Mock retrieval client for testing"""
    
    def __init__(self):
        self.mock_content = "This is mock content from the retrieval service for testing purposes."
    
    def get_context(self, course_id: int, query: str, limit: int = 5, document_ids: List[int] = None) -> str:
        """Mock context retrieval"""
        return f"Mock context for query '{query}': {self.mock_content}"
    
    def get_page_range(self, document_id: int, start_page: int, end_page: int) -> str:
        """Mock page range retrieval"""
        return f"Mock content for document {document_id}, pages {start_page}-{end_page}: {self.mock_content}"
    
    def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        return {"status": "healthy", "service": "mock-retrieval"}


class MockPydanticParser:
    """Mock Pydantic parser for testing"""
    
    def __init__(self, return_object):
        self.return_object = return_object
        self.pydantic_object = return_object.__class__
    
    def parse(self, text: str):
        """Mock parse method"""
        return self.return_object
    
    def get_format_instructions(self) -> str:
        """Mock format instructions"""
        return "Mock format instructions for testing"


def create_mock_generation_context(
    course_id: int = 1,
    user_id: int = 1,
    content: str = "Test content for generation",
    topic: str = "Test Topic",
    difficulty_level: str = "medium"
) -> GenerationContext:
    """Create a mock generation context for testing"""
    return GenerationContext(
        course_id=course_id,
        user_id=user_id,
        content=content,
        topic=topic,
        difficulty_level=difficulty_level,
        learning_objectives=["Understand test concepts", "Apply test knowledge"],
        document_ids=[1, 2, 3],
        constraints={"count": 5, "auto_save": False}
    )


def create_mock_content_analysis() -> ContentAnalysis:
    """Create a mock content analysis for testing"""
    return ContentAnalysis(
        complexity_level="moderate",
        key_concepts=["concept1", "concept2", "concept3"],
        concept_relationships=[("concept1", "concept2")],
        suitable_formats=["basic_qa", "definition", "multiple_choice"],
        estimated_items=8,
        quality_indicators={"clarity": 0.8, "depth": 0.7, "coverage": 0.9}
    )


def create_mock_flashcard_data() -> List[Dict[str, Any]]:
    """Create mock flashcard data for testing"""
    return [
        {
            "question": "What is machine learning?",
            "answer": "A subset of AI that enables computers to learn without explicit programming",
            "explanation": "Machine learning uses algorithms to find patterns in data",
            "difficulty_level": "medium",
            "tags": ["ml", "ai", "basics"],
            "format_type": "basic_qa",
            "cognitive_level": "understand",
            "generated_by_ai": True,
            "ai_model_used": "mock-gpt-4",
            "generation_confidence": 0.85
        },
        {
            "question": "What does 'supervised learning' mean?",
            "answer": "Learning with labeled training data",
            "explanation": "The algorithm learns from input-output pairs",
            "difficulty_level": "medium",
            "tags": ["ml", "supervised"],
            "format_type": "definition",
            "cognitive_level": "remember",
            "generated_by_ai": True,
            "ai_model_used": "mock-gpt-4",
            "generation_confidence": 0.90
        }
    ]


def create_mock_quiz_data() -> List[Dict[str, Any]]:
    """Create mock quiz question data for testing"""
    return [
        {
            "question_text": "Which of the following is a supervised learning algorithm?",
            "question_type": "multiple_choice",
            "answer_options": ["Linear Regression", "K-means", "DBSCAN", "PCA"],
            "correct_answers": ["Linear Regression"],
            "explanation": "Linear regression uses labeled data to learn the relationship between features and target",
            "difficulty_level": "medium",
            "points": 1,
            "order": 1,
            "cognitive_domain": "understand",
            "estimated_time_minutes": 1.5
        },
        {
            "question_text": "Explain the difference between classification and regression.",
            "question_type": "short_answer",
            "answer_options": [],
            "correct_answers": ["Classification predicts categories, regression predicts continuous values"],
            "explanation": "Classification outputs discrete labels while regression outputs numerical values",
            "difficulty_level": "medium",
            "points": 2,
            "order": 2,
            "cognitive_domain": "analyze",
            "estimated_time_minutes": 3.0
        }
    ]


class BaseTestCase(TestCase):
    """Base test case with common setup for assessments tests"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.course = CourseFactory(user=self.user)
        self.assessment = AssessmentFactory(user=self.user, course=self.course)
        
        # Mock external dependencies
        self.mock_llm_patcher = patch('assessments.services.ai_agents.base_agent.ChatOpenAI')
        self.mock_llm = self.mock_llm_patcher.start()
        self.mock_llm.return_value = MockLLM()
        
        self.mock_retrieval_patcher = patch('assessments.services.ai_agents.base_agent.get_retrieval_client')
        self.mock_retrieval = self.mock_retrieval_patcher.start()
        self.mock_retrieval.return_value = MockRetrievalClient()
        
        # Mock parser
        self.mock_parser_patcher = patch('assessments.services.ai_agents.base_agent.PydanticOutputParser')
        self.mock_parser = self.mock_parser_patcher.start()
        
    def tearDown(self):
        """Clean up after tests"""
        self.mock_llm_patcher.stop()
        self.mock_retrieval_patcher.stop()
        self.mock_parser_patcher.stop()


@pytest.fixture
def user():
    """Pytest fixture for test user"""
    return UserFactory()


@pytest.fixture
def course(user):
    """Pytest fixture for test course"""
    return CourseFactory(user=user)


@pytest.fixture
def assessment(user, course):
    """Pytest fixture for test assessment"""
    return AssessmentFactory(user=user, course=course)


@pytest.fixture
def mock_llm():
    """Pytest fixture for mock LLM"""
    return MockLLM()


@pytest.fixture
def mock_retrieval_client():
    """Pytest fixture for mock retrieval client"""
    return MockRetrievalClient()


@pytest.fixture
def generation_context():
    """Pytest fixture for generation context"""
    return create_mock_generation_context()


@pytest.fixture
def content_analysis():
    """Pytest fixture for content analysis"""
    return create_mock_content_analysis()


@pytest.fixture
def mock_flashcard_data():
    """Pytest fixture for mock flashcard data"""
    return create_mock_flashcard_data()


@pytest.fixture
def mock_quiz_data():
    """Pytest fixture for mock quiz data"""
    return create_mock_quiz_data()