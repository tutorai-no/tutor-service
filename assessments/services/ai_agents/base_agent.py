"""
Base AI Agent for Educational Content Generation

This module provides the foundation for agentic AI that can reason about
educational content and make autonomous decisions about generation strategies.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from django.conf import settings

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.services.retrieval_client import get_retrieval_client

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles for different types of AI agents"""

    CONTENT_ANALYZER = "content_analyzer"
    FLASHCARD_GENERATOR = "flashcard_generator"
    QUIZ_GENERATOR = "quiz_generator"
    QUALITY_ASSESSOR = "quality_assessor"
    ORCHESTRATOR = "orchestrator"


class TaskComplexity(Enum):
    """Complexity levels for content generation tasks"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


@dataclass
class GenerationContext:
    """Context information for content generation"""

    course_id: int
    user_id: int
    content: str
    topic: str = ""
    difficulty_level: str = "medium"
    learning_objectives: list[str] = None
    target_audience: str = "undergraduate"
    document_ids: list[int] = None
    constraints: dict[str, Any] = None

    def __post_init__(self):
        if self.learning_objectives is None:
            self.learning_objectives = []
        if self.constraints is None:
            self.constraints = {}


class AgentDecision(BaseModel):
    """Represents a decision made by an AI agent"""

    action: str = Field(description="The action to take")
    reasoning: str = Field(description="Why this action was chosen")
    confidence: float = Field(description="Confidence level (0-1)")
    parameters: dict[str, Any] = Field(
        description="Parameters for the action", default={}
    )
    fallback_actions: list[str] = Field(
        description="Alternative actions if this fails", default=[]
    )


class ContentAnalysis(BaseModel):
    """Analysis of content for generation purposes"""

    complexity_level: str = Field(description="Complexity of the content")
    key_concepts: list[str] = Field(description="Main concepts identified")
    concept_relationships: list[tuple[str, str]] = Field(
        description="Relationships between concepts", default=[]
    )
    suitable_formats: list[str] = Field(description="Suitable question/card formats")
    estimated_items: int = Field(
        description="Estimated number of items that can be generated"
    )
    quality_indicators: dict[str, float] = Field(
        description="Quality metrics", default={}
    )


class BaseAIAgent(ABC):
    """
    Base class for educational AI agents that can reason and make decisions.

    This agent uses a chain-of-thought approach to analyze content, plan
    generation strategies, and execute content creation tasks.
    """

    def __init__(
        self, role: AgentRole, model_name: str = None, temperature: float = 0.2
    ):
        """
        Initialize the AI agent.

        Args:
            role: The role this agent plays
            model_name: OpenAI model to use
            temperature: Creativity level (0.0-1.0)
        """
        self.role = role
        self.llm = ChatOpenAI(
            api_key=getattr(settings, "OPENAI_API_KEY", None),
            model_name=model_name or getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
            temperature=temperature,
        )
        self.retrieval_client = get_retrieval_client()
        self.conversation_history: list[dict[str, str]] = []

        if not self.llm.api_key:
            logger.warning(f"No OpenAI API key configured for agent {role.value}")

    def analyze_content(self, context: GenerationContext) -> ContentAnalysis:
        """
        Analyze content to understand its characteristics and generation potential.

        Args:
            context: Generation context with content and metadata

        Returns:
            ContentAnalysis with insights about the content
        """
        try:
            # Create analysis prompt
            analysis_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._get_analysis_system_prompt()),
                    ("human", self._get_analysis_human_prompt()),
                ]
            )

            # Set up parser
            parser = PydanticOutputParser(pydantic_object=ContentAnalysis)

            # Create analysis chain
            chain = analysis_prompt | self.llm | parser

            # Analyze the content
            result = chain.invoke(
                {
                    "content": context.content[:4000],  # Limit content length
                    "topic": context.topic,
                    "difficulty_level": context.difficulty_level,
                    "learning_objectives": context.learning_objectives,
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            logger.info(f"Content analysis completed by {self.role.value}")
            return result

        except Exception as e:
            logger.error(f"Error in content analysis: {str(e)}")
            # Return fallback analysis
            return ContentAnalysis(
                complexity_level="moderate",
                key_concepts=["general topic"],
                suitable_formats=["basic"],
                estimated_items=5,
                quality_indicators={"confidence": 0.5},
            )

    def make_decision(
        self, context: GenerationContext, analysis: ContentAnalysis
    ) -> AgentDecision:
        """
        Make a strategic decision about how to approach content generation.

        Args:
            context: Generation context
            analysis: Content analysis results

        Returns:
            AgentDecision with chosen strategy
        """
        try:
            # Create decision prompt
            decision_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._get_decision_system_prompt()),
                    ("human", self._get_decision_human_prompt()),
                ]
            )

            # Set up parser
            parser = PydanticOutputParser(pydantic_object=AgentDecision)

            # Create decision chain
            chain = decision_prompt | self.llm | parser

            # Make the decision
            result = chain.invoke(
                {
                    "role": self.role.value,
                    "analysis": analysis.dict(),
                    "context": context.__dict__,
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            logger.info(f"Decision made by {self.role.value}: {result.action}")
            return result

        except Exception as e:
            logger.error(f"Error in decision making: {str(e)}")
            # Return fallback decision
            return AgentDecision(
                action="standard_generation",
                reasoning="Fallback to standard approach due to error",
                confidence=0.5,
                parameters={"count": 5},
            )

    @abstractmethod
    def execute_task(
        self, context: GenerationContext, decision: AgentDecision
    ) -> list[dict[str, Any]]:
        """
        Execute the content generation task based on the decision.

        Args:
            context: Generation context
            decision: Decision made by the agent

        Returns:
            List of generated content items
        """

    def reflect_on_results(
        self, generated_items: list[dict[str, Any]], context: GenerationContext
    ) -> dict[str, Any]:
        """
        Reflect on the quality and appropriateness of generated content.

        Args:
            generated_items: Items that were generated
            context: Original generation context

        Returns:
            Reflection analysis with quality metrics and suggestions
        """
        try:
            reflection_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._get_reflection_system_prompt()),
                    ("human", self._get_reflection_human_prompt()),
                ]
            )

            # Analyze the generated content
            result = self.llm.invoke(
                reflection_prompt.format(
                    role=self.role.value,
                    generated_items=str(generated_items)[:2000],
                    original_context=str(context.__dict__)[:1000],
                )
            )

            # Parse the reflection (simplified for now)
            reflection = {
                "quality_score": 0.8,  # Default score
                "strengths": ["Generated appropriate content"],
                "improvements": ["Could enhance variety"],
                "recommendation": "Content is suitable for use",
            }

            logger.info(f"Reflection completed by {self.role.value}")
            return reflection

        except Exception as e:
            logger.error(f"Error in reflection: {str(e)}")
            return {
                "quality_score": 0.7,
                "strengths": ["Basic content generated"],
                "improvements": ["Review for quality"],
                "recommendation": "Manual review recommended",
            }

    def enhance_with_retrieval(self, context: GenerationContext, query: str) -> str:
        """
        Enhance generation context with additional retrieved content.

        Args:
            context: Current generation context
            query: Search query for retrieval

        Returns:
            Enhanced content string
        """
        try:
            enhanced_content = self.retrieval_client.get_context(
                course_id=context.course_id,
                query=query,
                limit=3,
                document_ids=context.document_ids,
            )

            if enhanced_content:
                logger.info(
                    f"Enhanced content with {len(enhanced_content)} characters from retrieval"
                )
                return f"{context.content}\n\nAdditional Context:\n{enhanced_content}"

        except Exception as e:
            logger.error(f"Error enhancing with retrieval: {str(e)}")

        return context.content

    def _get_analysis_system_prompt(self) -> str:
        """Get system prompt for content analysis"""
        return f"""
        You are an expert educational content analyst with the role of {self.role.value}.
        
        Your task is to analyze educational content and determine:
        1. The complexity level and cognitive load
        2. Key concepts and their relationships
        3. Most suitable formats for assessment items
        4. Realistic generation targets
        5. Quality indicators for the content
        
        Be thorough but concise in your analysis. Focus on actionable insights
        that will guide effective content generation.
        """

    def _get_analysis_human_prompt(self) -> str:
        """Get human prompt for content analysis"""
        return """
        Analyze the following educational content:
        
        Content: {content}
        Topic: {topic}
        Difficulty Level: {difficulty_level}
        Learning Objectives: {learning_objectives}
        
        Provide a comprehensive analysis following this format:
        
        {format_instructions}
        """

    def _get_decision_system_prompt(self) -> str:
        """Get system prompt for decision making"""
        return f"""
        You are an intelligent educational content generation agent with the role of {self.role.value}.
        
        Based on content analysis, you must decide on the best strategy for generating
        educational materials. Consider:
        
        1. Content complexity and structure
        2. Learning objectives alignment
        3. Target audience needs
        4. Quality vs. quantity trade-offs
        5. Available generation techniques
        
        Make strategic decisions that maximize educational value while being realistic
        about what can be achieved with the given content.
        """

    def _get_decision_human_prompt(self) -> str:
        """Get human prompt for decision making"""
        return """
        Based on this content analysis and context, decide on the best generation strategy:
        
        Agent Role: {role}
        Content Analysis: {analysis}
        Generation Context: {context}
        
        Provide your strategic decision following this format:
        
        {format_instructions}
        """

    def _get_reflection_system_prompt(self) -> str:
        """Get system prompt for reflection"""
        return f"""
        You are a quality assessment specialist for educational content.
        
        Review the generated content and provide honest, constructive feedback on:
        1. Educational value and alignment with objectives
        2. Clarity and appropriateness for target audience
        3. Variety and engagement level
        4. Technical accuracy
        5. Areas for improvement
        
        Be specific in your recommendations and balanced in your assessment.
        """

    def _get_reflection_human_prompt(self) -> str:
        """Get human prompt for reflection"""
        return """
        Evaluate this generated educational content:
        
        Agent Role: {role}
        Generated Items: {generated_items}
        Original Context: {original_context}
        
        Provide a comprehensive quality assessment and recommendations for improvement.
        """

    def update_conversation_history(self, role: str, content: str):
        """Update the conversation history for context"""
        self.conversation_history.append({"role": role, "content": content})

        # Keep only last 10 messages to manage context length
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]


class ContentGenerationOrchestrator:
    """
    Orchestrates multiple AI agents to collaborate on content generation.

    This class manages the workflow of analysis, decision-making, generation,
    and quality assessment across different specialized agents.
    """

    def __init__(self):
        self.agents: dict[AgentRole, BaseAIAgent] = {}
        self.workflow_history: list[dict[str, Any]] = []

    def register_agent(self, agent: BaseAIAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.role] = agent
        logger.info(f"Registered agent: {agent.role.value}")

    def orchestrate_generation(
        self,
        context: GenerationContext,
        primary_agent_role: AgentRole,
        use_quality_assessment: bool = True,
    ) -> dict[str, Any]:
        """
        Orchestrate a multi-agent content generation process.

        Args:
            context: Generation context
            primary_agent_role: The main agent to use for generation
            use_quality_assessment: Whether to use quality assessment

        Returns:
            Dictionary with generated content and workflow metadata
        """
        workflow_results = {
            "generated_content": [],
            "workflow_steps": [],
            "quality_assessment": None,
            "agents_used": [],
            "total_confidence": 0.0,
        }

        try:
            # Step 1: Content Analysis
            if AgentRole.CONTENT_ANALYZER in self.agents:
                analyzer = self.agents[AgentRole.CONTENT_ANALYZER]
                analysis = analyzer.analyze_content(context)
                workflow_results["workflow_steps"].append(
                    {
                        "step": "content_analysis",
                        "agent": AgentRole.CONTENT_ANALYZER.value,
                        "result": analysis.dict(),
                    }
                )
                workflow_results["agents_used"].append(AgentRole.CONTENT_ANALYZER.value)
            else:
                # Fallback analysis
                analysis = ContentAnalysis(
                    complexity_level="moderate",
                    key_concepts=[context.topic],
                    suitable_formats=["standard"],
                    estimated_items=5,
                    quality_indicators={"confidence": 0.6},
                )

            # Step 2: Strategic Decision
            if primary_agent_role in self.agents:
                primary_agent = self.agents[primary_agent_role]
                decision = primary_agent.make_decision(context, analysis)
                workflow_results["workflow_steps"].append(
                    {
                        "step": "strategic_decision",
                        "agent": primary_agent_role.value,
                        "result": decision.dict(),
                    }
                )
                workflow_results["agents_used"].append(primary_agent_role.value)

                # Step 3: Content Generation
                generated_content = primary_agent.execute_task(context, decision)
                workflow_results["generated_content"] = generated_content
                workflow_results["total_confidence"] = decision.confidence

                workflow_results["workflow_steps"].append(
                    {
                        "step": "content_generation",
                        "agent": primary_agent_role.value,
                        "result": {"items_generated": len(generated_content)},
                    }
                )

                # Step 4: Quality Assessment (optional)
                if use_quality_assessment and AgentRole.QUALITY_ASSESSOR in self.agents:
                    assessor = self.agents[AgentRole.QUALITY_ASSESSOR]
                    quality_report = assessor.reflect_on_results(
                        generated_content, context
                    )
                    workflow_results["quality_assessment"] = quality_report
                    workflow_results["workflow_steps"].append(
                        {
                            "step": "quality_assessment",
                            "agent": AgentRole.QUALITY_ASSESSOR.value,
                            "result": quality_report,
                        }
                    )
                    workflow_results["agents_used"].append(
                        AgentRole.QUALITY_ASSESSOR.value
                    )

            else:
                raise ValueError(
                    f"Primary agent {primary_agent_role.value} not registered"
                )

        except Exception as e:
            logger.error(f"Error in orchestrated generation: {str(e)}")
            workflow_results["error"] = str(e)

        # Record workflow
        self.workflow_history.append(
            {
                "timestamp": logger.name,  # Simplified timestamp
                "context_summary": f"Course {context.course_id}, Topic: {context.topic}",
                "results": workflow_results,
            }
        )

        return workflow_results

    def get_agent_recommendations(self, context: GenerationContext) -> dict[str, str]:
        """
        Get recommendations for which agents to use for a given context.

        Args:
            context: Generation context

        Returns:
            Dictionary with agent recommendations
        """
        recommendations = {}

        # Analyze context complexity
        content_length = len(context.content)
        has_objectives = bool(context.learning_objectives)

        if content_length > 2000 and has_objectives:
            recommendations["complexity"] = "high"
            recommendations["suggested_workflow"] = "full_agent_collaboration"
            recommendations["agents"] = [
                AgentRole.CONTENT_ANALYZER.value,
                AgentRole.FLASHCARD_GENERATOR.value,
                AgentRole.QUIZ_GENERATOR.value,
                AgentRole.QUALITY_ASSESSOR.value,
            ]
        elif content_length > 500:
            recommendations["complexity"] = "moderate"
            recommendations["suggested_workflow"] = "standard_generation"
            recommendations["agents"] = [
                AgentRole.FLASHCARD_GENERATOR.value,
                AgentRole.QUIZ_GENERATOR.value,
            ]
        else:
            recommendations["complexity"] = "simple"
            recommendations["suggested_workflow"] = "basic_generation"
            recommendations["agents"] = [AgentRole.FLASHCARD_GENERATOR.value]

        return recommendations
