"""
Analytics Serializers
=====================
Serializers for dashboard stats, campaign analytics, simulation analytics,
risk trends, training effectiveness, and data exports.
"""

from rest_framework import serializers


# ============================================================================
# Dashboard Overview Serializers
# ============================================================================

class DashboardOverviewSerializer(serializers.Serializer):
    """Overall platform/company statistics for dashboard."""

    # User metrics
    total_users = serializers.IntegerField()
    total_employees = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    active_users_30_days = serializers.IntegerField()

    # Campaign metrics
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    completed_campaigns = serializers.IntegerField()
    campaign_completion_rate = serializers.FloatField(allow_null=True)
    average_quiz_score = serializers.FloatField(allow_null=True)

    # Simulation metrics
    total_simulations = serializers.IntegerField()
    active_simulations = serializers.IntegerField()
    completed_simulations = serializers.IntegerField()
    overall_click_rate = serializers.FloatField(allow_null=True)
    overall_report_rate = serializers.FloatField(allow_null=True)

    # Risk metrics
    average_risk_score = serializers.FloatField(allow_null=True)
    low_risk_count = serializers.IntegerField()
    medium_risk_count = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    critical_risk_count = serializers.IntegerField()

    # Training metrics
    total_trainings_assigned = serializers.IntegerField()
    trainings_completed = serializers.IntegerField()
    trainings_passed = serializers.IntegerField()
    training_completion_rate = serializers.FloatField(allow_null=True)
    training_pass_rate = serializers.FloatField(allow_null=True)

    # Gamification metrics
    total_badges_awarded = serializers.IntegerField()
    total_points_distributed = serializers.IntegerField()


class TrendDataPointSerializer(serializers.Serializer):
    """Single data point for trend charts."""

    date = serializers.DateField()
    value = serializers.FloatField()
    count = serializers.IntegerField(required=False)


class DashboardTrendsSerializer(serializers.Serializer):
    """Time-series trend data for dashboard charts."""

    period = serializers.CharField()  # 7d, 30d, 90d, custom
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    # Quiz performance trend
    quiz_scores = TrendDataPointSerializer(many=True)
    quiz_completions = TrendDataPointSerializer(many=True)

    # Simulation trend
    simulation_click_rates = TrendDataPointSerializer(many=True)
    simulation_report_rates = TrendDataPointSerializer(many=True)

    # Risk score trend
    average_risk_scores = TrendDataPointSerializer(many=True)
    high_risk_counts = TrendDataPointSerializer(many=True)

    # Training trend
    training_completions = TrendDataPointSerializer(many=True)


# ============================================================================
# Campaign Analytics Serializers
# ============================================================================

class CampaignPerformanceSerializer(serializers.Serializer):
    """Performance metrics for a single campaign."""

    campaign_id = serializers.IntegerField()
    campaign_name = serializers.CharField()
    status = serializers.CharField()
    start_date = serializers.DateTimeField(allow_null=True)
    end_date = serializers.DateTimeField(allow_null=True)

    # Participation
    total_assigned = serializers.IntegerField()
    total_started = serializers.IntegerField()
    total_completed = serializers.IntegerField()
    completion_rate = serializers.FloatField(allow_null=True)

    # Scores
    average_score = serializers.FloatField(allow_null=True)
    median_score = serializers.FloatField(allow_null=True)
    min_score = serializers.FloatField(allow_null=True)
    max_score = serializers.FloatField(allow_null=True)

    # Phishing detection
    average_phishing_detection_rate = serializers.FloatField(allow_null=True)
    average_false_positive_rate = serializers.FloatField(allow_null=True)

    # Time metrics
    average_time_seconds = serializers.FloatField(allow_null=True)


