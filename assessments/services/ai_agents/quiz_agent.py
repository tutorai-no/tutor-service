"""
Specialized AI Agent for Quiz Generation

This agent uses agentic AI to create comprehensive quizzes with strategic
question selection, difficulty balancing, and pedagogical alignment.
"""

import logging
from enum import Enum
from typing import Any

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from .base_agent import (
    AgentDecision,
    AgentRole,
    BaseAIAgent,
    ContentAnalysis,
    GenerationContext,
)

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of quiz questions"""

    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    ESSAY = "essay"
    MATCHING = "matching"
    ORDERING = "ordering"
    CALCULATION = "calculation"


class QuizPurpose(Enum):
    """Different purposes for quizzes"""

    FORMATIVE_ASSESSMENT = "formative_assessment"
    SUMMATIVE_ASSESSMENT = "summative_assessment"
    PRACTICE_QUIZ = "practice_quiz"
    DIAGNOSTIC_TEST = "diagnostic_test"
    REVIEW_SESSION = "review_session"
    COMPETENCY_CHECK = "competency_check"


class CognitiveDomain(Enum):
    """Bloom's taxonomy cognitive domains"""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class QuizQuestion(BaseModel):
    """Individual quiz question with comprehensive metadata"""

    question_text: str = Field(description="The question text")
    question_type: str = Field(description="Type of question")
    answer_options: list[str] = Field(
        description="Answer options for multiple choice", default=[]
    )
    correct_answers: list[str] = Field(description="Correct answer(s)")
    explanation: str = Field(description="Explanation of correct answer", default="")
    difficulty_level: str = Field(description="Difficulty: easy, medium, hard")
    cognitive_domain: str = Field(
        description="Bloom's taxonomy level", default="remember"
    )
    points: int = Field(description="Point value", default=1)
    estimated_time_minutes: float = Field(
        description="Estimated time to answer", default=1.0
    )
    tags: list[str] = Field(description="Content tags", default=[])
    learning_objective: str = Field(
        description="Associated learning objective", default=""
    )
    distractor_analysis: dict[str, str] = Field(
        description="Analysis of wrong answers", default={}
    )
    prerequisite_knowledge: list[str] = Field(
        description="Required prior knowledge", default=[]
    )


class QuizStructure(BaseModel):
    """Strategic structure for quiz organization"""

    purpose: str = Field(description="Quiz purpose/type")
    total_questions: int = Field(description="Total number of questions")
    question_type_distribution: dict[str, int] = Field(
        description="Distribution by question type"
    )
    difficulty_progression: list[str] = Field(description="Difficulty sequence")
    cognitive_distribution: dict[str, int] = Field(
        description="Cognitive level distribution"
    )
    time_allocation: dict[str, float] = Field(description="Time per section/type")
    scoring_strategy: str = Field(description="How to score the quiz")
    section_organization: list[dict[str, Any]] = Field(
        description="Quiz sections", default=[]
    )


class QuizGenerationStrategy(BaseModel):
    """Comprehensive strategy for quiz generation"""

    assessment_approach: str = Field(description="Overall assessment approach")
    content_sampling: str = Field(description="How to sample from content")
    question_sequencing: str = Field(description="Question ordering strategy")
    difficulty_balancing: str = Field(description="Difficulty distribution approach")
    engagement_techniques: list[str] = Field(
        description="Techniques to maintain engagement"
    )
    quality_criteria: list[str] = Field(description="Quality assessment criteria")
    adaptive_elements: list[str] = Field(
        description="Adaptive quiz features", default=[]
    )


class QuizBatch(BaseModel):
    """A batch of quiz questions with metadata"""

    questions: list[QuizQuestion]
    section_info: dict[str, Any] = Field(default={})
    quality_metrics: dict[str, float] = Field(default={})
    generation_notes: list[str] = Field(default=[])


