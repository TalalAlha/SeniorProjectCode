"""
Training App Serializers
========================
Serializers for Risk Scoring & Remediation Training.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import (
    RiskScore,
    RiskScoreHistory,
    TrainingModule,
    TrainingQuestion,
    RemediationTraining,
    TrainingQuizAnswer
)

User = get_user_model()


# =============================================================================
# Risk Score Serializers
# =============================================================================

class RiskScoreListSerializer(serializers.ModelSerializer):
    """Serializer for RiskScore list view."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    quiz_accuracy = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    simulation_click_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    training_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = RiskScore
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'company', 'company_name', 'score', 'risk_level',
            'requires_remediation', 'quiz_accuracy', 'simulation_click_rate',
            'training_completion_rate', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class RiskScoreDetailSerializer(serializers.ModelSerializer):
    """Serializer for RiskScore detail view with full statistics."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    quiz_accuracy = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    simulation_click_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    training_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    training_pass_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = RiskScore
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'company', 'company_name', 'score', 'risk_level',
            # Quiz statistics
            'total_quizzes_taken', 'total_quiz_questions', 'correct_quiz_answers',
            'phishing_emails_missed', 'quiz_accuracy',
            # Simulation statistics
            'total_simulations_received', 'simulations_opened', 'simulations_clicked',
            'simulations_reported', 'credentials_entered', 'simulation_click_rate',
            # Training statistics
            'trainings_assigned', 'trainings_completed', 'trainings_passed',
            'training_completion_rate', 'training_pass_rate',
            # Flags and dates
            'requires_remediation', 'last_quiz_date', 'last_simulation_date',
            'last_training_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RiskScoreEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for employee's own risk score view (limited data)."""

    quiz_accuracy = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    simulation_click_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    training_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    pending_trainings = serializers.SerializerMethodField()
    is_new_user = serializers.SerializerMethodField()

    class Meta:
        model = RiskScore
        fields = [
            'id', 'score', 'risk_level', 'total_quizzes_taken',
            'quiz_accuracy', 'simulation_click_rate',
            'total_simulations_received', 'simulations_clicked',
            'trainings_assigned', 'trainings_completed',
            'training_completion_rate', 'requires_remediation',
            'pending_trainings', 'is_new_user', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']

    def get_pending_trainings(self, obj):
        """Get count of pending trainings for this employee."""
        return obj.employee.remediation_trainings.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).count()

    def get_is_new_user(self, obj):
        """Check if user has no activity data yet."""
        return (
            obj.total_quizzes_taken == 0
            and obj.total_simulations_received == 0
            and obj.trainings_assigned == 0
        )


class RiskScoreUpdateSerializer(serializers.ModelSerializer):
    """Serializer for manual risk score adjustment (admin only)."""

    adjustment_reason = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = RiskScore
        fields = ['score', 'adjustment_reason']

    def validate_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Score must be between 0 and 100")
        return value


# =============================================================================
# Risk Score History Serializers
# =============================================================================

class RiskScoreHistorySerializer(serializers.ModelSerializer):
    """Serializer for RiskScoreHistory records."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = RiskScoreHistory
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'event_type', 'previous_score', 'new_score', 'score_change',
            'previous_risk_level', 'new_risk_level', 'source_type',
            'source_id', 'description', 'description_ar', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'score_change']


# =============================================================================
# Training Module Serializers
# =============================================================================

class TrainingQuestionSerializer(serializers.ModelSerializer):
    """Serializer for TrainingQuestion - hides correct answer."""

    class Meta:
        model = TrainingQuestion
        fields = [
            'id', 'question_number', 'question_text', 'question_text_ar',
            'options', 'options_ar'
        ]
        read_only_fields = ['id']


class TrainingQuestionDetailSerializer(serializers.ModelSerializer):
    """Serializer for TrainingQuestion with correct answer (for results)."""

    correct_answer = serializers.CharField(read_only=True)

    class Meta:
        model = TrainingQuestion
        fields = [
            'id', 'question_number', 'question_text', 'question_text_ar',
            'options', 'options_ar', 'correct_answer_index', 'correct_answer',
            'explanation', 'explanation_ar', 'is_active'
        ]
        read_only_fields = ['id', 'correct_answer']


class TrainingQuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating TrainingQuestion."""

    class Meta:
        model = TrainingQuestion
        fields = [
            'module', 'question_number', 'question_text', 'question_text_ar',
            'options', 'options_ar', 'correct_answer_index',
            'explanation', 'explanation_ar', 'is_active'
        ]

    def validate_options(self, value):
        if not value or len(value) < 2:
            raise serializers.ValidationError("At least 2 options are required")
        if len(value) > 4:
            raise serializers.ValidationError("Maximum 4 options allowed")
        return value

    def validate(self, attrs):
        options = attrs.get('options', [])
        correct_index = attrs.get('correct_answer_index', 0)
        if correct_index >= len(options):
            raise serializers.ValidationError({
                'correct_answer_index': f'Index must be less than {len(options)}'
            })
        return attrs


