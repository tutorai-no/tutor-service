"""
Quiz Generation Service

High-level service that orchestrates agentic AI quiz generation
with business logic, validation, and database integration.
"""
import logging
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model

from assessments.models import Quiz, QuizQuestion
from courses.models import Course
from ..ai_agents.base_agent import GenerationContext, ContentGenerationOrchestrator, AgentRole
from ..ai_agents.quiz_agent import create_quiz_agent

User = get_user_model()
logger = logging.getLogger(__name__)


class QuizGenerationService:
    """
    Service for generating quizzes using agentic AI.
    
    This service provides a high-level interface for quiz generation,
    handling business logic, validation, and database operations.
    """
    
    def __init__(self):
        self.orchestrator = ContentGenerationOrchestrator()
        self._setup_agents()
    
    def _setup_agents(self):
        """Set up the AI agents for quiz generation"""
        try:
            quiz_agent = create_quiz_agent()
            self.orchestrator.register_agent(quiz_agent)
            logger.info("Quiz generation agents initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up quiz agents: {str(e)}")
    
    def generate_quiz(
        self,
        user_id: int,
        course_id: int,
        title: str = None,
        content: str = None,
        topic: str = "",
        document_ids: List[int] = None,
        question_count: int = 10,
        difficulty_level: str = "medium",
        quiz_type: str = "practice",
        time_limit_minutes: int = None,
        question_types: List[str] = None,
        learning_objectives: List[str] = None,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a quiz using agentic AI.
        
        Args:
            user_id: ID of the user requesting generation
            course_id: ID of the course
            title: Title for the quiz
            content: Direct content to generate from
            topic: Topic to search for if no content provided
            document_ids: Specific document IDs to use
            question_count: Number of questions to generate
            difficulty_level: Difficulty level (easy, medium, hard)
            quiz_type: Type of quiz (practice, assessment, exam)
            time_limit_minutes: Time limit for the quiz
            question_types: Types of questions to include
            learning_objectives: Learning objectives to align with
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
            
            # Set defaults
            if not title:
                title = f"Quiz on {topic}" if topic else "Generated Quiz"
            
            if not question_types:
                question_types = ["multiple_choice", "short_answer"]
            
            if not time_limit_minutes:
                time_limit_minutes = max(15, question_count * 2)  # 2 minutes per question minimum
            
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
                    "question_count": question_count,
                    "quiz_type": quiz_type,
                    "time_limit_minutes": time_limit_minutes,
                    "question_types": question_types,
                    "auto_save": auto_save
                }
            )
            
            # Orchestrate generation
            results = self.orchestrator.orchestrate_generation(
                context=context,
                primary_agent_role=AgentRole.QUIZ_GENERATOR,
                use_quality_assessment=True
            )
            
            # Process results
            if results.get("error"):
                return {
                    "success": False,
                    "error": results["error"],
                    "quiz": None,
                    "questions": [],
                    "metadata": results
                }
            
            generated_questions = results.get("generated_content", [])
            
            # Save to database if requested
            saved_quiz = None
            if auto_save and generated_questions:
                saved_quiz = self._save_quiz_to_db(
                    user, course, title, generated_questions, context
                )
            
            # Prepare response
            response = {
                "success": True,
                "quiz": saved_quiz,
                "questions": generated_questions,
                "question_count": len(generated_questions),
                "auto_saved": auto_save,
                "generation_metadata": {
                    "workflow_steps": results.get("workflow_steps", []),
                    "agents_used": results.get("agents_used", []),
                    "confidence": results.get("total_confidence", 0.0),
                    "quality_assessment": results.get("quality_assessment")
                }
            }
            
            logger.info(f"Successfully generated quiz with {len(generated_questions)} questions for course {course_id}")
            return response
            
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {"success": False, "error": "User not found", "quiz": None, "questions": []}
        except Course.DoesNotExist:
            logger.error(f"Course {course_id} not found for user {user_id}")
            return {"success": False, "error": "Course not found", "quiz": None, "questions": []}
        except Exception as e:
            logger.error(f"Error in quiz generation: {str(e)}")
            return {"success": False, "error": str(e), "quiz": None, "questions": []}
    
    def _save_quiz_to_db(
        self,
        user: User,
        course: Course,
        title: str,
        question_data: List[Dict[str, Any]],
        context: GenerationContext
    ) -> Dict[str, Any]:
        """
        Save generated quiz and questions to the database.
        
        Args:
            user: User instance
            course: Course instance
            title: Quiz title
            question_data: List of question dictionaries
            context: Generation context
            
        Returns:
            Dictionary with saved quiz information
        """
        try:
            with transaction.atomic():
                # Create quiz
                quiz = Quiz.objects.create(
                    user=user,
                    course=course,
                    title=title,
                    description=f"AI-generated quiz on {context.topic}",
                    quiz_type=context.constraints.get("quiz_type", "practice"),
                    time_limit_minutes=context.constraints.get("time_limit_minutes", 30),
                    max_attempts=3,
                    passing_score=70.0,
                    show_correct_answers=True,
                    show_explanations=True,
                    generated_by_ai=True,
                    ai_model_used="agentic_ai",
                    source_content=context.content[:500] + "..." if len(context.content) > 500 else context.content
                )
                
                # Create questions
                saved_questions = []
                total_points = 0
                
                for i, q_data in enumerate(question_data):
                    question = QuizQuestion.objects.create(
                        quiz=quiz,
                        question_text=q_data.get("question_text", ""),
                        question_type=q_data.get("question_type", "short_answer"),
                        difficulty_level=q_data.get("difficulty_level", "medium"),
                        order=q_data.get("order", i + 1),
                        points=q_data.get("points", 1),
                        answer_options=q_data.get("answer_options", []),
                        correct_answers=q_data.get("correct_answers", []),
                        explanation=q_data.get("explanation", ""),
                        hint="",
                        tags=[],
                        source_content=q_data.get("source_content", "")
                    )
                    
                    total_points += question.points
                    
                    question_dict = {
                        "id": question.id,
                        "question_text": question.question_text,
                        "question_type": question.question_type,
                        "answer_options": question.answer_options,
                        "correct_answers": question.correct_answers,
                        "explanation": question.explanation,
                        "difficulty_level": question.difficulty_level,
                        "points": question.points,
                        "order": question.order
                    }
                    saved_questions.append(question_dict)
                
                # Update quiz totals
                quiz.total_questions = len(saved_questions)
                quiz.save()
                
                quiz_dict = {
                    "id": quiz.id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "quiz_type": quiz.quiz_type,
                    "status": quiz.status,
                    "time_limit_minutes": quiz.time_limit_minutes,
                    "total_questions": quiz.total_questions,
                    "total_points": total_points,
                    "created_at": quiz.created_at.isoformat(),
                    "questions": saved_questions
                }
                
                logger.info(f"Saved quiz '{title}' with {len(saved_questions)} questions to database")
                return quiz_dict
                
        except Exception as e:
            logger.error(f"Error saving quiz to database: {str(e)}")
            return {
                "id": None,
                "title": title,
                "error": str(e),
                "questions": question_data
            }
    
    def generate_adaptive_quiz(
        self,
        user_id: int,
        course_id: int,
        topic: str,
        target_duration_minutes: int = 20,
        adaptive_difficulty: bool = True,
        performance_history: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate an adaptive quiz that adjusts based on user performance.
        
        Args:
            user_id: ID of the user
            course_id: ID of the course
            topic: Topic for the quiz
            target_duration_minutes: Target duration for the quiz
            adaptive_difficulty: Whether to use adaptive difficulty
            performance_history: User's performance history for adaptation
            
        Returns:
            Dictionary with adaptive quiz results
        """
        try:
            # Analyze user performance to determine starting difficulty
            if performance_history:
                avg_score = performance_history.get("average_score", 0.7)
                if avg_score >= 0.9:
                    start_difficulty = "hard"
                    question_count = 8  # Fewer questions for advanced users
                elif avg_score >= 0.7:
                    start_difficulty = "medium"
                    question_count = 10
                else:
                    start_difficulty = "easy"
                    question_count = 12  # More questions for beginners
            else:
                start_difficulty = "medium"
                question_count = 10
            
            # Generate the adaptive quiz
            result = self.generate_quiz(
                user_id=user_id,
                course_id=course_id,
                title=f"Adaptive Quiz: {topic}",
                topic=topic,
                question_count=question_count,
                difficulty_level=start_difficulty,
                quiz_type="adaptive",
                time_limit_minutes=target_duration_minutes,
                question_types=["multiple_choice", "short_answer"],
                auto_save=True
            )
            
            if result.get("success"):
                # Add adaptive metadata
                result["adaptive_metadata"] = {
                    "starting_difficulty": start_difficulty,
                    "user_performance_level": performance_history.get("average_score", 0.0) if performance_history else 0.0,
                    "adaptation_strategy": "difficulty_based",
                    "recommended_next_topics": self._get_next_topic_recommendations(topic, start_difficulty)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating adaptive quiz: {str(e)}")
            return {"success": False, "error": str(e), "quiz": None, "questions": []}
    
    def _get_next_topic_recommendations(self, current_topic: str, difficulty: str) -> List[str]:
        """Get recommendations for next topics based on current performance."""
        # This is a simplified implementation
        # In practice, this would use learning analytics and curriculum mapping
        
        if difficulty == "easy":
            return [f"Review {current_topic}", f"Basic {current_topic} concepts"]
        elif difficulty == "medium":
            return [f"Advanced {current_topic}", f"{current_topic} applications"]
        else:
            return [f"{current_topic} mastery", f"Complex {current_topic} scenarios"]
    
    def bulk_generate_quizzes(
        self,
        user_id: int,
        course_id: int,
        topics: List[str],
        questions_per_quiz: int = 8,
        difficulty_level: str = "medium",
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Generate multiple quizzes in bulk for different topics.
        
        Args:
            user_id: ID of the user
            course_id: ID of the course
            topics: List of topics to create quizzes for
            questions_per_quiz: Number of questions per quiz
            difficulty_level: Difficulty level for all quizzes
            auto_save: Whether to auto-save to database
            
        Returns:
            Dictionary with bulk generation results
        """
        try:
            all_results = []
            total_quizzes = 0
            
            for topic in topics:
                try:
                    result = self.generate_quiz(
                        user_id=user_id,
                        course_id=course_id,
                        title=f"Quiz: {topic}",
                        topic=topic,
                        question_count=questions_per_quiz,
                        difficulty_level=difficulty_level,
                        quiz_type="practice",
                        auto_save=auto_save
                    )
                    
                    result["topic"] = topic
                    all_results.append(result)
                    
                    if result.get("success"):
                        total_quizzes += 1
                
                except Exception as e:
                    logger.error(f"Error generating quiz for topic '{topic}': {str(e)}")
                    all_results.append({
                        "topic": topic,
                        "success": False,
                        "error": str(e),
                        "quiz": None,
                        "questions": []
                    })
            
            return {
                "success": True,
                "total_quizzes": total_quizzes,
                "topics_processed": len(topics),
                "results_per_topic": all_results,
                "summary": {
                    "successful_quizzes": len([r for r in all_results if r.get("success")]),
                    "failed_quizzes": len([r for r in all_results if not r.get("success")]),
                    "average_questions_per_quiz": questions_per_quiz
                }
            }
            
        except Exception as e:
            logger.error(f"Error in bulk quiz generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_quizzes": 0,
                "results_per_topic": []
            }
    
    def get_quiz_recommendations(
        self,
        user_id: int,
        course_id: int,
        content_sample: str = "",
        user_performance: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get recommendations for quiz generation based on content and user performance.
        
        Args:
            user_id: ID of the user
            course_id: ID of the course
            content_sample: Sample content to analyze
            user_performance: User's performance data
            
        Returns:
            Dictionary with quiz recommendations
        """
        try:
            # Analyze content complexity
            content_length = len(content_sample)
            
            if content_length < 500:
                suggested_questions = 5
                time_estimate = 10
                complexity = "simple"
            elif content_length < 2000:
                suggested_questions = 10
                time_estimate = 20
                complexity = "moderate"
            else:
                suggested_questions = 15
                time_estimate = 30
                complexity = "complex"
            
            # Adjust based on user performance
            if user_performance:
                avg_score = user_performance.get("average_score", 0.7)
                if avg_score >= 0.85:
                    difficulty = "hard"
                    suggested_questions -= 2  # Fewer, harder questions
                elif avg_score <= 0.6:
                    difficulty = "easy"
                    suggested_questions += 3  # More, easier questions
                else:
                    difficulty = "medium"
            else:
                difficulty = "medium"
            
            return {
                "recommendations": {
                    "suggested_question_count": max(3, suggested_questions),
                    "difficulty_level": difficulty,
                    "question_types": ["multiple_choice", "short_answer", "true_false"],
                    "estimated_time_minutes": time_estimate,
                    "quiz_type": "practice",
                    "adaptive_features": user_performance is not None
                },
                "content_analysis": {
                    "length": content_length,
                    "complexity": complexity,
                    "estimated_concepts": max(1, content_length // 150)
                },
                "user_analysis": {
                    "performance_level": user_performance.get("average_score", 0.0) if user_performance else None,
                    "recommended_difficulty": difficulty,
                    "adaptive_ready": user_performance is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting quiz recommendations: {str(e)}")
            return {
                "recommendations": {
                    "suggested_question_count": 8,
                    "difficulty_level": "medium",
                    "question_types": ["multiple_choice", "short_answer"],
                    "estimated_time_minutes": 15
                },
                "error": str(e)
            }


# Factory function
def get_quiz_service() -> QuizGenerationService:
    """
    Factory function to get a quiz generation service instance.
    
    Returns:
        QuizGenerationService instance
    """
    return QuizGenerationService()