class QuestionAnalyticsSerializer(serializers.Serializer):
    """Analytics for individual quiz questions."""

    question_id = serializers.IntegerField()
    email_subject = serializers.CharField()
    email_type = serializers.CharField()  # PHISHING or LEGITIMATE
    category = serializers.CharField()
    difficulty = serializers.CharField()

    times_shown = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    incorrect_answers = serializers.IntegerField()
    accuracy_rate = serializers.FloatField(allow_null=True)

    average_time_seconds = serializers.FloatField(allow_null=True)


class EmployeeQuizPerformanceSerializer(serializers.Serializer):
    """Individual employee performance in a campaign."""

    employee_id = serializers.IntegerField()
    employee_email = serializers.CharField()
    employee_name = serializers.CharField()

    quiz_status = serializers.CharField()
    score = serializers.FloatField(allow_null=True)
    correct_answers = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    phishing_detected = serializers.IntegerField()
    phishing_missed = serializers.IntegerField()
    false_positives = serializers.IntegerField()

    time_taken_seconds = serializers.IntegerField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)
    risk_level = serializers.CharField(allow_null=True)


class CampaignAnalyticsDetailSerializer(serializers.Serializer):
    """Full analytics detail for a campaign."""

    overview = CampaignPerformanceSerializer()
    question_analytics = QuestionAnalyticsSerializer(many=True)
    employee_performance = EmployeeQuizPerformanceSerializer(many=True)
    score_distribution = serializers.DictField()  # {0-20: count, 21-40: count, etc.}


class CampaignListAnalyticsSerializer(serializers.Serializer):
    """List of campaigns with basic analytics."""

    campaigns = CampaignPerformanceSerializer(many=True)
    total_count = serializers.IntegerField()


# ============================================================================
# Simulation Analytics Serializers
# ============================================================================

class SimulationPerformanceSerializer(serializers.Serializer):
    """Performance metrics for a simulation campaign."""

    simulation_id = serializers.IntegerField()
    simulation_name = serializers.CharField()
    template_name = serializers.CharField()
    attack_vector = serializers.CharField()
    difficulty = serializers.CharField()
    status = serializers.CharField()
    sent_at = serializers.DateTimeField(allow_null=True)

    # Delivery
    total_sent = serializers.IntegerField()
    total_delivered = serializers.IntegerField()
    delivery_rate = serializers.FloatField(allow_null=True)

    # Engagement (bad)
    total_opened = serializers.IntegerField()
    open_rate = serializers.FloatField(allow_null=True)
    total_clicked = serializers.IntegerField()
    click_rate = serializers.FloatField(allow_null=True)
    total_credentials = serializers.IntegerField()
    credential_rate = serializers.FloatField(allow_null=True)

    # Good behavior
    total_reported = serializers.IntegerField()
    report_rate = serializers.FloatField(allow_null=True)

    # Risk metrics
    compromise_rate = serializers.FloatField(allow_null=True)


class SimulationEmployeeDetailSerializer(serializers.Serializer):
    """Individual employee behavior in simulation."""

    employee_id = serializers.IntegerField()
    employee_email = serializers.CharField()
    employee_name = serializers.CharField()

    email_status = serializers.CharField()
    was_opened = serializers.BooleanField()
    was_clicked = serializers.BooleanField()
    was_reported = serializers.BooleanField()
    credentials_entered = serializers.BooleanField()

    first_opened_at = serializers.DateTimeField(allow_null=True)
    clicked_at = serializers.DateTimeField(allow_null=True)
    reported_at = serializers.DateTimeField(allow_null=True)

    time_to_click_seconds = serializers.IntegerField(allow_null=True)
    current_risk_score = serializers.IntegerField(allow_null=True)


class TemplateComparisonSerializer(serializers.Serializer):
    """Compare effectiveness of different templates."""

    template_id = serializers.IntegerField()
    template_name = serializers.CharField()
    attack_vector = serializers.CharField()
    difficulty = serializers.CharField()

    times_used = serializers.IntegerField()
    total_sent = serializers.IntegerField()
    average_click_rate = serializers.FloatField(allow_null=True)
    average_credential_rate = serializers.FloatField(allow_null=True)
    average_report_rate = serializers.FloatField(allow_null=True)