class TrainingModuleListSerializer(serializers.ModelSerializer):
    """Serializer for TrainingModule list view."""

    company_name = serializers.CharField(source='company.name', read_only=True)
    total_questions = serializers.IntegerField(read_only=True)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    pass_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    times_assigned = serializers.IntegerField(read_only=True)
    times_completed = serializers.IntegerField(read_only=True)
    times_passed = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingModule
        fields = [
            'id', 'title', 'title_ar', 'content_type', 'category',
            'difficulty', 'duration_minutes', 'passing_score',
            'total_questions', 'is_active', 'is_mandatory',
            'company', 'company_name', 'times_assigned', 'times_completed',
            'times_passed', 'completion_rate', 'pass_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'times_assigned', 'times_completed', 'times_passed']


class TrainingModuleDetailSerializer(serializers.ModelSerializer):
    """Serializer for TrainingModule detail view."""

    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    questions = TrainingQuestionSerializer(many=True, read_only=True)
    total_questions = serializers.IntegerField(read_only=True)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    pass_rate = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = TrainingModule
        fields = [
            'id', 'title', 'title_ar', 'description', 'description_ar',
            'content_type', 'category', 'difficulty', 'content_html',
            'content_html_ar', 'video_url', 'duration_minutes',
            'passing_score', 'min_questions_required', 'score_reduction_on_pass',
            'is_active', 'is_mandatory', 'company', 'company_name',
            'created_by', 'created_by_name', 'questions', 'total_questions',
            'times_assigned', 'times_completed', 'times_passed', 'average_score',
            'completion_rate', 'pass_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'times_assigned',
            'times_completed', 'times_passed', 'average_score'
        ]


class TrainingModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating TrainingModule."""

    class Meta:
        model = TrainingModule
        fields = [
            'title', 'title_ar', 'description', 'description_ar',
            'content_type', 'category', 'difficulty', 'content_html',
            'content_html_ar', 'video_url', 'duration_minutes',
            'passing_score', 'min_questions_required', 'score_reduction_on_pass',
            'is_active', 'is_mandatory', 'company'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TrainingModuleEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for employee view of training module (no admin stats)."""

    total_questions = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingModule
        fields = [
            'id', 'title', 'title_ar', 'description', 'description_ar',
            'content_type', 'category', 'difficulty', 'content_html',
            'content_html_ar', 'video_url', 'duration_minutes',
            'passing_score', 'total_questions'
        ]
        read_only_fields = ['id']


# =============================================================================
# Remediation Training Serializers
# =============================================================================

class RemediationTrainingListSerializer(serializers.ModelSerializer):
    """Serializer for RemediationTraining list view."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)
    training_title = serializers.CharField(source='training_module.title', read_only=True)
    training_category = serializers.CharField(source='training_module.category', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = RemediationTraining
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'training_module', 'training_title', 'training_category',
            'status', 'assignment_reason', 'assigned_at', 'due_date',
            'is_overdue', 'quiz_score', 'passed', 'completed_at'
        ]
        read_only_fields = ['id', 'assigned_at']


class RemediationTrainingDetailSerializer(serializers.ModelSerializer):
    """Serializer for RemediationTraining detail view."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    training_module_detail = TrainingModuleEmployeeSerializer(source='training_module', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    passed = serializers.BooleanField(read_only=True)
    time_spent_formatted = serializers.CharField(read_only=True)

    class Meta:
        model = RemediationTraining
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'company', 'company_name', 'training_module', 'training_module_detail',
            'status', 'assignment_reason', 'assigned_by', 'assigned_by_name',
            'assigned_at', 'started_at', 'completed_at', 'due_date', 'is_overdue',
            'quiz_attempts', 'quiz_score', 'correct_answers', 'total_questions',
            'passed', 'content_viewed', 'content_viewed_at', 'time_spent_seconds',
            'time_spent_formatted', 'risk_score_before', 'risk_score_after',
            'source_type', 'source_id', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'assigned_at', 'created_at', 'updated_at',
            'quiz_score', 'correct_answers', 'total_questions',
            'risk_score_before', 'risk_score_after'
        ]


class RemediationTrainingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating RemediationTraining (admin assignment)."""

    class Meta:
        model = RemediationTraining
        fields = [
            'employee', 'training_module', 'assignment_reason',
            'due_date', 'notes'
        ]

    def validate(self, attrs):
        employee = attrs.get('employee')
        training_module = attrs.get('training_module')

        # Check if employee already has this training assigned and not completed
        existing = RemediationTraining.objects.filter(
            employee=employee,
            training_module=training_module,
            status__in=['ASSIGNED', 'IN_PROGRESS']
        ).exists()

        if existing:
            raise serializers.ValidationError(
                "Employee already has this training assigned and pending"
            )

        return attrs

    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        validated_data['company'] = validated_data['employee'].company

        # Set default due date if not provided (7 days from now)
        if not validated_data.get('due_date'):
            validated_data['due_date'] = timezone.now() + timedelta(days=7)

        return super().create(validated_data)


class RemediationTrainingEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for employee view of their assigned training."""

    training_module = TrainingModuleEmployeeSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    passed = serializers.BooleanField(read_only=True)
    time_spent_formatted = serializers.CharField(read_only=True)

    class Meta:
        model = RemediationTraining
        fields = [
            'id', 'training_module', 'status', 'assignment_reason',
            'assigned_at', 'started_at', 'completed_at', 'due_date',
            'is_overdue', 'quiz_attempts', 'quiz_score', 'passed',
            'content_viewed', 'time_spent_formatted'
        ]
        read_only_fields = ['id', 'assigned_at', 'quiz_score']


class TrainingQuizAnswerSerializer(serializers.ModelSerializer):
    """Serializer for TrainingQuizAnswer."""

    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = TrainingQuizAnswer
        fields = [
            'id', 'question', 'question_text', 'selected_answer_index',
            'is_correct', 'time_spent_seconds', 'answered_at'
        ]
        read_only_fields = ['id', 'is_correct', 'answered_at']


# =============================================================================
# Action Serializers
# =============================================================================

class BulkAssignTrainingSerializer(serializers.Serializer):
    """Serializer for bulk assigning training to multiple employees."""

    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of employee IDs to assign training to"
    )
    training_module_id = serializers.IntegerField(
        help_text="ID of training module to assign"
    )
    assignment_reason = serializers.ChoiceField(
        choices=RemediationTraining.ASSIGNMENT_REASON_CHOICES,
        default='MANUAL_ADMIN'
    )
    due_date = serializers.DateTimeField(required=False)

    def validate_training_module_id(self, value):
        if not TrainingModule.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Training module not found or inactive")
        return value


class SubmitTrainingQuizSerializer(serializers.Serializer):
    """Serializer for submitting training quiz answers."""

    answers = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=3),
        help_text="Dict mapping question_id to selected_answer_index"
    )


class RecalculateRiskScoreSerializer(serializers.Serializer):
    """Serializer for triggering risk score recalculation."""

    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of employee IDs to recalculate. Empty = all employees."
    )


# =============================================================================
# Statistics Serializers
# =============================================================================

class CompanyRiskStatisticsSerializer(serializers.Serializer):
    """Serializer for company-wide risk statistics."""

    total_employees = serializers.IntegerField()
    employees_with_scores = serializers.IntegerField()

    # Risk level distribution
    low_risk_count = serializers.IntegerField()
    medium_risk_count = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    critical_risk_count = serializers.IntegerField()

    # Averages
    average_risk_score = serializers.DecimalField(max_digits=5, decimal_places=1)
    average_quiz_accuracy = serializers.DecimalField(max_digits=5, decimal_places=1)
    average_simulation_click_rate = serializers.DecimalField(max_digits=5, decimal_places=1)

    # Training stats
    total_trainings_assigned = serializers.IntegerField()
    total_trainings_completed = serializers.IntegerField()
    total_trainings_passed = serializers.IntegerField()
    training_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=1)

    # Requiring attention
    employees_requiring_remediation = serializers.IntegerField()
    overdue_trainings_count = serializers.IntegerField()


class EmployeeRiskTrendSerializer(serializers.Serializer):
    """Serializer for employee risk score trend data."""

    date = serializers.DateField()
    score = serializers.IntegerField()
    risk_level = serializers.CharField()
    event_type = serializers.CharField()
