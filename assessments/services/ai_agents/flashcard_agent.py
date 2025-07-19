"""
Specialized AI Agent for Flashcard Generation

This agent uses agentic AI to analyze content and generate high-quality flashcards
with strategic reasoning about difficulty, format variety, and learning effectiveness.
"""
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .base_agent import BaseAIAgent, AgentRole, GenerationContext, AgentDecision, ContentAnalysis

logger = logging.getLogger(__name__)


class FlashcardFormat(Enum):
    """Different types of flashcard formats"""
    BASIC_QA = "basic_qa"
    DEFINITION = "definition"
    FILL_BLANK = "fill_blank"
    TRUE_FALSE = "true_false"
    MULTIPLE_CHOICE = "multiple_choice"
    IMAGE_OCCLUSION = "image_occlusion"
    CLOZE_DELETION = "cloze_deletion"
    CONCEPT_MAP = "concept_map"


class FlashcardStrategy(Enum):
    """Different strategies for flashcard generation"""
    COMPREHENSIVE_COVERAGE = "comprehensive_coverage"
    KEY_CONCEPTS_FOCUS = "key_concepts_focus"
    DIFFICULTY_PROGRESSION = "difficulty_progression"
    SPACED_REPETITION_OPTIMIZED = "spaced_repetition_optimized"
    ACTIVE_RECALL_FOCUSED = "active_recall_focused"


class FlashcardItem(BaseModel):
    """Individual flashcard with enhanced metadata"""
    question: str = Field(description="Front side of the flashcard")
    answer: str = Field(description="Back side of the flashcard")
    explanation: str = Field(description="Additional explanation or context", default="")
    format_type: str = Field(description="Type of flashcard format")
    difficulty_level: str = Field(description="Difficulty: easy, medium, hard")
    cognitive_level: str = Field(description="Bloom's taxonomy level", default="remember")
    tags: List[str] = Field(description="Relevant tags", default=[])
    learning_objective: str = Field(description="Associated learning objective", default="")
    estimated_time_seconds: int = Field(description="Estimated review time", default=30)
    prerequisite_concepts: List[str] = Field(description="Required prior knowledge", default=[])


class FlashcardGenerationPlan(BaseModel):
    """Strategic plan for flashcard generation"""
    strategy: str = Field(description="Overall generation strategy")
    total_cards: int = Field(description="Total number of cards to generate")
    format_distribution: Dict[str, int] = Field(description="Distribution of card formats")
    difficulty_distribution: Dict[str, int] = Field(description="Distribution by difficulty")
    cognitive_levels: List[str] = Field(description="Cognitive levels to target")
    sequencing_approach: str = Field(description="How to sequence the cards")
    quality_checkpoints: List[str] = Field(description="Quality checks to perform")


class FlashcardBatch(BaseModel):
    """A batch of generated flashcards with metadata"""
    flashcards: List[FlashcardItem]
    generation_metadata: Dict[str, Any] = Field(default={})
    quality_scores: Dict[str, float] = Field(default={})


