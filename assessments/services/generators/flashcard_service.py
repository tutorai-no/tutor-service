"""
Flashcard Generation Service

Advanced flashcard generation service with sophisticated multi-format generation.
Migrated and enhanced from src/learning_materials/flashcards/flashcards_service.py
"""
import logging
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.conf import settings
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from assessments.models import Flashcard
from courses.models import Course
from ..ai_agents.base_agent import GenerationContext, ContentGenerationOrchestrator, AgentRole
from ..ai_agents.flashcard_agent import create_flashcard_agent

User = get_user_model()
logger = logging.getLogger(__name__)


class FlashcardData(BaseModel):
    """Pydantic model for individual flashcard data."""
    front: str
    back: str
    page_num: Optional[int] = None
    document_name: Optional[str] = None


class FlashcardWrapper(BaseModel):
    """Wrapper for multiple flashcards from sophisticated generation."""
    flashcards: List[FlashcardData]


class AdvancedFlashcardGenerator:
    """
    Advanced flashcard generator with multi-format support.
    Migrated from src/learning_materials/flashcards/flashcards_service.py
    """
    
    def __init__(self):
        self.model = ChatOpenAI(
            temperature=0,
            api_key=getattr(settings, 'OPENAI_API_KEY', None),
            model=getattr(settings, 'LLM_MODEL', 'gpt-4o-mini')
        )
        self.parser = PydanticOutputParser(pydantic_object=FlashcardWrapper)
    
    def generate_flashcards(
        self, 
        content: str, 
        language: str = "en",
        page_num: Optional[int] = None,
        document_name: Optional[str] = None
    ) -> List[FlashcardData]:
        """
        Generate sophisticated multi-format flashcards from content.
        
        Args:
            content: Source content for flashcard generation
            language: Language code for generation
            page_num: Optional page number for context
            document_name: Optional document name for context
            
        Returns:
            List of generated flashcard data
        """
        try:
            template = self._generate_template(content, language)
            
            prompt = PromptTemplate(
                template="Answer the user query.\n{format_instructions}\n{query}\n",
                input_variables=["query"],
                partial_variables={
                    "format_instructions": self.parser.get_format_instructions()
                },
            )
            
            # Create the LangChain with prompt, model, and parser
            chain = prompt | self.model | self.parser
            
            # Generate flashcards
            wrapper = chain.invoke({"query": template})
            flashcards = wrapper.flashcards
            
            # Set context information
            for flashcard in flashcards:
                if page_num is not None:
                    flashcard.page_num = page_num
                if document_name:
                    flashcard.document_name = document_name
            
            logger.info(f"Generated {len(flashcards)} flashcards using advanced multi-format algorithm")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating advanced flashcards: {str(e)}")
            return []
    
    def _generate_template(self, context: str, language: str = "en") -> str:
        """
        Generate sophisticated flashcard template with multiple formats.
        Migrated from src/ with enhancements.
        """
        template = f"""Create flashcards from the provided text using any of the following formats: Standard Q&A, Vocabulary, Fill-in-the-Blank, Multiple Choice, and True/False. Choose the best format(s) based on the content of the text.  
        
        The following examples are provided in English solely for guidance on the desired format. Do not include these examples in your final output:
        
        1. Q&A:
        * Front: "What is a question?"
        * Back: "This is an answer."
        
        2. Vocabulary:
        * Front: "Word"
        * Back: "This is the definition."
        
        3. Fill-in-the-Blank:
        * Front: "The ... is ____."
        * Back: "The ... is <answer>."
        
        4. Multiple Choice:
        * Front: "<question> (a) <option1> (b) <option2> (c) <option3>"
        * Back: "(x) <correct answer>"
        
        5. True/False:
        * Front: "This is a statement."
        * Back: "True/False"
        
        Generate all flashcards in the language corresponding to the language code "{language}". If this code represents a language other than English, ensure that every flashcard (both front and back) is entirely in that language.

        The same information shall not be repeated in multiple flashcards. Each flashcard should focus on a unique piece of information or concept. Avoid generating flashcards that are too similar to each other.
        
        Generate flashcards that best represent the content of the text. Do NOT ask questions about meta data from the text, like author or publisher. Each flashcard should be clear, directly derived from the text, and formatted using only the styles listed above.
        
        Text:
        {context}
        """
        
        return template
    


