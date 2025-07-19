import logging
from typing import Dict, List, Any, Optional
from django.conf import settings
import json
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class FlashcardData(BaseModel):
    """Pydantic model for flashcard generation"""
    question: str = Field(description="The question for the flashcard")
    answer: str = Field(description="The answer for the flashcard")
    explanation: str = Field(description="Optional explanation or context", default="")
    difficulty_level: str = Field(description="Difficulty level: easy, medium, hard", default="medium")


class FlashcardWrapper(BaseModel):
    """Wrapper for multiple flashcards"""
    flashcards: List[FlashcardData]


class QuizQuestionData(BaseModel):
    """Pydantic model for quiz question generation"""
    question_text: str = Field(description="The question text")
    question_type: str = Field(description="Type: multiple_choice, short_answer, true_false")
    answer_options: List[str] = Field(description="List of answer options for multiple choice", default=[])
    correct_answers: List[str] = Field(description="List of correct answers")
    explanation: str = Field(description="Explanation of the correct answer", default="")
    difficulty_level: str = Field(description="Difficulty level: easy, medium, hard", default="medium")


class QuizWrapper(BaseModel):
    """Wrapper for multiple quiz questions"""
    questions: List[QuizQuestionData]


class AIServiceBase:
    """
    Base class for AI service integrations.
    """
    
    def __init__(self, api_key: str = None, provider: str = None):
        self.api_key = api_key or getattr(settings, 'LLM_API_KEY', None)
        self.provider = provider or getattr(settings, 'LLM_PROVIDER', 'openai')
        
        if not self.api_key:
            logger.warning("No API key provided for AI service")
    
    def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a completion from the AI service.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for the API call
            
        Returns:
            Dictionary with completion result
        """
        raise NotImplementedError("Subclasses must implement generate_completion")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            List of embedding values
        """
        raise NotImplementedError("Subclasses must implement generate_embedding")


class OpenAIService(AIServiceBase):
    """
    OpenAI API integration service.
    """
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key, 'openai')
        self.client = None
        
        # Initialize OpenAI client if available
        try:
            import openai
            if self.api_key:
                self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            logger.warning("OpenAI library not installed")
    
    def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate completion using OpenAI API."""
        if not self.client:
            return {
                'error': 'OpenAI client not initialized',
                'content': None
            }
        
        try:
            response = self.client.chat.completions.create(
                model=kwargs.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7)
            )
            
            return {
                'error': None,
                'content': response.choices[0].message.content,
                'usage': response.usage.dict() if response.usage else None
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                'error': str(e),
                'content': None
            }
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI API."""
        if not self.client:
            logger.error("OpenAI client not initialized")
            return []
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            return []


class MockAIService(AIServiceBase):
    """
    Mock AI service for testing and development.
    """
    
    def __init__(self):
        super().__init__("mock-key", "mock")
    
    def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate mock completion."""
        return {
            'error': None,
            'content': f"Mock response for: {prompt[:50]}...",
            'usage': {'total_tokens': 100}
        }
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embeddings."""
        # Return a mock embedding vector
        return [0.1] * 1536  # OpenAI ada-002 embedding size


class AIServiceFactory:
    """
    Factory for creating AI service instances.
    """
    
    @staticmethod
    def create_service(provider: str = None, api_key: str = None) -> AIServiceBase:
        """
        Create an AI service instance.
        
        Args:
            provider: AI service provider ('openai', 'mock')
            api_key: API key for the service
            
        Returns:
            AIServiceBase instance
        """
        provider = provider or getattr(settings, 'LLM_PROVIDER', 'mock')
        
        if provider == 'openai':
            return OpenAIService(api_key)
        elif provider == 'mock':
            return MockAIService()
        else:
            logger.warning(f"Unknown AI provider: {provider}, using mock")
            return MockAIService()