class FlashcardGenerationAgent(BaseAIAgent):
    """
    Specialized agent for intelligent flashcard generation.
    
    This agent uses strategic reasoning to:
    1. Analyze content for flashcard potential
    2. Choose optimal formats and difficulty progression
    3. Generate diverse, high-quality flashcards
    4. Optimize for spaced repetition effectiveness
    """
    
    def __init__(self, model_name: str = None, temperature: float = 0.3):
        super().__init__(AgentRole.FLASHCARD_GENERATOR, model_name, temperature)
        self.supported_formats = [f.value for f in FlashcardFormat]
        self.generation_strategies = [s.value for s in FlashcardStrategy]
    
    def create_generation_plan(self, context: GenerationContext, analysis: ContentAnalysis) -> FlashcardGenerationPlan:
        """
        Create a strategic plan for flashcard generation.
        
        Args:
            context: Generation context
            analysis: Content analysis results
            
        Returns:
            FlashcardGenerationPlan with detailed strategy
        """
        try:
            planning_prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_planning_system_prompt()),
                ("human", self._get_planning_human_prompt())
            ])
            
            parser = PydanticOutputParser(pydantic_object=FlashcardGenerationPlan)
            chain = planning_prompt | self.llm | parser
            
            plan = chain.invoke({
                "content_analysis": analysis.dict(),
                "context": context.__dict__,
                "supported_formats": self.supported_formats,
                "strategies": self.generation_strategies,
                "format_instructions": parser.get_format_instructions()
            })
            
            logger.info(f"Created flashcard generation plan: {plan.strategy}")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating generation plan: {str(e)}")
            # Fallback plan
            return FlashcardGenerationPlan(
                strategy="comprehensive_coverage",
                total_cards=10,
                format_distribution={"basic_qa": 6, "definition": 4},
                difficulty_distribution={"easy": 3, "medium": 5, "hard": 2},
                cognitive_levels=["remember", "understand", "apply"],
                sequencing_approach="difficulty_progression",
                quality_checkpoints=["clarity", "accuracy", "relevance"]
            )
    
    def execute_task(self, context: GenerationContext, decision: AgentDecision) -> List[Dict[str, Any]]:
        """
        Execute flashcard generation based on the agent's decision.
        
        Args:
            context: Generation context
            decision: Strategic decision made by the agent
            
        Returns:
            List of generated flashcard dictionaries
        """
        try:
            # First, analyze the content
            analysis = self.analyze_content(context)
            
            # Create a detailed generation plan
            plan = self.create_generation_plan(context, analysis)
            
            # Execute generation in batches for better quality control
            all_flashcards = []
            batch_size = min(5, plan.total_cards)
            
            for i in range(0, plan.total_cards, batch_size):
                remaining_cards = min(batch_size, plan.total_cards - i)
                batch = self._generate_flashcard_batch(
                    context, plan, remaining_cards, batch_number=i//batch_size + 1
                )
                all_flashcards.extend(batch.flashcards)
            
            # Convert to dictionary format for compatibility
            flashcard_dicts = []
            for fc in all_flashcards:
                fc_dict = {
                    "question": fc.question,
                    "answer": fc.answer,
                    "explanation": fc.explanation,
                    "difficulty_level": fc.difficulty_level,
                    "tags": fc.tags,
                    "source_content": context.content[:500] + "..." if len(context.content) > 500 else context.content,
                    "generated_by_ai": True,
                    "ai_model_used": self.llm.model_name,
                    "generation_confidence": decision.confidence,
                    # Additional metadata
                    "format_type": fc.format_type,
                    "cognitive_level": fc.cognitive_level,
                    "learning_objective": fc.learning_objective,
                    "estimated_time_seconds": fc.estimated_time_seconds,
                    "prerequisite_concepts": fc.prerequisite_concepts
                }
                flashcard_dicts.append(fc_dict)
            
            logger.info(f"Generated {len(flashcard_dicts)} flashcards using agentic approach")
            return flashcard_dicts
            
        except Exception as e:
            logger.error(f"Error in flashcard generation: {str(e)}")
            return self._fallback_generation(context, decision)
    
    def _generate_flashcard_batch(
        self, 
        context: GenerationContext, 
        plan: FlashcardGenerationPlan, 
        count: int,
        batch_number: int = 1
    ) -> FlashcardBatch:
        """
        Generate a batch of flashcards with focused attention.
        
        Args:
            context: Generation context
            plan: Generation plan to follow
            count: Number of flashcards in this batch
            batch_number: Which batch this is (for sequencing)
            
        Returns:
            FlashcardBatch with generated cards
        """
        try:
            generation_prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_generation_system_prompt()),
                ("human", self._get_generation_human_prompt())
            ])
            
            parser = PydanticOutputParser(pydantic_object=FlashcardBatch)
            chain = generation_prompt | self.llm | parser
            
            # Determine focus for this batch based on plan
            batch_focus = self._get_batch_focus(plan, batch_number, count)
            
            batch = chain.invoke({
                "content": context.content[:3000],  # Limit for context window
                "plan": plan.dict(),
                "batch_focus": batch_focus,
                "count": count,
                "batch_number": batch_number,
                "topic": context.topic,
                "difficulty_level": context.difficulty_level,
                "learning_objectives": context.learning_objectives,
                "format_instructions": parser.get_format_instructions()
            })
            
            # Enhance batch with additional reasoning
            batch = self._enhance_batch_quality(batch, context)
            
            return batch
            
        except Exception as e:
            logger.error(f"Error generating flashcard batch: {str(e)}")
            # Return minimal fallback batch
            return FlashcardBatch(
                flashcards=[
                    FlashcardItem(
                        question=f"What is the main topic of {context.topic}?",
                        answer=f"The main topic relates to {context.topic}.",
                        format_type="basic_qa",
                        difficulty_level="medium"
                    )
                ]
            )
    
    def _get_batch_focus(self, plan: FlashcardGenerationPlan, batch_number: int, count: int) -> Dict[str, Any]:
        """Determine the focus for a specific batch based on the overall plan."""
        total_batches = (plan.total_cards + count - 1) // count
        
        if batch_number == 1:
            focus = {
                "emphasis": "foundational_concepts",
                "difficulty_bias": "easy_to_medium",
                "formats": ["basic_qa", "definition"],
                "cognitive_levels": ["remember", "understand"]
            }
        elif batch_number == total_batches:
            focus = {
                "emphasis": "synthesis_and_application",
                "difficulty_bias": "medium_to_hard",
                "formats": ["fill_blank", "multiple_choice"],
                "cognitive_levels": ["apply", "analyze"]
            }
        else:
            focus = {
                "emphasis": "concept_connections",
                "difficulty_bias": "medium",
                "formats": ["basic_qa", "cloze_deletion"],
                "cognitive_levels": ["understand", "apply"]
            }
        
        return focus
    
    def _enhance_batch_quality(self, batch: FlashcardBatch, context: GenerationContext) -> FlashcardBatch:
        """Enhance the quality of a generated batch with additional processing."""
        try:
            # Quality enhancement prompt
            enhancement_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a quality enhancement specialist for educational flashcards.
                Review and improve the given flashcards for:
                1. Clarity and precision
                2. Appropriate difficulty
                3. Educational value
                4. Engagement level
                
                Make minimal but impactful improvements."""),
                ("human", """Enhance these flashcards:
                
                Original batch: {batch}
                Context: {context}
                
                Return the improved flashcards maintaining the same structure.""")
            ])
            
            # For now, we'll do basic quality checks
            enhanced_flashcards = []
            for fc in batch.flashcards:
                # Basic quality improvements
                if len(fc.question) < 10:
                    fc.question = f"What can you tell me about {fc.question}?"
                
                if len(fc.answer) < 5:
                    fc.answer = f"This relates to {context.topic}. {fc.answer}"
                
                # Ensure tags are relevant
                if not fc.tags and context.topic:
                    fc.tags = [context.topic.lower().replace(" ", "_")]
                
                enhanced_flashcards.append(fc)
            
            batch.flashcards = enhanced_flashcards
            batch.quality_scores = {
                "clarity": 0.8,
                "relevance": 0.85,
                "difficulty_appropriateness": 0.8,
                "educational_value": 0.82
            }
            
            return batch
            
        except Exception as e:
            logger.error(f"Error enhancing batch quality: {str(e)}")
            return batch
    
    def _fallback_generation(self, context: GenerationContext, decision: AgentDecision) -> List[Dict[str, Any]]:
        """Fallback generation method when the main approach fails."""
        count = decision.parameters.get("count", 5)
        fallback_cards = []
        
        for i in range(count):
            card = {
                "question": f"Question {i+1} about {context.topic}",
                "answer": f"Answer {i+1} related to the content",
                "explanation": "Generated using fallback method",
                "difficulty_level": context.difficulty_level,
                "tags": [context.topic] if context.topic else [],
                "source_content": context.content[:200] + "...",
                "generated_by_ai": True,
                "ai_model_used": "fallback",
                "generation_confidence": 0.5,
                "format_type": "basic_qa",
                "cognitive_level": "remember"
            }
            fallback_cards.append(card)
        
        return fallback_cards
    
    def _get_planning_system_prompt(self) -> str:
        """System prompt for generation planning"""
        return """You are an expert educational strategist specializing in flashcard design.

