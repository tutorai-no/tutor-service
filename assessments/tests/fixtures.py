"""
Test fixtures and mock objects for assessments tests
"""

from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from assessments.models import Assessment, Flashcard, Quiz, QuizQuestion
from assessments.services.ai_agents.base_agent import ContentAnalysis, GenerationContext
from courses.models import Course

User = get_user_model()

# Counter for unique test data
_test_counter = 0


def get_next_counter():
    global _test_counter
    _test_counter += 1
    return _test_counter


class UserFactory:
    """Simple factory for creating test users"""

    @staticmethod
    def create(**kwargs):
        counter = get_next_counter()
        defaults = {
            "username": f"testuser{counter}",
            "email": f"testuser{counter}@test.com",
            "first_name": f"Test{counter}",
            "last_name": f"User{counter}",
            "is_active": True,
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)


class CourseFactory:
    """Simple factory for creating test courses"""

    @staticmethod
    def create(**kwargs):
        counter = get_next_counter()
        if "user" not in kwargs:
            kwargs["user"] = UserFactory.create()

        defaults = {
            "name": f"Test Course {counter}",
            "description": f"Test course description {counter}",
            "course_code": f"COURSE{counter:03d}",
            "semester": "Fall 2024",
            "language": "en",
            "difficulty_level": 3,
        }
        defaults.update(kwargs)
        return Course.objects.create(**defaults)


class FlashcardFactory:
    """Simple factory for creating test flashcards"""

    @staticmethod
    def create(**kwargs):
        counter = get_next_counter()
        if "user" not in kwargs:
            kwargs["user"] = UserFactory.create()
        if "course" not in kwargs:
            kwargs["course"] = CourseFactory.create(user=kwargs["user"])

        defaults = {
            "question": f"Test question {counter}?",
            "answer": f"Test answer {counter}",
            "explanation": f"Test explanation {counter}",
            "difficulty_level": "medium",
            "tags": ["test", "generated"],
            "generated_by_ai": True,
        }
        defaults.update(kwargs)
        return Flashcard.objects.create(**defaults)


class QuizFactory:
    """Simple factory for creating test quizzes"""

    @staticmethod
    def create(**kwargs):
        counter = get_next_counter()
        if "user" not in kwargs:
            kwargs["user"] = UserFactory.create()
        if "course" not in kwargs:
            kwargs["course"] = CourseFactory.create(user=kwargs["user"])

        defaults = {
            "title": f"Test Quiz {counter}",
            "description": f"Test quiz description {counter}",
            "quiz_type": "practice",
            "time_limit_minutes": 30,
            "max_attempts": 3,
            "passing_score": 70.0,
        }
        defaults.update(kwargs)
        return Quiz.objects.create(**defaults)


class QuizQuestionFactory:
    """Simple factory for creating test quiz questions"""

    @staticmethod
    def create(**kwargs):
        counter = get_next_counter()
        if "quiz" not in kwargs:
            kwargs["quiz"] = QuizFactory.create()

        defaults = {
            "question_text": f"Test question {counter}?",
            "question_type": "multiple_choice",
            "difficulty_level": "medium",
            "order": counter,
            "points": 1,
            "answer_options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answers": ["Option A"],
            "explanation": f"Test explanation {counter}",
        }
        defaults.update(kwargs)
        return QuizQuestion.objects.create(**defaults)


class AssessmentFactory:
    """Simple factory for creating test assessments"""

    @staticmethod
    def create(**kwargs):
        counter = get_next_counter()
        if "user" not in kwargs:
            kwargs["user"] = UserFactory.create()
        if "course" not in kwargs:
            kwargs["course"] = CourseFactory.create(user=kwargs["user"])

        defaults = {
            "title": f"Test Assessment {counter}",
            "description": f"Test assessment description {counter}",
            "assessment_type": "formative",
            "include_flashcards": True,
            "include_quizzes": True,
            "flashcard_count": 10,
            "quiz_count": 5,
        }
        defaults.update(kwargs)
        return Assessment.objects.create(**defaults)


class MockAIResponse:
    """Mock AI response for testing"""

    def __init__(self, content: str):
        self.content = content


class MockLLM:
    """Mock LangChain LLM for testing that implements Runnable interface"""

    def __init__(self, responses: list[str] = None):
        self.responses = responses or ["Mock AI response"]
        self.call_count = 0
        self.model_name = "mock-gpt-4"
        self.api_key = "mock-key"
        # Add required attributes for LangChain compatibility
        self.temperature = 0.0

    def invoke(self, prompt_or_messages, *args, **kwargs):
        """Mock invoke method compatible with LangChain Runnable interface"""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = self.responses[-1] if self.responses else "Default mock response"

        self.call_count += 1
        return MockAIResponse(response)

    def stream(self, *args, **kwargs):
        """Mock stream method for LangChain compatibility"""
        response = self.invoke(*args, **kwargs)
        yield response

    def batch(self, inputs, *args, **kwargs):
        """Mock batch method for LangChain compatibility"""
        return [self.invoke(inp, *args, **kwargs) for inp in inputs]

    def __or__(self, other):
        """Support for LangChain's pipe operator (|) used in chains"""
        return MockChain([self, other])

    def __ror__(self, other):
        """Support for reverse pipe operator"""
        return MockChain([other, self])


