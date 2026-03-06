"""
Analytics Views
===============
API views for dashboards, campaign analytics, simulation analytics,
risk trends, training effectiveness, and data exports.
"""

import csv
import io
from datetime import timedelta
from collections import defaultdict

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Sum, Min, Max, Q, F
from django.db.models.functions import TruncDate, Coalesce
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import get_user_model

from .serializers import (
    DashboardOverviewSerializer,
    DashboardTrendsSerializer,
    CampaignPerformanceSerializer,
    CampaignAnalyticsDetailSerializer,
    CampaignListAnalyticsSerializer,
    SimulationPerformanceSerializer,
    SimulationAnalyticsDetailSerializer,
    SimulationListAnalyticsSerializer,
    TemplateComparisonSerializer,
    RiskDistributionSerializer,
    RiskTrendSerializer,
    HighRiskEmployeeSerializer,
    RiskAnalyticsSummarySerializer,
    TrainingModuleStatsSerializer,
    TrainingEffectivenessSerializer,
    TrainingAnalyticsSummarySerializer,
    PendingTrainingSerializer,
    ExportRequestSerializer,
)
from apps.core.permissions import IsSuperAdminOrCompanyAdmin

User = get_user_model()


def get_date_range(request):
    """Extract date range from query params."""
    period = request.query_params.get('period', '30d')
    end_date = timezone.now().date()

    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    elif period == '90d':
        start_date = end_date - timedelta(days=90)
    elif period == 'custom':
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        if start_str and end_str:
            from datetime import datetime
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)

    return start_date, end_date, period


def get_company_filter(user):
    """Get company filter based on user role."""
    if user.is_super_admin:
        return {}
    return {'company': user.company}