class QuizGenerationAgent(BaseAIAgent):
    """
    Specialized agent for intelligent quiz generation.

    This agent employs strategic reasoning to:
    1. Analyze content for assessment potential
    2. Design appropriate quiz structures
    3. Generate balanced, high-quality questions
    4. Optimize for learning objectives and pedagogy
    """

    def __init__(self, model_name: str = None, temperature: float = 0.2):
        super().__init__(AgentRole.QUIZ_GENERATOR, model_name, temperature)
        self.supported_question_types = [qt.value for qt in QuestionType]
        self.cognitive_domains = [cd.value for cd in CognitiveDomain]
        self.quiz_purposes = [qp.value for qp in QuizPurpose]

    def design_quiz_structure(
        self,
        context: GenerationContext,
        analysis: ContentAnalysis,
        target_duration_minutes: int = 20,
    ) -> QuizStructure:
        """
        Design the overall structure and strategy for the quiz.

        Args:
            context: Generation context
            analysis: Content analysis results
            target_duration_minutes: Target quiz duration

        Returns:
            QuizStructure with detailed organization plan
        """
        try:
            structure_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._get_structure_design_system_prompt()),
                    ("human", self._get_structure_design_human_prompt()),
                ]
            )

            parser = PydanticOutputParser(pydantic_object=QuizStructure)
            chain = structure_prompt | self.llm | parser

            structure = chain.invoke(
                {
                    "content_analysis": analysis.dict(),
                    "context": context.__dict__,
                    "target_duration": target_duration_minutes,
                    "question_types": self.supported_question_types,
                    "cognitive_domains": self.cognitive_domains,
                    "quiz_purposes": self.quiz_purposes,
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            logger.info(
                f"Designed quiz structure: {structure.purpose}, {structure.total_questions} questions"
            )
            return structure

        except Exception as e:
            logger.error(f"Error designing quiz structure: {str(e)}")
            # Fallback structure
            return QuizStructure(
                purpose="practice_quiz",
                total_questions=10,
                question_type_distribution={"multiple_choice": 6, "short_answer": 4},
                difficulty_progression=["easy", "medium", "medium", "medium", "hard"],
                cognitive_distribution={"remember": 3, "understand": 4, "apply": 3},
                time_allocation={"multiple_choice": 1.0, "short_answer": 2.0},
                scoring_strategy="equal_points",
            )

    def create_generation_strategy(
        self, context: GenerationContext, structure: QuizStructure
    ) -> QuizGenerationStrategy:
        """
        Create a detailed strategy for generating quiz content.

        Args:
            context: Generation context
            structure: Quiz structure design

        Returns:
            QuizGenerationStrategy with detailed approach
        """
        try:
            strategy_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._get_strategy_system_prompt()),
                    ("human", self._get_strategy_human_prompt()),
                ]
            )

            parser = PydanticOutputParser(pydantic_object=QuizGenerationStrategy)
            chain = strategy_prompt | self.llm | parser

            strategy = chain.invoke(
                {
                    "context": context.__dict__,
                    "structure": structure.dict(),
                    "content_complexity": "moderate",  # Could be derived from analysis
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            logger.info(f"Created generation strategy: {strategy.assessment_approach}")
            return strategy

        except Exception as e:
            logger.error(f"Error creating generation strategy: {str(e)}")
            # Fallback strategy
            return QuizGenerationStrategy(
                assessment_approach="balanced_assessment",
                content_sampling="representative_coverage",
                question_sequencing="difficulty_progression",
                difficulty_balancing="normal_distribution",
                engagement_techniques=["varied_formats", "clear_language"],
                quality_criteria=["accuracy", "clarity", "relevance"],
            )

    def execute_task(
        self, context: GenerationContext, decision: AgentDecision
    ) -> list[dict[str, Any]]:
        """
        Execute quiz generation based on the agent's strategic decision.

        Args:
            context: Generation context
            decision: Strategic decision made by the agent

        Returns:
            List of generated quiz question dictionaries
        """
        try:
            # Step 1: Analyze content
            analysis = self.analyze_content(context)

            # Step 2: Design quiz structure
            target_duration = decision.parameters.get("duration_minutes", 20)
            structure = self.design_quiz_structure(context, analysis, target_duration)

            # Step 3: Create generation strategy
            strategy = self.create_generation_strategy(context, structure)

            # Step 4: Generate questions in strategic batches
            all_questions = []

            # Create sections based on structure
            if structure.section_organization:
                sections = structure.section_organization
            else:
                # Create default sections
                sections = self._create_default_sections(structure)

            for section in sections:
                section_questions = self._generate_section_questions(
                    context, structure, strategy, section
                )
                all_questions.extend(section_questions)

            # Step 5: Final quality enhancement and sequencing
            enhanced_questions = self._enhance_question_quality(
                all_questions, context, strategy
            )
            sequenced_questions = self._sequence_questions(enhanced_questions, strategy)

            # Convert to dictionary format
            question_dicts = []
            for i, question in enumerate(sequenced_questions):
                q_dict = {
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "answer_options": question.answer_options,
                    "correct_answers": question.correct_answers,
                    "explanation": question.explanation,
                    "difficulty_level": question.difficulty_level,
                    "points": question.points,
                    "order": i + 1,
                    "source_content": (
                        context.content[:500] + "..."
                        if len(context.content) > 500
                        else context.content
                    ),
                    # Enhanced metadata
                    "cognitive_domain": question.cognitive_domain,
                    "estimated_time_minutes": question.estimated_time_minutes,
                    "tags": question.tags,
                    "learning_objective": question.learning_objective,
                    "prerequisite_knowledge": question.prerequisite_knowledge,
                }
                question_dicts.append(q_dict)

            logger.info(
                f"Generated {len(question_dicts)} quiz questions using agentic approach"
            )
            return question_dicts

        except Exception as e:
            logger.error(f"Error in quiz generation: {str(e)}")
            return self._fallback_generation(context, decision)

    def _create_default_sections(
        self, structure: QuizStructure
    ) -> list[dict[str, Any]]:
        """Create default sections based on quiz structure."""
        sections = []

        # Warm-up section (easy questions)
        sections.append(
            {
                "name": "warm_up",
                "question_count": max(1, structure.total_questions // 4),
                "difficulty_focus": "easy",
                "cognitive_focus": ["remember", "understand"],
                "question_types": ["multiple_choice", "true_false"],
            }
        )

        # Main section (varied difficulty)
        sections.append(
            {
                "name": "main_assessment",
                "question_count": structure.total_questions // 2,
                "difficulty_focus": "medium",
                "cognitive_focus": ["understand", "apply", "analyze"],
                "question_types": ["multiple_choice", "short_answer"],
            }
        )

        # Challenge section (harder questions)
        remaining = structure.total_questions - sum(
            s["question_count"] for s in sections
        )
        if remaining > 0:
            sections.append(
                {
                    "name": "challenge",
                    "question_count": remaining,
                    "difficulty_focus": "hard",
                    "cognitive_focus": ["apply", "analyze", "evaluate"],
                    "question_types": ["short_answer", "essay"],
                }
            )

        return sections

    def _generate_section_questions(
        self,
        context: GenerationContext,
        structure: QuizStructure,
        strategy: QuizGenerationStrategy,
        section: dict[str, Any],
    ) -> list[QuizQuestion]:
        """Generate questions for a specific section."""
        try:
            section_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self._get_section_generation_system_prompt()),
                    ("human", self._get_section_generation_human_prompt()),
                ]
            )

            parser = PydanticOutputParser(pydantic_object=QuizBatch)
            chain = section_prompt | self.llm | parser

            batch = chain.invoke(
                {
                    "content": context.content[:3000],
                    "topic": context.topic,
                    "learning_objectives": context.learning_objectives,
                    "section": section,
                    "structure": structure.dict(),
                    "strategy": strategy.dict(),
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            return batch.questions

        except Exception as e:
            logger.error(f"Error generating section questions: {str(e)}")
            # Fallback questions for this section
            fallback_questions = []
            for i in range(section["question_count"]):
                question = QuizQuestion(
                    question_text=f"What is an important concept related to {context.topic}?",
                    question_type="short_answer",
                    correct_answers=[f"A concept related to {context.topic}"],
                    difficulty_level=section.get("difficulty_focus", "medium"),
                    cognitive_domain="understand",
                )
                fallback_questions.append(question)
            return fallback_questions

    def _enhance_question_quality(
        self,
        questions: list[QuizQuestion],
        context: GenerationContext,
        strategy: QuizGenerationStrategy,
    ) -> list[QuizQuestion]:
        """Enhance the quality of generated questions."""
        enhanced_questions = []

        for question in questions:
            # Basic quality checks and improvements
            enhanced_question = self._apply_quality_improvements(question, context)
            enhanced_questions.append(enhanced_question)

        return enhanced_questions

    def _apply_quality_improvements(
        self, question: QuizQuestion, context: GenerationContext
    ) -> QuizQuestion:
        """Apply specific quality improvements to a question."""
        # Ensure question clarity
        if len(question.question_text) < 10:
            question.question_text = (
                f"Regarding {context.topic}: {question.question_text}"
            )

        # Ensure adequate explanation
        if not question.explanation and question.question_type != "essay":
            question.explanation = (
                f"This question tests understanding of {context.topic} concepts."
            )

        # Validate multiple choice options
        if question.question_type == "multiple_choice":
            if len(question.answer_options) < 3:
                # Add placeholder options
                while len(question.answer_options) < 4:
                    question.answer_options.append(
                        f"Option {len(question.answer_options) + 1}"
                    )

        # Ensure tags
        if not question.tags and context.topic:
            question.tags = [context.topic.lower().replace(" ", "_")]

        return question

    def _sequence_questions(
        self, questions: list[QuizQuestion], strategy: QuizGenerationStrategy
    ) -> list[QuizQuestion]:
        """Sequence questions according to the strategy."""
        if strategy.question_sequencing == "difficulty_progression":
            # Sort by difficulty: easy -> medium -> hard
            difficulty_order = {"easy": 1, "medium": 2, "hard": 3}
            return sorted(
                questions, key=lambda q: difficulty_order.get(q.difficulty_level, 2)
            )

        elif strategy.question_sequencing == "cognitive_progression":
            # Sort by cognitive complexity
            cognitive_order = {
                "remember": 1,
                "understand": 2,
                "apply": 3,
                "analyze": 4,
                "evaluate": 5,
                "create": 6,
            }
            return sorted(
                questions, key=lambda q: cognitive_order.get(q.cognitive_domain, 3)
            )

        elif strategy.question_sequencing == "mixed_engagement":
            # Alternate between different types for engagement
            mc_questions = [
                q for q in questions if q.question_type == "multiple_choice"
            ]
            other_questions = [
                q for q in questions if q.question_type != "multiple_choice"
            ]

            sequenced = []
            for i in range(max(len(mc_questions), len(other_questions))):
                if i < len(mc_questions):
                    sequenced.append(mc_questions[i])
                if i < len(other_questions):
                    sequenced.append(other_questions[i])

            return sequenced

        # Default: return as-is
        return questions

    def _fallback_generation(
        self, context: GenerationContext, decision: AgentDecision
    ) -> list[dict[str, Any]]:
        """Fallback generation when main approach fails."""
        count = decision.parameters.get("count", 5)
        fallback_questions = []

        for i in range(count):
            question = {
                "question_text": f"Question {i+1}: What is important to know about {context.topic}?",
                "question_type": "short_answer",
                "answer_options": [],
                "correct_answers": [f"Important aspects of {context.topic}"],
                "explanation": "This question assesses understanding of key concepts.",
                "difficulty_level": context.difficulty_level,
                "points": 1,
                "order": i + 1,
                "source_content": context.content[:200] + "...",
                "cognitive_domain": "understand",
                "estimated_time_minutes": 2.0,
                "tags": [context.topic] if context.topic else [],
                "learning_objective": "Understand key concepts",
            }
            fallback_questions.append(question)

        return fallback_questions

    def _get_structure_design_system_prompt(self) -> str:
        """System prompt for quiz structure design"""
        return """You are an expert assessment designer with deep knowledge of educational psychology and testing theory.

Design quiz structures that:
1. Align with learning objectives and content complexity
2. Balance comprehensiveness with time constraints
3. Use appropriate question type distributions
4. Follow sound pedagogical principles
5. Consider cognitive load and test-taking experience

Create structures that maximize validity, reliability, and educational value."""

    def _get_structure_design_human_prompt(self) -> str:
        """Human prompt for quiz structure design"""
        return """Design a comprehensive quiz structure based on:

Content Analysis: {content_analysis}
Generation Context: {context}
Target Duration: {target_duration} minutes
Available Question Types: {question_types}
Cognitive Domains: {cognitive_domains}
Quiz Purposes: {quiz_purposes}

Create a well-balanced, pedagogically sound quiz structure.

{format_instructions}"""

    def _get_strategy_system_prompt(self) -> str:
        """System prompt for strategy creation"""
        return """You are a strategic assessment planner with expertise in educational measurement.

Develop generation strategies that:
1. Ensure comprehensive content coverage
2. Maintain appropriate difficulty distribution
3. Engage students effectively
4. Support reliable measurement
5. Consider practical constraints

Focus on creating effective, fair, and engaging assessments."""

    def _get_strategy_human_prompt(self) -> str:
        """Human prompt for strategy creation"""
        return """Develop a quiz generation strategy for:

Context: {context}
Quiz Structure: {structure}
Content Complexity: {content_complexity}

Create a strategy that optimizes assessment quality and student engagement.

{format_instructions}"""

    def _get_section_generation_system_prompt(self) -> str:
        """System prompt for section generation"""
        return """You are an expert question writer creating high-quality assessment items.

Generate questions that:
1. Test meaningful understanding, not just memorization
2. Use clear, unambiguous language
3. Have well-crafted distractors (for multiple choice)
4. Include helpful explanations
5. Align with specified cognitive levels

Focus on educational value and assessment validity."""

    def _get_section_generation_human_prompt(self) -> str:
        """Human prompt for section generation"""
        return """Generate quiz questions for this section:

Content: {content}
Topic: {topic}
Learning Objectives: {learning_objectives}
Section Requirements: {section}
Overall Structure: {structure}
Generation Strategy: {strategy}

Create high-quality questions that meet the section requirements.

{format_instructions}"""


def create_quiz_agent(model_name: str = None) -> QuizGenerationAgent:
    """
    Factory function to create a quiz generation agent.

    Args:
        model_name: Optional OpenAI model name

    Returns:
        QuizGenerationAgent instance
    """
    return QuizGenerationAgent(model_name=model_name)