class SimulationAnalyticsDetailSerializer(serializers.Serializer):
    """Full analytics detail for a simulation."""

    overview = SimulationPerformanceSerializer()
    employee_details = SimulationEmployeeDetailSerializer(many=True)
    hourly_activity = serializers.ListField(child=serializers.DictField())
    vulnerability_by_department = serializers.DictField(required=False)


class SimulationListAnalyticsSerializer(serializers.Serializer):
    """List of simulations with basic analytics."""

    simulations = SimulationPerformanceSerializer(many=True)
    total_count = serializers.IntegerField()
    template_comparison = TemplateComparisonSerializer(many=True)


# ============================================================================
# Risk Analytics Serializers
# ============================================================================

class RiskDistributionSerializer(serializers.Serializer):
    """Risk score distribution across employees."""

    total_employees = serializers.IntegerField()
    low_risk = serializers.IntegerField()
    low_risk_percentage = serializers.FloatField()
    medium_risk = serializers.IntegerField()
    medium_risk_percentage = serializers.FloatField()
    high_risk = serializers.IntegerField()
    high_risk_percentage = serializers.FloatField()
    critical_risk = serializers.IntegerField()
    critical_risk_percentage = serializers.FloatField()

    average_score = serializers.FloatField(allow_null=True)
    median_score = serializers.FloatField(allow_null=True)


class RiskTrendSerializer(serializers.Serializer):
    """Risk score trends over time."""

    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    distribution_start = RiskDistributionSerializer()
    distribution_end = RiskDistributionSerializer()

    daily_averages = TrendDataPointSerializer(many=True)
    daily_high_risk_counts = TrendDataPointSerializer(many=True)

    improvement_count = serializers.IntegerField()
    deterioration_count = serializers.IntegerField()
    unchanged_count = serializers.IntegerField()


class HighRiskEmployeeSerializer(serializers.Serializer):
    """High risk employee details."""

    employee_id = serializers.IntegerField()
    employee_email = serializers.CharField()
    employee_name = serializers.CharField()
    department = serializers.CharField(allow_null=True)

    risk_score = serializers.IntegerField()
    risk_level = serializers.CharField()
    previous_score = serializers.IntegerField(allow_null=True)
    score_change = serializers.IntegerField(allow_null=True)

    # Contributing factors
    quiz_accuracy = serializers.FloatField(allow_null=True)
    simulation_click_rate = serializers.FloatField(allow_null=True)
    phishing_emails_missed = serializers.IntegerField()
    credentials_entered = serializers.IntegerField()
    trainings_pending = serializers.IntegerField()

    requires_remediation = serializers.BooleanField()
    last_activity_date = serializers.DateTimeField(allow_null=True)


class RiskFactorAnalysisSerializer(serializers.Serializer):
    """Analyze what's contributing to risk scores."""

    factor = serializers.CharField()
    impact_level = serializers.CharField()  # HIGH, MEDIUM, LOW
    affected_employees = serializers.IntegerField()
    average_score_impact = serializers.FloatField()
    recommendation = serializers.CharField()


class RiskAnalyticsSummarySerializer(serializers.Serializer):
    """Complete risk analytics summary."""

    distribution = RiskDistributionSerializer()
    trends = RiskTrendSerializer(required=False)
    high_risk_employees = HighRiskEmployeeSerializer(many=True)
    risk_factors = RiskFactorAnalysisSerializer(many=True)


# ============================================================================
# Training Analytics Serializers
# ============================================================================

class TrainingModuleStatsSerializer(serializers.Serializer):
    """Statistics for a training module."""

    module_id = serializers.IntegerField()
    module_title = serializers.CharField()
    category = serializers.CharField()
    difficulty = serializers.CharField()
    duration_minutes = serializers.IntegerField()

    times_assigned = serializers.IntegerField()
    times_started = serializers.IntegerField()
    times_completed = serializers.IntegerField()
    times_passed = serializers.IntegerField()

    completion_rate = serializers.FloatField(allow_null=True)
    pass_rate = serializers.FloatField(allow_null=True)
    average_score = serializers.FloatField(allow_null=True)
    average_time_minutes = serializers.FloatField(allow_null=True)