class FlashcardGenerationService:
    """
    Service for generating flashcards using agentic AI.
    
    This service provides a high-level interface for flashcard generation,
    handling business logic, validation, and database operations.
    """
    
    def __init__(self):
        self.orchestrator = ContentGenerationOrchestrator()
        self.advanced_generator = AdvancedFlashcardGenerator()
        self._setup_agents()
    
    def _setup_agents(self):
        """Set up the AI agents for flashcard generation"""
        try:
            flashcard_agent = create_flashcard_agent()
            self.orchestrator.register_agent(flashcard_agent)
            logger.info("Flashcard generation agents initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up flashcard agents: {str(e)}")
    
    def generate_flashcards(
        self,
        user_id: int,
        course_id: int,
        content: str = None,
        topic: str = "",
        document_ids: List[int] = None,
        count: int = 10,
        difficulty_level: str = "medium",
        learning_objectives: List[str] = None,
        tags: List[str] = None,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Generate flashcards using agentic AI.
        
        Args:
            user_id: ID of the user requesting generation
            course_id: ID of the course
            content: Direct content to generate from
            topic: Topic to search for if no content provided
            document_ids: Specific document IDs to use
            count: Number of flashcards to generate
            difficulty_level: Difficulty level (easy, medium, hard)
            learning_objectives: Learning objectives to align with
            tags: Tags to apply to generated flashcards
            auto_save: Whether to automatically save to database
            
        Returns:
            Dictionary with generation results and metadata
        """
        try:
            # Validate inputs
            user = User.objects.get(id=user_id)
            course = Course.objects.get(id=course_id, user=user)
            
            if not content and not topic:
                raise ValueError("Either content or topic must be provided")
            
            # Create generation context
            context = GenerationContext(
                course_id=course_id,
                user_id=user_id,
                content=content or "",
                topic=topic,
                difficulty_level=difficulty_level,
                learning_objectives=learning_objectives or [],
                document_ids=document_ids,
                constraints={
                    "count": count,
                    "tags": tags or [],
                    "auto_save": auto_save
                }
            )
            
            # Orchestrate generation
            results = self.orchestrator.orchestrate_generation(
                context=context,
                primary_agent_role=AgentRole.FLASHCARD_GENERATOR,
                use_quality_assessment=True
            )
            
            # Process results
            if results.get("error"):
                return {
                    "success": False,
                    "error": results["error"],
                    "flashcards": [],
                    "metadata": results
                }
            
            generated_flashcards = results.get("generated_content", [])
            
            # Save to database if requested
            saved_flashcards = []
            if auto_save and generated_flashcards:
                saved_flashcards = self._save_flashcards_to_db(
                    user, course, generated_flashcards, tags
                )
            
            # Prepare response
            response = {
                "success": True,
                "flashcards": saved_flashcards if auto_save else generated_flashcards,
                "count": len(generated_flashcards),
                "auto_saved": auto_save,
                "generation_metadata": {
                    "workflow_steps": results.get("workflow_steps", []),
                    "agents_used": results.get("agents_used", []),
                    "confidence": results.get("total_confidence", 0.0),
                    "quality_assessment": results.get("quality_assessment")
                }
            }
            
            logger.info(f"Successfully generated {len(generated_flashcards)} flashcards for course {course_id}")
            return response
            
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {"success": False, "error": "User not found", "flashcards": []}
        except Course.DoesNotExist:
            logger.error(f"Course {course_id} not found for user {user_id}")
            return {"success": False, "error": "Course not found", "flashcards": []}
        except Exception as e:
            logger.error(f"Error in flashcard generation: {str(e)}")
            return {"success": False, "error": str(e), "flashcards": []}
    
    def _save_flashcards_to_db(
        self,
        user: User,
        course: Course,
        flashcard_data: List[Dict[str, Any]],
        additional_tags: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Save generated flashcards to the database.
        
        Args:
            user: User instance
            course: Course instance
            flashcard_data: List of flashcard dictionaries
            additional_tags: Additional tags to apply
            
        Returns:
            List of saved flashcard dictionaries with IDs
        """
        saved_flashcards = []
        
        try:
            with transaction.atomic():
                for fc_data in flashcard_data:
                    # Merge tags
                    tags = fc_data.get("tags", [])
                    if additional_tags:
                        tags.extend(additional_tags)
                    
                    # Create flashcard
                    flashcard = Flashcard.objects.create(
                        user=user,
                        course=course,
                        question=fc_data.get("question", ""),
                        answer=fc_data.get("answer", ""),
                        explanation=fc_data.get("explanation", ""),
                        difficulty_level=fc_data.get("difficulty_level", "medium"),
                        tags=list(set(tags)),  # Remove duplicates
                        source_content=fc_data.get("source_content", ""),
                        generated_by_ai=fc_data.get("generated_by_ai", True),
                        ai_model_used=fc_data.get("ai_model_used", ""),
                        generation_confidence=fc_data.get("generation_confidence", 0.8)
                    )
                    
                    # Convert to dictionary with ID
                    flashcard_dict = {
                        "id": str(flashcard.id),
                        "question": flashcard.question,
                        "answer": flashcard.answer,
                        "explanation": flashcard.explanation,
                        "difficulty_level": flashcard.difficulty_level,
                        "tags": flashcard.tags,
                        "created_at": flashcard.created_at.isoformat(),
                        "is_active": flashcard.is_active,
                        "mastery_level": flashcard.mastery_level,
                        "next_review_date": flashcard.next_review_date.isoformat()
                    }
                    saved_flashcards.append(flashcard_dict)
                
                logger.info(f"Saved {len(saved_flashcards)} flashcards to database")
                
        except Exception as e:
            logger.error(f"Error saving flashcards to database: {str(e)}")
            # Return the original data without IDs if saving fails
            return flashcard_data
        
        return saved_flashcards
    
    def bulk_generate_from_documents(
        self,
        user_id: int,
        course_id: int,
        document_ids: List[int],
        cards_per_document: int = 5,
        difficulty_level: str = "medium",
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Generate flashcards from multiple documents in bulk.
        
        Args:
            user_id: ID of the user
            course_id: ID of the course
            document_ids: List of document IDs to process
            cards_per_document: Number of cards per document
            difficulty_level: Difficulty level for all cards
            auto_save: Whether to auto-save to database
            
        Returns:
            Dictionary with bulk generation results
        """
        try:
            from core.services.retrieval_client import get_retrieval_client
            
            retrieval_client = get_retrieval_client()
            all_results = []
            total_flashcards = 0
            
            for doc_id in document_ids:
                try:
                    # Get content for this document
                    content = retrieval_client.get_page_range(doc_id, 1, 999)  # Get all pages
                    
                    if content:
                        # Generate flashcards for this document
                        result = self.generate_flashcards(
                            user_id=user_id,
                            course_id=course_id,
                            content=content,
                            topic=f"Document {doc_id} content",
                            count=cards_per_document,
                            difficulty_level=difficulty_level,
                            tags=[f"doc_{doc_id}"],
                            auto_save=auto_save
                        )
                        
                        result["document_id"] = doc_id
                        all_results.append(result)
                        
                        if result.get("success"):
                            total_flashcards += result.get("count", 0)
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc_id}: {str(e)}")
                    all_results.append({
                        "document_id": doc_id,
                        "success": False,
                        "error": str(e),
                        "flashcards": []
                    })
            
            return {
                "success": True,
                "total_flashcards": total_flashcards,
                "documents_processed": len(document_ids),
                "results_per_document": all_results,
                "summary": {
                    "successful_documents": len([r for r in all_results if r.get("success")]),
                    "failed_documents": len([r for r in all_results if not r.get("success")]),
                    "average_cards_per_document": total_flashcards / len(document_ids) if document_ids else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in bulk flashcard generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_flashcards": 0,
                "results_per_document": []
            }
    
    def get_generation_recommendations(
        self,
        user_id: int,
        course_id: int,
        content_sample: str = ""
    ) -> Dict[str, Any]:
        """
        Get recommendations for flashcard generation based on content analysis.
        
        Args:
            user_id: ID of the user
            course_id: ID of the course
            content_sample: Sample content to analyze
            
        Returns:
            Dictionary with generation recommendations
        """
        try:
            if not content_sample:
                return {
                    "recommendations": {
                        "suggested_count": 10,
                        "difficulty_level": "medium",
                        "formats": ["basic_qa", "definition"],
                        "estimated_time_minutes": 15
                    }
                }
            
            # Create minimal context for analysis
            context = GenerationContext(
                course_id=course_id,
                user_id=user_id,
                content=content_sample,
                topic="content analysis"
            )
            
            # Get agent recommendations
            agent_recommendations = self.orchestrator.get_agent_recommendations(context)
            
            # Analyze content complexity
            content_length = len(content_sample)
            
            if content_length < 500:
                suggested_count = 3
                time_estimate = 5
            elif content_length < 2000:
                suggested_count = 8
                time_estimate = 12
            else:
                suggested_count = 15
                time_estimate = 20
            
            return {
                "recommendations": {
                    "suggested_count": suggested_count,
                    "difficulty_level": "medium",
                    "formats": ["basic_qa", "definition", "fill_blank"],
                    "estimated_time_minutes": time_estimate,
                    "agent_workflow": agent_recommendations.get("suggested_workflow", "standard_generation"),
                    "complexity_assessment": agent_recommendations.get("complexity", "moderate")
                },
                "content_analysis": {
                    "length": content_length,
                    "estimated_concepts": max(1, content_length // 200),
                    "readability": "moderate"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting generation recommendations: {str(e)}")
            return {
                "recommendations": {
                    "suggested_count": 5,
                    "difficulty_level": "medium",
                    "formats": ["basic_qa"],
                    "estimated_time_minutes": 8
                },
                "error": str(e)
            }


# Factory function
def get_flashcard_service() -> FlashcardGenerationService:
    """
    Factory function to get a flashcard generation service instance.
    
    Returns:
        FlashcardGenerationService instance
    """
    return FlashcardGenerationService()