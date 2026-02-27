"""
Company Management Serializers
==============================
Serializers for company CRUD, user management, and statistics.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .models import Company

User = get_user_model()


# ============================================================================
# Company Serializers
# ============================================================================

class CompanyListSerializer(serializers.ModelSerializer):
    """Serializer for listing companies with basic stats."""

    total_users = serializers.IntegerField(read_only=True)
    total_employees = serializers.IntegerField(read_only=True)
    total_admins = serializers.IntegerField(read_only=True)
    is_subscription_active = serializers.BooleanField(read_only=True)
    average_risk_score = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'name_ar', 'email', 'industry', 'company_size',
            'country', 'city', 'is_active', 'is_subscription_active',
            'total_users', 'total_employees', 'total_admins',
            'average_risk_score',
            'subscription_start_date', 'subscription_end_date',
            'created_at'
        ]

    def get_average_risk_score(self, obj):
        """Get average risk score for the company's employees."""
        try:
            from apps.training.models import RiskScore
            avg = RiskScore.objects.filter(
                employee__company=obj
            ).aggregate(avg=Avg('score'))['avg']
            return round(avg, 2) if avg is not None else None
        except Exception:
            return None


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Serializer for company detail view with full information."""

    total_users = serializers.IntegerField(read_only=True)
    total_employees = serializers.IntegerField(read_only=True)
    total_admins = serializers.IntegerField(read_only=True)
    is_subscription_active = serializers.BooleanField(read_only=True)
    active_campaigns_count = serializers.SerializerMethodField()
    active_simulations_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'name_ar', 'description', 'description_ar',
            'email', 'phone', 'website',
            'country', 'city', 'address',
            'industry', 'company_size',
            'is_active', 'is_subscription_active',
            'subscription_start_date', 'subscription_end_date',
            'total_users', 'total_employees', 'total_admins',
            'active_campaigns_count', 'active_simulations_count',
            'created_at', 'updated_at'
        ]

    def get_active_campaigns_count(self, obj):
        """Get count of active quiz campaigns."""
        try:
            from apps.campaigns.models import Campaign
            return Campaign.objects.filter(
                company=obj,
                status='ACTIVE'
            ).count()
        except Exception:
            return 0

    def get_active_simulations_count(self, obj):
        """Get count of active simulation campaigns."""
        try:
            from apps.simulations.models import SimulationCampaign
            return SimulationCampaign.objects.filter(
                company=obj,
                status='ACTIVE'
            ).count()
        except Exception:
            return 0


class CompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating companies."""

    class Meta:
        model = Company
        fields = [
            'name', 'name_ar', 'description', 'description_ar',
            'email', 'phone', 'website',
            'country', 'city', 'address',
            'industry', 'company_size',
            'is_active',
            'subscription_start_date', 'subscription_end_date'
        ]

    def validate_name(self, value):
        """Ensure company name is unique (case-insensitive)."""
        instance = self.instance
        if Company.objects.filter(name__iexact=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value

    def validate(self, data):
        """Validate subscription dates."""
        start_date = data.get('subscription_start_date')
        end_date = data.get('subscription_end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'subscription_end_date': 'End date must be after start date.'
            })

        return data


class CompanyStatsSerializer(serializers.Serializer):
    """Serializer for company dashboard statistics."""

    # User stats
    total_users = serializers.IntegerField()
    total_employees = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    active_users = serializers.IntegerField()

    # Campaign stats
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    completed_campaigns = serializers.IntegerField()

    # Simulation stats
    total_simulations = serializers.IntegerField()
    active_simulations = serializers.IntegerField()
    completed_simulations = serializers.IntegerField()

    # Risk & Training stats
    average_risk_score = serializers.FloatField(allow_null=True)
    employees_at_high_risk = serializers.IntegerField()
    training_completion_rate = serializers.FloatField(allow_null=True)

    # Engagement stats
    total_quiz_completions = serializers.IntegerField()
    total_training_completions = serializers.IntegerField()
    total_phishing_clicks = serializers.IntegerField()


# ============================================================================
# Company User Serializers
# ============================================================================

class CompanyUserSerializer(serializers.ModelSerializer):
    """Serializer for users within a company."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)
    risk_score = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'preferred_language',
            'is_active', 'is_verified',
            'date_joined', 'last_login', 'risk_score'
        ]
        read_only_fields = ['date_joined', 'last_login']

    def get_risk_score(self, obj):
        """Get user's current risk score and stats if available."""
        try:
            from apps.training.models import RiskScore
            risk = RiskScore.objects.filter(employee=obj).first()
            if risk:
                return {
                    'score': risk.score,
                    'risk_level': risk.risk_level,
                    'total_quizzes_taken': risk.total_quizzes_taken,
                    'quiz_accuracy': risk.quiz_accuracy,
                    'total_simulations_received': risk.total_simulations_received,
                    'simulations_clicked': risk.simulations_clicked,
                    'simulation_click_rate': risk.simulation_click_rate,
                    'trainings_assigned': risk.trainings_assigned,
                    'trainings_completed': risk.trainings_completed,
                    'requires_remediation': risk.requires_remediation,
                }
            return None
        except Exception:
            return None


class CompanyUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users within a company."""

    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'role', 'preferred_language', 'password'
        ]

    def validate_role(self, value):
        """Restrict roles that can be assigned."""
        allowed_roles = ['COMPANY_ADMIN', 'EMPLOYEE']
        if value not in allowed_roles:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(allowed_roles)}"
            )
        return value

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            # Generate random password for invited users
            user.set_unusable_password()
        user.save()
        return user


class CompanyUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users within a company."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'role', 'preferred_language', 'is_active'
        ]

    def validate_role(self, value):
        """Restrict roles that can be assigned."""
        allowed_roles = ['COMPANY_ADMIN', 'EMPLOYEE']
        if value not in allowed_roles:
            raise serializers.ValidationError(
                f"Role must be one of: {', '.join(allowed_roles)}"
            )
        return value


class BulkInviteSerializer(serializers.Serializer):
    """Serializer for bulk user invitations."""

    emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=100
    )
    role = serializers.ChoiceField(
        choices=['COMPANY_ADMIN', 'EMPLOYEE'],
        default='EMPLOYEE'
    )
    send_invitation = serializers.BooleanField(default=True)

    def validate_emails(self, value):
        """Validate and normalize emails."""
        normalized = [email.lower().strip() for email in value]
        # Remove duplicates while preserving order
        seen = set()
        unique_emails = []
        for email in normalized:
            if email not in seen:
                seen.add(email)
                unique_emails.append(email)
        return unique_emails


class BulkCSVImportSerializer(serializers.Serializer):
    """Serializer for CSV bulk import."""

    csv_file = serializers.FileField()
    default_role = serializers.ChoiceField(
        choices=['COMPANY_ADMIN', 'EMPLOYEE'],
        default='EMPLOYEE'
    )
    send_invitation = serializers.BooleanField(default=True)

    def validate_csv_file(self, value):
        """Validate CSV file format."""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV file.")
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("File size must be under 5MB.")
        return value


# ============================================================================
# Activity Serializers
# ============================================================================

class CompanyActivitySerializer(serializers.Serializer):
    """Serializer for company activity log."""

    activity_type = serializers.CharField()
    description = serializers.CharField()
    user_email = serializers.CharField(allow_null=True)
    user_name = serializers.CharField(allow_null=True)
    timestamp = serializers.DateTimeField()
    details = serializers.DictField(allow_null=True)
