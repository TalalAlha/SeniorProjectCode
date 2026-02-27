"""
Company Management Views
========================
API views for company CRUD, user management, and statistics.
"""

import csv
import io
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q, F
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Company
from .serializers import (
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanyCreateSerializer,
    CompanyStatsSerializer,
    CompanyUserSerializer,
    CompanyUserCreateSerializer,
    CompanyUserUpdateSerializer,
    BulkInviteSerializer,
    BulkCSVImportSerializer,
    CompanyActivitySerializer,
)
from apps.core.permissions import (
    IsSuperAdmin,
    IsSuperAdminOrCompanyAdmin,
    IsSameCompany,
)

User = get_user_model()


class CompanyPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company management.

    Permissions:
    - Super Admin: Full access to all companies
    - Company Admin: Read/update access to their own company only
    - Employee: Read-only access to their own company
    """

    queryset = Company.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = CompanyPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'name_ar', 'email']
    ordering_fields = ['name', 'created_at', 'total_users', 'is_active']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CompanyCreateSerializer
        elif self.action == 'retrieve':
            return CompanyDetailSerializer
        return CompanyListSerializer

    def get_queryset(self):
        user = self.request.user

        # Public users (registration page) only see active companies
        if self.action == 'list' and not user.is_authenticated:
            return Company.objects.filter(is_active=True)

        if user.is_super_admin:
            queryset = Company.objects.all()
        elif user.company:
            # Company Admin or Employee can only see their own company
            queryset = Company.objects.filter(id=user.company_id)
        else:
            queryset = Company.objects.none()

        # Apply filters from query params (only for company list, not nested actions like users)
        if self.action == 'list':
            is_active = self.request.query_params.get('is_active')
            if is_active is not None:
                is_active_bool = is_active.lower() == 'true'
                queryset = queryset.filter(is_active=is_active_bool)

        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry=industry)

        return queryset

    def get_permissions(self):
        """Allow public access to list companies (for registration page)."""
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'create':
            return [IsAuthenticated(), IsSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin(), IsSameCompany()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsSuperAdmin()]
        elif self.action in ['activate', 'deactivate']:
            return [IsAuthenticated(), IsSuperAdmin()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check access for non-super admins
        if not request.user.is_super_admin and request.user.company != instance:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a new company (Super Admin only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        return Response(
            CompanyDetailSerializer(company).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update company details."""
        instance = self.get_object()
        # Company admin can only update their own company
        if not request.user.is_super_admin and request.user.company != instance:
            return Response(
                {'error': 'You can only update your own company.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a company (Super Admin only). Hard delete with cascade."""
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return Response(
            {'message': f'Company "{name}" has been permanently deleted.'},
            status=status.HTTP_200_OK
        )

    # ========================================================================
    # Custom Actions - Company Status
    # ========================================================================

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a company (Super Admin only)."""
        company = self.get_object()
        if company.is_active:
            return Response(
                {'message': 'Company is already active.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        company.is_active = True
        company.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': f'Company "{company.name}" has been activated.'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a company (Super Admin only)."""
        company = self.get_object()
        if not company.is_active:
            return Response(
                {'message': 'Company is already inactive.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        company.is_active = False
        company.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': f'Company "{company.name}" has been deactivated.'})

    # ========================================================================
    # Custom Actions - Statistics
    # ========================================================================

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get comprehensive company statistics."""
        company = self.get_object()

        # Check access
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # User stats
        users = User.objects.filter(company=company)
        total_users = users.count()
        total_employees = users.filter(role='EMPLOYEE').count()
        total_admins = users.filter(role='COMPANY_ADMIN').count()
        active_users = users.filter(is_active=True).count()

        # Campaign stats
        try:
            from apps.campaigns.models import Campaign
            campaigns = Campaign.objects.filter(company=company)
            total_campaigns = campaigns.count()
            active_campaigns = campaigns.filter(status='ACTIVE').count()
            completed_campaigns = campaigns.filter(status='COMPLETED').count()
        except Exception:
            total_campaigns = active_campaigns = completed_campaigns = 0

        # Simulation stats
        try:
            from apps.simulations.models import SimulationCampaign
            simulations = SimulationCampaign.objects.filter(company=company)
            total_simulations = simulations.count()
            active_simulations = simulations.filter(status='ACTIVE').count()
            completed_simulations = simulations.filter(status='COMPLETED').count()
        except Exception:
            total_simulations = active_simulations = completed_simulations = 0

        # Risk score stats
        try:
            from apps.training.models import RiskScore
            risk_scores = RiskScore.objects.filter(employee__company=company)
            avg_risk = risk_scores.aggregate(avg=Avg('score'))['avg']
            high_risk_count = risk_scores.filter(score__gte=70).count()
        except Exception:
            avg_risk = None
            high_risk_count = 0

        # Training stats
        try:
            from apps.training.models import RemediationTraining
            trainings = RemediationTraining.objects.filter(employee__company=company)
            total_training = trainings.count()
            completed_training = trainings.filter(status='COMPLETED').count()
            training_rate = (completed_training / total_training * 100) if total_training > 0 else None
        except Exception:
            training_rate = None
            total_training = completed_training = 0

        # Quiz completion stats
        try:
            from apps.campaigns.models import QuizResult
            quiz_completions = QuizResult.objects.filter(
                employee__company=company, is_passed=True
            ).count()
        except Exception:
            quiz_completions = 0

        # Phishing click stats
        try:
            from apps.simulations.models import TrackingEvent
            phishing_clicks = TrackingEvent.objects.filter(
                simulation__campaign__company=company,
                event_type='LINK_CLICK'
            ).count()
        except Exception:
            phishing_clicks = 0

        stats_data = {
            'total_users': total_users,
            'total_employees': total_employees,
            'total_admins': total_admins,
            'active_users': active_users,
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'completed_campaigns': completed_campaigns,
            'total_simulations': total_simulations,
            'active_simulations': active_simulations,
            'completed_simulations': completed_simulations,
            'average_risk_score': round(avg_risk, 2) if avg_risk else None,
            'employees_at_high_risk': high_risk_count,
            'training_completion_rate': round(training_rate, 2) if training_rate else None,
            'total_quiz_completions': quiz_completions,
            'total_training_completions': completed_training,
            'total_phishing_clicks': phishing_clicks,
        }

        serializer = CompanyStatsSerializer(stats_data)
        return Response(serializer.data)

    # ========================================================================
    # Custom Actions - User Management
    # ========================================================================

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """List all users in a company."""
        company = self.get_object()

        # Check access
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        users = User.objects.filter(company=company).exclude(invitation_status='PENDING')

        # Apply filters
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')

        search = request.query_params.get('search')
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        users = users.order_by('-date_joined')

        # Paginate
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = CompanyUserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CompanyUserSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='users/add')
    @transaction.atomic
    def add_user(self, request, pk=None):
        """Add a single user to the company."""
        company = self.get_object()

        # Check access (must be admin)
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_super_admin and not request.user.is_company_admin:
            return Response(
                {'error': 'Only admins can add users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CompanyUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save(company=company)

        return Response(
            CompanyUserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['put', 'patch'], url_path=r'users/(?P<user_id>\d+)')
    @transaction.atomic
    def update_user(self, request, pk=None, user_id=None):
        """Update a user within the company."""
        company = self.get_object()

        # Check access
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_super_admin and not request.user.is_company_admin:
            return Response(
                {'error': 'Only admins can update users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = get_object_or_404(User, id=user_id, company=company)

        # Prevent changing super admin users
        if user.is_super_admin:
            return Response(
                {'error': 'Cannot modify super admin users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CompanyUserUpdateSerializer(
            user, data=request.data, partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(CompanyUserSerializer(user).data)

    @action(detail=True, methods=['delete'], url_path=r'users/(?P<user_id>\d+)/remove')
    @transaction.atomic
    def remove_user(self, request, pk=None, user_id=None):
        """Remove a user from the company. Hard delete."""
        company = self.get_object()

        # Check access
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_super_admin and not request.user.is_company_admin:
            return Response(
                {'error': 'Only admins can remove users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = get_object_or_404(User, id=user_id, company=company)

        # Prevent removing super admins or self
        if user.is_super_admin:
            return Response(
                {'error': 'Cannot remove super admin users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user == request.user:
            return Response(
                {'error': 'Cannot remove yourself.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = user.email
        user.delete()

        return Response({'message': f'User "{email}" has been permanently removed.'})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def invite_users(self, request, pk=None):
        """Bulk invite users to the company via email."""
        company = self.get_object()

        # Check access
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_super_admin and not request.user.is_company_admin:
            return Response(
                {'error': 'Only admins can invite users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BulkInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emails = serializer.validated_data['emails']
        role = serializer.validated_data['role']
        send_invitation = serializer.validated_data['send_invitation']

        created = []
        existing = []
        errors = []

        for email in emails:
            # Check if user already exists
            if User.objects.filter(email__iexact=email).exists():
                existing_user = User.objects.get(email__iexact=email)
                if existing_user.company == company:
                    existing.append(email)
                else:
                    errors.append({
                        'email': email,
                        'error': 'User belongs to another company'
                    })
                continue

            try:
                user = User.objects.create(
                    email=email.lower(),
                    role=role,
                    company=company,
                    is_active=True,
                    is_verified=False
                )
                user.set_unusable_password()
                user.save()
                created.append(email)

                # TODO: Send invitation email if send_invitation is True
                # This would integrate with email service

            except Exception as e:
                errors.append({
                    'email': email,
                    'error': str(e)
                })

        return Response({
            'created': len(created),
            'existing': len(existing),
            'errors': len(errors),
            'created_emails': created,
            'existing_emails': existing,
            'error_details': errors,
            'message': f'Successfully invited {len(created)} users.'
        })

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    @transaction.atomic
    def import_csv(self, request, pk=None):
        """
        Bulk import users from CSV file.

        Expected CSV format:
        email,first_name,last_name,role
        john@example.com,John,Doe,EMPLOYEE
        """
        company = self.get_object()

        # Check access
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_super_admin and not request.user.is_company_admin:
            return Response(
                {'error': 'Only admins can import users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BulkCSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data['csv_file']
        default_role = serializer.validated_data['default_role']

        # Parse CSV
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
        except Exception as e:
            return Response(
                {'error': f'Invalid CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        existing = []
        errors = []
        row_number = 1

        for row in reader:
            row_number += 1
            email = row.get('email', '').strip().lower()

            if not email:
                errors.append({
                    'row': row_number,
                    'error': 'Missing email'
                })
                continue

            # Check if user already exists
            if User.objects.filter(email__iexact=email).exists():
                existing.append(email)
                continue

            # Determine role
            role = row.get('role', '').strip().upper()
            if role not in ['COMPANY_ADMIN', 'EMPLOYEE']:
                role = default_role

            try:
                user = User.objects.create(
                    email=email,
                    first_name=row.get('first_name', '').strip(),
                    last_name=row.get('last_name', '').strip(),
                    role=role,
                    company=company,
                    is_active=True,
                    is_verified=False
                )
                user.set_unusable_password()
                user.save()
                created.append(email)

            except Exception as e:
                errors.append({
                    'row': row_number,
                    'email': email,
                    'error': str(e)
                })

        return Response({
            'total_rows': row_number - 1,
            'created': len(created),
            'existing': len(existing),
            'errors': len(errors),
            'created_emails': created,
            'existing_emails': existing,
            'error_details': errors,
            'message': f'Successfully imported {len(created)} users from CSV.'
        })

    # ========================================================================
    # Custom Actions - Activity
    # ========================================================================

    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """Get recent activity for the company."""
        company = self.get_object()

        # Check access
        if not request.user.is_super_admin and request.user.company != company:
            return Response(
                {'error': 'You do not have access to this company.'},
                status=status.HTTP_403_FORBIDDEN
            )

        activities = []
        limit = int(request.query_params.get('limit', 20))

        # Get recent quiz results
        try:
            from apps.campaigns.models import QuizResult
            quiz_results = QuizResult.objects.filter(
                employee__company=company
            ).select_related('employee', 'quiz').order_by('-completed_at')[:limit]

            for result in quiz_results:
                activities.append({
                    'activity_type': 'QUIZ_COMPLETED',
                    'description': f'Completed quiz "{result.quiz.title}" with score {result.score}%',
                    'user_email': result.employee.email,
                    'user_name': result.employee.get_full_name(),
                    'timestamp': result.completed_at,
                    'details': {
                        'quiz_id': result.quiz_id,
                        'score': result.score,
                        'passed': result.is_passed
                    }
                })
        except Exception:
            pass

        # Get recent training completions
        try:
            from apps.training.models import RemediationTraining
            trainings = RemediationTraining.objects.filter(
                employee__company=company,
                status='COMPLETED'
            ).select_related('employee', 'module').order_by('-completed_at')[:limit]

            for training in trainings:
                activities.append({
                    'activity_type': 'TRAINING_COMPLETED',
                    'description': f'Completed training module "{training.module.title}"',
                    'user_email': training.employee.email,
                    'user_name': training.employee.get_full_name(),
                    'timestamp': training.completed_at,
                    'details': {
                        'module_id': training.module_id,
                        'score': training.score
                    }
                })
        except Exception:
            pass

        # Get recent phishing events
        try:
            from apps.simulations.models import TrackingEvent
            events = TrackingEvent.objects.filter(
                simulation__campaign__company=company,
                event_type__in=['LINK_CLICK', 'CREDENTIAL_SUBMIT']
            ).select_related(
                'simulation__employee'
            ).order_by('-created_at')[:limit]

            for event in events:
                event_desc = 'clicked a phishing link' if event.event_type == 'LINK_CLICK' else 'submitted credentials on phishing page'
                activities.append({
                    'activity_type': f'PHISHING_{event.event_type}',
                    'description': f'Employee {event_desc}',
                    'user_email': event.simulation.employee.email if event.simulation.employee else None,
                    'user_name': event.simulation.employee.get_full_name() if event.simulation.employee else None,
                    'timestamp': event.created_at,
                    'details': {
                        'event_type': event.event_type,
                        'simulation_id': event.simulation_id
                    }
                })
        except Exception:
            pass

        # Get recent badge awards
        try:
            from apps.gamification.models import EmployeeBadge
            badges = EmployeeBadge.objects.filter(
                company=company
            ).select_related('employee', 'badge').order_by('-awarded_at')[:limit]

            for badge_award in badges:
                activities.append({
                    'activity_type': 'BADGE_AWARDED',
                    'description': f'Earned badge "{badge_award.badge.name}"',
                    'user_email': badge_award.employee.email,
                    'user_name': badge_award.employee.get_full_name(),
                    'timestamp': badge_award.awarded_at,
                    'details': {
                        'badge_id': badge_award.badge_id,
                        'badge_name': badge_award.badge.name,
                        'points': badge_award.points_awarded
                    }
                })
        except Exception:
            pass

        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)

        # Limit to requested amount
        activities = activities[:limit]

        serializer = CompanyActivitySerializer(activities, many=True)
        return Response(serializer.data)

    # ========================================================================
    # Utility endpoint for current user's company
    # ========================================================================

    @action(detail=False, methods=['get'])
    def my_company(self, request):
        """Get current user's company details."""
        user = request.user

        if not user.company:
            return Response(
                {'error': 'You are not associated with any company.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanyDetailSerializer(user.company)
        return Response(serializer.data)