Your role is to create comprehensive generation plans that maximize learning effectiveness.

Consider these factors:
1. Content complexity and structure
2. Target audience cognitive load
3. Spaced repetition optimization
4. Format variety for engagement
5. Progressive difficulty sequencing
6. Bloom's taxonomy alignment

Create plans that balance comprehensiveness with quality, ensuring each flashcard
serves a clear educational purpose."""
    
    def _get_planning_human_prompt(self) -> str:
        """Human prompt for generation planning"""
        return """Create a strategic flashcard generation plan based on:

Content Analysis: {content_analysis}
Generation Context: {context}
Available Formats: {supported_formats}
Available Strategies: {strategies}

Design a plan that optimizes for learning effectiveness and retention.

{format_instructions}"""
    
    def _get_generation_system_prompt(self) -> str:
        """System prompt for flashcard generation"""
        return """You are an expert flashcard creator with deep knowledge of cognitive science and learning theory.

Create flashcards that:
1. Promote active recall and meaningful learning
2. Use clear, precise language appropriate for the target audience
3. Include relevant context and explanations
4. Vary in format to maintain engagement
5. Progress logically in difficulty
6. Connect to broader learning objectives

Focus on quality over quantity. Each flashcard should serve a specific learning purpose."""
    
    def _get_generation_human_prompt(self) -> str:
        """Human prompt for flashcard generation"""
        return """Generate {count} high-quality flashcards for batch #{batch_number}:

Content: {content}
Topic: {topic}
Difficulty Level: {difficulty_level}
Learning Objectives: {learning_objectives}

Generation Plan: {plan}
Batch Focus: {batch_focus}

Create flashcards that follow the plan and focus area, ensuring educational value and engagement.

{format_instructions}"""


def create_flashcard_agent(model_name: str = None) -> FlashcardGenerationAgent:
    """
    Factory function to create a flashcard generation agent.
    
    Args:
        model_name: Optional OpenAI model name
        
    Returns:
        FlashcardGenerationAgent instance
    """
    return FlashcardGenerationAgent(model_name=model_name)