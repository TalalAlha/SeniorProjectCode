"""
Training App Admin
==================
Django admin configuration for Risk Scoring & Remediation Training.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    RiskScore,
    RiskScoreHistory,
    TrainingModule,
    TrainingQuestion,
    RemediationTraining,
    TrainingQuizAnswer
)


class TrainingQuestionInline(admin.TabularInline):
    """Inline admin for TrainingQuestion in TrainingModule."""
    model = TrainingQuestion
    extra = 1
    fields = ['question_number', 'question_text', 'options', 'correct_answer_index', 'is_active']


@admin.register(RiskScore)
class RiskScoreAdmin(admin.ModelAdmin):
    """Admin for RiskScore model."""

    list_display = [
        'employee_email', 'company_name', 'score_display', 'risk_level_display',
        'quiz_accuracy_display', 'requires_remediation', 'updated_at'
    ]
    list_filter = ['risk_level', 'requires_remediation', 'company']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = [
        'employee', 'company', 'score', 'risk_level',
        'total_quizzes_taken', 'total_quiz_questions', 'correct_quiz_answers',
        'phishing_emails_missed', 'total_simulations_received', 'simulations_opened',
        'simulations_clicked', 'simulations_reported', 'credentials_entered',
        'trainings_assigned', 'trainings_completed', 'trainings_passed',
        'last_quiz_date', 'last_simulation_date', 'last_training_date',
        'created_at', 'updated_at'
    ]
    ordering = ['-score', '-updated_at']

    fieldsets = [
        (_('Employee Information'), {
            'fields': ['employee', 'company']
        }),
        (_('Risk Assessment'), {
            'fields': ['score', 'risk_level', 'requires_remediation']
        }),
        (_('Quiz Statistics'), {
            'fields': [
                'total_quizzes_taken', 'total_quiz_questions',
                'correct_quiz_answers', 'phishing_emails_missed', 'last_quiz_date'
            ]
        }),
        (_('Simulation Statistics'), {
            'fields': [
                'total_simulations_received', 'simulations_opened',
                'simulations_clicked', 'simulations_reported',
                'credentials_entered', 'last_simulation_date'
            ]
        }),
        (_('Training Statistics'), {
            'fields': [
                'trainings_assigned', 'trainings_completed',
                'trainings_passed', 'last_training_date'
            ]
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def employee_email(self, obj):
        return obj.employee.email
    employee_email.short_description = _('Employee')

    def company_name(self, obj):
        return obj.company.name if obj.company else '-'
    company_name.short_description = _('Company')

    def score_display(self, obj):
        color = 'green' if obj.score <= 30 else 'orange' if obj.score <= 60 else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.score)
    score_display.short_description = _('Score')

    def risk_level_display(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred'
        }
        color = colors.get(obj.risk_level, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_risk_level_display())
    risk_level_display.short_description = _('Risk Level')

    def quiz_accuracy_display(self, obj):
        accuracy = obj.quiz_accuracy
        if accuracy is None:
            return '-'
        return f'{accuracy:.1f}%'
    quiz_accuracy_display.short_description = _('Quiz Accuracy')


@admin.register(RiskScoreHistory)
class RiskScoreHistoryAdmin(admin.ModelAdmin):
    """Admin for RiskScoreHistory model."""

    list_display = [
        'employee_email', 'event_type', 'score_change_display',
        'previous_score', 'new_score', 'created_at'
    ]
    list_filter = ['event_type', 'new_risk_level', 'created_at']
    search_fields = ['employee__email', 'description']
    readonly_fields = [
        'risk_score', 'employee', 'event_type', 'previous_score',
        'new_score', 'score_change', 'previous_risk_level', 'new_risk_level',
        'source_type', 'source_id', 'description', 'description_ar', 'created_at'
    ]
    ordering = ['-created_at']

    def employee_email(self, obj):
        return obj.employee.email
    employee_email.short_description = _('Employee')

    def score_change_display(self, obj):
        if obj.score_change > 0:
            return format_html('<span style="color: red;">+{}</span>', obj.score_change)
        elif obj.score_change < 0:
            return format_html('<span style="color: green;">{}</span>', obj.score_change)
        return '0'
    score_change_display.short_description = _('Change')


@admin.register(TrainingModule)
class TrainingModuleAdmin(admin.ModelAdmin):
    """Admin for TrainingModule model."""

    list_display = [
        'title', 'category', 'difficulty', 'content_type',
        'duration_minutes', 'passing_score', 'is_active',
        'times_assigned', 'times_passed', 'company_name'
    ]
    list_filter = ['category', 'difficulty', 'content_type', 'is_active', 'is_mandatory']
    search_fields = ['title', 'title_ar', 'description']
    prepopulated_fields = {}
    readonly_fields = ['times_assigned', 'times_completed', 'times_passed', 'average_score', 'created_at', 'updated_at']
    ordering = ['category', 'difficulty', 'title']
    inlines = [TrainingQuestionInline]

    fieldsets = [
        (_('Basic Information'), {
            'fields': ['title', 'title_ar', 'description', 'description_ar']
        }),
        (_('Classification'), {
            'fields': ['category', 'difficulty', 'content_type']
        }),
        (_('Content'), {
            'fields': ['content_html', 'content_html_ar', 'video_url', 'duration_minutes']
        }),
        (_('Quiz Settings'), {
            'fields': ['passing_score', 'min_questions_required', 'score_reduction_on_pass']
        }),
        (_('Settings'), {
            'fields': ['is_active', 'is_mandatory', 'company', 'created_by']
        }),
        (_('Statistics'), {
            'fields': ['times_assigned', 'times_completed', 'times_passed', 'average_score'],
            'classes': ['collapse']
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def company_name(self, obj):
        return obj.company.name if obj.company else _('Global')
    company_name.short_description = _('Company')


@admin.register(TrainingQuestion)
class TrainingQuestionAdmin(admin.ModelAdmin):
    """Admin for TrainingQuestion model."""

    list_display = ['module', 'question_number', 'question_preview', 'correct_answer_index', 'is_active']
    list_filter = ['module', 'is_active']
    search_fields = ['question_text', 'question_text_ar', 'module__title']
    ordering = ['module', 'question_number']

    def question_preview(self, obj):
        text = obj.question_text[:50]
        if len(obj.question_text) > 50:
            text += '...'
        return text
    question_preview.short_description = _('Question')


@admin.register(RemediationTraining)
class RemediationTrainingAdmin(admin.ModelAdmin):
    """Admin for RemediationTraining model."""

    list_display = [
        'employee_email', 'training_title', 'status_display',
        'assignment_reason', 'quiz_score_display', 'due_date', 'is_overdue'
    ]
    list_filter = ['status', 'assignment_reason', 'company', 'training_module']
    search_fields = ['employee__email', 'training_module__title']
    readonly_fields = [
        'assigned_at', 'started_at', 'completed_at', 'content_viewed_at',
        'quiz_attempts', 'quiz_score', 'correct_answers', 'total_questions',
        'risk_score_before', 'risk_score_after', 'time_spent_seconds',
        'created_at', 'updated_at'
    ]
    ordering = ['-assigned_at']
    raw_id_fields = ['employee', 'assigned_by']

    fieldsets = [
        (_('Assignment'), {
            'fields': ['employee', 'company', 'training_module', 'assignment_reason', 'assigned_by']
        }),
        (_('Status'), {
            'fields': ['status', 'due_date']
        }),
        (_('Progress'), {
            'fields': [
                'content_viewed', 'content_viewed_at', 'time_spent_seconds',
                'started_at', 'completed_at'
            ]
        }),
        (_('Quiz Results'), {
            'fields': ['quiz_attempts', 'quiz_score', 'correct_answers', 'total_questions']
        }),
        (_('Risk Score Impact'), {
            'fields': ['risk_score_before', 'risk_score_after']
        }),
        (_('Metadata'), {
            'fields': ['source_type', 'source_id', 'notes'],
            'classes': ['collapse']
        }),
        (_('Timestamps'), {
            'fields': ['assigned_at', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def employee_email(self, obj):
        return obj.employee.email
    employee_email.short_description = _('Employee')

    def training_title(self, obj):
        return obj.training_module.title
    training_title.short_description = _('Training')

    def status_display(self, obj):
        colors = {
            'ASSIGNED': 'blue',
            'IN_PROGRESS': 'orange',
            'COMPLETED': 'gray',
            'PASSED': 'green',
            'FAILED': 'red',
            'EXPIRED': 'darkgray'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    status_display.short_description = _('Status')

    def quiz_score_display(self, obj):
        if obj.quiz_score is None:
            return '-'
        color = 'green' if obj.passed else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, obj.quiz_score)
    quiz_score_display.short_description = _('Score')


@admin.register(TrainingQuizAnswer)
class TrainingQuizAnswerAdmin(admin.ModelAdmin):
    """Admin for TrainingQuizAnswer model."""

    list_display = [
        'training_employee', 'training_module', 'question_number',
        'is_correct_display', 'answered_at'
    ]
    list_filter = ['is_correct', 'remediation_training__training_module']
    search_fields = ['remediation_training__employee__email']
    readonly_fields = ['remediation_training', 'question', 'selected_answer_index', 'is_correct', 'answered_at']
    ordering = ['-answered_at']

    def training_employee(self, obj):
        return obj.remediation_training.employee.email
    training_employee.short_description = _('Employee')

    def training_module(self, obj):
        return obj.remediation_training.training_module.title
    training_module.short_description = _('Module')

    def question_number(self, obj):
        return f'Q{obj.question.question_number}'
    question_number.short_description = _('Question')

    def is_correct_display(self, obj):
        if obj.is_correct:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    is_correct_display.short_description = _('Correct')
