"""
Assessments Services Package

This package contains all services related to assessment functionality,
organized into logical modules:

- ai_agents/: Agentic AI components for intelligent content generation
- generators/: High-level generation services for flashcards and quizzes
- analytics/: Analytics and performance tracking services
- spaced_repetition.py: Spaced repetition algorithm implementation
"""

# Import agent components
from .ai_agents.base_agent import (
    AgentRole,
    ContentGenerationOrchestrator,
    GenerationContext,
)
from .ai_agents.flashcard_agent import create_flashcard_agent
from .ai_agents.quiz_agent import create_quiz_agent

# Import key services for easy access
from .generators.flashcard_service import get_flashcard_service
from .generators.quiz_service import get_quiz_service
from .spaced_repetition import SpacedRepetitionService

__all__ = [
    # Services
    "get_flashcard_service",
    "get_quiz_service",
    "SpacedRepetitionService",
    # AI Agents
    "ContentGenerationOrchestrator",
    "AgentRole",
    "GenerationContext",
    "create_flashcard_agent",
    "create_quiz_agent",
]
