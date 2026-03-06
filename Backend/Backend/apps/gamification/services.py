"""
Gamification Services
=====================
Business logic for badge awarding and points management.
"""

from django.utils import timezone
from django.db import transaction
from django.db.models import F
from datetime import timedelta, date
import logging

from .models import Badge, EmployeeBadge, PointsTransaction, EmployeePoints

logger = logging.getLogger(__name__)


# ============================================================================
# Points Configuration
# ============================================================================

POINTS_CONFIG = {
    'PHISHING_REPORTED': 25,
    'TRAINING_COMPLETED': 15,
    'TRAINING_PASSED': 30,
    'FIRST_ATTEMPT_PASS': 20,
}

# Hybrid quiz scoring constants
QUIZ_BASE_POINTS = 30
QUIZ_PERFORMANCE_MULTIPLIER = 0.7


def calculate_quiz_points(quiz_score):
    """
    Calculate leaderboard points using the Hybrid Model (30/70 split).

    Formula: base_points + int(quiz_score * multiplier)
    Examples:
      100% -> 30 + 70 = 100 points
       80% -> 30 + 56 =  86 points
       60% -> 30 + 42 =  72 points

    Args:
        quiz_score: Percentage score (0–100)

    Returns:
        dict with keys: total, base_points, performance_bonus
    """
    base_points = QUIZ_BASE_POINTS
    performance_bonus = int(quiz_score * QUIZ_PERFORMANCE_MULTIPLIER)
    return {
        'total': base_points + performance_bonus,
        'base_points': base_points,
        'performance_bonus': performance_bonus,
        'quiz_score': quiz_score,
    }


# ============================================================================
# Helper Functions
# ============================================================================

def get_week_start():
    """Get the start of the current week (Monday)."""
    today = date.today()
    return today - timedelta(days=today.weekday())


def get_month_start():
    """Get the start of the current month."""
    today = date.today()
    return today.replace(day=1)


def get_or_create_employee_points(employee):
    """
    Get or create EmployeePoints record for an employee.

    Args:
        employee: User instance

    Returns:
        (EmployeePoints, created) tuple
    """
    if not employee or not employee.company:
        return None, False

    emp_points, created = EmployeePoints.objects.get_or_create(
        employee=employee,
        defaults={
            'company': employee.company,
            'total_points': 0,
            'weekly_points': 0,
            'monthly_points': 0,
            'week_start': get_week_start(),
            'month_start': get_month_start(),
        }
    )
    return emp_points, created


def reset_period_points_if_needed(emp_points):
    """
    Reset weekly/monthly points if period has changed.

    Args:
        emp_points: EmployeePoints instance

    Returns:
        Updated EmployeePoints instance
    """
    current_week_start = get_week_start()
    current_month_start = get_month_start()

    updated_fields = []

    if emp_points.week_start != current_week_start:
        emp_points.weekly_points = 0
        emp_points.week_start = current_week_start
        updated_fields.extend(['weekly_points', 'week_start'])

    if emp_points.month_start != current_month_start:
        emp_points.monthly_points = 0
        emp_points.month_start = current_month_start
        updated_fields.extend(['monthly_points', 'month_start'])

    if updated_fields:
        emp_points.save(update_fields=updated_fields + ['updated_at'])

    return emp_points


def update_streak(emp_points):
    """
    Update streak tracking for an employee.

    Args:
        emp_points: EmployeePoints instance
    """
    today = date.today()

    if emp_points.last_activity_date:
        days_diff = (today - emp_points.last_activity_date).days

        if days_diff == 0:
            # Same day, no change
            return
        elif days_diff == 1:
            # Consecutive day, increase streak
            emp_points.current_streak_days += 1
        else:
            # Streak broken, reset
            emp_points.current_streak_days = 1
    else:
        # First activity
        emp_points.current_streak_days = 1

    # Update longest streak if needed
    if emp_points.current_streak_days > emp_points.longest_streak_days:
        emp_points.longest_streak_days = emp_points.current_streak_days

    emp_points.last_activity_date = today


@transaction.atomic
def award_points(employee, transaction_type, points, source_type='', source_id=None, description='', metadata=None):
    """
    Award points to an employee and update aggregates.

    Args:
        employee: User instance
        transaction_type: Type of transaction (from TRANSACTION_TYPE_CHOICES)
        points: Number of points to award
        source_type: Model name that triggered this
        source_id: ID of the source object
        description: Human-readable description
        metadata: Optional dict for additional context (e.g. quiz score breakdown)

    Returns:
        PointsTransaction instance or None
    """
    if not employee or not employee.company:
        return None

    emp_points, _ = get_or_create_employee_points(employee)
    if not emp_points:
        return None

    reset_period_points_if_needed(emp_points)
    update_streak(emp_points)

    # Calculate new balance
    new_balance = emp_points.total_points + points

    # Create transaction record
    pt = PointsTransaction.objects.create(
        employee=employee,
        company=employee.company,
        transaction_type=transaction_type,
        points=points,
        balance_after=new_balance,
        source_type=source_type,
        source_id=source_id,
        description=description,
        metadata=metadata or {}
    )

    # Update aggregates using F() for atomicity
    EmployeePoints.objects.filter(pk=emp_points.pk).update(
        total_points=F('total_points') + points,
        weekly_points=F('weekly_points') + points,
        monthly_points=F('monthly_points') + points,
        last_activity_date=date.today(),
        updated_at=timezone.now()
    )

    return pt


