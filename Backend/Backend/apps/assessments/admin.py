from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import EmailTemplate, QuizQuestion


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for EmailTemplate model."""

    list_display = ['subject', 'email_type', 'category', 'difficulty', 'is_ai_generated', 'campaign', 'language', 'created_at']
    list_filter = ['email_type', 'category', 'difficulty', 'is_ai_generated', 'language', 'campaign', 'created_at']
    search_fields = ['subject', 'sender_name', 'sender_email', 'body', 'campaign__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'is_phishing']

    fieldsets = (
        (_('Campaign'), {
            'fields': ('campaign',)
        }),
        (_('Email Details'), {
            'fields': ('sender_name', 'sender_email', 'subject', 'body', 'language')
        }),
        (_('Attachments & Links'), {
            'fields': ('has_attachments', 'attachment_names', 'links'),
            'classes': ('collapse',)
        }),
        (_('Classification'), {
            'fields': ('email_type', 'category', 'difficulty', 'is_phishing')
        }),
        (_('AI Generation'), {
            'fields': ('is_ai_generated', 'ai_model_used', 'generation_prompt'),
            'classes': ('collapse',)
        }),
        (_('Learning Content'), {
            'fields': ('red_flags', 'explanation', 'explanation_ar')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    """Admin configuration for QuizQuestion model."""

    list_display = ['quiz', 'question_number', 'email_template_subject', 'answer', 'is_correct', 'time_spent_seconds', 'answered_at']
    list_filter = ['is_correct', 'requires_training', 'answer', 'answered_at']
    search_fields = ['quiz__employee__email', 'email_template__subject']
    ordering = ['quiz', 'question_number']
    readonly_fields = ['created_at', 'updated_at', 'correct_answer']

    fieldsets = (
        (_('Question Details'), {
            'fields': ('quiz', 'email_template', 'question_number')
        }),
        (_('Employee Response'), {
            'fields': ('answer', 'is_correct', 'correct_answer', 'confidence_level')
        }),
        (_('Timing'), {
            'fields': ('time_spent_seconds', 'answered_at')
        }),
        (_('Feedback'), {
            'fields': ('requires_training',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def email_template_subject(self, obj):
        """Display email template subject."""
        return obj.email_template.subject[:50]
    email_template_subject.short_description = 'Email Subject'