class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard analytics endpoints.

    Provides overview statistics and trend data for the admin dashboard.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get dashboard overview statistics.

        Query params:
        - company: Company ID (super admin only)
        """
        user = request.user
        company_filter = get_company_filter(user)

        # Super admin can filter by specific company
        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        # User metrics
        users = User.objects.filter(**{k.replace('company', 'company'): v for k, v in company_filter.items()})
        if company_filter:
            users = User.objects.filter(company_id=company_filter.get('company_id') or company_filter.get('company'))
        else:
            users = User.objects.all()

        total_users = users.count()
        total_employees = users.filter(role='EMPLOYEE').count()
        total_admins = users.filter(role__in=['SUPER_ADMIN', 'COMPANY_ADMIN']).count()

        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users_30_days = users.filter(last_login__gte=thirty_days_ago).count()

        # Campaign metrics
        try:
            from apps.campaigns.models import Campaign, QuizResult
            campaigns = Campaign.objects.filter(**company_filter)
            total_campaigns = campaigns.count()
            active_campaigns = campaigns.filter(status='ACTIVE').count()
            completed_campaigns = campaigns.filter(status='COMPLETED').count()

            results = QuizResult.objects.filter(
                campaign__in=campaigns
            )
            avg_quiz_score = results.aggregate(avg=Avg('score'))['avg']

            total_assigned = campaigns.aggregate(total=Sum('total_participants'))['total'] or 0
            total_completed = campaigns.aggregate(total=Sum('completed_participants'))['total'] or 0
            campaign_completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else None
        except Exception:
            total_campaigns = active_campaigns = completed_campaigns = 0
            avg_quiz_score = campaign_completion_rate = None

        # Simulation metrics
        try:
            from apps.simulations.models import SimulationCampaign
            simulations = SimulationCampaign.objects.filter(**company_filter)
            total_simulations = simulations.count()
            active_simulations = simulations.filter(status='IN_PROGRESS').count()
            completed_simulations = simulations.filter(status='COMPLETED').count()

            sim_stats = simulations.aggregate(
                total_sent=Sum('total_sent'),
                total_clicked=Sum('total_clicked'),
                total_reported=Sum('total_reported')
            )
            total_sent = sim_stats['total_sent'] or 0
            overall_click_rate = (sim_stats['total_clicked'] / total_sent * 100) if total_sent > 0 else None
            overall_report_rate = (sim_stats['total_reported'] / total_sent * 100) if total_sent > 0 else None
        except Exception:
            total_simulations = active_simulations = completed_simulations = 0
            overall_click_rate = overall_report_rate = None

        # Risk metrics
        try:
            from apps.training.models import RiskScore
            risk_filter = {k.replace('company', 'company'): v for k, v in company_filter.items()}
            risk_scores = RiskScore.objects.filter(**risk_filter)
            avg_risk = risk_scores.aggregate(avg=Avg('score'))['avg']
            low_risk = risk_scores.filter(risk_level='LOW').count()
            medium_risk = risk_scores.filter(risk_level='MEDIUM').count()
            high_risk = risk_scores.filter(risk_level='HIGH').count()
            critical_risk = risk_scores.filter(risk_level='CRITICAL').count()
        except Exception:
            avg_risk = None
            low_risk = medium_risk = high_risk = critical_risk = 0

        # Training metrics
        try:
            from apps.training.models import RemediationTraining
            trainings = RemediationTraining.objects.filter(**company_filter)
            total_trainings = trainings.count()
            completed_trainings = trainings.filter(status__in=['COMPLETED', 'PASSED']).count()
            passed_trainings = trainings.filter(status='PASSED').count()
            training_completion_rate = (completed_trainings / total_trainings * 100) if total_trainings > 0 else None
            training_pass_rate = (passed_trainings / completed_trainings * 100) if completed_trainings > 0 else None
        except Exception:
            total_trainings = completed_trainings = passed_trainings = 0
            training_completion_rate = training_pass_rate = None

        # Gamification metrics
        try:
            from apps.gamification.models import EmployeeBadge, PointsTransaction
            badges_awarded = EmployeeBadge.objects.filter(**company_filter).count()
            points_dist = PointsTransaction.objects.filter(
                **company_filter,
                transaction_type='AWARD'
            ).aggregate(total=Sum('points'))['total'] or 0
        except Exception:
            badges_awarded = 0
            points_dist = 0

        data = {
            'total_users': total_users,
            'total_employees': total_employees,
            'total_admins': total_admins,
            'active_users_30_days': active_users_30_days,
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'completed_campaigns': completed_campaigns,
            'campaign_completion_rate': round(campaign_completion_rate, 2) if campaign_completion_rate else None,
            'average_quiz_score': round(avg_quiz_score, 2) if avg_quiz_score else None,
            'total_simulations': total_simulations,
            'active_simulations': active_simulations,
            'completed_simulations': completed_simulations,
            'overall_click_rate': round(overall_click_rate, 2) if overall_click_rate else None,
            'overall_report_rate': round(overall_report_rate, 2) if overall_report_rate else None,
            'average_risk_score': round(avg_risk, 2) if avg_risk else None,
            'low_risk_count': low_risk,
            'medium_risk_count': medium_risk,
            'high_risk_count': high_risk,
            'critical_risk_count': critical_risk,
            'total_trainings_assigned': total_trainings,
            'trainings_completed': completed_trainings,
            'trainings_passed': passed_trainings,
            'training_completion_rate': round(training_completion_rate, 2) if training_completion_rate else None,
            'training_pass_rate': round(training_pass_rate, 2) if training_pass_rate else None,
            'total_badges_awarded': badges_awarded,
            'total_points_distributed': points_dist,
        }

        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Get trend data for dashboard charts.

        Query params:
        - period: 7d, 30d, 90d, custom
        - start_date: YYYY-MM-DD (for custom)
        - end_date: YYYY-MM-DD (for custom)
        - company: Company ID (super admin only)
        """
        user = request.user
        start_date, end_date, period = get_date_range(request)
        company_filter = get_company_filter(user)

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        # Initialize trend data
        quiz_scores = []
        quiz_completions = []
        sim_click_rates = []
        sim_report_rates = []
        avg_risk_scores = []
        high_risk_counts = []
        training_completions = []

        # Quiz trends
        try:
            from apps.campaigns.models import QuizResult
            results = QuizResult.objects.filter(
                campaign__company_id=company_filter.get('company_id') or company_filter.get('company'),
                completed_at__date__gte=start_date,
                completed_at__date__lte=end_date
            ).annotate(
                date=TruncDate('completed_at')
            ).values('date').annotate(
                avg_score=Avg('score'),
                count=Count('id')
            ).order_by('date')

            for r in results:
                quiz_scores.append({'date': r['date'], 'value': float(r['avg_score'] or 0), 'count': r['count']})
                quiz_completions.append({'date': r['date'], 'value': r['count'], 'count': r['count']})
        except Exception:
            pass

        # Simulation trends
        try:
            from apps.simulations.models import TrackingEvent
            events = TrackingEvent.objects.filter(
                campaign__company_id=company_filter.get('company_id') or company_filter.get('company'),
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                clicks=Count('id', filter=Q(event_type='LINK_CLICKED')),
                reports=Count('id', filter=Q(event_type='EMAIL_REPORTED')),
                total=Count('id')
            ).order_by('date')

            for e in events:
                if e['total'] > 0:
                    sim_click_rates.append({
                        'date': e['date'],
                        'value': e['clicks'] / e['total'] * 100 if e['total'] > 0 else 0,
                        'count': e['clicks']
                    })
                    sim_report_rates.append({
                        'date': e['date'],
                        'value': e['reports'] / e['total'] * 100 if e['total'] > 0 else 0,
                        'count': e['reports']
                    })
        except Exception:
            pass

        # Risk score trends
        try:
            from apps.training.models import RiskScoreHistory
            history = RiskScoreHistory.objects.filter(
                risk_score__company_id=company_filter.get('company_id') or company_filter.get('company'),
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                avg_score=Avg('new_score'),
                high_risk=Count('id', filter=Q(new_score__gte=70))
            ).order_by('date')

            for h in history:
                avg_risk_scores.append({'date': h['date'], 'value': float(h['avg_score'] or 0)})
                high_risk_counts.append({'date': h['date'], 'value': h['high_risk']})
        except Exception:
            pass

        # Training trends
        try:
            from apps.training.models import RemediationTraining
            trainings = RemediationTraining.objects.filter(
                company_id=company_filter.get('company_id') or company_filter.get('company'),
                completed_at__date__gte=start_date,
                completed_at__date__lte=end_date,
                status__in=['COMPLETED', 'PASSED']
            ).annotate(
                date=TruncDate('completed_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            for t in trainings:
                training_completions.append({'date': t['date'], 'value': t['count'], 'count': t['count']})
        except Exception:
            pass

        data = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'quiz_scores': quiz_scores,
            'quiz_completions': quiz_completions,
            'simulation_click_rates': sim_click_rates,
            'simulation_report_rates': sim_report_rates,
            'average_risk_scores': avg_risk_scores,
            'high_risk_counts': high_risk_counts,
            'training_completions': training_completions,
        }

        serializer = DashboardTrendsSerializer(data)
        return Response(serializer.data)


class CampaignAnalyticsViewSet(viewsets.ViewSet):
    """
    Campaign analytics endpoints.

    Provides detailed analytics for quiz campaigns.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    def list(self, request):
        """
        List all campaigns with analytics.

        Query params:
        - status: Filter by status
        - company: Company ID (super admin only)
        - period: 7d, 30d, 90d, all
        """
        user = request.user
        company_filter = get_company_filter(user)

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        try:
            from apps.campaigns.models import Campaign, QuizResult

            campaigns = Campaign.objects.filter(**company_filter)

            status_filter = request.query_params.get('status')
            if status_filter:
                campaigns = campaigns.filter(status=status_filter)

            campaigns = campaigns.annotate(
                avg_score=Avg('results__score'),
                min_score=Min('results__score'),
                max_score=Max('results__score'),
                avg_time=Avg('results__time_taken_seconds'),
                avg_detection=Avg('results__phishing_emails_identified'),
            ).order_by('-created_at')

            campaign_list = []
            for c in campaigns[:50]:  # Limit to 50
                total_assigned = c.total_participants
                total_completed = c.completed_participants
                completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else None

                campaign_list.append({
                    'campaign_id': c.id,
                    'campaign_name': c.name,
                    'status': c.status,
                    'start_date': c.start_date,
                    'end_date': c.end_date,
                    'total_assigned': total_assigned,
                    'total_started': c.quizzes.filter(status='IN_PROGRESS').count() + total_completed,
                    'total_completed': total_completed,
                    'completion_rate': round(completion_rate, 2) if completion_rate else None,
                    'average_score': round(float(c.avg_score), 2) if c.avg_score else None,
                    'median_score': None,  # Would require more complex query
                    'min_score': round(float(c.min_score), 2) if c.min_score else None,
                    'max_score': round(float(c.max_score), 2) if c.max_score else None,
                    'average_phishing_detection_rate': None,
                    'average_false_positive_rate': None,
                    'average_time_seconds': round(float(c.avg_time), 2) if c.avg_time else None,
                })

            data = {
                'campaigns': campaign_list,
                'total_count': campaigns.count(),
            }

            serializer = CampaignListAnalyticsSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def retrieve(self, request, pk=None):
        """Get detailed analytics for a specific campaign."""
        user = request.user

        try:
            from apps.campaigns.models import Campaign, QuizResult, Quiz
            from apps.assessments.models import QuizQuestion, EmailTemplate

            campaign = Campaign.objects.get(pk=pk)

            # Check access
            if not user.is_super_admin and user.company != campaign.company:
                return Response({'error': 'Access denied'}, status=403)

            # Overview
            results = QuizResult.objects.filter(campaign=campaign)
            result_stats = results.aggregate(
                avg_score=Avg('score'),
                min_score=Min('score'),
                max_score=Max('score'),
                avg_time=Avg('time_taken_seconds'),
                avg_detection=Avg('phishing_emails_identified'),
                avg_fp=Avg('false_positives'),
            )

            total_assigned = campaign.total_participants
            total_completed = campaign.completed_participants

            overview = {
                'campaign_id': campaign.id,
                'campaign_name': campaign.name,
                'status': campaign.status,
                'start_date': campaign.start_date,
                'end_date': campaign.end_date,
                'total_assigned': total_assigned,
                'total_started': Quiz.objects.filter(campaign=campaign).exclude(status='NOT_STARTED').count(),
                'total_completed': total_completed,
                'completion_rate': round(total_completed / total_assigned * 100, 2) if total_assigned > 0 else None,
                'average_score': round(float(result_stats['avg_score']), 2) if result_stats['avg_score'] else None,
                'median_score': None,
                'min_score': round(float(result_stats['min_score']), 2) if result_stats['min_score'] else None,
                'max_score': round(float(result_stats['max_score']), 2) if result_stats['max_score'] else None,
                'average_phishing_detection_rate': None,
                'average_false_positive_rate': round(float(result_stats['avg_fp']), 2) if result_stats['avg_fp'] else None,
                'average_time_seconds': round(float(result_stats['avg_time']), 2) if result_stats['avg_time'] else None,
            }

            # Question analytics
            question_analytics = []
            try:
                questions = QuizQuestion.objects.filter(
                    quiz__campaign=campaign
                ).select_related('email_template').values(
                    'email_template__id',
                    'email_template__subject',
                    'email_template__email_type',
                    'email_template__category',
                    'email_template__difficulty'
                ).annotate(
                    times_shown=Count('id'),
                    correct=Count('id', filter=Q(is_correct=True)),
                    incorrect=Count('id', filter=Q(is_correct=False)),
                    avg_time=Avg('time_spent_seconds')
                )

                for q in questions:
                    times_shown = q['times_shown']
                    question_analytics.append({
                        'question_id': q['email_template__id'],
                        'email_subject': q['email_template__subject'] or 'N/A',
                        'email_type': q['email_template__email_type'] or 'N/A',
                        'category': q['email_template__category'] or 'N/A',
                        'difficulty': q['email_template__difficulty'] or 'N/A',
                        'times_shown': times_shown,
                        'correct_answers': q['correct'],
                        'incorrect_answers': q['incorrect'],
                        'accuracy_rate': round(q['correct'] / times_shown * 100, 2) if times_shown > 0 else None,
                        'average_time_seconds': round(float(q['avg_time']), 2) if q['avg_time'] else None,
                    })
            except Exception:
                pass

            # Employee performance
            employee_performance = []
            for result in results.select_related('employee').order_by('-score')[:100]:
                employee_performance.append({
                    'employee_id': result.employee.id,
                    'employee_email': result.employee.email,
                    'employee_name': result.employee.get_full_name(),
                    'quiz_status': 'COMPLETED',
                    'score': float(result.score) if result.score else None,
                    'correct_answers': result.correct_answers,
                    'total_questions': result.total_questions,
                    'phishing_detected': result.phishing_emails_identified,
                    'phishing_missed': result.phishing_emails_missed,
                    'false_positives': result.false_positives,
                    'time_taken_seconds': result.time_taken_seconds,
                    'completed_at': result.completed_at,
                    'risk_level': result.risk_level,
                })

            # Score distribution
            score_distribution = {
                '0-20': results.filter(score__lt=20).count(),
                '21-40': results.filter(score__gte=20, score__lt=40).count(),
                '41-60': results.filter(score__gte=40, score__lt=60).count(),
                '61-80': results.filter(score__gte=60, score__lt=80).count(),
                '81-100': results.filter(score__gte=80).count(),
            }

            data = {
                'overview': overview,
                'question_analytics': question_analytics,
                'employee_performance': employee_performance,
                'score_distribution': score_distribution,
            }

            serializer = CampaignAnalyticsDetailSerializer(data)
            return Response(serializer.data)

        except Campaign.DoesNotExist:
            return Response({'error': 'Campaign not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class SimulationAnalyticsViewSet(viewsets.ViewSet):
    """
    Simulation analytics endpoints.

    Provides detailed analytics for phishing simulations.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    def list(self, request):
        """List all simulations with analytics."""
        user = request.user
        company_filter = get_company_filter(user)

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        try:
            from apps.simulations.models import SimulationCampaign, SimulationTemplate

            simulations = SimulationCampaign.objects.filter(
                **company_filter
            ).select_related('template').order_by('-created_at')

            status_filter = request.query_params.get('status')
            if status_filter:
                simulations = simulations.filter(status=status_filter)

            simulation_list = []
            for s in simulations[:50]:
                total_sent = s.total_sent or 0
                simulation_list.append({
                    'simulation_id': s.id,
                    'simulation_name': s.name,
                    'template_name': s.template.name,
                    'attack_vector': s.template.attack_vector,
                    'difficulty': s.template.difficulty,
                    'status': s.status,
                    'sent_at': s.sent_at,
                    'total_sent': total_sent,
                    'total_delivered': s.total_delivered,
                    'delivery_rate': round(s.total_delivered / total_sent * 100, 2) if total_sent > 0 else None,
                    'total_opened': s.total_opened,
                    'open_rate': round(s.total_opened / total_sent * 100, 2) if total_sent > 0 else None,
                    'total_clicked': s.total_clicked,
                    'click_rate': round(s.total_clicked / total_sent * 100, 2) if total_sent > 0 else None,
                    'total_credentials': s.total_credentials_entered,
                    'credential_rate': round(s.total_credentials_entered / total_sent * 100, 2) if total_sent > 0 else None,
                    'total_reported': s.total_reported,
                    'report_rate': round(s.total_reported / total_sent * 100, 2) if total_sent > 0 else None,
                    'compromise_rate': round(max(s.total_clicked, s.total_credentials_entered) / total_sent * 100, 2) if total_sent > 0 else None,
                })

            # Template comparison
            templates = SimulationTemplate.objects.filter(
                Q(company__isnull=True) | Q(**company_filter)
            ).annotate(
                total_campaigns=Count('campaigns'),
                total_sent=Sum('campaigns__total_sent'),
                total_clicked=Sum('campaigns__total_clicked'),
                total_creds=Sum('campaigns__total_credentials_entered'),
                total_reported=Sum('campaigns__total_reported'),
            ).filter(total_campaigns__gt=0)

            template_comparison = []
            for t in templates:
                total_sent = t.total_sent or 0
                template_comparison.append({
                    'template_id': t.id,
                    'template_name': t.name,
                    'attack_vector': t.attack_vector,
                    'difficulty': t.difficulty,
                    'times_used': t.total_campaigns,
                    'total_sent': total_sent,
                    'average_click_rate': round((t.total_clicked or 0) / total_sent * 100, 2) if total_sent > 0 else None,
                    'average_credential_rate': round((t.total_creds or 0) / total_sent * 100, 2) if total_sent > 0 else None,
                    'average_report_rate': round((t.total_reported or 0) / total_sent * 100, 2) if total_sent > 0 else None,
                })

            data = {
                'simulations': simulation_list,
                'total_count': simulations.count(),
                'template_comparison': template_comparison,
            }

            serializer = SimulationListAnalyticsSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def retrieve(self, request, pk=None):
        """Get detailed analytics for a specific simulation."""
        user = request.user

        try:
            from apps.simulations.models import SimulationCampaign, EmailSimulation, TrackingEvent
            from apps.training.models import RiskScore

            simulation = SimulationCampaign.objects.select_related('template').get(pk=pk)

            # Check access
            if not user.is_super_admin and user.company != simulation.company:
                return Response({'error': 'Access denied'}, status=403)

            total_sent = simulation.total_sent or 0

            overview = {
                'simulation_id': simulation.id,
                'simulation_name': simulation.name,
                'template_name': simulation.template.name,
                'attack_vector': simulation.template.attack_vector,
                'difficulty': simulation.template.difficulty,
                'status': simulation.status,
                'sent_at': simulation.sent_at,
                'total_sent': total_sent,
                'total_delivered': simulation.total_delivered,
                'delivery_rate': round(simulation.total_delivered / total_sent * 100, 2) if total_sent > 0 else None,
                'total_opened': simulation.total_opened,
                'open_rate': round(simulation.total_opened / total_sent * 100, 2) if total_sent > 0 else None,
                'total_clicked': simulation.total_clicked,
                'click_rate': round(simulation.total_clicked / total_sent * 100, 2) if total_sent > 0 else None,
                'total_credentials': simulation.total_credentials_entered,
                'credential_rate': round(simulation.total_credentials_entered / total_sent * 100, 2) if total_sent > 0 else None,
                'total_reported': simulation.total_reported,
                'report_rate': round(simulation.total_reported / total_sent * 100, 2) if total_sent > 0 else None,
                'compromise_rate': round(max(simulation.total_clicked, simulation.total_credentials_entered) / total_sent * 100, 2) if total_sent > 0 else None,
            }

            # Employee details
            employee_details = []
            emails = EmailSimulation.objects.filter(
                campaign=simulation
            ).select_related('employee').order_by('-was_clicked', '-credentials_entered')

            for email in emails[:100]:
                time_to_click = None
                if email.sent_at and email.clicked_at:
                    time_to_click = int((email.clicked_at - email.sent_at).total_seconds())

                risk_score = None
                try:
                    rs = RiskScore.objects.get(employee=email.employee)
                    risk_score = rs.score
                except RiskScore.DoesNotExist:
                    pass

                employee_details.append({
                    'employee_id': email.employee.id,
                    'employee_email': email.employee.email,
                    'employee_name': email.employee.get_full_name(),
                    'email_status': email.status,
                    'was_opened': email.was_opened,
                    'was_clicked': email.was_clicked,
                    'was_reported': email.was_reported,
                    'credentials_entered': email.credentials_entered,
                    'first_opened_at': email.first_opened_at,
                    'clicked_at': email.clicked_at,
                    'reported_at': email.reported_at,
                    'time_to_click_seconds': time_to_click,
                    'current_risk_score': risk_score,
                })

            # Hourly activity
            hourly_activity = []
            events = TrackingEvent.objects.filter(
                campaign=simulation
            ).annotate(
                hour=TruncDate('created_at')
            ).values('hour').annotate(
                opens=Count('id', filter=Q(event_type='EMAIL_OPENED')),
                clicks=Count('id', filter=Q(event_type='LINK_CLICKED')),
                reports=Count('id', filter=Q(event_type='EMAIL_REPORTED')),
            ).order_by('hour')

            for e in events:
                hourly_activity.append({
                    'date': str(e['hour']),
                    'opens': e['opens'],
                    'clicks': e['clicks'],
                    'reports': e['reports'],
                })

            data = {
                'overview': overview,
                'employee_details': employee_details,
                'hourly_activity': hourly_activity,
            }

            serializer = SimulationAnalyticsDetailSerializer(data)
            return Response(serializer.data)

        except SimulationCampaign.DoesNotExist:
            return Response({'error': 'Simulation not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class RiskAnalyticsViewSet(viewsets.ViewSet):
    """
    Risk analytics endpoints.

    Provides risk score trends and high-risk employee identification.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    @action(detail=False, methods=['get'])
    def distribution(self, request):
        """Get current risk score distribution."""
        user = request.user
        company_filter = get_company_filter(user)

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        try:
            from apps.training.models import RiskScore

            scores = RiskScore.objects.filter(**company_filter)
            total = scores.count()

            if total == 0:
                return Response({
                    'total_employees': 0,
                    'low_risk': 0, 'low_risk_percentage': 0,
                    'medium_risk': 0, 'medium_risk_percentage': 0,
                    'high_risk': 0, 'high_risk_percentage': 0,
                    'critical_risk': 0, 'critical_risk_percentage': 0,
                    'average_score': None, 'median_score': None,
                })

            low = scores.filter(risk_level='LOW').count()
            medium = scores.filter(risk_level='MEDIUM').count()
            high = scores.filter(risk_level='HIGH').count()
            critical = scores.filter(risk_level='CRITICAL').count()

            avg = scores.aggregate(avg=Avg('score'))['avg']

            data = {
                'total_employees': total,
                'low_risk': low,
                'low_risk_percentage': round(low / total * 100, 2),
                'medium_risk': medium,
                'medium_risk_percentage': round(medium / total * 100, 2),
                'high_risk': high,
                'high_risk_percentage': round(high / total * 100, 2),
                'critical_risk': critical,
                'critical_risk_percentage': round(critical / total * 100, 2),
                'average_score': round(avg, 2) if avg else None,
                'median_score': None,
            }

            serializer = RiskDistributionSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get risk score trends over time."""
        user = request.user
        start_date, end_date, period = get_date_range(request)
        company_filter = get_company_filter(user)

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        try:
            from apps.training.models import RiskScore, RiskScoreHistory

            # Current distribution
            scores = RiskScore.objects.filter(**company_filter)
            total = scores.count()

            distribution_end = {
                'total_employees': total,
                'low_risk': scores.filter(risk_level='LOW').count(),
                'low_risk_percentage': 0,
                'medium_risk': scores.filter(risk_level='MEDIUM').count(),
                'medium_risk_percentage': 0,
                'high_risk': scores.filter(risk_level='HIGH').count(),
                'high_risk_percentage': 0,
                'critical_risk': scores.filter(risk_level='CRITICAL').count(),
                'critical_risk_percentage': 0,
                'average_score': float(scores.aggregate(avg=Avg('score'))['avg'] or 0),
                'median_score': None,
            }

            if total > 0:
                distribution_end['low_risk_percentage'] = round(distribution_end['low_risk'] / total * 100, 2)
                distribution_end['medium_risk_percentage'] = round(distribution_end['medium_risk'] / total * 100, 2)
                distribution_end['high_risk_percentage'] = round(distribution_end['high_risk'] / total * 100, 2)
                distribution_end['critical_risk_percentage'] = round(distribution_end['critical_risk'] / total * 100, 2)

            # Daily averages
            history = RiskScoreHistory.objects.filter(
                risk_score__company_id=company_filter.get('company_id') or company_filter.get('company'),
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                avg_score=Avg('new_score'),
                high_count=Count('id', filter=Q(new_score__gte=70))
            ).order_by('date')

            daily_averages = [{'date': h['date'], 'value': float(h['avg_score'] or 0)} for h in history]
            daily_high_risk = [{'date': h['date'], 'value': h['high_count']} for h in history]

            # Improvement/deterioration counts
            improvements = RiskScoreHistory.objects.filter(
                risk_score__company_id=company_filter.get('company_id') or company_filter.get('company'),
                created_at__date__gte=start_date,
                score_change__lt=0
            ).count()

            deteriorations = RiskScoreHistory.objects.filter(
                risk_score__company_id=company_filter.get('company_id') or company_filter.get('company'),
                created_at__date__gte=start_date,
                score_change__gt=0
            ).count()

            data = {
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
                'distribution_start': distribution_end,  # Simplified
                'distribution_end': distribution_end,
                'daily_averages': daily_averages,
                'daily_high_risk_counts': daily_high_risk,
                'improvement_count': improvements,
                'deterioration_count': deteriorations,
                'unchanged_count': 0,
            }

            serializer = RiskTrendSerializer(data)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def high_risk_employees(self, request):
        """Get list of high-risk employees."""
        user = request.user
        company_filter = get_company_filter(user)

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        try:
            from apps.training.models import RiskScore, RemediationTraining

            scores = RiskScore.objects.filter(
                **company_filter,
                risk_level__in=['HIGH', 'CRITICAL']
            ).select_related('employee').order_by('-score')[:50]

            employees = []
            for rs in scores:
                # Get pending trainings
                pending = RemediationTraining.objects.filter(
                    employee=rs.employee,
                    status__in=['ASSIGNED', 'IN_PROGRESS']
                ).count()

                employees.append({
                    'employee_id': rs.employee.id,
                    'employee_email': rs.employee.email,
                    'employee_name': rs.employee.get_full_name(),
                    'department': None,
                    'risk_score': rs.score,
                    'risk_level': rs.risk_level,
                    'previous_score': None,
                    'score_change': None,
                    'quiz_accuracy': rs.quiz_accuracy,
                    'simulation_click_rate': rs.simulation_click_rate,
                    'phishing_emails_missed': rs.phishing_emails_missed,
                    'credentials_entered': rs.credentials_entered,
                    'trainings_pending': pending,
                    'requires_remediation': rs.requires_remediation,
                    'last_activity_date': rs.updated_at,
                })

            serializer = HighRiskEmployeeSerializer(employees, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)


class TrainingAnalyticsViewSet(viewsets.ViewSet):
    """
    Training analytics endpoints.

    Provides training effectiveness and completion metrics.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    def list(self, request):
        """Get training analytics summary."""
        user = request.user
        company_filter = get_company_filter(user)

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_filter = {'company_id': int(company_id)}

        try:
            from apps.training.models import TrainingModule, RemediationTraining

            # Module stats
            modules = TrainingModule.objects.filter(
                Q(company__isnull=True) | Q(**company_filter)
            ).annotate(
                assigned=Count('assignments', filter=Q(**{f'assignments__{k}': v for k, v in company_filter.items()}) if company_filter else Q()),
                started=Count('assignments', filter=Q(assignments__status__in=['IN_PROGRESS', 'COMPLETED', 'PASSED', 'FAILED'])),
                completed=Count('assignments', filter=Q(assignments__status__in=['COMPLETED', 'PASSED', 'FAILED'])),
                passed_count=Count('assignments', filter=Q(assignments__status='PASSED')),
                avg_score=Avg('assignments__quiz_score', filter=Q(assignments__quiz_score__isnull=False)),
                avg_time=Avg('assignments__time_spent_seconds'),
            )

            module_stats = []
            for m in modules:
                module_stats.append({
                    'module_id': m.id,
                    'module_title': m.title,
                    'category': m.category,
                    'difficulty': m.difficulty,
                    'duration_minutes': m.duration_minutes,
                    'times_assigned': m.assigned,
                    'times_started': m.started,
                    'times_completed': m.completed,
                    'times_passed': m.passed_count,
                    'completion_rate': round(m.completed / m.assigned * 100, 2) if m.assigned > 0 else None,
                    'pass_rate': round(m.passed_count / m.completed * 100, 2) if m.completed > 0 else None,
                    'average_score': round(float(m.avg_score), 2) if m.avg_score else None,
                    'average_time_minutes': round(float(m.avg_time) / 60, 2) if m.avg_time else None,
                })

            # Effectiveness (risk reduction)
            effectiveness = []
            for m in modules:
                trainings = RemediationTraining.objects.filter(
                    training_module=m,
                    status='PASSED',
                    risk_score_before__isnull=False,
                    risk_score_after__isnull=False,
                    **company_filter
                )

                if trainings.exists():
                    stats = trainings.aggregate(
                        avg_before=Avg('risk_score_before'),
                        avg_after=Avg('risk_score_after'),
                        count=Count('id')
                    )

                    avg_before = stats['avg_before'] or 0
                    avg_after = stats['avg_after'] or 0
                    reduction = avg_before - avg_after

                    effectiveness.append({
                        'module_id': m.id,
                        'module_title': m.title,
                        'category': m.category,
                        'employees_trained': stats['count'],
                        'employees_passed': stats['count'],
                        'average_risk_before': round(avg_before, 2),
                        'average_risk_after': round(avg_after, 2),
                        'average_risk_reduction': round(reduction, 2),
                        'risk_reduction_percentage': round(reduction / avg_before * 100, 2) if avg_before > 0 else None,
                        'click_rate_before': None,
                        'click_rate_after': None,
                        'click_rate_improvement': None,
                    })

            # Pending trainings
            pending = RemediationTraining.objects.filter(
                **company_filter,
                status__in=['ASSIGNED', 'IN_PROGRESS']
            ).select_related('employee', 'training_module').order_by('due_date')[:50]

            pending_list = []
            now = timezone.now()
            for p in pending:
                is_overdue = p.due_date and p.due_date < now
                days_overdue = (now - p.due_date).days if is_overdue else None

                pending_list.append({
                    'employee_id': p.employee.id,
                    'employee_email': p.employee.email,
                    'employee_name': p.employee.get_full_name(),
                    'training_id': p.id,
                    'module_title': p.training_module.title,
                    'category': p.training_module.category,
                    'status': p.status,
                    'assigned_at': p.assigned_at,
                    'due_date': p.due_date,
                    'is_overdue': is_overdue,
                    'days_overdue': days_overdue,
                })

            # Overall metrics
            all_trainings = RemediationTraining.objects.filter(**company_filter)
            total = all_trainings.count()
            completed = all_trainings.filter(status__in=['COMPLETED', 'PASSED', 'FAILED']).count()
            passed = all_trainings.filter(status='PASSED').count()

            data = {
                'module_stats': module_stats,
                'effectiveness': effectiveness,
                'pending_trainings': pending_list,
                'total_modules': modules.count(),
                'total_assignments': total,
                'overall_completion_rate': round(completed / total * 100, 2) if total > 0 else None,
                'overall_pass_rate': round(passed / completed * 100, 2) if completed > 0 else None,
                'average_risk_reduction': None,
            }

            serializer = TrainingAnalyticsSummarySerializer(data)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def effectiveness(self, request):
        """Get training effectiveness analysis."""
        # Reuse list endpoint logic
        return self.list(request)


class ExportViewSet(viewsets.ViewSet):
    """
    Data export endpoints.

    Provides CSV exports for various data types.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    @action(detail=False, methods=['post'])
    def csv(self, request):
        """
        Export data to CSV.

        Request body:
        - export_type: campaigns, simulations, risk_scores, training, users
        - start_date: YYYY-MM-DD (optional)
        - end_date: YYYY-MM-DD (optional)
        - company_id: int (super admin only)
        - campaign_id/simulation_id: int (for specific exports)
        """
        serializer = ExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        export_type = data['export_type']
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        include_pii = data.get('include_pii', False)

        company_filter = get_company_filter(user)
        if user.is_super_admin and data.get('company_id'):
            company_filter = {'company_id': data['company_id']}

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        row_count = 0

        try:
            if export_type == 'campaigns':
                row_count = self._export_campaigns(writer, company_filter, start_date, end_date, include_pii)
            elif export_type == 'simulations':
                row_count = self._export_simulations(writer, company_filter, start_date, end_date, include_pii)
            elif export_type == 'risk_scores':
                row_count = self._export_risk_scores(writer, company_filter, include_pii)
            elif export_type == 'training':
                row_count = self._export_training(writer, company_filter, start_date, end_date, include_pii)
            elif export_type == 'users':
                row_count = self._export_users(writer, company_filter, include_pii)
            else:
                return Response({'error': 'Invalid export type'}, status=400)

            # Create response
            output.seek(0)
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            filename = f'{export_type}_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def _export_campaigns(self, writer, company_filter, start_date, end_date, include_pii):
        """Export campaign results to CSV."""
        from apps.campaigns.models import QuizResult

        headers = ['Campaign', 'Status', 'Score', 'Correct', 'Total', 'Risk Level', 'Completed At']
        if include_pii:
            headers = ['Employee Email', 'Employee Name'] + headers
        writer.writerow(headers)

        results = QuizResult.objects.filter(
            campaign__company_id=company_filter.get('company_id') or company_filter.get('company')
        ).select_related('employee', 'campaign')

        if start_date:
            results = results.filter(completed_at__date__gte=start_date)
        if end_date:
            results = results.filter(completed_at__date__lte=end_date)

        count = 0
        for r in results:
            row = [
                r.campaign.name,
                r.campaign.status,
                float(r.score),
                r.correct_answers,
                r.total_questions,
                r.risk_level,
                r.completed_at.isoformat() if r.completed_at else '',
            ]
            if include_pii:
                row = [r.employee.email, r.employee.get_full_name()] + row
            writer.writerow(row)
            count += 1

        return count

    def _export_simulations(self, writer, company_filter, start_date, end_date, include_pii):
        """Export simulation results to CSV."""
        from apps.simulations.models import EmailSimulation

        headers = ['Simulation', 'Template', 'Status', 'Opened', 'Clicked', 'Reported', 'Credentials', 'Sent At']
        if include_pii:
            headers = ['Employee Email', 'Employee Name'] + headers
        writer.writerow(headers)

        emails = EmailSimulation.objects.filter(
            campaign__company_id=company_filter.get('company_id') or company_filter.get('company')
        ).select_related('employee', 'campaign', 'campaign__template')

        if start_date:
            emails = emails.filter(sent_at__date__gte=start_date)
        if end_date:
            emails = emails.filter(sent_at__date__lte=end_date)

        count = 0
        for e in emails:
            row = [
                e.campaign.name,
                e.campaign.template.name,
                e.status,
                'Yes' if e.was_opened else 'No',
                'Yes' if e.was_clicked else 'No',
                'Yes' if e.was_reported else 'No',
                'Yes' if e.credentials_entered else 'No',
                e.sent_at.isoformat() if e.sent_at else '',
            ]
            if include_pii:
                row = [e.employee.email, e.employee.get_full_name()] + row
            writer.writerow(row)
            count += 1

        return count

    def _export_risk_scores(self, writer, company_filter, include_pii):
        """Export risk scores to CSV."""
        from apps.training.models import RiskScore

        headers = ['Score', 'Risk Level', 'Quiz Accuracy', 'Click Rate', 'Phishing Missed', 'Trainings Completed', 'Updated At']
        if include_pii:
            headers = ['Employee Email', 'Employee Name'] + headers
        writer.writerow(headers)

        scores = RiskScore.objects.filter(**company_filter).select_related('employee')

        count = 0
        for s in scores:
            row = [
                s.score,
                s.risk_level,
                s.quiz_accuracy or '',
                s.simulation_click_rate or '',
                s.phishing_emails_missed,
                s.trainings_completed,
                s.updated_at.isoformat(),
            ]
            if include_pii:
                row = [s.employee.email, s.employee.get_full_name()] + row
            writer.writerow(row)
            count += 1

        return count

    def _export_training(self, writer, company_filter, start_date, end_date, include_pii):
        """Export training records to CSV."""
        from apps.training.models import RemediationTraining

        headers = ['Module', 'Category', 'Status', 'Score', 'Attempts', 'Assigned At', 'Completed At']
        if include_pii:
            headers = ['Employee Email', 'Employee Name'] + headers
        writer.writerow(headers)

        trainings = RemediationTraining.objects.filter(**company_filter).select_related('employee', 'training_module')

        if start_date:
            trainings = trainings.filter(assigned_at__date__gte=start_date)
        if end_date:
            trainings = trainings.filter(assigned_at__date__lte=end_date)

        count = 0
        for t in trainings:
            row = [
                t.training_module.title,
                t.training_module.category,
                t.status,
                float(t.quiz_score) if t.quiz_score else '',
                t.quiz_attempts,
                t.assigned_at.isoformat(),
                t.completed_at.isoformat() if t.completed_at else '',
            ]
            if include_pii:
                row = [t.employee.email, t.employee.get_full_name()] + row
            writer.writerow(row)
            count += 1

        return count

    def _export_users(self, writer, company_filter, include_pii):
        """Export user list to CSV."""
        headers = ['Role', 'Active', 'Verified', 'Date Joined', 'Last Login']
        if include_pii:
            headers = ['Email', 'First Name', 'Last Name'] + headers
        writer.writerow(headers)

        users = User.objects.filter(
            company_id=company_filter.get('company_id') or company_filter.get('company')
        )

        count = 0
        for u in users:
            row = [
                u.role,
                'Yes' if u.is_active else 'No',
                'Yes' if u.is_verified else 'No',
                u.date_joined.isoformat(),
                u.last_login.isoformat() if u.last_login else '',
            ]
            if include_pii:
                row = [u.email, u.first_name, u.last_name] + row
            writer.writerow(row)
            count += 1

        return count
