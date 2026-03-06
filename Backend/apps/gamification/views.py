"""
Gamification Views
==================
API views for badges, points, and leaderboards.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction

from .models import Badge, EmployeeBadge, PointsTransaction, EmployeePoints
from .serializers import (
    BadgeListSerializer,
    BadgeDetailSerializer,
    BadgeCreateSerializer,
    EmployeeBadgeSerializer,
    EmployeeBadgeListSerializer,
    PointsTransactionSerializer,
    EmployeePointsSerializer,
    AdminPointsAdjustmentSerializer,
    BulkBadgeAwardSerializer,
    LeaderboardEntrySerializer,
)
from .services import (
    get_or_create_employee_points,
    award_points,
    check_and_award_badge,
    get_leaderboard,
    get_employee_rank,
)
from apps.core.permissions import (
    IsSuperAdminOrCompanyAdmin,
    HasCompanyAccess,
)


# ============================================================================
# Badge ViewSet
# ============================================================================

class BadgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Badge CRUD operations.

    - Anyone authenticated can list available badges
    - Only admins can create/update/delete badges
    """

    queryset = Badge.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BadgeCreateSerializer
        elif self.action == 'retrieve':
            return BadgeDetailSerializer
        return BadgeListSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_super_admin:
            queryset = Badge.objects.all()
        else:
            # Show global badges + company-specific badges
            queryset = Badge.objects.filter(
                Q(company__isnull=True) | Q(company=user.company)
            )

        # Apply filters
        if not user.is_super_admin and not user.is_company_admin:
            # Employees don't see hidden badges they haven't earned
            earned_badge_ids = EmployeeBadge.objects.filter(
                employee=user
            ).values_list('badge_id', flat=True)
            queryset = queryset.filter(
                Q(is_hidden=False) | Q(id__in=earned_badge_ids)
            )

        queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]

    @action(detail=False, methods=['get'])
    def my_badges(self, request):
        """Get current user's earned badges."""
        badges = EmployeeBadge.objects.filter(
            employee=request.user
        ).select_related('badge').order_by('-awarded_at')

        serializer = EmployeeBadgeListSerializer(badges, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently awarded badges (company-wide)."""
        user = request.user

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                queryset = EmployeeBadge.objects.filter(company_id=company_id)
            else:
                queryset = EmployeeBadge.objects.all()
        else:
            queryset = EmployeeBadge.objects.filter(company=user.company)

        queryset = queryset.select_related('badge', 'employee').order_by('-awarded_at')[:20]
        serializer = EmployeeBadgeSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    @transaction.atomic
    def bulk_award(self, request, pk=None):
        """Award a badge to multiple employees."""
        badge = self.get_object()
        serializer = BulkBadgeAwardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee_ids = serializer.validated_data['employee_ids']

        from apps.accounts.models import User

        # Filter to company employees if not super admin
        if not request.user.is_super_admin:
            employees = User.objects.filter(
                id__in=employee_ids,
                role='EMPLOYEE',
                company=request.user.company
            )
        else:
            employees = User.objects.filter(id__in=employee_ids, role='EMPLOYEE')

        awarded = []
        skipped = []

        for employee in employees:
            emp_badge = check_and_award_badge(
                employee=employee,
                badge_type=badge.badge_type,
                source_type='AdminAward',
                source_id=request.user.id
            )
            if emp_badge:
                awarded.append(employee.email)
            else:
                skipped.append(employee.email)

        return Response({
            'awarded': len(awarded),
            'skipped': len(skipped),
            'awarded_to': awarded,
            'skipped_emails': skipped
        })


# ============================================================================
# Points ViewSet
# ============================================================================

class PointsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for points and transactions.

    - Employees can see their own points
    - Admins can see company-wide points
    """

    queryset = EmployeePoints.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]
    serializer_class = EmployeePointsSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_super_admin:
            queryset = EmployeePoints.objects.all()
        elif user.is_company_admin:
            queryset = EmployeePoints.objects.filter(company=user.company)
        else:
            queryset = EmployeePoints.objects.filter(employee=user)

        return queryset.select_related('employee', 'company')

    @action(detail=False, methods=['get'])
    def my_summary(self, request):
        """Get current user's points summary."""
        emp_points, _ = get_or_create_employee_points(request.user)

        if not emp_points:
            return Response({
                'total_points': 0,
                'weekly_points': 0,
                'monthly_points': 0,
                'badge_count': 0,
                'rank_all_time': None,
                'rank_weekly': None,
                'rank_monthly': None,
                'current_streak_days': 0,
                'longest_streak_days': 0,
            })

        return Response({
            'total_points': emp_points.total_points,
            'weekly_points': emp_points.weekly_points,
            'monthly_points': emp_points.monthly_points,
            'badge_count': emp_points.badge_count,
            'rank_all_time': get_employee_rank(request.user, 'all_time'),
            'rank_weekly': get_employee_rank(request.user, 'weekly'),
            'rank_monthly': get_employee_rank(request.user, 'monthly'),
            'current_streak_days': emp_points.current_streak_days,
            'longest_streak_days': emp_points.longest_streak_days,
        })

    @action(detail=False, methods=['get'])
    def my_transactions(self, request):
        """Get current user's points transaction history."""
        transactions = PointsTransaction.objects.filter(
            employee=request.user
        ).order_by('-created_at')

        # Paginate
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = PointsTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PointsTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    @transaction.atomic
    def adjust(self, request):
        """Admin manual points adjustment."""
        serializer = AdminPointsAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.accounts.models import User

        employee_id = serializer.validated_data['employee_id']
        points = serializer.validated_data['points']
        description = serializer.validated_data['description']
        description_ar = serializer.validated_data.get('description_ar', '')

        # Get employee
        employee = get_object_or_404(User, id=employee_id, role='EMPLOYEE')

        # Check company access
        if not request.user.is_super_admin and employee.company != request.user.company:
            return Response(
                {'error': 'You can only adjust points for your company employees'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create adjustment
        pt = award_points(
            employee=employee,
            transaction_type='ADMIN_ADJUSTMENT',
            points=points,
            source_type='AdminAdjustment',
            source_id=request.user.id,
            description=description
        )

        if pt:
            pt.description_ar = description_ar
            pt.save(update_fields=['description_ar'])

        return Response({
            'success': True,
            'employee': employee.email,
            'points_adjusted': points,
            'new_balance': pt.balance_after if pt else 0
        })


# ============================================================================
# Leaderboard ViewSet
# ============================================================================

class LeaderboardViewSet(viewsets.ViewSet):
    """
    ViewSet for leaderboard queries.

    Supports:
    - Company-wide leaderboards
    - Time-based periods (weekly, monthly, all-time)
    """

    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def list(self, request):
        """
        Get leaderboard.

        Query params:
        - period: 'weekly', 'monthly', 'all_time' (default)
        - company: Company ID (super admin only)
        - limit: Number of entries (default 10, max 100)
        - offset: Pagination offset
        """
        user = request.user
        period = request.query_params.get('period', 'all_time')
        limit = min(int(request.query_params.get('limit', 10)), 100)
        offset = int(request.query_params.get('offset', 0))

        # Determine company filter
        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                company_id = int(company_id)
        else:
            company_id = user.company_id

        # Get leaderboard entries
        entries = get_leaderboard(
            company_id=company_id,
            period=period,
            limit=limit,
            offset=offset
        )

        # Add rank, period-correct points, and is_current_user to each entry
        entries_with_rank = []
        for idx, entry in enumerate(entries):
            entry_data = LeaderboardEntrySerializer(entry).data
            entry_data['rank'] = offset + idx + 1

            # Resolve points for the requested period
            if period == 'weekly':
                entry_data['points'] = entry.weekly_points
            elif period == 'monthly':
                entry_data['points'] = entry.monthly_points
            else:
                entry_data['points'] = entry.total_points

            # Flag the requesting user's own row
            entry_data['is_current_user'] = (entry.employee_id == user.id)

            entries_with_rank.append(entry_data)

        # Get current user's rank and points
        my_rank = get_employee_rank(user, period) if user.role == 'EMPLOYEE' else None
        try:
            my_points_obj = EmployeePoints.objects.get(employee=user)
            if period == 'weekly':
                my_points = my_points_obj.weekly_points
            elif period == 'monthly':
                my_points = my_points_obj.monthly_points
            else:
                my_points = my_points_obj.total_points
        except EmployeePoints.DoesNotExist:
            my_points = 0

        # Get company name
        company_name = None
        if company_id:
            from apps.companies.models import Company
            try:
                company_name = Company.objects.get(id=company_id).name
            except Company.DoesNotExist:
                pass

        # Get total participants
        total_query = EmployeePoints.objects.all()
        if company_id:
            total_query = total_query.filter(company_id=company_id)
        total_participants = total_query.count()

        return Response({
            'period': period,
            'company_id': company_id,
            'company_name': company_name,
            'total_participants': total_participants,
            'entries': entries_with_rank,
            'my_rank': my_rank,
            'my_points': my_points if user.role == 'EMPLOYEE' else None,
        })

    @action(detail=False, methods=['get'])
    def my_position(self, request):
        """Get current user's position in leaderboard."""
        user = request.user

        if user.role != 'EMPLOYEE':
            return Response({'error': 'Only employees have leaderboard positions'}, status=400)

        emp_points = EmployeePoints.objects.filter(employee=user).first()

        total_participants = EmployeePoints.objects.filter(
            company=user.company
        ).count() if user.company else 0

        return Response({
            'all_time': {
                'rank': get_employee_rank(user, 'all_time'),
                'points': emp_points.total_points if emp_points else 0,
                'total': total_participants,
            },
            'monthly': {
                'rank': get_employee_rank(user, 'monthly'),
                'points': emp_points.monthly_points if emp_points else 0,
                'total': total_participants,
            },
            'weekly': {
                'rank': get_employee_rank(user, 'weekly'),
                'points': emp_points.weekly_points if emp_points else 0,
                'total': total_participants,
            },
        })
