"""
Review scheduling service for intelligent review timing and spaced repetition optimization.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, time, date
from django.utils import timezone
from django.db.models import Q, Avg, Count, Max
import math

from .base import AdaptiveLearningService, StudyMetrics

logger = logging.getLogger(__name__)


class ReviewSchedulingService(AdaptiveLearningService):
    """
    Service for intelligent review scheduling using spaced repetition algorithms.
    """
    
    def __init__(self):
        """Initialize the review scheduling service."""
        super().__init__()
        self.base_intervals = [1, 3, 7, 14, 30, 90]  # Base review intervals in days
        self.difficulty_multipliers = {
            'easy': 1.3,
            'medium': 1.0,
            'hard': 0.6,
            'again': 0.2
        }
        self.max_interval = 365  # Maximum interval between reviews
        self.min_interval = 1    # Minimum interval between reviews
    
    def schedule_intelligent_reviews(
        self,
        user,
        course=None,
        target_retention: float = 0.85
    ) -> Dict[str, Any]:
        """
        Schedule intelligent reviews for optimal retention.
        
        Args:
            user: User object
            course: Optional course filter
            target_retention: Target retention rate (0-1)
            
        Returns:
            Optimized review schedule
        """
        try:
            self.logger.info(f"Scheduling reviews for user {user.id}")
            
            # Get items that need review
            review_items = self._get_items_needing_review(user, course)
            
            # Analyze user's retention patterns
            retention_analysis = self._analyze_retention_patterns(user, course)
            
            # Calculate optimal review schedule
            review_schedule = self._calculate_optimal_schedule(
                review_items, retention_analysis, target_retention
            )
            
            # Distribute reviews across available time
            distributed_schedule = self._distribute_reviews_optimally(
                review_schedule, user, course
            )
            
            return {
                'success': True,
                'review_schedule': distributed_schedule,
                'retention_analysis': retention_analysis,
                'scheduling_stats': {
                    'total_items': len(review_items),
                    'reviews_today': len([r for r in distributed_schedule if r['date'] == timezone.now().date().isoformat()]),
                    'reviews_this_week': len([r for r in distributed_schedule if self._is_this_week(r['date'])]),
                    'target_retention': target_retention
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error scheduling reviews: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'review_schedule': []
            }
    
    def update_review_schedule_realtime(
        self,
        user,
        item_id: str,
        item_type: str,
        performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update review schedule in real-time based on performance.
        
        Args:
            user: User object
            item_id: ID of the reviewed item
            item_type: Type of item (flashcard, topic, etc.)
            performance: Performance data from review
            
        Returns:
            Updated schedule for the item
        """
        try:
            # Calculate next review date based on performance
            next_review = self._calculate_next_review_date(
                item_id, item_type, performance, user
            )
            
            # Update difficulty based on performance
            updated_difficulty = self._update_item_difficulty(
                item_id, item_type, performance
            )
            
            # Adjust related items if needed
            related_adjustments = self._adjust_related_items(
                item_id, item_type, performance, user
            )
            
            return {
                'success': True,
                'next_review_date': next_review.isoformat(),
                'updated_difficulty': updated_difficulty,
                'related_adjustments': related_adjustments,
                'performance_impact': self._analyze_performance_impact(performance)
            }
            
        except Exception as e:
            self.logger.error(f"Error updating review schedule: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def optimize_daily_review_load(
        self,
        user,
        target_daily_reviews: int = 50,
        max_daily_reviews: int = 100
    ) -> Dict[str, Any]:
        """
        Optimize daily review load to maintain consistent practice.
        
        Args:
            user: User object
            target_daily_reviews: Target number of daily reviews
            max_daily_reviews: Maximum daily reviews
            
        Returns:
            Optimized daily review distribution
        """
        try:
            # Get upcoming reviews
            upcoming_reviews = self._get_upcoming_reviews(user, days_ahead=14)
            
            # Analyze current load distribution
            load_analysis = self._analyze_review_load_distribution(upcoming_reviews)
            
            # Redistribute overloaded days
            optimized_schedule = self._redistribute_review_load(
                upcoming_reviews, target_daily_reviews, max_daily_reviews
            )
            
            # Calculate load balancing recommendations
            recommendations = self._generate_load_balancing_recommendations(
                load_analysis, optimized_schedule
            )
            
            return {
                'success': True,
                'current_load_analysis': load_analysis,
                'optimized_schedule': optimized_schedule,
                'recommendations': recommendations,
                'load_metrics': {
                    'average_daily_reviews': load_analysis['average_daily_load'],
                    'peak_load_day': load_analysis['peak_day'],
                    'load_variance': load_analysis['load_variance']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing review load: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_items_needing_review(self, user, course) -> List[Dict[str, Any]]:
        """Get all items that need review."""
        items = []
        
        # Get flashcards needing review
        flashcard_items = self._get_flashcards_for_review(user, course)
        items.extend(flashcard_items)
        
        # Get topics needing review
        topic_items = self._get_topics_for_review(user, course)
        items.extend(topic_items)
        
        # Get concepts needing reinforcement
        concept_items = self._get_concepts_for_review(user, course)
        items.extend(concept_items)
        
        return items
    
    def _get_flashcards_for_review(self, user, course) -> List[Dict[str, Any]]:
        """Get flashcards that need review."""
        from assessments.models import Flashcard, FlashcardReview
        
        flashcards = Flashcard.objects.filter(user=user)
        if course:
            flashcards = flashcards.filter(course=course)
        
        review_items = []
        
        for flashcard in flashcards:
            # Get last review
            last_review = FlashcardReview.objects.filter(
                flashcard=flashcard,
                user=user
            ).order_by('-created_at').first()
            
            if not last_review:
                # New card - needs initial review
                review_items.append({
                    'id': str(flashcard.id),
                    'type': 'flashcard',
                    'title': flashcard.front[:50] + '...' if len(flashcard.front) > 50 else flashcard.front,
                    'difficulty': 'medium',
                    'last_reviewed': None,
                    'next_review_date': timezone.now().date(),
                    'priority': 'high',
                    'estimated_time_minutes': 2
                })
            else:
                # Calculate next review date
                next_review = self._calculate_next_flashcard_review(flashcard, last_review)
                
                if next_review <= timezone.now().date():
                    review_items.append({
                        'id': str(flashcard.id),
                        'type': 'flashcard',
                        'title': flashcard.front[:50] + '...' if len(flashcard.front) > 50 else flashcard.front,
                        'difficulty': last_review.difficulty,
                        'last_reviewed': last_review.created_at.date().isoformat(),
                        'next_review_date': next_review.isoformat(),
                        'priority': self._calculate_review_priority(last_review),
                        'estimated_time_minutes': 2
                    })
        
        return review_items
    
    def _get_topics_for_review(self, user, course) -> List[Dict[str, Any]]:
        """Get topics that need review."""
        from learning.models import LearningProgress
        
        progress_entries = LearningProgress.objects.filter(user=user)
        if course:
            progress_entries = progress_entries.filter(course=course)
        
        review_items = []
        
        for progress in progress_entries:
            # Topics with mastery level < 4 need review
            if progress.mastery_level < 4:
                days_since_update = (timezone.now().date() - progress.updated_at.date()).days
                
                # Review frequency based on mastery level
                review_intervals = {1: 1, 2: 3, 3: 7}  # days
                needed_interval = review_intervals.get(progress.mastery_level, 7)
                
                if days_since_update >= needed_interval:
                    review_items.append({
                        'id': str(progress.id),
                        'type': 'topic',
                        'title': f"Review: {progress.topic}",
                        'difficulty': self._mastery_to_difficulty(progress.mastery_level),
                        'last_reviewed': progress.updated_at.date().isoformat(),
                        'next_review_date': timezone.now().date().isoformat(),
                        'priority': self._calculate_topic_priority(progress),
                        'estimated_time_minutes': 15
                    })
        
        return review_items
    
    def _get_concepts_for_review(self, user, course) -> List[Dict[str, Any]]:
        """Get concepts that need reinforcement based on quiz performance."""
        from assessments.models import QuizAttempt
        
        # Find concepts where user scored below 75%
        recent_attempts = QuizAttempt.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=30),
            score__lt=75
        )
        
        if course:
            recent_attempts = recent_attempts.filter(quiz__course=course)
        
        review_items = []
        
        # Group by quiz and identify weak concepts
        for attempt in recent_attempts:
            review_items.append({
                'id': f"concept_{attempt.quiz.id}",
                'type': 'concept',
                'title': f"Review concepts from: {attempt.quiz.title}",
                'difficulty': 'hard' if attempt.score < 50 else 'medium',
                'last_reviewed': attempt.created_at.date().isoformat(),
                'next_review_date': timezone.now().date().isoformat(),
                'priority': 'high' if attempt.score < 50 else 'medium',
                'estimated_time_minutes': 20
            })
        
        return review_items
    
    def _analyze_retention_patterns(self, user, course) -> Dict[str, Any]:
        """Analyze user's retention patterns."""
        from assessments.models import FlashcardReview
        
        reviews = FlashcardReview.objects.filter(user=user)
        if course:
            reviews = reviews.filter(flashcard__course=course)
        
        if not reviews.exists():
            return {
                'average_retention': 0.8,
                'optimal_intervals': self.base_intervals,
                'difficulty_patterns': {},
                'forgetting_curve': {}
            }
        
        # Calculate retention rates at different intervals
        retention_by_interval = self._calculate_retention_by_interval(reviews)
        
        # Analyze difficulty patterns
        difficulty_patterns = self._analyze_difficulty_patterns(reviews)
        
        # Model forgetting curve
        forgetting_curve = self._model_forgetting_curve(reviews)
        
        return {
            'average_retention': retention_by_interval.get('overall', 0.8),
            'retention_by_interval': retention_by_interval,
            'difficulty_patterns': difficulty_patterns,
            'forgetting_curve': forgetting_curve,
            'optimal_intervals': self._calculate_optimal_intervals(retention_by_interval)
        }
    
    def _calculate_optimal_schedule(
        self,
        review_items: List[Dict[str, Any]],
        retention_analysis: Dict[str, Any],
        target_retention: float
    ) -> List[Dict[str, Any]]:
        """Calculate optimal review schedule."""
        scheduled_items = []
        
        for item in review_items:
            # Calculate optimal review date
            optimal_date = self._calculate_optimal_review_date(
                item, retention_analysis, target_retention
            )
            
            # Add scheduling metadata
            scheduled_item = item.copy()
            scheduled_item.update({
                'optimal_review_date': optimal_date.isoformat(),
                'retention_prediction': self._predict_retention(item, optimal_date),
                'scheduling_confidence': self._calculate_scheduling_confidence(item, retention_analysis)
            })
            
            scheduled_items.append(scheduled_item)
        
        # Sort by priority and date
        scheduled_items.sort(key=lambda x: (
            x['priority'] != 'high',
            x['optimal_review_date'],
            x['difficulty'] == 'hard'
        ))
        
        return scheduled_items
    
    def _distribute_reviews_optimally(
        self,
        review_schedule: List[Dict[str, Any]],
        user,
        course
    ) -> List[Dict[str, Any]]:
        """Distribute reviews optimally across available time."""
        # Get user's available study time and preferences
        metrics = StudyMetrics(user, course)
        optimal_times = metrics.get_optimal_study_time()
        
        # Group reviews by date
        reviews_by_date = {}
        for review in review_schedule:
            date = review['optimal_review_date']
            if date not in reviews_by_date:
                reviews_by_date[date] = []
            reviews_by_date[date].append(review)
        
        # Distribute within each day
        distributed_schedule = []
        
        for date, day_reviews in reviews_by_date.items():
            # Calculate available time for reviews
            available_minutes = self._calculate_available_review_time(date, user)
            
            # Prioritize and fit reviews into available time
            fitted_reviews = self._fit_reviews_to_time(
                day_reviews, available_minutes, optimal_times
            )
            
            distributed_schedule.extend(fitted_reviews)
        
        return distributed_schedule
    
    def _calculate_next_review_date(
        self,
        item_id: str,
        item_type: str,
        performance: Dict[str, Any],
        user
    ) -> datetime:
        """Calculate next review date based on performance."""
        difficulty = performance.get('difficulty', 'medium')
        response_time = performance.get('response_time', 5)
        correctness = performance.get('correct', True)
        
        if item_type == 'flashcard':
            return self._calculate_flashcard_next_review(
                item_id, difficulty, response_time, correctness, user
            )
        elif item_type == 'topic':
            return self._calculate_topic_next_review(
                item_id, performance, user
            )
        else:
            # Default interval based on difficulty
            base_interval = 3  # days
            multiplier = self.difficulty_multipliers.get(difficulty, 1.0)
            
            if not correctness:
                multiplier *= 0.5  # Halve interval for incorrect responses
            
            interval_days = max(1, int(base_interval * multiplier))
            return timezone.now() + timedelta(days=interval_days)
    
    def _calculate_flashcard_next_review(
        self,
        flashcard_id: str,
        difficulty: str,
        response_time: float,
        correctness: bool,
        user
    ) -> datetime:
        """Calculate next review date for flashcard using spaced repetition."""
        from assessments.models import Flashcard, FlashcardReview
        
        try:
            flashcard = Flashcard.objects.get(id=flashcard_id)
            
            # Get review history
            reviews = FlashcardReview.objects.filter(
                flashcard=flashcard,
                user=user
            ).order_by('-created_at')
            
            review_count = reviews.count()
            
            # Calculate interval based on SM-2 algorithm
            if review_count == 0:
                interval = 1
            elif review_count == 1:
                interval = 6
            else:
                last_review = reviews.first()
                previous_interval = last_review.interval if hasattr(last_review, 'interval') else 6
                
                # Easiness factor based on difficulty
                ease_factor = {
                    'easy': 2.5,
                    'medium': 2.0,
                    'hard': 1.5,
                    'again': 1.0
                }.get(difficulty, 2.0)
                
                interval = int(previous_interval * ease_factor)
            
            # Adjust for response time
            if response_time < 2:
                interval = int(interval * 1.2)  # Quick response = increase interval
            elif response_time > 10:
                interval = int(interval * 0.8)  # Slow response = decrease interval
            
            # Ensure bounds
            interval = max(self.min_interval, min(interval, self.max_interval))
            
            return timezone.now() + timedelta(days=interval)
            
        except Exception as e:
            self.logger.error(f"Error calculating flashcard review date: {str(e)}")
            return timezone.now() + timedelta(days=3)  # Default fallback
    
    def _calculate_topic_next_review(
        self,
        topic_id: str,
        performance: Dict[str, Any],
        user
    ) -> datetime:
        """Calculate next review date for topic."""
        mastery_level = performance.get('mastery_level', 2)
        understanding_score = performance.get('understanding_score', 50)
        
        # Interval based on mastery level
        intervals = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
        base_interval = intervals.get(mastery_level, 7)
        
        # Adjust based on understanding score
        if understanding_score < 50:
            multiplier = 0.5
        elif understanding_score < 70:
            multiplier = 0.8
        elif understanding_score > 90:
            multiplier = 1.5
        else:
            multiplier = 1.0
        
        interval_days = max(1, int(base_interval * multiplier))
        return timezone.now() + timedelta(days=interval_days)
    
    def _update_item_difficulty(
        self,
        item_id: str,
        item_type: str,
        performance: Dict[str, Any]
    ) -> str:
        """Update item difficulty based on performance."""
        current_difficulty = performance.get('current_difficulty', 'medium')
        correctness = performance.get('correct', True)
        response_time = performance.get('response_time', 5)
        
        # Adjust difficulty based on performance
        if correctness and response_time < 3:
            # Quick and correct - make easier
            if current_difficulty == 'hard':
                return 'medium'
            elif current_difficulty == 'medium':
                return 'easy'
        elif not correctness or response_time > 10:
            # Incorrect or slow - make harder
            if current_difficulty == 'easy':
                return 'medium'
            elif current_difficulty == 'medium':
                return 'hard'
        
        return current_difficulty
    
    def _adjust_related_items(
        self,
        item_id: str,
        item_type: str,
        performance: Dict[str, Any],
        user
    ) -> List[Dict[str, Any]]:
        """Adjust related items based on performance."""
        adjustments = []
        
        if item_type == 'flashcard':
            # If user struggled with a card, schedule related cards sooner
            if not performance.get('correct', True):
                # Find related flashcards (same topic/category)
                related_cards = self._find_related_flashcards(item_id, user)
                
                for card in related_cards:
                    adjustments.append({
                        'item_id': str(card.id),
                        'item_type': 'flashcard',
                        'adjustment': 'schedule_sooner',
                        'reason': 'related_item_difficulty'
                    })
        
        return adjustments
    
    def _find_related_flashcards(self, flashcard_id: str, user) -> List:
        """Find flashcards related to the given flashcard."""
        from assessments.models import Flashcard
        
        try:
            flashcard = Flashcard.objects.get(id=flashcard_id)
            
            # Find cards with similar tags or from same course
            related = Flashcard.objects.filter(
                user=user,
                course=flashcard.course
            ).exclude(id=flashcard_id)[:5]  # Limit to 5 related cards
            
            return list(related)
            
        except Exception:
            return []
    
    def _analyze_performance_impact(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the impact of performance on learning."""
        correctness = performance.get('correct', True)
        response_time = performance.get('response_time', 5)
        confidence = performance.get('confidence', 3)
        
        impact = {
            'learning_efficiency': 'high' if correctness and response_time < 5 else 'medium',
            'retention_prediction': 'strong' if correctness and confidence >= 4 else 'weak',
            'adjustment_needed': not correctness or response_time > 10 or confidence < 3
        }
        
        return impact
    
    def _get_upcoming_reviews(self, user, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """Get upcoming reviews for the next N days."""
        # This would integrate with the review scheduling system
        # For now, return empty list as placeholder
        return []
    
    def _analyze_review_load_distribution(self, upcoming_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the distribution of review load."""
        if not upcoming_reviews:
            return {
                'average_daily_load': 0,
                'peak_day': timezone.now().date().isoformat(),
                'load_variance': 0,
                'overloaded_days': []
            }
        
        # Group by date
        daily_loads = {}
        for review in upcoming_reviews:
            date = review.get('date', timezone.now().date().isoformat())
            daily_loads[date] = daily_loads.get(date, 0) + 1
        
        loads = list(daily_loads.values())
        avg_load = sum(loads) / len(loads) if loads else 0
        peak_day = max(daily_loads.items(), key=lambda x: x[1])[0] if daily_loads else timezone.now().date().isoformat()
        
        # Calculate variance
        variance = sum((load - avg_load) ** 2 for load in loads) / len(loads) if loads else 0
        
        # Find overloaded days (more than 50% above average)
        overloaded_days = [
            date for date, load in daily_loads.items()
            if load > avg_load * 1.5
        ]
        
        return {
            'average_daily_load': round(avg_load, 1),
            'peak_day': peak_day,
            'load_variance': round(variance, 1),
            'overloaded_days': overloaded_days,
            'daily_distribution': daily_loads
        }
    
    def _redistribute_review_load(
        self,
        upcoming_reviews: List[Dict[str, Any]],
        target_daily_reviews: int,
        max_daily_reviews: int
    ) -> List[Dict[str, Any]]:
        """Redistribute review load to balance daily workload."""
        # Group reviews by date
        reviews_by_date = {}
        for review in upcoming_reviews:
            date = review.get('date')
            if date not in reviews_by_date:
                reviews_by_date[date] = []
            reviews_by_date[date].append(review)
        
        # Redistribute overloaded days
        redistributed_schedule = []
        
        for date, day_reviews in reviews_by_date.items():
            if len(day_reviews) <= max_daily_reviews:
                # No redistribution needed
                redistributed_schedule.extend(day_reviews)
            else:
                # Redistribute excess reviews
                kept_reviews = day_reviews[:target_daily_reviews]
                excess_reviews = day_reviews[target_daily_reviews:]
                
                redistributed_schedule.extend(kept_reviews)
                
                # Move excess reviews to nearby days
                for i, excess_review in enumerate(excess_reviews):
                    new_date = self._find_available_date(
                        date, reviews_by_date, max_daily_reviews, i
                    )
                    excess_review['date'] = new_date
                    excess_review['redistributed'] = True
                    redistributed_schedule.append(excess_review)
        
        return redistributed_schedule
    
    def _find_available_date(
        self,
        original_date: str,
        reviews_by_date: Dict[str, List],
        max_daily_reviews: int,
        offset: int
    ) -> str:
        """Find available date for redistributed review."""
        base_date = datetime.fromisoformat(original_date).date()
        
        # Try days after the original date
        for days_offset in range(1, 8):  # Try next 7 days
            candidate_date = base_date + timedelta(days=days_offset)
            candidate_str = candidate_date.isoformat()
            
            current_load = len(reviews_by_date.get(candidate_str, []))
            if current_load < max_daily_reviews:
                return candidate_str
        
        # If no available day found, return original date + offset
        return (base_date + timedelta(days=offset + 1)).isoformat()
    
    def _generate_load_balancing_recommendations(
        self,
        load_analysis: Dict[str, Any],
        optimized_schedule: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for load balancing."""
        recommendations = []
        
        if load_analysis['load_variance'] > 100:
            recommendations.append('Consider spreading reviews more evenly across the week')
        
        if load_analysis['overloaded_days']:
            recommendations.append(f"Reschedule reviews from overloaded days: {', '.join(load_analysis['overloaded_days'])}")
        
        if load_analysis['average_daily_load'] > 80:
            recommendations.append('Your review load is quite high - consider extending review intervals for mastered items')
        
        return recommendations
    
    def _calculate_next_flashcard_review(self, flashcard, last_review):
        """Calculate next review date for a flashcard."""
        difficulty = last_review.difficulty
        days_since_review = (timezone.now().date() - last_review.created_at.date()).days
        
        # Simple interval calculation
        intervals = {
            'easy': max(6, days_since_review * 2),
            'medium': max(3, days_since_review * 1.5),
            'hard': max(1, days_since_review),
            'again': 1
        }
        
        interval = intervals.get(difficulty, 3)
        return last_review.created_at.date() + timedelta(days=int(interval))
    
    def _calculate_review_priority(self, last_review) -> str:
        """Calculate priority for review item."""
        days_overdue = (timezone.now().date() - self._calculate_next_flashcard_review(
            last_review.flashcard, last_review
        )).days
        
        if days_overdue > 7:
            return 'high'
        elif days_overdue > 3:
            return 'medium'
        else:
            return 'low'
    
    def _mastery_to_difficulty(self, mastery_level: int) -> str:
        """Convert mastery level to difficulty."""
        if mastery_level <= 2:
            return 'hard'
        elif mastery_level <= 3:
            return 'medium'
        else:
            return 'easy'
    
    def _calculate_topic_priority(self, progress) -> str:
        """Calculate priority for topic review."""
        if progress.mastery_level <= 2:
            return 'high'
        elif progress.mastery_level <= 3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_retention_by_interval(self, reviews) -> Dict[str, float]:
        """Calculate retention rates at different intervals."""
        # Placeholder implementation
        return {
            'overall': 0.75,
            '1_day': 0.9,
            '3_days': 0.8,
            '7_days': 0.7,
            '14_days': 0.6
        }
    
    def _analyze_difficulty_patterns(self, reviews) -> Dict[str, Any]:
        """Analyze patterns in difficulty responses."""
        difficulty_counts = {
            'easy': reviews.filter(difficulty='easy').count(),
            'medium': reviews.filter(difficulty='medium').count(),
            'hard': reviews.filter(difficulty='hard').count(),
            'again': reviews.filter(difficulty='again').count()
        }
        
        total = sum(difficulty_counts.values())
        
        return {
            'distribution': {
                k: v / total if total > 0 else 0
                for k, v in difficulty_counts.items()
            },
            'dominant_difficulty': max(difficulty_counts.items(), key=lambda x: x[1])[0] if total > 0 else 'medium'
        }
    
    def _model_forgetting_curve(self, reviews) -> Dict[str, Any]:
        """Model user's forgetting curve."""
        # Simplified forgetting curve model
        return {
            'initial_retention': 0.9,
            'decay_rate': 0.1,
            'half_life_days': 7,
            'model_confidence': 0.75
        }
    
    def _calculate_optimal_intervals(self, retention_by_interval: Dict[str, float]) -> List[int]:
        """Calculate optimal review intervals."""
        # Use base intervals adjusted by retention rates
        return self.base_intervals
    
    def _calculate_optimal_review_date(
        self,
        item: Dict[str, Any],
        retention_analysis: Dict[str, Any],
        target_retention: float
    ) -> date:
        """Calculate optimal review date for an item."""
        difficulty = item.get('difficulty', 'medium')
        item_type = item.get('type', 'flashcard')
        
        # Base interval based on difficulty
        base_intervals = {
            'easy': 7,
            'medium': 3,
            'hard': 1
        }
        
        base_interval = base_intervals.get(difficulty, 3)
        
        # Adjust based on retention analysis
        avg_retention = retention_analysis.get('average_retention', 0.8)
        if avg_retention < target_retention:
            # User has lower retention - shorten intervals
            multiplier = avg_retention / target_retention
        else:
            # User has good retention - can extend intervals
            multiplier = min(1.5, avg_retention / target_retention)
        
        interval_days = max(1, int(base_interval * multiplier))
        
        return timezone.now().date() + timedelta(days=interval_days)
    
    def _predict_retention(self, item: Dict[str, Any], review_date: date) -> float:
        """Predict retention probability for item at review date."""
        days_until_review = (review_date - timezone.now().date()).days
        difficulty = item.get('difficulty', 'medium')
        
        # Simple retention prediction model
        base_retention = {
            'easy': 0.9,
            'medium': 0.8,
            'hard': 0.6
        }.get(difficulty, 0.8)
        
        # Decay over time
        decay_rate = 0.05  # 5% per day
        predicted_retention = base_retention * (1 - decay_rate) ** days_until_review
        
        return max(0.1, min(1.0, predicted_retention))
    
    def _calculate_scheduling_confidence(
        self,
        item: Dict[str, Any],
        retention_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence in scheduling decision."""
        # Based on amount of historical data
        model_confidence = retention_analysis.get('forgetting_curve', {}).get('model_confidence', 0.5)
        
        # Adjust for item difficulty
        difficulty_confidence = {
            'easy': 0.9,
            'medium': 0.8,
            'hard': 0.6
        }.get(item.get('difficulty', 'medium'), 0.8)
        
        return (model_confidence + difficulty_confidence) / 2
    
    def _calculate_available_review_time(self, date: str, user) -> int:
        """Calculate available time for reviews on a given date."""
        # Default to 30 minutes for reviews
        return 30
    
    def _fit_reviews_to_time(
        self,
        day_reviews: List[Dict[str, Any]],
        available_minutes: int,
        optimal_times: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fit reviews into available time slots."""
        # Sort by priority
        day_reviews.sort(key=lambda x: (
            x['priority'] != 'high',
            x['difficulty'] == 'hard'
        ))
        
        fitted_reviews = []
        used_time = 0
        
        for review in day_reviews:
            estimated_time = review.get('estimated_time_minutes', 5)
            
            if used_time + estimated_time <= available_minutes:
                # Add time slot information
                review_with_time = review.copy()
                review_with_time.update({
                    'scheduled_time': self._assign_time_slot(used_time, optimal_times),
                    'duration_minutes': estimated_time
                })
                fitted_reviews.append(review_with_time)
                used_time += estimated_time
            else:
                # Move to next available day
                review['rescheduled'] = True
                fitted_reviews.append(review)
        
        return fitted_reviews
    
    def _assign_time_slot(self, offset_minutes: int, optimal_times: Dict[str, Any]) -> str:
        """Assign specific time slot for review."""
        # Use peak productivity hour as base
        peak_hour = optimal_times.get('peak_productivity_hour', 9)
        
        # Add offset
        total_minutes = peak_hour * 60 + offset_minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        return f"{hours:02d}:{minutes:02d}"
    
    def _is_this_week(self, date_str: str) -> bool:
        """Check if date is in current week."""
        try:
            date = datetime.fromisoformat(date_str).date()
            today = timezone.now().date()
            
            # Calculate start of week (Monday)
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            return week_start <= date <= week_end
        except:
            return False


# Global service instance
review_scheduling_service = ReviewSchedulingService()


def get_review_scheduling_service() -> ReviewSchedulingService:
    """Get the global review scheduling service instance."""
    return review_scheduling_service