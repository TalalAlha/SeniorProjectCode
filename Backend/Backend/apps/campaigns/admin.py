from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Campaign, Quiz, QuizResult


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin configuration for Campaign model."""

    list_display = ['name', 'company', 'status', 'num_emails', 'phishing_ratio', 'total_participants', 'completion_rate', 'created_at']
    list_filter = ['status', 'company', 'created_at', 'start_date']
    search_fields = ['name', 'name_ar', 'description', 'company__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'total_participants', 'completed_participants', 'average_score', 'num_phishing_emails', 'num_legitimate_emails', 'is_active', 'completion_rate']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'name_ar', 'description', 'description_ar')
        }),
        (_('Campaign Configuration'), {
            'fields': ('company', 'created_by', 'num_emails', 'phishing_ratio', 'num_phishing_emails', 'num_legitimate_emails')
        }),
        (_('Status & Dates'), {
            'fields': ('status', 'start_date', 'end_date', 'is_active')
        }),
        (_('Statistics'), {
            'fields': ('total_participants', 'completed_participants', 'average_score', 'completion_rate'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for Quiz model."""

    list_display = ['employee', 'campaign', 'status', 'progress_percentage', 'started_at', 'completed_at']
    list_filter = ['status', 'campaign', 'started_at', 'completed_at']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'campaign__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'time_taken', 'total_questions', 'answered_questions', 'progress_percentage']

    fieldsets = (
        (_('Quiz Information'), {
            'fields': ('campaign', 'employee', 'status', 'current_question_index')
        }),
        (_('Progress'), {
            'fields': ('total_questions', 'answered_questions', 'progress_percentage')
        }),
        (_('Timestamps'), {
            'fields': ('started_at', 'completed_at', 'time_taken', 'created_at')
        }),
    )


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    """Admin configuration for QuizResult model."""

    list_display = ['employee', 'campaign', 'score', 'accuracy', 'risk_level', 'passed', 'completed_at']
    list_filter = ['risk_level', 'campaign', 'completed_at']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'campaign__name']
    ordering = ['-completed_at']
    readonly_fields = ['completed_at', 'accuracy', 'phishing_detection_rate', 'passed']

    fieldsets = (
        (_('Quiz Information'), {
            'fields': ('quiz', 'employee', 'campaign')
        }),
        (_('Score Metrics'), {
            'fields': ('total_questions', 'correct_answers', 'incorrect_answers', 'score', 'accuracy')
        }),
        (_('Phishing Detection'), {
            'fields': ('phishing_emails_identified', 'phishing_emails_missed', 'false_positives', 'phishing_detection_rate')
        }),
        (_('Time Metrics'), {
            'fields': ('time_taken_seconds', 'average_time_per_question')
        }),
        (_('Risk Assessment'), {
            'fields': ('risk_level', 'passed')
        }),
        (_('Timestamps'), {
            'fields': ('completed_at',)
        }),
    )
