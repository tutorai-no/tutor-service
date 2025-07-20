"""
Spaced Repetition Algorithm Implementation

This module implements the SM-2 (SuperMemo 2) algorithm for spaced repetition
learning, which is used for scheduling flashcard reviews.
"""

from datetime import datetime, timedelta


class SpacedRepetitionService:
    """Legacy SM-2 implementation for backward compatibility."""

    @staticmethod
    def calculate_next_review(
        current_ease_factor: float,
        current_interval: int,
        repetitions: int,
        quality_response: int,
    ) -> tuple[float, int, int, datetime]:
        """
        Calculate next review parameters based on SM-2 algorithm.

        Args:
            current_ease_factor: Current ease factor (1.3 to 5.0)
            current_interval: Current interval in days
            repetitions: Number of successful repetitions
            quality_response: Quality of response (0-5)
                0: Complete blackout
                1: Incorrect but remembered
                2: Incorrect but easy
                3: Correct with difficulty
                4: Correct with hesitation
                5: Perfect recall

        Returns:
            Tuple of (new_ease_factor, new_interval, new_repetitions, next_review_date)
        """

        # Ensure quality response is in valid range
        quality_response = max(0, min(5, quality_response))

        # Initialize variables
        ease_factor = current_ease_factor
        interval = current_interval
        reps = repetitions

        if quality_response >= 3:
            # Correct response
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = int(interval * ease_factor)

            reps += 1

            # Update ease factor based on quality
            ease_factor = ease_factor + (
                0.1 - (5 - quality_response) * (0.08 + (5 - quality_response) * 0.02)
            )
        else:
            # Incorrect response - reset repetitions and set short interval
            reps = 0
            interval = 1
            ease_factor = ease_factor - 0.2

        # Ensure ease factor stays within bounds
        ease_factor = max(1.3, min(5.0, ease_factor))

        # Calculate next review date
        next_review_date = datetime.now() + timedelta(days=interval)

        return ease_factor, interval, reps, next_review_date

    @staticmethod
    def get_difficulty_multiplier(difficulty_level: str) -> float:
        """Get multiplier for difficulty level."""
        multipliers = {
            "easy": 1.2,
            "medium": 1.0,
            "hard": 0.8,
        }
        return multipliers.get(difficulty_level, 1.0)

    @staticmethod
    def adjust_for_difficulty(interval: int, difficulty_level: str) -> int:
        """Adjust interval based on difficulty level."""
        multiplier = SpacedRepetitionService.get_difficulty_multiplier(difficulty_level)
        return max(1, int(interval * multiplier))

    @staticmethod
    def calculate_retention_rate(reviews: list, time_window_days: int = 30) -> float:
        """
        Calculate retention rate over a given time window.

        Args:
            reviews: List of review objects with quality_response and created_at
            time_window_days: Time window in days to calculate retention

        Returns:
            Retention rate as float between 0 and 1
        """
        if not reviews:
            return 0.0

        # Filter reviews within time window
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        recent_reviews = [r for r in reviews if r.created_at >= cutoff_date]

        if not recent_reviews:
            return 0.0

        # Calculate retention (quality >= 3 is considered successful)
        successful_reviews = [r for r in recent_reviews if r.quality_response >= 3]

        return len(successful_reviews) / len(recent_reviews)

    @staticmethod
    def get_optimal_batch_size(
        total_due: int, available_time_minutes: int, avg_time_per_card: int = 30
    ) -> int:
        """
        Calculate optimal batch size for study session.

        Args:
            total_due: Total number of cards due
            available_time_minutes: Available study time in minutes
            avg_time_per_card: Average time per card in seconds

        Returns:
            Optimal batch size
        """
        max_cards_by_time = (available_time_minutes * 60) // avg_time_per_card

        # Balance between time constraint and effective learning
        optimal_batch = min(
            total_due, max_cards_by_time, 50  # Maximum reasonable batch size
        )

        return max(1, optimal_batch)

    @staticmethod
    def prioritize_cards(flashcards: list) -> list:
        """
        Prioritize flashcards for review based on multiple factors.

        Args:
            flashcards: List of flashcard objects

        Returns:
            Sorted list of flashcards by priority
        """

        def priority_score(card):
            score = 0

            # Overdue cards get higher priority
            if card.next_review_date < datetime.now():
                overdue_days = (datetime.now() - card.next_review_date).days
                score += overdue_days * 10

            # Cards with low success rate get higher priority
            if card.total_reviews > 0:
                score += (1 - card.success_rate) * 20

            # Difficult cards get slightly higher priority
            if card.difficulty_level == "hard":
                score += 5
            elif card.difficulty_level == "medium":
                score += 2

            # Starred cards get higher priority
            if card.is_starred:
                score += 15

            # Cards with low ease factor (struggling) get higher priority
            if card.ease_factor < 2.0:
                score += (2.0 - card.ease_factor) * 10

            return score

        return sorted(flashcards, key=priority_score, reverse=True)

    @staticmethod
    def calculate_study_load(flashcards: list) -> dict:
        """
        Calculate study load metrics.

        Args:
            flashcards: List of flashcard objects

        Returns:
            Dictionary with study load metrics
        """
        now = datetime.now()

        # Count cards by status
        due_today = len(
            [f for f in flashcards if f.next_review_date.date() <= now.date()]
        )
        overdue = len([f for f in flashcards if f.next_review_date < now])
        due_this_week = len(
            [
                f
                for f in flashcards
                if f.next_review_date.date() <= (now + timedelta(days=7)).date()
            ]
        )

        # Calculate difficulty distribution
        difficulty_counts = {
            "easy": len([f for f in flashcards if f.difficulty_level == "easy"]),
            "medium": len([f for f in flashcards if f.difficulty_level == "medium"]),
            "hard": len([f for f in flashcards if f.difficulty_level == "hard"]),
        }

        # Calculate mastery distribution
        mastery_counts = {}
        for card in flashcards:
            mastery_level = card.mastery_level
            mastery_counts[mastery_level] = mastery_counts.get(mastery_level, 0) + 1

        # Estimate time requirements
        estimated_time_minutes = {
            "today": due_today * 0.5,  # 30 seconds per card
            "this_week": due_this_week * 0.5,
            "overdue": overdue * 0.75,  # Overdue cards take longer
        }

        return {
            "total_cards": len(flashcards),
            "due_today": due_today,
            "overdue": overdue,
            "due_this_week": due_this_week,
            "difficulty_distribution": difficulty_counts,
            "mastery_distribution": mastery_counts,
            "estimated_time_minutes": estimated_time_minutes,
            "study_pressure": (
                min(100, (overdue * 2 + due_today) / len(flashcards) * 100)
                if flashcards
                else 0
            ),
        }

    @staticmethod
    def get_review_recommendations(user_stats: dict, current_time: datetime) -> list:
        """
        Get personalized review recommendations.

        Args:
            user_stats: Dictionary with user statistics
            current_time: Current datetime

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Check for overdue cards
        if user_stats.get("overdue", 0) > 0:
            recommendations.append(
                {
                    "type": "overdue_cards",
                    "priority": "high",
                    "message": f"You have {user_stats['overdue']} overdue cards. Review them to maintain your progress.",
                    "action": "review_overdue",
                }
            )

        # Check for due cards
        if user_stats.get("due_today", 0) > 0:
            recommendations.append(
                {
                    "type": "due_cards",
                    "priority": "medium",
                    "message": f"You have {user_stats['due_today']} cards due for review today.",
                    "action": "start_review_session",
                }
            )

        # Check study pressure
        study_pressure = user_stats.get("study_pressure", 0)
        if study_pressure > 70:
            recommendations.append(
                {
                    "type": "high_workload",
                    "priority": "high",
                    "message": "Your study workload is high. Consider increasing daily review time or reducing new cards.",
                    "action": "adjust_settings",
                }
            )

        # Check for long gaps
        if user_stats.get("days_since_last_review", 0) > 2:
            recommendations.append(
                {
                    "type": "study_gap",
                    "priority": "medium",
                    "message": "You haven't reviewed in a while. Regular practice is key to retention.",
                    "action": "resume_studying",
                }
            )

        # Time-based recommendations
        hour = current_time.hour
        if 9 <= hour <= 11:
            recommendations.append(
                {
                    "type": "optimal_time",
                    "priority": "low",
                    "message": "Morning is a great time for focused studying. Your brain is fresh!",
                    "action": "start_morning_session",
                }
            )

        return recommendations