class MockChain:
    """Mock LangChain chain for testing"""

    def __init__(self, components):
        self.components = components

    def invoke(self, inputs, *args, **kwargs):
        """Execute the chain by passing data through components"""
        result = inputs
        for component in self.components:
            if hasattr(component, "invoke"):
                result = component.invoke(result, *args, **kwargs)
            elif hasattr(component, "format"):
                # Handle prompt templates
                if isinstance(result, dict):
                    result = component.format(**result)
                else:
                    result = component.format(result)
            elif hasattr(component, "parse"):
                # Handle parsers - this is likely a MockPydanticParser
                if hasattr(result, "content"):
                    result = component.parse(result.content)
                elif hasattr(component, "return_object"):
                    # This is our MockPydanticParser, return the mock object directly
                    result = component.return_object
                else:
                    result = component.parse(str(result))
        return result

    def __or__(self, other):
        """Support chaining with pipe operator"""
        return MockChain(self.components + [other])


class MockRetrievalClient:
    """Mock retrieval client for testing"""

    def __init__(self):
        self.mock_content = (
            "This is mock content from the retrieval service for testing purposes."
        )

    def get_context(
        self, course_id: int, query: str, limit: int = 5, document_ids: list[int] = None
    ) -> str:
        """Mock context retrieval"""
        return f"Mock context for query '{query}': {self.mock_content}"

    def get_page_range(self, document_id: int, start_page: int, end_page: int) -> str:
        """Mock page range retrieval"""
        return f"Mock content for document {document_id}, pages {start_page}-{end_page}: {self.mock_content}"

    def health_check(self) -> dict[str, Any]:
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
    difficulty_level: str = "medium",
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
        constraints={"count": 5, "auto_save": False},
    )


def create_mock_content_analysis() -> ContentAnalysis:
    """Create a mock content analysis for testing"""
    return ContentAnalysis(
        complexity_level="moderate",
        key_concepts=["concept1", "concept2", "concept3"],
        concept_relationships=[("concept1", "concept2")],
        suitable_formats=["basic_qa", "definition", "multiple_choice"],
        estimated_items=8,
        quality_indicators={"clarity": 0.8, "depth": 0.7, "coverage": 0.9},
    )


def create_mock_flashcard_data() -> list[dict[str, Any]]:
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
            "generation_confidence": 0.85,
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
            "generation_confidence": 0.90,
        },
    ]


def create_mock_quiz_data() -> list[dict[str, Any]]:
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
            "estimated_time_minutes": 1.5,
        },
        {
            "question_text": "Explain the difference between classification and regression.",
            "question_type": "short_answer",
            "answer_options": [],
            "correct_answers": [
                "Classification predicts categories, regression predicts continuous values"
            ],
            "explanation": "Classification outputs discrete labels while regression outputs numerical values",
            "difficulty_level": "medium",
            "points": 2,
            "order": 2,
            "cognitive_domain": "analyze",
            "estimated_time_minutes": 3.0,
        },
    ]


class BaseTestCase(TestCase):
    """Base test case with common setup for assessments tests"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory.create()
        self.course = CourseFactory.create(user=self.user)
        self.assessment = AssessmentFactory.create(user=self.user, course=self.course)

        # Mock external dependencies
        self.mock_llm_patcher = patch(
            "assessments.services.ai_agents.base_agent.ChatOpenAI"
        )
        self.mock_llm = self.mock_llm_patcher.start()
        self.mock_llm.return_value = MockLLM()

        self.mock_retrieval_patcher = patch(
            "assessments.services.ai_agents.base_agent.get_retrieval_client"
        )
        self.mock_retrieval = self.mock_retrieval_patcher.start()
        self.mock_retrieval.return_value = MockRetrievalClient()

        # Mock parser
        self.mock_parser_patcher = patch(
            "assessments.services.ai_agents.base_agent.PydanticOutputParser"
        )
        self.mock_parser = self.mock_parser_patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.mock_llm_patcher.stop()
        self.mock_retrieval_patcher.stop()
        self.mock_parser_patcher.stop()


# Django test case base class handles fixture creation through setUp method
# No pytest fixtures needed when using Django's test framework