@transaction.atomic
def check_and_award_badge(employee, badge_type, source_type='', source_id=None):
    """
    Check if employee already has badge, if not award it.

    Args:
        employee: User instance
        badge_type: Badge type string
        source_type: Model name that triggered this
        source_id: ID of source object

    Returns:
        EmployeeBadge instance if awarded, None if already had badge or error
    """
    if not employee or not employee.company:
        return None

    # Check if badge exists and is active
    try:
        badge = Badge.objects.get(
            badge_type=badge_type,
            is_active=True
        )
    except Badge.DoesNotExist:
        logger.warning(f'Badge type {badge_type} not found or inactive')
        return None

    # Check if employee already has this badge
    if EmployeeBadge.objects.filter(employee=employee, badge=badge).exists():
        return None

    # Award the badge
    emp_badge = EmployeeBadge.objects.create(
        employee=employee,
        badge=badge,
        company=employee.company,
        source_type=source_type,
        source_id=source_id,
        points_awarded=badge.points_awarded
    )

    # Award points for the badge
    if badge.points_awarded > 0:
        award_points(
            employee=employee,
            transaction_type='BADGE_EARNED',
            points=badge.points_awarded,
            source_type='EmployeeBadge',
            source_id=emp_badge.id,
            description=f'Earned badge: {badge.name}'
        )

    # Update badge count
    EmployeePoints.objects.filter(employee=employee).update(
        badge_count=F('badge_count') + 1,
        updated_at=timezone.now()
    )

    logger.info(f'Awarded badge {badge.name} to {employee.email}')
    return emp_badge


def check_training_champion_badge(employee):
    """
    Check and award "Training Champion" badge.
    Condition: All assigned trainings completed (none pending).

    Args:
        employee: User instance

    Returns:
        EmployeeBadge if awarded, None otherwise
    """
    from apps.training.models import RemediationTraining

    # Check if there are any pending trainings
    pending_trainings = RemediationTraining.objects.filter(
        employee=employee,
        status__in=['ASSIGNED', 'IN_PROGRESS']
    ).exists()

    if pending_trainings:
        return None

    # Check if employee has completed at least one training
    completed_count = RemediationTraining.objects.filter(
        employee=employee,
        status__in=['PASSED', 'COMPLETED']
    ).count()

    if completed_count > 0:
        return check_and_award_badge(
            employee=employee,
            badge_type='TRAINING_CHAMPION',
            source_type='RemediationTraining'
        )

    return None


def check_security_aware_badge(employee, risk_score):
    """
    Check and award "Security Aware" badge.
    Condition: LOW risk score maintained for 30+ days.

    Args:
        employee: User instance
        risk_score: RiskScore instance

    Returns:
        EmployeeBadge if awarded, None otherwise
    """
    from apps.training.models import RiskScoreHistory

    # Must have LOW risk level currently
    if risk_score.risk_level != 'LOW':
        return None

    # Check if score has been LOW for 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Look for any non-LOW entries in the last 30 days
    non_low_entries = RiskScoreHistory.objects.filter(
        employee=employee,
        created_at__gte=thirty_days_ago
    ).exclude(
        new_risk_level='LOW'
    ).exists()

    if non_low_entries:
        return None

    # Check that the employee has had a risk score for at least 30 days
    if risk_score.created_at > thirty_days_ago:
        return None

    return check_and_award_badge(
        employee=employee,
        badge_type='SECURITY_AWARE',
        source_type='RiskScore',
        source_id=risk_score.id
    )


def get_leaderboard(company_id=None, period='all_time', limit=10, offset=0):
    """
    Get leaderboard rankings.

    Args:
        company_id: Filter by company (None for all)
        period: 'weekly', 'monthly', or 'all_time'
        limit: Number of results
        offset: Pagination offset

    Returns:
        QuerySet of EmployeePoints ordered by points
    """
    queryset = EmployeePoints.objects.select_related('employee', 'company')

    if company_id:
        queryset = queryset.filter(company_id=company_id)

    # Determine which field to order by
    if period == 'weekly':
        order_field = '-weekly_points'
    elif period == 'monthly':
        order_field = '-monthly_points'
    else:  # all_time
        order_field = '-total_points'

    return queryset.order_by(order_field, 'employee__first_name')[offset:offset + limit]


def get_employee_rank(employee, period='all_time'):
    """
    Get an employee's rank in their company leaderboard.

    Args:
        employee: User instance
        period: 'weekly', 'monthly', or 'all_time'

    Returns:
        int: Rank (1-based), or None if not ranked
    """
    if not employee or not employee.company:
        return None

    try:
        emp_points = EmployeePoints.objects.get(employee=employee)
    except EmployeePoints.DoesNotExist:
        return None

    # Determine which field to compare
    if period == 'weekly':
        points_value = emp_points.weekly_points
        field_name = 'weekly_points'
    elif period == 'monthly':
        points_value = emp_points.monthly_points
        field_name = 'monthly_points'
    else:
        points_value = emp_points.total_points
        field_name = 'total_points'

    # Count employees with more points in the same company
    higher_ranked = EmployeePoints.objects.filter(
        company=employee.company,
        **{f'{field_name}__gt': points_value}
    ).count()

    return higher_ranked + 1