class ContentGenerator:
    """
    Service for generating educational content using AI.
    """
    
    def __init__(self, ai_service: AIServiceBase = None):
        self.ai_service = ai_service or AIServiceFactory.create_service()
    
    def generate_flashcards(self, content: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """
        Generate flashcards from content.
        
        Args:
            content: Source content
            num_cards: Number of flashcards to generate
            
        Returns:
            List of flashcard dictionaries
        """
        prompt = f"""
        Generate {num_cards} flashcards from the following content. 
        Each flashcard should have a clear question on the front and a concise answer on the back.
        Format as JSON array with 'front' and 'back' fields.
        
        Content: {content[:2000]}...
        """
        
        response = self.ai_service.generate_completion(prompt)
        
        if response['error']:
            logger.error(f"Error generating flashcards: {response['error']}")
            return []
        
        try:
            # Try to parse JSON response
            flashcards = json.loads(response['content'])
            return flashcards[:num_cards]
        except (json.JSONDecodeError, TypeError):
            # Fallback to simple parsing
            content_lines = response['content'].split('\n')
            flashcards = []
            
            for i, line in enumerate(content_lines[:num_cards]):
                if line.strip():
                    flashcards.append({
                        'front': f"Question {i+1}: {line[:100]}...",
                        'back': f"Answer {i+1}: Generated from content"
                    })
            
            return flashcards
    
    def generate_quiz_questions(self, content: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Generate quiz questions from content.
        
        Args:
            content: Source content
            num_questions: Number of questions to generate
            
        Returns:
            List of question dictionaries
        """
        prompt = f"""
        Generate {num_questions} multiple choice questions from the following content.
        Each question should have 4 options with one correct answer.
        Format as JSON array with 'question', 'options', and 'correct_answer' fields.
        
        Content: {content[:2000]}...
        """
        
        response = self.ai_service.generate_completion(prompt)
        
        if response['error']:
            logger.error(f"Error generating quiz questions: {response['error']}")
            return []
        
        try:
            # Try to parse JSON response
            questions = json.loads(response['content'])
            return questions[:num_questions]
        except (json.JSONDecodeError, TypeError):
            # Fallback to simple questions
            return [
                {
                    'question': f"Question {i+1} about the content",
                    'options': [
                        f"Option A for question {i+1}",
                        f"Option B for question {i+1}",
                        f"Option C for question {i+1}",
                        f"Option D for question {i+1}"
                    ],
                    'correct_answer': 0
                }
                for i in range(num_questions)
            ]
    
    def generate_summary(self, content: str, max_length: int = 500) -> str:
        """
        Generate a summary of content.
        
        Args:
            content: Source content
            max_length: Maximum summary length
            
        Returns:
            Summary string
        """
        prompt = f"""
        Summarize the following content in {max_length} characters or less.
        Focus on the key points and main ideas.
        
        Content: {content[:3000]}...
        """
        
        response = self.ai_service.generate_completion(prompt, max_tokens=max_length//3)
        
        if response['error']:
            logger.error(f"Error generating summary: {response['error']}")
            return "Summary generation failed"
        
        return response['content'][:max_length]
    
    def generate_study_plan(self, course_content: str, duration_weeks: int = 4) -> Dict[str, Any]:
        """
        Generate a study plan for course content.
        
        Args:
            course_content: Course content to plan for
            duration_weeks: Duration in weeks
            
        Returns:
            Study plan dictionary
        """
        prompt = f"""
        Create a {duration_weeks}-week study plan for the following course content.
        Break down the content into weekly topics and daily tasks.
        Include reading assignments, practice exercises, and review sessions.
        Format as JSON with 'weeks' array containing weekly plans.
        
        Content: {course_content[:2000]}...
        """
        
        response = self.ai_service.generate_completion(prompt)
        
        if response['error']:
            logger.error(f"Error generating study plan: {response['error']}")
            return {'error': response['error']}
        
        try:
            # Try to parse JSON response
            study_plan = json.loads(response['content'])
            return study_plan
        except (json.JSONDecodeError, TypeError):
            # Fallback to simple plan
            return {
                'weeks': [
                    {
                        'week': i+1,
                        'topic': f"Week {i+1} Topic",
                        'tasks': [
                            f"Day {j+1}: Study content",
                            f"Day {j+2}: Practice exercises",
                            f"Day {j+3}: Review and test"
                        ]
                    }
                    for i in range(duration_weeks)
                ]
            }


class LangChainContentGenerator:
    """
    LangChain-based content generator for educational materials.
    """
    
    def __init__(self, api_key: str = None):
        self.llm = ChatOpenAI(
            api_key=api_key or getattr(settings, 'OPENAI_API_KEY', None),
            temperature=0.0,
            model_name=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
        )
    
    def generate_flashcards(
        self,
        content: str,
        count: int = 5,
        difficulty: str = "medium",
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcards using LangChain and structured output.
        
        Args:
            content: Source content for flashcard generation
            count: Number of flashcards to generate
            difficulty: Difficulty level (easy, medium, hard)
            language: Language for generation
            
        Returns:
            List of flashcard dictionaries
        """
        try:
            # Set up parser
            parser = PydanticOutputParser(pydantic_object=FlashcardWrapper)
            
            # Create prompt template
            template = f"""
            Create {{count}} flashcards from the provided text using various formats.
            
            Generate all flashcards in the language corresponding to the language code "{language}".
            
            Content:
            {{content}}
            
            Requirements:
            - Difficulty level: {{difficulty}}
            - Each flashcard should focus on unique information
            - Use clear, concise language
            - Include helpful explanations when needed
            - Vary question types (Q&A, vocabulary, fill-in-blank, etc.)
            
            {{format_instructions}}
            """
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["content", "count", "difficulty"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Create chain
            chain = prompt | self.llm | parser
            
            # Generate flashcards
            result = chain.invoke({
                "content": content[:3000],  # Limit content length
                "count": count,
                "difficulty": difficulty
            })
            
            # Convert to dictionary format
            flashcards = []
            for fc in result.flashcards:
                flashcards.append({
                    "question": fc.question,
                    "answer": fc.answer,
                    "explanation": fc.explanation,
                    "difficulty_level": fc.difficulty_level,
                    "generated_by_ai": True,
                    "ai_model_used": self.llm.model_name,
                    "generation_confidence": 0.8
                })
            
            logger.info(f"Generated {len(flashcards)} flashcards")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            return []
    
    def generate_quiz_questions(
        self,
        content: str,
        count: int = 5,
        question_types: List[str] = None,
        difficulty: str = "medium",
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions using LangChain and structured output.
        
        Args:
            content: Source content for question generation
            count: Number of questions to generate
            question_types: List of question types to include
            difficulty: Difficulty level (easy, medium, hard)
            language: Language for generation
            
        Returns:
            List of quiz question dictionaries
        """
        try:
            # Default question types
            if not question_types:
                question_types = ["multiple_choice", "short_answer"]
            
            # Set up parser
            parser = PydanticOutputParser(pydantic_object=QuizWrapper)
            
            # Create prompt template
            template = f"""
            Create {{count}} quiz questions from the provided text.
            
            Generate all questions in the language corresponding to the language code "{language}".
            
            Content:
            {{content}}
            
            Requirements:
            - Question types: {{question_types}}
            - Difficulty level: {{difficulty}}
            - For multiple choice: provide 4 options with one correct answer
            - For short answer: expect 1-3 sentence responses
            - Include clear explanations for correct answers
            - Test understanding of key concepts
            
            {{format_instructions}}
            """
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["content", "count", "question_types", "difficulty"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Create chain
            chain = prompt | self.llm | parser
            
            # Generate questions
            result = chain.invoke({
                "content": content[:3000],  # Limit content length
                "count": count,
                "question_types": ", ".join(question_types),
                "difficulty": difficulty
            })
            
            # Convert to dictionary format
            questions = []
            for q in result.questions:
                questions.append({
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "answer_options": q.answer_options,
                    "correct_answers": q.correct_answers,
                    "explanation": q.explanation,
                    "difficulty_level": q.difficulty_level,
                    "points": 1,
                    "order": len(questions) + 1
                })
            
            logger.info(f"Generated {len(questions)} quiz questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating quiz questions: {str(e)}")
            return []