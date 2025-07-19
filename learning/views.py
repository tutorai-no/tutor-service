import logging
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F, Max, Min
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

from .models import (
    StudyPlan,
    StudyGoal,
    LearningProgress,
    StudySession,
    StudyRecommendation,
)
from .serializers import (
    StudyPlanSerializer,
    StudyPlanDetailSerializer,
    StudyPlanCreateSerializer,
    StudyGoalSerializer,
    StudyGoalCreateSerializer,
    LearningProgressSerializer,
    StudySessionSerializer,
    StudySessionCreateSerializer,
    StudyRecommendationSerializer,
    StudyAnalyticsSerializer,
    LearningPathAnalysisSerializer,
    PerformanceTrendsSerializer,
    LearningRecommendationSerializer,
)


class StudyPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing study plans."""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return StudyPlanSerializer
        elif self.action == 'create':
            return StudyPlanCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return StudyPlanDetailSerializer
        return StudyPlanSerializer
    
    def get_queryset(self):
        """Get study plans for the authenticated user."""
        return StudyPlan.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a new study plan."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a study plan."""
        study_plan = self.get_object()
        
        # Deactivate other active plans for the same course
        StudyPlan.objects.filter(
            user=request.user,
            course=study_plan.course,
            is_active=True
        ).exclude(id=study_plan.id).update(is_active=False)
        
        study_plan.is_active = True
        study_plan.save()
        
        return Response({'status': 'activated'})
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get progress report for a study plan."""
        study_plan = self.get_object()
        progress_data = study_plan.get_progress_summary()
        
        serializer = ProgressReportSerializer(data=progress_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_schedule(self, request, pk=None):
        """Generate an optimal study schedule."""
        study_plan = self.get_object()
        
        # Get parameters
        hours_per_day = request.data.get('hours_per_day', 2)
        preferred_times = request.data.get('preferred_times', ['evening'])
        include_weekends = request.data.get('include_weekends', True)
        
        # Generate schedule based on plan and preferences
        schedule_data = self._generate_optimal_schedule(
            study_plan, hours_per_day, preferred_times, include_weekends
        )
        
        # Save schedule if requested
        if request.data.get('save_schedule', False):
            schedule = StudySchedule.objects.create(
                user=request.user,
                study_plan=study_plan,
                schedule_data=schedule_data,
                hours_per_day=hours_per_day,
                preferred_times=preferred_times,
                include_weekends=include_weekends
            )
            return Response(StudyScheduleSerializer(schedule).data)
        
        return Response(schedule_data)
    
    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Get AI-powered recommendations for the study plan."""
        study_plan = self.get_object()
        
        # Generate recommendations based on progress and performance
        recommendations = self._generate_recommendations(study_plan, request.user)
        
        # Save recommendations
        for rec_data in recommendations:
            LearningRecommendation.objects.create(
                user=request.user,
                study_plan=study_plan,
                **rec_data
            )
        
        return Response({'recommendations': recommendations})
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get study plan dashboard data."""
        user = request.user
        
        # Active plans
        active_plans = self.get_queryset().filter(is_active=True)
        
        # Upcoming milestones
        upcoming_goals = LearningGoal.objects.filter(
            study_plan__user=user,
            status__in=['not_started', 'in_progress'],
            target_date__gte=timezone.now(),
            target_date__lte=timezone.now() + timedelta(days=7)
        ).order_by('target_date')[:5]
        
        # Recent progress
        recent_progress = ProgressEntry.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        # Study streak
        study_streak = self._calculate_study_streak(user)
        
        dashboard_data = {
            'active_plans': StudyPlanSerializer(active_plans, many=True).data,
            'upcoming_goals': LearningGoalSerializer(upcoming_goals, many=True).data,
            'recent_progress': ProgressEntrySerializer(recent_progress, many=True).data,
            'study_streak': study_streak,
            'weekly_hours': self._calculate_weekly_hours(user),
            'completion_rate': self._calculate_completion_rate(user),
        }
        
        return Response(dashboard_data)
    
    def _generate_optimal_schedule(self, study_plan, hours_per_day, preferred_times, include_weekends):
        """Generate an optimal study schedule based on goals and preferences."""
        schedule = []
        current_date = timezone.now().date()
        end_date = study_plan.end_date or (current_date + timedelta(days=90))
        
        # Get incomplete goals sorted by priority and target date
        goals = study_plan.goals.filter(
            status__in=['not_started', 'in_progress']
        ).order_by('priority', 'target_date')
        
        # Distribute study time across goals
        while current_date <= end_date and goals:
            if include_weekends or current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                daily_schedule = {
                    'date': current_date,
                    'sessions': [],
                    'total_hours': 0
                }
                
                remaining_hours = hours_per_day
                for goal in goals:
                    if remaining_hours <= 0:
                        break
                    
                    session_hours = min(remaining_hours, goal.estimated_hours / 10)  # Spread over days
                    if session_hours > 0.25:  # Minimum 15 minutes
                        session = {
                            'goal_id': str(goal.id),
                            'goal_title': goal.title,
                            'duration_hours': round(session_hours, 2),
                            'time_slot': self._get_time_slot(preferred_times),
                            'focus_areas': goal.key_concepts[:3] if goal.key_concepts else [],
                        }
                        daily_schedule['sessions'].append(session)
                        daily_schedule['total_hours'] += session_hours
                        remaining_hours -= session_hours
                
                if daily_schedule['sessions']:
                    schedule.append(daily_schedule)
            
            current_date += timedelta(days=1)
        
        return schedule
    
    def _get_time_slot(self, preferred_times):
        """Get a time slot based on preferences."""
        time_slots = {
            'morning': {'start': '06:00', 'end': '09:00'},
            'late_morning': {'start': '09:00', 'end': '12:00'},
            'afternoon': {'start': '14:00', 'end': '17:00'},
            'evening': {'start': '18:00', 'end': '21:00'},
            'night': {'start': '21:00', 'end': '23:00'},
        }
        
        for pref in preferred_times:
            if pref in time_slots:
                return time_slots[pref]
        
        return time_slots['evening']  # Default
    
    def _generate_recommendations(self, study_plan, user):
        """Generate AI-powered learning recommendations."""
        recommendations = []
        
        # Analyze current progress
        progress = study_plan.get_progress_summary()
        
        # Check if behind schedule
        if progress['completion_percentage'] < progress['expected_completion']:
            recommendations.append({
                'type': 'schedule',
                'priority': 'high',
                'title': 'You are behind schedule',
                'description': f'Your completion rate is {progress["completion_percentage"]:.0f}% but should be {progress["expected_completion"]:.0f}%',
                'action': 'increase_study_time',
                'metadata': {
                    'suggested_hours': 3,
                    'focus_goals': [str(g.id) for g in study_plan.goals.filter(status='in_progress')[:3]]
                }
            })
        
        # Check for struggling areas
        low_performance_goals = study_plan.goals.filter(
            progress_percentage__lt=50,
            status='in_progress'
        )
        if low_performance_goals.exists():
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'title': 'Focus on challenging topics',
                'description': 'Some goals need more attention based on your progress',
                'action': 'review_materials',
                'metadata': {
                    'struggling_goals': [str(g.id) for g in low_performance_goals[:3]],
                    'suggested_resources': ['practice_problems', 'video_tutorials', 'peer_discussion']
                }
            })
        
        # Suggest break if studying too much
        recent_sessions = StudySession.objects.filter(
            user=user,
            started_at__gte=timezone.now() - timedelta(days=7)
        )
        total_recent_hours = sum(s.duration_minutes or 0 for s in recent_sessions) / 60
        if total_recent_hours > 40:  # More than 40 hours in a week
            recommendations.append({
                'type': 'wellbeing',
                'priority': 'medium',
                'title': 'Consider taking a break',
                'description': f'You have studied {total_recent_hours:.1f} hours this week',
                'action': 'schedule_break',
                'metadata': {
                    'suggested_break_days': 1,
                    'relaxation_activities': ['exercise', 'meditation', 'hobby']
                }
            })
        
        return recommendations
    
    def _calculate_study_streak(self, user):
        """Calculate the user's study streak."""
        sessions = StudySession.objects.filter(
            user=user,
            status='completed'
        ).order_by('-started_at')
        
        if not sessions:
            return {'current_streak': 0, 'longest_streak': 0}
        
        current_streak = 0
        longest_streak = 0
        last_date = None
        temp_streak = 0
        
        for session in sessions:
            session_date = session.started_at.date()
            
            if last_date is None:
                temp_streak = 1
                if session_date == timezone.now().date():
                    current_streak = 1
            elif (last_date - session_date).days == 1:
                temp_streak += 1
                if session_date == timezone.now().date() or (
                    last_date == timezone.now().date() and (last_date - session_date).days == 1
                ):
                    current_streak = temp_streak
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
            
            last_date = session_date
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_study_date': last_date.isoformat() if last_date else None
        }
    
    def _calculate_weekly_hours(self, user):
        """Calculate study hours for the current week."""
        week_start = timezone.now() - timedelta(days=timezone.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        sessions = StudySession.objects.filter(
            user=user,
            started_at__gte=week_start,
            status='completed'
        )
        
        total_minutes = sum(s.duration_minutes or 0 for s in sessions)
        return round(total_minutes / 60, 1)
    
    def _calculate_completion_rate(self, user):
        """Calculate overall goal completion rate."""
        total_goals = LearningGoal.objects.filter(
            study_plan__user=user
        ).count()
        
        if total_goals == 0:
            return 0
        
        completed_goals = LearningGoal.objects.filter(
            study_plan__user=user,
            status='completed'
        ).count()
        
        return round((completed_goals / total_goals) * 100, 1)


class StudyGoalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing learning goals."""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return LearningGoalCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return LearningGoalDetailSerializer
        return LearningGoalSerializer
    
    def get_queryset(self):
        """Get learning goals for the authenticated user."""
        return LearningGoal.objects.filter(study_plan__user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a new learning goal."""
        study_plan = serializer.validated_data['study_plan']
        if study_plan.user != self.request.user:
            raise permissions.PermissionDenied("You can only create goals for your own study plans")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a goal as completed."""
        goal = self.get_object()
        goal.status = 'completed'
        goal.actual_completion_date = timezone.now()
        goal.progress_percentage = 100
        goal.save()
        
        # Create progress entry
        ProgressEntry.objects.create(
            user=request.user,
            study_plan=goal.study_plan,
            goal=goal,
            progress_type='goal_completed',
            description=f'Completed goal: {goal.title}',
            metadata={'goal_id': str(goal.id), 'completion_date': timezone.now().isoformat()}
        )
        
        return Response({'status': 'completed'})
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update progress for a goal."""
        goal = self.get_object()
        progress_percentage = request.data.get('progress_percentage')
        notes = request.data.get('notes', '')
        
        if progress_percentage is not None:
            goal.progress_percentage = min(100, max(0, progress_percentage))
            if goal.progress_percentage == 100:
                goal.status = 'completed'
                goal.actual_completion_date = timezone.now()
            elif goal.progress_percentage > 0:
                goal.status = 'in_progress'
            goal.save()
            
            # Create progress entry
            ProgressEntry.objects.create(
                user=request.user,
                study_plan=goal.study_plan,
                goal=goal,
                progress_type='progress_update',
                description=f'Updated progress to {goal.progress_percentage}%',
                notes=notes,
                metadata={
                    'goal_id': str(goal.id),
                    'progress_percentage': goal.progress_percentage
                }
            )
        
        return Response(LearningGoalDetailSerializer(goal).data)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        """Get recommended resources for a goal."""
        goal = self.get_object()
        
        # Generate resource recommendations based on goal
        resources = self._generate_resource_recommendations(goal)
        
        return Response({'resources': resources})
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming goals."""
        goals = self.get_queryset().filter(
            status__in=['not_started', 'in_progress'],
            target_date__gte=timezone.now(),
            target_date__lte=timezone.now() + timedelta(days=30)
        ).order_by('target_date')
        
        serializer = LearningGoalSerializer(goals, many=True)
        return Response(serializer.data)
    
    def _generate_resource_recommendations(self, goal):
        """Generate resource recommendations for a goal."""
        resources = []
        
        # Based on goal type and content
        if 'programming' in goal.title.lower() or 'code' in goal.title.lower():
            resources.extend([
                {
                    'type': 'practice',
                    'title': 'Coding exercises on LeetCode',
                    'url': 'https://leetcode.com',
                    'estimated_time': '30 minutes',
                    'difficulty': 'medium'
                },
                {
                    'type': 'tutorial',
                    'title': 'Interactive programming tutorials',
                    'url': 'https://www.codecademy.com',
                    'estimated_time': '1 hour',
                    'difficulty': 'beginner'
                }
            ])
        
        if 'math' in goal.title.lower() or 'calculus' in goal.title.lower():
            resources.extend([
                {
                    'type': 'video',
                    'title': 'Khan Academy Mathematics',
                    'url': 'https://www.khanacademy.org/math',
                    'estimated_time': '45 minutes',
                    'difficulty': 'adaptive'
                },
                {
                    'type': 'practice',
                    'title': 'Practice problems with solutions',
                    'url': 'https://www.wolframalpha.com',
                    'estimated_time': '30 minutes',
                    'difficulty': 'medium'
                }
            ])
        
        # Add general resources
        resources.extend([
            {
                'type': 'article',
                'title': 'Study techniques for effective learning',
                'url': 'https://www.coursera.org/articles/study-techniques',
                'estimated_time': '15 minutes',
                'difficulty': 'easy'
            }
        ])
        
        return resources


class StudySessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing study sessions."""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return StudySessionCreateSerializer
        elif self.action == 'complete':
            return StudySessionCompleteSerializer
        return StudySessionSerializer
    
    def get_queryset(self):
        """Get study sessions for the authenticated user."""
        return StudySession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create and start a new study session."""
        serializer.save(
            user=self.request.user,
            started_at=timezone.now(),
            status='active'
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a study session."""
        session = self.get_object()
        
        if session.status != 'active':
            return Response(
                {'error': 'Session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = StudySessionCompleteSerializer(data=request.data)
        if serializer.is_valid():
            # Update session
            session.ended_at = timezone.now()
            session.status = 'completed'
            session.duration_minutes = int((session.ended_at - session.started_at).total_seconds() / 60)
            session.productivity_rating = serializer.validated_data.get('productivity_rating')
            session.notes = serializer.validated_data.get('notes', '')
            session.topics_covered = serializer.validated_data.get('topics_covered', [])
            session.goals_worked_on = serializer.validated_data.get('goals_worked_on', [])
            session.save()
            
            # Update goal progress if provided
            progress_updates = serializer.validated_data.get('progress_updates', [])
            for update in progress_updates:
                goal_id = update.get('goal_id')
                progress = update.get('progress_percentage')
                if goal_id and progress is not None:
                    try:
                        goal = LearningGoal.objects.get(
                            id=goal_id,
                            study_plan__user=request.user
                        )
                        goal.progress_percentage = min(100, max(0, progress))
                        if goal.progress_percentage > 0:
                            goal.status = 'in_progress'
                        if goal.progress_percentage == 100:
                            goal.status = 'completed'
                        goal.save()
                    except LearningGoal.DoesNotExist:
                        pass
            
            # Create progress entry
            ProgressEntry.objects.create(
                user=request.user,
                study_plan=session.study_plan,
                progress_type='study_session',
                description=f'Completed {session.duration_minutes} minute study session',
                notes=session.notes,
                metadata={
                    'session_id': str(session.id),
                    'duration_minutes': session.duration_minutes,
                    'productivity_rating': session.productivity_rating,
                    'topics_covered': session.topics_covered
                }
            )
            
            return Response(StudySessionSerializer(session).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a study session."""
        session = self.get_object()
        
        if session.status != 'active':
            return Response(
                {'error': 'Session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'paused'
        session.save()
        
        return Response({'status': 'paused'})
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused study session."""
        session = self.get_object()
        
        if session.status != 'paused':
            return Response(
                {'error': 'Session is not paused'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'active'
        session.save()
        
        return Response({'status': 'active'})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active study sessions."""
        active_sessions = self.get_queryset().filter(
            status__in=['active', 'paused']
        )
        
        serializer = StudySessionSerializer(active_sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get study session statistics."""
        sessions = self.get_queryset().filter(status='completed')
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            sessions = sessions.filter(started_at__gte=start_date)
        if end_date:
            sessions = sessions.filter(started_at__lte=end_date)
        
        # Calculate statistics
        total_sessions = sessions.count()
        total_minutes = sum(s.duration_minutes or 0 for s in sessions)
        avg_duration = total_minutes / total_sessions if total_sessions > 0 else 0
        avg_productivity = sessions.aggregate(
            avg_productivity=Avg('productivity_rating')
        )['avg_productivity'] or 0
        
        # Sessions by time of day
        sessions_by_hour = sessions.annotate(
            hour=F('started_at__hour')
        ).values('hour').annotate(
            count=Count('id'),
            avg_duration=Avg('duration_minutes')
        ).order_by('hour')
        
        # Sessions by day of week
        sessions_by_weekday = sessions.annotate(
            weekday=F('started_at__week_day')
        ).values('weekday').annotate(
            count=Count('id'),
            avg_duration=Avg('duration_minutes')
        ).order_by('weekday')
        
        # Most productive times
        productive_times = sessions.filter(
            productivity_rating__gte=4
        ).annotate(
            hour=F('started_at__hour')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        stats = {
            'total_sessions': total_sessions,
            'total_hours': round(total_minutes / 60, 1),
            'average_duration_minutes': round(avg_duration, 1),
            'average_productivity': round(avg_productivity, 1),
            'sessions_by_hour': list(sessions_by_hour),
            'sessions_by_weekday': list(sessions_by_weekday),
            'most_productive_hours': list(productive_times),
            'current_streak': self._calculate_study_streak(request.user),
        }
        
        return Response(stats)
    
    def _calculate_study_streak(self, user):
        """Calculate study streak for stats."""
        sessions = StudySession.objects.filter(
            user=user,
            status='completed'
        ).order_by('-started_at')
        
        if not sessions:
            return {'current': 0, 'longest': 0}
        
        current_streak = 0
        longest_streak = 0
        last_date = None
        temp_streak = 0
        
        for session in sessions:
            session_date = session.started_at.date()
            
            if last_date is None:
                temp_streak = 1
                if session_date == timezone.now().date():
                    current_streak = 1
            elif (last_date - session_date).days == 1:
                temp_streak += 1
                if session_date == timezone.now().date() or (
                    last_date == timezone.now().date() and (last_date - session_date).days == 1
                ):
                    current_streak = temp_streak
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
            
            last_date = session_date
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {'current': current_streak, 'longest': longest_streak}


class LearningProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for tracking learning progress."""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProgressEntryCreateSerializer
        return ProgressEntrySerializer
    
    def get_queryset(self):
        """Get progress entries for the authenticated user."""
        return ProgressEntry.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a new progress entry."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """Get progress timeline."""
        entries = self.get_queryset().order_by('-created_at')
        
        # Filter by study plan if specified
        study_plan_id = request.query_params.get('study_plan')
        if study_plan_id:
            entries = entries.filter(study_plan_id=study_plan_id)
        
        # Filter by goal if specified
        goal_id = request.query_params.get('goal')
        if goal_id:
            entries = entries.filter(goal_id=goal_id)
        
        # Group by date
        timeline = {}
        for entry in entries[:50]:  # Limit to recent 50 entries
            date_key = entry.created_at.date().isoformat()
            if date_key not in timeline:
                timeline[date_key] = []
            timeline[date_key].append(ProgressEntrySerializer(entry).data)
        
        return Response(timeline)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get progress summary."""
        entries = self.get_queryset()
        
        # Filter by date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        entries = entries.filter(created_at__gte=start_date)
        
        # Calculate summary statistics
        summary = {
            'total_entries': entries.count(),
            'by_type': entries.values('progress_type').annotate(
                count=Count('id')
            ).order_by('-count'),
            'goals_completed': entries.filter(
                progress_type='goal_completed'
            ).count(),
            'study_sessions': entries.filter(
                progress_type='study_session'
            ).count(),
            'milestones_reached': entries.filter(
                progress_type='milestone'
            ).count(),
        }
        
        return Response(summary)


class LearningAnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for learning analytics and insights."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get learning analytics overview."""
        user = request.user
        
        # Date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Study time analytics
        study_sessions = StudySession.objects.filter(
            user=user,
            status='completed',
            started_at__gte=start_date
        )
        
        total_study_minutes = sum(s.duration_minutes or 0 for s in study_sessions)
        total_study_hours = round(total_study_minutes / 60, 1)
        
        # Goal completion analytics
        goals = LearningGoal.objects.filter(
            study_plan__user=user
        )
        completed_goals = goals.filter(
            status='completed',
            actual_completion_date__gte=start_date
        ).count()
        
        # Progress over time
        progress_by_week = ProgressEntry.objects.filter(
            user=user,
            created_at__gte=start_date
        ).annotate(
            week=TruncWeek('created_at')
        ).values('week').annotate(
            count=Count('id'),
            goals_completed=Count('id', filter=Q(progress_type='goal_completed'))
        ).order_by('week')
        
        # Learning velocity
        learning_velocity = self._calculate_learning_velocity(user, start_date)
        
        # Productivity patterns
        productivity_patterns = self._analyze_productivity_patterns(user, start_date)
        
        analytics = {
            'total_study_hours': total_study_hours,
            'average_daily_hours': round(total_study_hours / days, 1),
            'goals_completed': completed_goals,
            'completion_rate': round(
                (completed_goals / goals.count() * 100) if goals.count() > 0 else 0,
                1
            ),
            'progress_by_week': list(progress_by_week),
            'learning_velocity': learning_velocity,
            'productivity_patterns': productivity_patterns,
            'recommendations': self._generate_analytics_recommendations(
                user, total_study_hours, completed_goals, productivity_patterns
            ),
        }
        
        return Response(analytics)
    
    @action(detail=False, methods=['get'])
    def performance_trends(self, request):
        """Get performance trends over time."""
        user = request.user
        
        # Date range
        days = int(request.query_params.get('days', 90))
        start_date = timezone.now() - timedelta(days=days)
        
        # Goal completion trends
        goal_trends = LearningGoal.objects.filter(
            study_plan__user=user,
            actual_completion_date__gte=start_date
        ).annotate(
            month=TruncMonth('actual_completion_date')
        ).values('month').annotate(
            completed=Count('id'),
            avg_time_to_complete=Avg(
                F('actual_completion_date') - F('created_at')
            )
        ).order_by('month')
        
        # Study consistency trends
        study_trends = StudySession.objects.filter(
            user=user,
            status='completed',
            started_at__gte=start_date
        ).annotate(
            week=TruncWeek('started_at')
        ).values('week').annotate(
            sessions=Count('id'),
            total_hours=Sum('duration_minutes') / 60.0,
            avg_productivity=Avg('productivity_rating')
        ).order_by('week')
        
        # Knowledge area progress
        knowledge_progress = self._analyze_knowledge_progress(user, start_date)
        
        trends = {
            'goal_completion_trends': list(goal_trends),
            'study_consistency_trends': list(study_trends),
            'knowledge_area_progress': knowledge_progress,
            'improvement_areas': self._identify_improvement_areas(user),
        }
        
        return Response(trends)
    
    @action(detail=False, methods=['get'])
    def learning_path_analysis(self, request):
        """Analyze and optimize learning paths."""
        user = request.user
        
        # Get active study plans
        active_plans = StudyPlan.objects.filter(
            user=user,
            is_active=True
        )
        
        path_analysis = []
        for plan in active_plans:
            analysis = {
                'study_plan': StudyPlanSerializer(plan).data,
                'current_progress': plan.get_progress_summary(),
                'bottlenecks': self._identify_bottlenecks(plan),
                'optimal_sequence': self._suggest_optimal_sequence(plan),
                'time_estimates': self._calculate_time_estimates(plan),
                'success_probability': self._calculate_success_probability(plan),
            }
            path_analysis.append(analysis)
        
        return Response({'learning_paths': path_analysis})
    
    def _calculate_learning_velocity(self, user, start_date):
        """Calculate how fast the user is learning."""
        goals_completed = LearningGoal.objects.filter(
            study_plan__user=user,
            status='completed',
            actual_completion_date__gte=start_date
        ).count()
        
        weeks = (timezone.now() - start_date).days / 7
        goals_per_week = goals_completed / weeks if weeks > 0 else 0
        
        # Compare with target
        active_plans = StudyPlan.objects.filter(user=user, is_active=True)
        target_goals_per_week = sum(
            plan.goals.count() / ((plan.end_date - plan.start_date).days / 7)
            for plan in active_plans
            if plan.end_date and plan.start_date
        )
        
        return {
            'current_velocity': round(goals_per_week, 2),
            'target_velocity': round(target_goals_per_week, 2),
            'velocity_ratio': round(
                goals_per_week / target_goals_per_week if target_goals_per_week > 0 else 0,
                2
            ),
            'status': 'on_track' if goals_per_week >= target_goals_per_week * 0.9 else 'behind'
        }
    
    def _analyze_productivity_patterns(self, user, start_date):
        """Analyze when the user is most productive."""
        sessions = StudySession.objects.filter(
            user=user,
            status='completed',
            started_at__gte=start_date,
            productivity_rating__isnull=False
        )
        
        # By hour of day
        by_hour = sessions.annotate(
            hour=F('started_at__hour')
        ).values('hour').annotate(
            avg_productivity=Avg('productivity_rating'),
            count=Count('id')
        ).filter(count__gte=3).order_by('-avg_productivity')
        
        # By day of week
        by_weekday = sessions.annotate(
            weekday=F('started_at__week_day')
        ).values('weekday').annotate(
            avg_productivity=Avg('productivity_rating'),
            count=Count('id')
        ).order_by('-avg_productivity')
        
        return {
            'best_hours': list(by_hour[:3]),
            'best_days': list(by_weekday[:3]),
            'peak_productivity_time': by_hour[0]['hour'] if by_hour else None,
        }
    
    def _generate_analytics_recommendations(self, user, study_hours, goals_completed, patterns):
        """Generate recommendations based on analytics."""
        recommendations = []
        
        # Study time recommendations
        if study_hours < 20:  # Less than 20 hours in period
            recommendations.append({
                'type': 'study_time',
                'priority': 'high',
                'message': 'Increase study time to meet your goals',
                'suggestion': 'Try to study at least 1 hour daily'
            })
        
        # Productivity recommendations
        if patterns.get('peak_productivity_time'):
            recommendations.append({
                'type': 'scheduling',
                'priority': 'medium',
                'message': f'Schedule important study sessions around {patterns["peak_productivity_time"]}:00',
                'suggestion': 'You are most productive at this time'
            })
        
        # Goal completion recommendations
        if goals_completed < 5:
            recommendations.append({
                'type': 'goal_setting',
                'priority': 'medium',
                'message': 'Break down large goals into smaller, achievable tasks',
                'suggestion': 'This will help maintain momentum'
            })
        
        return recommendations
    
    def _analyze_knowledge_progress(self, user, start_date):
        """Analyze progress across different knowledge areas."""
        knowledge_areas = KnowledgeArea.objects.filter(user=user)
        
        progress = []
        for area in knowledge_areas:
            area_progress = {
                'area': area.name,
                'proficiency_level': area.proficiency_level,
                'goals_in_area': area.related_goals.count(),
                'completed_goals': area.related_goals.filter(status='completed').count(),
                'recent_activity': area.last_studied.isoformat() if area.last_studied else None,
            }
            progress.append(area_progress)
        
        return progress
    
    def _identify_improvement_areas(self, user):
        """Identify areas that need improvement."""
        # Find goals with low progress
        struggling_goals = LearningGoal.objects.filter(
            study_plan__user=user,
            status='in_progress',
            progress_percentage__lt=50,
            created_at__lte=timezone.now() - timedelta(days=14)  # At least 2 weeks old
        )
        
        improvement_areas = []
        for goal in struggling_goals[:5]:
            improvement_areas.append({
                'goal': goal.title,
                'current_progress': goal.progress_percentage,
                'days_since_start': (timezone.now() - goal.created_at).days,
                'suggested_action': 'Review materials and seek help if needed'
            })
        
        return improvement_areas
    
    def _identify_bottlenecks(self, study_plan):
        """Identify bottlenecks in a study plan."""
        bottlenecks = []
        
        # Find goals that are blocking others
        goals = study_plan.goals.filter(status__in=['not_started', 'in_progress'])
        for goal in goals:
            if goal.prerequisites:
                incomplete_prereqs = [
                    p for p in goal.prerequisites
                    if LearningGoal.objects.filter(
                        id=p,
                        status__in=['not_started', 'in_progress']
                    ).exists()
                ]
                if incomplete_prereqs:
                    bottlenecks.append({
                        'goal': goal.title,
                        'blocked_by': incomplete_prereqs,
                        'impact': 'high' if goal.priority == 1 else 'medium'
                    })
        
        return bottlenecks
    
    def _suggest_optimal_sequence(self, study_plan):
        """Suggest optimal sequence for completing goals."""
        goals = study_plan.goals.filter(
            status__in=['not_started', 'in_progress']
        ).order_by('priority', 'target_date')
        
        sequence = []
        completed_ids = set()
        
        # Simple topological sort considering prerequisites
        while goals:
            for goal in goals:
                prereqs = set(goal.prerequisites or [])
                if prereqs.issubset(completed_ids):
                    sequence.append({
                        'goal_id': str(goal.id),
                        'title': goal.title,
                        'estimated_hours': goal.estimated_hours,
                        'priority': goal.priority
                    })
                    completed_ids.add(str(goal.id))
                    goals = goals.exclude(id=goal.id)
                    break
            else:
                # No more goals can be scheduled
                break
        
        return sequence
    
    def _calculate_time_estimates(self, study_plan):
        """Calculate time estimates for completing the study plan."""
        remaining_goals = study_plan.goals.filter(
            status__in=['not_started', 'in_progress']
        )
        
        total_hours = sum(g.estimated_hours for g in remaining_goals)
        
        # Get user's average study hours per week
        recent_sessions = StudySession.objects.filter(
            user=study_plan.user,
            status='completed',
            started_at__gte=timezone.now() - timedelta(days=28)
        )
        
        weekly_hours = sum(s.duration_minutes or 0 for s in recent_sessions) / 60 / 4
        
        if weekly_hours > 0:
            weeks_to_complete = total_hours / weekly_hours
            estimated_completion = timezone.now() + timedelta(weeks=weeks_to_complete)
        else:
            weeks_to_complete = None
            estimated_completion = None
        
        return {
            'total_hours_remaining': round(total_hours, 1),
            'average_weekly_hours': round(weekly_hours, 1),
            'weeks_to_complete': round(weeks_to_complete, 1) if weeks_to_complete else None,
            'estimated_completion_date': estimated_completion.date().isoformat() if estimated_completion else None,
        }
    
    def _calculate_success_probability(self, study_plan):
        """Calculate probability of successfully completing the study plan."""
        # Simple heuristic based on progress and time
        progress = study_plan.get_progress_summary()
        
        if study_plan.end_date:
            time_remaining = (study_plan.end_date - timezone.now().date()).days
            total_time = (study_plan.end_date - study_plan.start_date).days
            time_ratio = time_remaining / total_time if total_time > 0 else 0
        else:
            time_ratio = 1  # No deadline
        
        # Calculate probability based on current progress vs expected
        if time_ratio > 0:
            progress_ratio = progress['completion_percentage'] / progress['expected_completion']
            probability = min(100, progress_ratio * 100)
        else:
            probability = progress['completion_percentage']
        
        return {
            'probability': round(probability, 1),
            'confidence': 'high' if probability > 80 else 'medium' if probability > 50 else 'low',
            'factors': {
                'current_progress': progress['completion_percentage'],
                'expected_progress': progress['expected_completion'],
                'time_remaining_ratio': round(time_ratio, 2),
            }
        }