class TrainingEffectivenessSerializer(serializers.Serializer):
    """Measure training effectiveness on risk reduction."""

    module_id = serializers.IntegerField()
    module_title = serializers.CharField()
    category = serializers.CharField()

    employees_trained = serializers.IntegerField()
    employees_passed = serializers.IntegerField()

    # Risk impact
    average_risk_before = serializers.FloatField(allow_null=True)
    average_risk_after = serializers.FloatField(allow_null=True)
    average_risk_reduction = serializers.FloatField(allow_null=True)
    risk_reduction_percentage = serializers.FloatField(allow_null=True)

    # Behavior change (post-training simulation performance)
    click_rate_before = serializers.FloatField(allow_null=True)
    click_rate_after = serializers.FloatField(allow_null=True)
    click_rate_improvement = serializers.FloatField(allow_null=True)


class TrainingCompletionTrendSerializer(serializers.Serializer):
    """Training completion trends over time."""

    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    daily_completions = TrendDataPointSerializer(many=True)
    daily_pass_rate = TrendDataPointSerializer(many=True)

    total_assigned = serializers.IntegerField()
    total_completed = serializers.IntegerField()
    total_passed = serializers.IntegerField()
    overall_completion_rate = serializers.FloatField(allow_null=True)
    overall_pass_rate = serializers.FloatField(allow_null=True)


class PendingTrainingSerializer(serializers.Serializer):
    """Pending/overdue training summary."""

    employee_id = serializers.IntegerField()
    employee_email = serializers.CharField()
    employee_name = serializers.CharField()

    training_id = serializers.IntegerField()
    module_title = serializers.CharField()
    category = serializers.CharField()

    status = serializers.CharField()
    assigned_at = serializers.DateTimeField()
    due_date = serializers.DateTimeField(allow_null=True)
    is_overdue = serializers.BooleanField()
    days_overdue = serializers.IntegerField(allow_null=True)


class TrainingAnalyticsSummarySerializer(serializers.Serializer):
    """Complete training analytics summary."""

    module_stats = TrainingModuleStatsSerializer(many=True)
    effectiveness = TrainingEffectivenessSerializer(many=True)
    completion_trends = TrainingCompletionTrendSerializer(required=False)
    pending_trainings = PendingTrainingSerializer(many=True)

    # Overall metrics
    total_modules = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    overall_completion_rate = serializers.FloatField(allow_null=True)
    overall_pass_rate = serializers.FloatField(allow_null=True)
    average_risk_reduction = serializers.FloatField(allow_null=True)


# ============================================================================
# Export Serializers
# ============================================================================

class ExportRequestSerializer(serializers.Serializer):
    """Request parameters for data export."""

    export_type = serializers.ChoiceField(choices=[
        ('campaigns', 'Campaign Results'),
        ('simulations', 'Simulation Results'),
        ('risk_scores', 'Risk Scores'),
        ('training', 'Training Records'),
        ('users', 'User List'),
        ('activity', 'Activity Log'),
    ])

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    company_id = serializers.IntegerField(required=False)
    campaign_id = serializers.IntegerField(required=False)
    simulation_id = serializers.IntegerField(required=False)
    include_pii = serializers.BooleanField(default=False)  # Include personal info

    def validate(self, data):
        """Validate date range."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })

        return data


class ExportResponseSerializer(serializers.Serializer):
    """Response for export request."""

    status = serializers.CharField()
    file_name = serializers.CharField()
    file_url = serializers.URLField(required=False)
    file_content = serializers.CharField(required=False)  # Base64 for inline
    row_count = serializers.IntegerField()
    generated_at = serializers.DateTimeField()
