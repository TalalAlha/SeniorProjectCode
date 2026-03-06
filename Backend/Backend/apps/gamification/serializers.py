"""
Gamification Serializers
========================
Serializers for badges, points, and leaderboard APIs.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Badge, EmployeeBadge, PointsTransaction, EmployeePoints

User = get_user_model()


# ============================================================================
# Badge Serializers
# ============================================================================

class BadgeListSerializer(serializers.ModelSerializer):
    """Serializer for listing available badges."""

    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'name_ar', 'badge_type', 'description', 'description_ar',
            'icon', 'color', 'rarity', 'points_awarded', 'is_hidden'
        ]


class BadgeDetailSerializer(serializers.ModelSerializer):
    """Serializer for badge detail view."""

    times_awarded = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'name_ar', 'badge_type', 'description', 'description_ar',
            'icon', 'color', 'rarity', 'points_awarded', 'criteria',
            'is_active', 'is_hidden', 'company', 'times_awarded',
            'created_at', 'updated_at'
        ]

    def get_times_awarded(self, obj):
        return obj.employee_badges.count()


class BadgeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating badges (admin only)."""

    class Meta:
        model = Badge
        fields = [
            'name', 'name_ar', 'badge_type', 'description', 'description_ar',
            'icon', 'color', 'rarity', 'points_awarded', 'criteria',
            'is_active', 'is_hidden', 'company'
        ]


# ============================================================================
# Employee Badge Serializers
# ============================================================================

class EmployeeBadgeSerializer(serializers.ModelSerializer):
    """Serializer for employee's earned badges."""

    badge = BadgeListSerializer(read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = EmployeeBadge
        fields = [
            'id', 'badge', 'employee', 'employee_name', 'employee_email',
            'awarded_at', 'points_awarded', 'source_type', 'is_notified'
        ]


class EmployeeBadgeListSerializer(serializers.ModelSerializer):
    """Compact serializer for badge lists."""

    badge_name = serializers.CharField(source='badge.name', read_only=True)
    badge_name_ar = serializers.CharField(source='badge.name_ar', read_only=True)
    badge_icon = serializers.CharField(source='badge.icon', read_only=True)
    badge_color = serializers.CharField(source='badge.color', read_only=True)
    badge_rarity = serializers.CharField(source='badge.rarity', read_only=True)
    badge_type = serializers.CharField(source='badge.badge_type', read_only=True)

    class Meta:
        model = EmployeeBadge
        fields = [
            'id', 'badge_name', 'badge_name_ar', 'badge_icon',
            'badge_color', 'badge_rarity', 'badge_type', 'awarded_at', 'points_awarded'
        ]


# ============================================================================
# Points Serializers
# ============================================================================

class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transaction history."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = PointsTransaction
        fields = [
            'id', 'employee', 'employee_name', 'transaction_type', 'transaction_type_display',
            'points', 'balance_after', 'description', 'description_ar',
            'source_type', 'source_id', 'metadata', 'created_at'
        ]


class EmployeePointsSerializer(serializers.ModelSerializer):
    """Serializer for employee points summary."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = EmployeePoints
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'total_points', 'weekly_points', 'monthly_points',
            'badge_count', 'current_streak_days', 'longest_streak_days',
            'last_activity_date', 'updated_at'
        ]


class EmployeePointsSummarySerializer(serializers.Serializer):
    """Serializer for employee's own points dashboard."""

    total_points = serializers.IntegerField()
    weekly_points = serializers.IntegerField()
    monthly_points = serializers.IntegerField()
    badge_count = serializers.IntegerField()
    rank_all_time = serializers.IntegerField(allow_null=True)
    rank_weekly = serializers.IntegerField(allow_null=True)
    rank_monthly = serializers.IntegerField(allow_null=True)
    current_streak_days = serializers.IntegerField()
    longest_streak_days = serializers.IntegerField()


# ============================================================================
# Leaderboard Serializers
# ============================================================================

class EmployeeShortSerializer(serializers.ModelSerializer):
    """Minimal employee info embedded in leaderboard entries."""

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """Serializer for leaderboard entries."""

    # Nested employee object — frontend reads entry.employee.first_name / .email
    employee = EmployeeShortSerializer(read_only=True)

    # Generic `points` field populated by the view based on the requested period
    points = serializers.IntegerField(default=0)

    # Whether this entry belongs to the requesting user (set by the view)
    is_current_user = serializers.BooleanField(default=False)

    class Meta:
        model = EmployeePoints
        fields = [
            'points', 'is_current_user',
            'employee', 'total_points', 'weekly_points',
            'monthly_points', 'badge_count',
        ]


class LeaderboardResponseSerializer(serializers.Serializer):
    """Serializer for full leaderboard response."""

    period = serializers.CharField()
    company_id = serializers.IntegerField(allow_null=True)
    company_name = serializers.CharField(allow_null=True)
    total_participants = serializers.IntegerField()
    entries = LeaderboardEntrySerializer(many=True)
    my_rank = serializers.IntegerField(allow_null=True)
    my_points = serializers.IntegerField(allow_null=True)


# ============================================================================
# Admin Serializers
# ============================================================================

class AdminPointsAdjustmentSerializer(serializers.Serializer):
    """Serializer for admin manual points adjustment."""

    employee_id = serializers.IntegerField()
    points = serializers.IntegerField()
    description = serializers.CharField(max_length=255)
    description_ar = serializers.CharField(max_length=255, required=False, allow_blank=True)


class BulkBadgeAwardSerializer(serializers.Serializer):
    """Serializer for bulk awarding badges."""

    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
