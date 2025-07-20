"""
Adaptive study plan generator service for creating optimal study schedules.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, time, date
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Avg, Sum

from .base import AdaptiveLearningService, StudyMetrics, TimeSlotOptimizer, calculate_cognitive_load

logger = logging.getLogger(__name__)


class StudyPlanGeneratorService(AdaptiveLearningService):
    """
    Service for generating adaptive study plans with optimal scheduling.
    """
    
    def __init__(self):
        """Initialize the study plan generator service."""
        super().__init__()
        self.max_daily_load = 85  # Maximum cognitive load per day
        self.optimal_session_gap = 2  # Hours between sessions
        self.min_session_duration = 15  # Minimum session length in minutes
        self.max_session_duration = 120  # Maximum session length in minutes
    
    def generate_adaptive_study_plan(
        self,
        user,
        course,
        plan_type: str = 'weekly',
        target_date: Optional[date] = None,
        preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate an adaptive study plan based on user performance and preferences.
        
        Args:
            user: User object
            course: Course object
            plan_type: Type of plan (weekly, monthly, exam_prep, custom)
            target_date: Target completion/exam date
            preferences: User preferences for study times and intensity
            
        Returns:
            Dictionary containing the generated study plan
        """
        try:
            self.logger.info(f"Generating adaptive study plan for user {user.id}, course {course.id}")
            
            # Analyze user performance and learning patterns
            metrics = StudyMetrics(user, course)
            performance_analysis = self._analyze_user_performance(metrics)
            
            # Get course structure and requirements
            course_structure = self._analyze_course_structure(course)
            
            # Calculate optimal study parameters
            study_parameters = self._calculate_study_parameters(
                performance_analysis, course_structure, plan_type, target_date, preferences
            )
            
            # Generate schedule
            schedule = self._generate_optimal_schedule(
                user, course, study_parameters, target_date, preferences
            )
            
            # Create study plan data
            plan_data = {
                'plan_type': plan_type,
                'generated_at': timezone.now().isoformat(),
                'performance_analysis': performance_analysis,
                'study_parameters': study_parameters,
                'schedule': schedule,
                'adaptations_made': self._get_adaptations_summary(performance_analysis),
                'estimated_completion': self._estimate_completion_date(schedule),
                'cognitive_load_distribution': self._analyze_cognitive_load(schedule)
            }
            
            # Log adaptation decisions
            self.log_adaptation(
                str(user.id),
                'study_plan_generation',
                {
                    'plan_type': plan_type,
                    'adaptations': plan_data['adaptations_made'],
                    'total_sessions': len(schedule),
                    'estimated_weeks': len(set(s['week'] for s in schedule))
                }
            )
            
            return {
                'success': True,
                'plan_data': plan_data,
                'recommendations': self._generate_plan_recommendations(performance_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating study plan: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'plan_data': {},
                'recommendations': []
            }
    
    def adapt_existing_plan(
        self,
        study_plan,
        performance_update: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Adapt an existing study plan based on recent performance.
        
        Args:
            study_plan: StudyPlan object to adapt
            performance_update: Recent performance data to consider
            
        Returns:
            Dictionary with updated plan data
        """
        try:
            # Get updated metrics
            metrics = StudyMetrics(study_plan.user, study_plan.course, time_period_days=7)
            current_performance = self._analyze_user_performance(metrics)
            
            # Compare with plan expectations
            adaptations_needed = self._identify_needed_adaptations(
                study_plan, current_performance, performance_update
            )
            
            if not adaptations_needed:
                return {
                    'success': True,
                    'adaptations_made': [],
                    'message': 'No adaptations needed - plan is on track'
                }
            
            # Apply adaptations
            updated_schedule = self._apply_adaptations(
                study_plan.plan_data.get('schedule', []),
                adaptations_needed,
                current_performance
            )
            
            # Update plan data
            updated_plan_data = study_plan.plan_data.copy()
            updated_plan_data.update({
                'schedule': updated_schedule,
                'last_adaptation': timezone.now().isoformat(),
                'adaptations_history': updated_plan_data.get('adaptations_history', []) + [{
                    'date': timezone.now().isoformat(),
                    'adaptations': adaptations_needed,
                    'performance_trigger': current_performance
                }]
            })
            
            # Log adaptations
            self.log_adaptation(
                str(study_plan.user.id),
                'plan_adaptation',
                {
                    'plan_id': str(study_plan.id),
                    'adaptations': adaptations_needed,
                    'performance_metrics': current_performance
                }
            )
            
            return {
                'success': True,
                'updated_plan_data': updated_plan_data,
                'adaptations_made': adaptations_needed,
                'recommendations': self._generate_adaptation_recommendations(adaptations_needed)
            }
            
        except Exception as e:
            self.logger.error(f"Error adapting study plan: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'adaptations_made': []
            }
    
    def _analyze_user_performance(self, metrics: StudyMetrics) -> Dict[str, Any]:
        """Analyze user performance to inform plan generation."""
        quiz_performance = metrics.get_quiz_performance()
        session_metrics = metrics.get_study_session_metrics()
        flashcard_retention = metrics.get_flashcard_retention()
        learning_velocity = metrics.get_learning_velocity()
        optimal_times = metrics.get_optimal_study_time()
        
        # Determine user's learning profile
        learning_profile = self._determine_learning_profile(
            quiz_performance, session_metrics, flashcard_retention
        )
        
        return {
            'quiz_performance': quiz_performance,
            'session_metrics': session_metrics,
            'flashcard_retention': flashcard_retention,
            'learning_velocity': learning_velocity,
            'optimal_study_times': optimal_times,
            'learning_profile': learning_profile,
            'performance_score': self._calculate_overall_performance_score(
                quiz_performance, session_metrics, flashcard_retention
            )
        }
    
    def _analyze_course_structure(self, course) -> Dict[str, Any]:
        """Analyze course structure to understand requirements."""
        # Get course topics and documents
        from courses.models import Document
        from learning.models import LearningProgress
        
        documents = Document.objects.filter(course=course)
        total_topics = documents.count()
        
        # Estimate study requirements based on documents
        estimated_hours = 0
        difficulty_distribution = {'easy': 0, 'medium': 0, 'hard': 0}
        
        for doc in documents:
            # Simple heuristic: estimate hours based on document size/type
            if doc.content_type == 'application/pdf':
                estimated_hours += max(2, doc.file_size / (1024 * 1024))  # 1 hour per MB
            else:
                estimated_hours += 1  # Default 1 hour for other types
            
            # Assume medium difficulty by default
            difficulty_distribution['medium'] += 1
        
        return {
            'total_topics': total_topics,
            'estimated_total_hours': estimated_hours,
            'difficulty_distribution': difficulty_distribution,
            'has_deadlines': False,  # TODO: Check for assignment deadlines
            'complexity_score': min(10, total_topics / 5)  # 1-10 scale
        }
    
    def _calculate_study_parameters(
        self,
        performance_analysis: Dict[str, Any],
        course_structure: Dict[str, Any],
        plan_type: str,
        target_date: Optional[date],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimal study parameters based on analysis."""
        # Base parameters
        default_daily_hours = 2.0
        default_sessions_per_day = 2
        default_study_days = 5
        
        # Adjust based on performance
        performance_score = performance_analysis['performance_score']
        learning_velocity = performance_analysis['learning_velocity']
        
        # Performance-based adjustments
        if performance_score < 60:
            # Struggling student - need more time, shorter sessions
            daily_hours_multiplier = 1.3
            session_length_multiplier = 0.8
            sessions_per_day = 3  # More frequent, shorter sessions
        elif performance_score > 85:
            # High performer - can handle longer, fewer sessions
            daily_hours_multiplier = 0.9
            session_length_multiplier = 1.2
            sessions_per_day = 1  # Fewer, longer sessions
        else:
            # Average performer - standard parameters
            daily_hours_multiplier = 1.0
            session_length_multiplier = 1.0
            sessions_per_day = 2
        
        # Apply user preferences
        if preferences:
            daily_hours_multiplier *= preferences.get('intensity_multiplier', 1.0)
            if preferences.get('prefer_short_sessions'):
                session_length_multiplier *= 0.8
                sessions_per_day = min(4, sessions_per_day + 1)
        
        # Calculate final parameters
        optimal_daily_hours = default_daily_hours * daily_hours_multiplier
        optimal_session_length = 45 * session_length_multiplier  # minutes
        
        # Ensure reasonable bounds
        optimal_daily_hours = max(0.5, min(6.0, optimal_daily_hours))
        optimal_session_length = max(15, min(120, optimal_session_length))
        
        return {
            'daily_hours': optimal_daily_hours,
            'session_length_minutes': int(optimal_session_length),
            'sessions_per_day': sessions_per_day,
            'study_days_per_week': default_study_days,
            'difficulty_adaptation': self._get_difficulty_adaptation(performance_score),
            'review_frequency': self._calculate_review_frequency(performance_analysis),
            'break_frequency': self._calculate_break_frequency(optimal_session_length)
        }
    
    def _generate_optimal_schedule(
        self,
        user,
        course,
        study_parameters: Dict[str, Any],
        target_date: Optional[date],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimal study schedule."""
        schedule = []
        
        # Initialize time slot optimizer
        optimizer = TimeSlotOptimizer(user, preferences)
        
        # Calculate schedule timeframe
        start_date = timezone.now().date()
        if target_date:
            end_date = target_date
            total_weeks = max(1, (end_date - start_date).days // 7)
        else:
            total_weeks = 12  # Default 12-week plan
            end_date = start_date + timedelta(weeks=total_weeks)
        
        # Get course content to schedule
        from courses.models import Document
        documents = Document.objects.filter(course=course).order_by('created_at')
        
        # Distribute content across weeks
        content_per_week = max(1, len(documents) // total_weeks)
        
        current_week = 1
        current_date = start_date
        
        while current_week <= total_weeks and current_date <= end_date:
            # Calculate week dates
            week_start = current_date
            week_end = min(current_date + timedelta(days=6), end_date)
            
            # Get content for this week
            week_documents = documents[
                (current_week - 1) * content_per_week:
                current_week * content_per_week
            ]
            
            # Generate sessions for this week
            week_sessions = self._generate_week_sessions(
                week_start, week_end, week_documents, study_parameters, optimizer
            )
            
            # Add to schedule
            for session in week_sessions:
                session.update({
                    'week': current_week,
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat()
                })
                schedule.append(session)
            
            current_week += 1
            current_date += timedelta(days=7)
        
        return schedule
    
    def _generate_week_sessions(
        self,
        week_start: date,
        week_end: date,
        documents: List,
        study_parameters: Dict[str, Any],
        optimizer: TimeSlotOptimizer
    ) -> List[Dict[str, Any]]:
        """Generate study sessions for a specific week."""
        sessions = []
        
        # Calculate total hours needed for this week
        weekly_hours = study_parameters['daily_hours'] * study_parameters['study_days_per_week']
        
        # Get optimal time slots
        time_slots = optimizer.get_optimal_time_slots(
            weekly_hours,
            ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        )
        
        # Create sessions
        session_id = 1
        current_date = week_start
        
        for day_offset in range(7):
            session_date = week_start + timedelta(days=day_offset)
            if session_date > week_end:
                break
            
            # Skip weekends unless specified
            if session_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
            # Create sessions for this day
            sessions_today = study_parameters['sessions_per_day']
            
            for session_num in range(sessions_today):
                if session_id > len(time_slots):
                    break
                
                time_slot = time_slots[session_id - 1] if session_id <= len(time_slots) else time_slots[0]
                
                # Assign content to session
                session_content = self._assign_content_to_session(
                    documents, session_num, sessions_today, study_parameters
                )
                
                session = {
                    'session_id': f"w{week_start.strftime('%W')}_s{session_id}",
                    'date': session_date.isoformat(),
                    'start_time': time_slot['start_time'].strftime('%H:%M'),
                    'duration_minutes': time_slot['duration_minutes'],
                    'content': session_content,
                    'estimated_cognitive_load': calculate_cognitive_load(session_content['tasks']),
                    'productivity_prediction': time_slot['productivity_score'],
                    'session_type': 'study',
                    'is_mandatory': True,
                    'can_reschedule': True
                }
                
                sessions.append(session)
                session_id += 1
        
        return sessions
    
    def _assign_content_to_session(
        self,
        documents: List,
        session_num: int,
        total_sessions: int,
        study_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assign content to a specific study session."""
        # Simple content assignment - distribute documents across sessions
        docs_per_session = max(1, len(documents) // total_sessions)
        start_idx = session_num * docs_per_session
        end_idx = min(start_idx + docs_per_session, len(documents))
        
        session_documents = documents[start_idx:end_idx]
        
        tasks = []
        for doc in session_documents:
            # Create tasks based on document
            if doc.content_type == 'application/pdf':
                tasks.append({
                    'id': f"read_{doc.id}",
                    'type': 'reading',
                    'title': f"Read: {doc.name}",
                    'document_id': str(doc.id),
                    'duration_minutes': 30,
                    'difficulty': 'medium',
                    'mandatory': True
                })
                
                # Add practice task
                tasks.append({
                    'id': f"practice_{doc.id}",
                    'type': 'practice',
                    'title': f"Practice exercises for {doc.name}",
                    'document_id': str(doc.id),
                    'duration_minutes': 15,
                    'difficulty': 'medium',
                    'mandatory': False
                })
        
        return {
            'focus_topic': session_documents[0].name if session_documents else 'General Study',
            'tasks': tasks,
            'estimated_duration': sum(task['duration_minutes'] for task in tasks),
            'learning_objectives': [f"Master content from {doc.name}" for doc in session_documents]
        }
    
    def _identify_needed_adaptations(
        self,
        study_plan,
        current_performance: Dict[str, Any],
        performance_update: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify what adaptations are needed for the study plan."""
        adaptations = []
        
        performance_score = current_performance['performance_score']
        plan_data = study_plan.plan_data
        
        # Check if performance has significantly changed
        original_score = plan_data.get('performance_analysis', {}).get('performance_score', 70)
        score_change = performance_score - original_score
        
        if score_change < -15:
            # Performance declining significantly
            adaptations.append({
                'type': 'reduce_difficulty',
                'reason': 'Performance declining',
                'severity': 'high',
                'details': {
                    'score_change': score_change,
                    'action': 'Add more review time, reduce session length'
                }
            })
        elif score_change > 15:
            # Performance improving significantly
            adaptations.append({
                'type': 'increase_challenge',
                'reason': 'Performance improving',
                'severity': 'medium',
                'details': {
                    'score_change': score_change,
                    'action': 'Increase session length, add advanced content'
                }
            })
        
        # Check completion rate
        completion_rate = current_performance['session_metrics']['completion_rate']
        if completion_rate < 70:
            adaptations.append({
                'type': 'reduce_session_length',
                'reason': 'Low completion rate',
                'severity': 'medium',
                'details': {
                    'completion_rate': completion_rate,
                    'action': 'Reduce session length to improve completion'
                }
            })
        
        # Check learning velocity
        learning_velocity = current_performance['learning_velocity']
        if learning_velocity < 0.5:  # Less than 0.5 topics per week
            adaptations.append({
                'type': 'increase_review_frequency',
                'reason': 'Slow learning velocity',
                'severity': 'medium',
                'details': {
                    'velocity': learning_velocity,
                    'action': 'Add more review sessions'
                }
            })
        
        return adaptations
    
    def _apply_adaptations(
        self,
        current_schedule: List[Dict[str, Any]],
        adaptations: List[Dict[str, Any]],
        performance_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply adaptations to the study schedule."""
        updated_schedule = current_schedule.copy()
        
        for adaptation in adaptations:
            adaptation_type = adaptation['type']
            
            if adaptation_type == 'reduce_difficulty':
                updated_schedule = self._reduce_schedule_difficulty(updated_schedule)
            elif adaptation_type == 'increase_challenge':
                updated_schedule = self._increase_schedule_challenge(updated_schedule)
            elif adaptation_type == 'reduce_session_length':
                updated_schedule = self._reduce_session_lengths(updated_schedule)
            elif adaptation_type == 'increase_review_frequency':
                updated_schedule = self._add_review_sessions(updated_schedule)
        
        return updated_schedule
    
    def _reduce_schedule_difficulty(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reduce difficulty of study schedule."""
        for session in schedule:
            # Reduce session duration by 25%
            session['duration_minutes'] = int(session['duration_minutes'] * 0.75)
            
            # Mark more tasks as optional
            for task in session.get('content', {}).get('tasks', []):
                if task.get('difficulty') == 'hard':
                    task['mandatory'] = False
                    task['difficulty'] = 'medium'
        
        return schedule
    
    def _increase_schedule_challenge(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Increase challenge level of study schedule."""
        for session in schedule:
            # Increase session duration by 25%
            session['duration_minutes'] = int(session['duration_minutes'] * 1.25)
            
            # Add challenge tasks
            content = session.get('content', {})
            if 'tasks' in content:
                content['tasks'].append({
                    'id': f"challenge_{session['session_id']}",
                    'type': 'challenge',
                    'title': 'Advanced practice exercise',
                    'duration_minutes': 15,
                    'difficulty': 'hard',
                    'mandatory': False
                })
        
        return schedule
    
    def _reduce_session_lengths(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reduce length of study sessions."""
        for session in schedule:
            # Reduce duration by 30%
            new_duration = int(session['duration_minutes'] * 0.7)
            session['duration_minutes'] = max(15, new_duration)  # Minimum 15 minutes
            
            # Reduce task durations proportionally
            for task in session.get('content', {}).get('tasks', []):
                task['duration_minutes'] = int(task['duration_minutes'] * 0.7)
        
        return schedule
    
    def _add_review_sessions(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add additional review sessions to schedule."""
        # Add review sessions every few regular sessions
        enhanced_schedule = []
        
        for i, session in enumerate(schedule):
            enhanced_schedule.append(session)
            
            # Add review session every 3rd session
            if (i + 1) % 3 == 0:
                review_session = {
                    'session_id': f"review_{session['session_id']}",
                    'date': session['date'],
                    'start_time': session['start_time'],
                    'duration_minutes': 20,
                    'content': {
                        'focus_topic': 'Review',
                        'tasks': [{
                            'id': f"review_task_{i}",
                            'type': 'review',
                            'title': 'Review previous topics',
                            'duration_minutes': 20,
                            'difficulty': 'easy',
                            'mandatory': True
                        }]
                    },
                    'session_type': 'review',
                    'is_mandatory': False,
                    'can_reschedule': True
                }
                enhanced_schedule.append(review_session)
        
        return enhanced_schedule
    
    def _determine_learning_profile(
        self,
        quiz_performance: Dict[str, Any],
        session_metrics: Dict[str, Any],
        flashcard_retention: Dict[str, Any]
    ) -> str:
        """Determine user's learning profile based on performance data."""
        avg_score = quiz_performance['average_score']
        completion_rate = session_metrics['completion_rate']
        retention_rate = flashcard_retention['retention_rate']
        
        if avg_score >= 85 and completion_rate >= 80 and retention_rate >= 80:
            return 'high_performer'
        elif avg_score >= 70 and completion_rate >= 70 and retention_rate >= 70:
            return 'steady_learner'
        elif completion_rate < 60:
            return 'needs_motivation'
        elif retention_rate < 60:
            return 'needs_repetition'
        else:
            return 'developing'
    
    def _calculate_overall_performance_score(
        self,
        quiz_performance: Dict[str, Any],
        session_metrics: Dict[str, Any],
        flashcard_retention: Dict[str, Any]
    ) -> float:
        """Calculate overall performance score (0-100)."""
        # Weighted average of different metrics
        quiz_weight = 0.4
        session_weight = 0.3
        flashcard_weight = 0.3
        
        quiz_score = quiz_performance['average_score']
        session_score = session_metrics['completion_rate']
        flashcard_score = flashcard_retention['retention_rate']
        
        overall_score = (
            quiz_score * quiz_weight +
            session_score * session_weight +
            flashcard_score * flashcard_weight
        )
        
        return round(overall_score, 1)
    
    def _get_difficulty_adaptation(self, performance_score: float) -> str:
        """Get difficulty adaptation recommendation."""
        if performance_score < 60:
            return 'easier'
        elif performance_score > 85:
            return 'harder'
        else:
            return 'maintain'
    
    def _calculate_review_frequency(self, performance_analysis: Dict[str, Any]) -> int:
        """Calculate optimal review frequency in days."""
        retention_rate = performance_analysis['flashcard_retention']['retention_rate']
        
        if retention_rate < 60:
            return 1  # Daily review
        elif retention_rate < 80:
            return 2  # Every 2 days
        else:
            return 3  # Every 3 days
    
    def _calculate_break_frequency(self, session_length_minutes: float) -> int:
        """Calculate break frequency within sessions."""
        if session_length_minutes >= 60:
            return 15  # Break every 15 minutes for long sessions
        elif session_length_minutes >= 30:
            return 25  # Break every 25 minutes for medium sessions
        else:
            return 0   # No breaks for short sessions
    
    def _get_adaptations_summary(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """Get summary of adaptations made based on performance."""
        adaptations = []
        
        performance_score = performance_analysis['performance_score']
        learning_profile = performance_analysis['learning_profile']
        
        if learning_profile == 'high_performer':
            adaptations.append('Increased session length for advanced learner')
            adaptations.append('Added challenge exercises')
        elif learning_profile == 'needs_motivation':
            adaptations.append('Reduced session length to improve completion')
            adaptations.append('Added more achievable milestones')
        elif learning_profile == 'needs_repetition':
            adaptations.append('Increased review frequency')
            adaptations.append('Added spaced repetition sessions')
        
        return adaptations
    
    def _estimate_completion_date(self, schedule: List[Dict[str, Any]]) -> str:
        """Estimate completion date based on schedule."""
        if not schedule:
            return timezone.now().date().isoformat()
        
        last_session = max(schedule, key=lambda s: s['date'])
        return last_session['date']
    
    def _analyze_cognitive_load(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cognitive load distribution across the schedule."""
        daily_loads = {}
        
        for session in schedule:
            date = session['date']
            load = session.get('estimated_cognitive_load', 50)
            
            if date not in daily_loads:
                daily_loads[date] = 0
            daily_loads[date] += load
        
        loads = list(daily_loads.values())
        
        return {
            'average_daily_load': sum(loads) / len(loads) if loads else 0,
            'max_daily_load': max(loads) if loads else 0,
            'min_daily_load': min(loads) if loads else 0,
            'load_distribution': daily_loads
        }
    
    def _generate_plan_recommendations(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the study plan."""
        recommendations = []
        
        learning_profile = performance_analysis['learning_profile']
        performance_score = performance_analysis['performance_score']
        
        if performance_score < 70:
            recommendations.append('Consider scheduling shorter, more frequent study sessions')
            recommendations.append('Focus on review and reinforcement activities')
        
        if learning_profile == 'high_performer':
            recommendations.append('Challenge yourself with advanced practice problems')
            recommendations.append('Consider peer tutoring to reinforce learning')
        
        optimal_times = performance_analysis['optimal_study_times']
        peak_hour = optimal_times.get('peak_productivity_hour', 9)
        recommendations.append(f'Schedule your most challenging topics around {peak_hour}:00')
        
        return recommendations
    
    def _generate_adaptation_recommendations(self, adaptations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on adaptations made."""
        recommendations = []
        
        for adaptation in adaptations:
            if adaptation['type'] == 'reduce_difficulty':
                recommendations.append('Take breaks between study sessions to avoid burnout')
                recommendations.append('Consider getting help from tutors or study groups')
            elif adaptation['type'] == 'increase_challenge':
                recommendations.append('Great progress! Consider exploring advanced topics')
                recommendations.append('Share your knowledge by helping other students')
        
        return recommendations


# Global service instance
study_plan_generator = StudyPlanGeneratorService()


def get_study_plan_generator() -> StudyPlanGeneratorService:
    """Get the global study plan generator service instance."""
    return study_plan_generator