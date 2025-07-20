import logging
from datetime import datetime, timedelta, date
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F, Max, Min
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Import adaptive learning services
from .services.study_plan_generator import get_study_plan_generator
from .services.performance_analysis import get_performance_analysis_service
from .services.review_scheduling import get_review_scheduling_service
from .services.progress_prediction import get_progress_prediction_service

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
        """Generate an optimal study schedule using adaptive learning."""
        study_plan = self.get_object()
        
        # Get parameters
        plan_type = request.data.get('plan_type', 'weekly')
        target_date = request.data.get('target_date')
        preferences = request.data.get('preferences', {})
        
        # Parse target date if provided
        if target_date:
            try:
                target_date = datetime.fromisoformat(target_date).date()
            except (ValueError, TypeError):
                target_date = None
        
        # Use adaptive study plan generator
        generator = get_study_plan_generator()
        result = generator.generate_adaptive_study_plan(
            user=request.user,
            course=study_plan.course,
            plan_type=plan_type,
            target_date=target_date,
            preferences=preferences
        )
        
        if result['success']:
            # Update study plan with adaptive data
            study_plan.plan_data = result['plan_data']
            study_plan.save()
            
            return Response({
                'schedule': result['plan_data']['schedule'],
                'adaptations_made': result['plan_data']['adaptations_made'],
                'recommendations': result['recommendations'],
                'estimated_completion': result['plan_data']['estimated_completion']
            })
        else:
            return Response(
                {'error': result.get('error', 'Failed to generate adaptive schedule')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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
    
    @action(detail=True, methods=['post'])
    def adapt_plan(self, request, pk=None):
        """Adapt existing study plan based on recent performance."""
        study_plan = self.get_object()
        performance_update = request.data.get('performance_update', {})
        
        # Use adaptive study plan generator to adapt plan
        generator = get_study_plan_generator()
        result = generator.adapt_existing_plan(study_plan, performance_update)
        
        if result['success']:
            # Update study plan with new adaptations
            study_plan.plan_data = result['updated_plan_data']
            study_plan.save()
            
            return Response({
                'adaptations_made': result['adaptations_made'],
                'recommendations': result['recommendations'],
                'updated_schedule': result['updated_plan_data']['schedule']
            })
        else:
            return Response(
                {'error': result.get('error', 'Failed to adapt plan')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def performance_analysis(self, request, pk=None):
        """Get comprehensive performance analysis for the study plan."""
        study_plan = self.get_object()
        time_period = int(request.query_params.get('days', 30))
        
        # Use performance analysis service
        performance_service = get_performance_analysis_service()
        analysis = performance_service.analyze_comprehensive_performance(
            user=request.user,
            course=study_plan.course,
            time_period_days=time_period
        )
        
        return Response(analysis)
    
    @action(detail=True, methods=['get'])
    def progress_prediction(self, request, pk=None):
        """Get progress prediction for course completion."""
        study_plan = self.get_object()
        target_mastery_level = int(request.query_params.get('mastery_level', 4))
        
        # Use progress prediction service
        prediction_service = get_progress_prediction_service()
        prediction = prediction_service.predict_course_completion(
            user=request.user,
            course=study_plan.course,
            target_mastery_level=target_mastery_level
        )
        
        return Response(prediction)
    
    @action(detail=True, methods=['get'])
    def review_schedule(self, request, pk=None):
        """Get intelligent review schedule for the course."""
        study_plan = self.get_object()
        target_retention = float(request.query_params.get('target_retention', 0.85))
        
        # Use review scheduling service
        review_service = get_review_scheduling_service()
        schedule = review_service.schedule_intelligent_reviews(
            user=request.user,
            course=study_plan.course,
            target_retention=target_retention
        )
        
        return Response(schedule)
    
    @action(detail=False, methods=['post'])
    def real_time_update(self, request):
        """Process real-time performance update and provide feedback."""
        recent_activity = request.data
        
        # Use performance analysis service for real-time feedback
        performance_service = get_performance_analysis_service()
        feedback = performance_service.get_real_time_performance_update(
            user=request.user,
            recent_activity=recent_activity
        )
        
        return Response(feedback)
    
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
            actual_start__gte=timezone.now() - timedelta(days=7),
            status='completed'
        )
        total_recent_hours = sum(
            (s.actual_end - s.actual_start).total_seconds() / 3600 
            for s in recent_sessions 
            if s.actual_end and s.actual_start
        )
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
            session_date = (session.actual_start or session.scheduled_start).date()
            
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
            session_date = (session.actual_start or session.scheduled_start).date()
            
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
    
    @action(detail=True, methods=['post'])
    def update_review_schedule(self, request, pk=None):
        """Update review schedule based on session performance."""
        session = self.get_object()
        
        if session.status != 'completed':
            return Response(
                {'error': 'Can only update review schedule for completed sessions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract performance data from session
        performance_data = {
            'correct': request.data.get('performance_rating', 3) >= 3,
            'response_time': session.duration_minutes * 60 / max(1, len(session.topics_covered)),
            'difficulty': 'medium',  # Default
            'confidence': request.data.get('confidence_rating', 3)
        }
        
        # Update review schedule for each topic covered
        review_service = get_review_scheduling_service()
        results = []
        
        for topic in session.topics_covered:
            result = review_service.update_review_schedule_realtime(
                user=request.user,
                item_id=topic,
                item_type='topic',
                performance=performance_data
            )
            results.append(result)
        
        return Response({'review_updates': results})


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
    
    @action(detail=False, methods=['get'])
    def adaptive_performance_analysis(self, request):
        """Get adaptive performance analysis with personalized insights."""
        time_period = int(request.query_params.get('days', 30))
        course_id = request.query_params.get('course_id')
        
        # Get course if specified
        course = None
        if course_id:
            try:
                from courses.models import Course
                course = Course.objects.get(id=course_id, user=request.user)
            except Course.DoesNotExist:
                return Response(
                    {'error': 'Course not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Use adaptive performance analysis service
        performance_service = get_performance_analysis_service()
        analysis = performance_service.analyze_comprehensive_performance(
            user=request.user,
            course=course,
            time_period_days=time_period
        )
        
        return Response(analysis)
    
    @action(detail=False, methods=['get'])
    def performance_trajectory(self, request):
        """Get predicted performance trajectory."""
        prediction_days = int(request.query_params.get('prediction_days', 30))
        course_id = request.query_params.get('course_id')
        
        # Get course if specified
        course = None
        if course_id:
            try:
                from courses.models import Course
                course = Course.objects.get(id=course_id, user=request.user)
            except Course.DoesNotExist:
                return Response(
                    {'error': 'Course not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Use performance analysis service
        performance_service = get_performance_analysis_service()
        trajectory = performance_service.predict_performance_trajectory(
            user=request.user,
            course=course,
            prediction_days=prediction_days
        )
        
        return Response(trajectory)
    
    @action(detail=False, methods=['get'])
    def completion_predictions(self, request):
        """Get completion predictions for all active courses."""
        # Get active study plans
        active_plans = StudyPlan.objects.filter(
            user=request.user,
            is_active=True
        )
        
        prediction_service = get_progress_prediction_service()
        predictions = []
        
        for plan in active_plans:
            prediction = prediction_service.predict_course_completion(
                user=request.user,
                course=plan.course
            )
            
            if prediction['success']:
                predictions.append({
                    'course_id': str(plan.course.id),
                    'course_name': plan.course.name,
                    'study_plan_id': str(plan.id),
                    'prediction': prediction
                })
        
        return Response({'course_predictions': predictions})
    
    @action(detail=False, methods=['get'])
    def optimal_schedules(self, request):
        """Get optimal schedule recommendations for all courses."""
        target_date_str = request.query_params.get('target_date')
        weekly_hours = float(request.query_params.get('weekly_hours', 20))
        
        # Parse target date
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.fromisoformat(target_date_str).date()
            except (ValueError, TypeError):
                pass
        
        # Get active study plans
        active_plans = StudyPlan.objects.filter(
            user=request.user,
            is_active=True
        )
        
        prediction_service = get_progress_prediction_service()
        schedules = []
        
        for plan in active_plans:
            if target_date:
                schedule = prediction_service.predict_optimal_study_schedule(
                    user=request.user,
                    course=plan.course,
                    target_completion_date=target_date,
                    weekly_hours_available=weekly_hours
                )
                
                if schedule['success']:
                    schedules.append({
                        'course_id': str(plan.course.id),
                        'course_name': plan.course.name,
                        'study_plan_id': str(plan.id),
                        'optimal_schedule': schedule
                    })
        
        return Response({'optimal_schedules': schedules})
    
    @action(detail=False, methods=['get'])
    def review_load_optimization(self, request):
        """Get review load optimization for all courses."""
        target_daily_reviews = int(request.query_params.get('target_daily_reviews', 50))
        max_daily_reviews = int(request.query_params.get('max_daily_reviews', 100))
        
        # Use review scheduling service
        review_service = get_review_scheduling_service()
        optimization = review_service.optimize_daily_review_load(
            user=request.user,
            target_daily_reviews=target_daily_reviews,
            max_daily_reviews=max_daily_reviews
        )
        
        return Response(optimization)
    
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


class AdaptiveLearningViewSet(viewsets.ViewSet):
    """ViewSet for adaptive learning features and AI-powered recommendations."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate_adaptive_plan(self, request):
        """Generate a completely new adaptive study plan."""
        course_id = request.data.get('course_id')
        plan_type = request.data.get('plan_type', 'weekly')
        target_date = request.data.get('target_date')
        preferences = request.data.get('preferences', {})
        
        # Validate course_id
        if not course_id:
            return Response(
                {'error': 'course_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get course
        try:
            from courses.models import Course
            course = Course.objects.get(id=course_id, user=request.user)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parse target date
        if target_date:
            try:
                target_date = datetime.fromisoformat(target_date).date()
            except (ValueError, TypeError):
                target_date = None
        
        # Generate adaptive study plan
        generator = get_study_plan_generator()
        result = generator.generate_adaptive_study_plan(
            user=request.user,
            course=course,
            plan_type=plan_type,
            target_date=target_date,
            preferences=preferences
        )
        
        if result['success']:
            # Create new study plan with adaptive data
            study_plan = StudyPlan.objects.create(
                user=request.user,
                course=course,
                title=f"Adaptive {plan_type.title()} Plan for {course.name}",
                description="AI-generated adaptive study plan",
                plan_type=plan_type,
                plan_data=result['plan_data'],
                start_date=timezone.now().date(),
                end_date=target_date or (timezone.now() + timedelta(days=30)).date(),
                daily_study_hours=preferences.get('daily_hours', 2.0),
                study_days_per_week=5 if not preferences.get('include_weekends', True) else 7,
                status='active'
            )
            
            # Deactivate other plans for the same course
            StudyPlan.objects.filter(
                user=request.user,
                course=course,
                status='active'
            ).exclude(id=study_plan.id).update(status='paused')
            
            return Response({
                'study_plan_id': str(study_plan.id),
                'plan_data': result['plan_data'],
                'recommendations': result['recommendations']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': result.get('error', 'Failed to generate adaptive plan')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def process_study_session(self, request):
        """Process completed study session and adapt learning."""
        session_data = request.data
        course_id = session_data.get('course_id')
        
        # Get course
        try:
            from courses.models import Course
            course = Course.objects.get(id=course_id, user=request.user)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process real-time performance update
        performance_service = get_performance_analysis_service()
        feedback = performance_service.get_real_time_performance_update(
            user=request.user,
            recent_activity={
                'type': 'study_session',
                'duration_minutes': session_data.get('duration_minutes', 0),
                'productivity_rating': session_data.get('productivity_rating', 3),
                'completed': session_data.get('completed', True),
                'topics_covered': session_data.get('topics_covered', [])
            }
        )
        
        # Update review schedules for covered topics
        review_service = get_review_scheduling_service()
        review_updates = []
        
        for topic in session_data.get('topics_covered', []):
            performance_data = {
                'correct': session_data.get('understanding_score', 70) >= 70,
                'response_time': session_data.get('duration_minutes', 30) * 60 / max(1, len(session_data.get('topics_covered', [topic]))),
                'difficulty': 'medium',
                'mastery_level': session_data.get('mastery_level', 3)
            }
            
            update_result = review_service.update_review_schedule_realtime(
                user=request.user,
                item_id=topic,
                item_type='topic',
                performance=performance_data
            )
            review_updates.append(update_result)
        
        # Check if study plan needs adaptation
        active_plan = StudyPlan.objects.filter(
            user=request.user,
            course=course,
            is_active=True
        ).first()
        
        adaptation_result = None
        if active_plan:
            generator = get_study_plan_generator()
            adaptation_result = generator.adapt_existing_plan(
                active_plan,
                performance_update=feedback
            )
            
            if adaptation_result.get('success') and adaptation_result.get('adaptations_made'):
                active_plan.plan_data = adaptation_result['updated_plan_data']
                active_plan.save()
        
        return Response({
            'performance_feedback': feedback,
            'review_updates': review_updates,
            'plan_adaptation': adaptation_result,
            'recommendations': adaptation_result.get('recommendations', []) if adaptation_result else []
        })
    
    @action(detail=False, methods=['get'])
    def learning_insights(self, request):
        """Get comprehensive learning insights and recommendations."""
        course_id = request.query_params.get('course_id')
        time_period = int(request.query_params.get('days', 30))
        
        # Get course if specified
        course = None
        if course_id:
            try:
                from courses.models import Course
                course = Course.objects.get(id=course_id, user=request.user)
            except Course.DoesNotExist:
                return Response(
                    {'error': 'Course not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get comprehensive performance analysis
        performance_service = get_performance_analysis_service()
        performance_analysis = performance_service.analyze_comprehensive_performance(
            user=request.user,
            course=course,
            time_period_days=time_period
        )
        
        # Get performance trajectory
        trajectory = performance_service.predict_performance_trajectory(
            user=request.user,
            course=course,
            prediction_days=30
        )
        
        # Get review schedule optimization
        review_service = get_review_scheduling_service()
        review_optimization = review_service.optimize_daily_review_load(
            user=request.user,
            target_daily_reviews=50,
            max_daily_reviews=100
        )
        
        # Get progress predictions
        predictions = []
        if course:
            prediction_service = get_progress_prediction_service()
            prediction = prediction_service.predict_course_completion(
                user=request.user,
                course=course
            )
            if prediction.get('success'):
                predictions.append(prediction)
        
        return Response({
            'performance_analysis': performance_analysis,
            'performance_trajectory': trajectory,
            'review_optimization': review_optimization,
            'completion_predictions': predictions,
            'learning_summary': {
                'overall_score': performance_analysis.get('overall_score', 0),
                'performance_category': performance_analysis.get('performance_category', 'unknown'),
                'main_strengths': performance_analysis.get('strengths_weaknesses', {}).get('strengths', []),
                'improvement_areas': performance_analysis.get('strengths_weaknesses', {}).get('weaknesses', []),
                'key_recommendations': performance_analysis.get('recommendations', [])[:3]
            }
        })
    
    @action(detail=False, methods=['post'])
    def manual_override(self, request):
        """Allow manual override of adaptive recommendations."""
        study_plan_id = request.data.get('study_plan_id')
        override_type = request.data.get('override_type')  # 'schedule', 'difficulty', 'review_frequency'
        override_data = request.data.get('override_data', {})
        reason = request.data.get('reason', '')
        
        # Validate required fields
        if not study_plan_id:
            return Response(
                {'error': 'study_plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not override_type:
            return Response(
                {'error': 'override_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_override_types = ['schedule', 'difficulty', 'review_frequency']
        if override_type not in valid_override_types:
            return Response(
                {'error': f'Invalid override_type. Must be one of: {", ".join(valid_override_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get study plan
        try:
            study_plan = StudyPlan.objects.get(
                id=study_plan_id,
                user=request.user
            )
        except StudyPlan.DoesNotExist:
            return Response(
                {'error': 'Study plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Apply manual override
        current_plan_data = study_plan.plan_data or {}
        
        if override_type == 'schedule':
            # Allow manual schedule modifications
            schedule = current_plan_data.get('schedule', [])
            session_id = override_data.get('session_id')
            new_date = override_data.get('new_date')
            new_time = override_data.get('new_time')
            
            for session in schedule:
                if session.get('session_id') == session_id:
                    if new_date:
                        session['date'] = new_date
                    if new_time:
                        session['start_time'] = new_time
                    session['manually_modified'] = True
                    break
            
            current_plan_data['schedule'] = schedule
        
        elif override_type == 'difficulty':
            # Allow difficulty adjustments
            difficulty_adjustment = override_data.get('adjustment', 0)  # -1, 0, 1
            current_plan_data['difficulty_override'] = difficulty_adjustment
        
        elif override_type == 'review_frequency':
            # Allow review frequency changes
            frequency_days = override_data.get('frequency_days', 3)
            current_plan_data['review_frequency_override'] = frequency_days
        
        # Add override tracking
        overrides = current_plan_data.get('manual_overrides', [])
        overrides.append({
            'timestamp': timezone.now().isoformat(),
            'type': override_type,
            'data': override_data,
            'user_reason': request.data.get('reason', '')
        })
        current_plan_data['manual_overrides'] = overrides
        
        # Save updated plan
        study_plan.plan_data = current_plan_data
        study_plan.save()
        
        return Response({
            'success': True,
            'message': f'Manual override applied for {override_type}',
            'override_applied': {
                'type': override_type,
                'reason': reason,
                'timestamp': timezone.now().isoformat()
            },
            'updated_plan': current_plan_data
        })
    
    @action(detail=False, methods=['get'])
    def adaptive_dashboard(self, request):
        """Get adaptive learning dashboard with all key metrics."""
        # Get performance analysis for all courses
        performance_service = get_performance_analysis_service()
        overall_analysis = performance_service.analyze_comprehensive_performance(
            user=request.user,
            course=None,  # All courses
            time_period_days=30
        )
        
        # Get active study plans with predictions
        active_plans = StudyPlan.objects.filter(
            user=request.user,
            status='active'
        )
        
        prediction_service = get_progress_prediction_service()
        plan_predictions = []
        
        for plan in active_plans:
            prediction = prediction_service.predict_course_completion(
                user=request.user,
                course=plan.course
            )
            
            if prediction.get('success'):
                plan_predictions.append({
                    'study_plan_id': str(plan.id),
                    'course_name': plan.course.name,
                    'prediction': prediction
                })
        
        # Get review schedule summary
        review_service = get_review_scheduling_service()
        review_summary = review_service.optimize_daily_review_load(
            user=request.user,
            target_daily_reviews=50,
            max_daily_reviews=100
        )
        
        # Calculate adaptive insights
        dashboard_data = {
            'overall_performance': {
                'score': overall_analysis.get('overall_score', 0),
                'category': overall_analysis.get('performance_category', 'unknown'),
                'trend': overall_analysis.get('trends', {}).get('overall_trend', 'stable')
            },
            'active_plans': len(active_plans),
            'completion_predictions': plan_predictions,
            'review_workload': {
                'today': review_summary.get('load_metrics', {}).get('average_daily_reviews', 0),
                'this_week': review_summary.get('load_metrics', {}).get('peak_load_day', 0),
                'optimization_needed': len(review_summary.get('recommendations', []))
            },
            'key_strengths': overall_analysis.get('strengths_weaknesses', {}).get('strengths', [])[:3],
            'improvement_areas': overall_analysis.get('strengths_weaknesses', {}).get('weaknesses', [])[:3],
            'priority_recommendations': overall_analysis.get('recommendations', [])[:5],
            'adaptation_status': {
                'plans_adapted_this_week': StudyPlan.objects.filter(
                    user=request.user,
                    updated_at__gte=timezone.now() - timedelta(days=7)
                ).count(),
                'manual_overrides_this_week': sum(
                    len(plan.plan_data.get('manual_overrides', [])) 
                    for plan in active_plans 
                    if plan.plan_data
                )
            }
        }
        
        return Response(dashboard_data)