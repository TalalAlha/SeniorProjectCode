from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import SimulationTemplate, SimulationCampaign, EmailSimulation, TrackingEvent


@admin.register(SimulationTemplate)
class SimulationTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for SimulationTemplate model."""

    list_display = ['name', 'attack_vector', 'difficulty', 'is_public', 'is_active', 'times_used', 'average_click_rate', 'created_at']
    list_filter = ['attack_vector', 'difficulty', 'is_active', 'is_public', 'language', 'created_at']
    search_fields = ['name', 'name_ar', 'description', 'subject']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'times_used', 'average_click_rate']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'name_ar', 'description', 'description_ar', 'company')
        }),
        (_('Email Content'), {
            'fields': ('sender_name', 'sender_email', 'reply_to_email', 'subject', 'body_html', 'body_plain')
        }),
        (_('Attack Configuration'), {
            'fields': ('attack_vector', 'difficulty', 'language')
        }),
        (_('Landing Page'), {
            'fields': ('requires_landing_page', 'landing_page_title', 'landing_page_message', 'landing_page_message_ar'),
            'classes': ('collapse',)
        }),
        (_('Red Flags'), {
            'fields': ('red_flags',)
        }),
        (_('Settings'), {
            'fields': ('is_active', 'is_public', 'created_by')
        }),
        (_('Statistics'), {
            'fields': ('times_used', 'average_click_rate'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SimulationCampaign)
class SimulationCampaignAdmin(admin.ModelAdmin):
    """Admin configuration for SimulationCampaign model."""

    list_display = ['name', 'company', 'status', 'template_name', 'total_sent', 'click_rate_display', 'compromise_rate_display', 'created_at']
    list_filter = ['status', 'company', 'send_date', 'created_at']
    search_fields = ['name', 'name_ar', 'description', 'company__name']
    ordering = ['-created_at']
    readonly_fields = [
        'created_at', 'updated_at', 'sent_at', 'completed_at',
        'total_sent', 'total_delivered', 'total_opened', 'total_clicked',
        'total_reported', 'total_credentials_entered',
        'open_rate', 'click_rate', 'report_rate', 'compromise_rate', 'is_active'
    ]
    filter_horizontal = ['target_employees']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'name_ar', 'description', 'description_ar')
        }),
        (_('Campaign Configuration'), {
            'fields': ('company', 'created_by', 'template', 'status')
        }),
        (_('Scheduling'), {
            'fields': ('send_date', 'end_date', 'sent_at', 'completed_at')
        }),
        (_('Targeting'), {
            'fields': ('target_all_employees', 'target_employees')
        }),
        (_('Tracking Configuration'), {
            'fields': ('track_email_opens', 'track_link_clicks', 'track_credentials')
        }),
        (_('Notifications'), {
            'fields': ('notify_on_click', 'notify_on_credential_entry'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': (
                'total_sent', 'total_delivered', 'total_opened', 'total_clicked',
                'total_reported', 'total_credentials_entered',
                'open_rate', 'click_rate', 'report_rate', 'compromise_rate'
            ),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def template_name(self, obj):
        """Display template name."""
        return obj.template.name
    template_name.short_description = 'Template'

    def click_rate_display(self, obj):
        """Display click rate with color coding."""
        rate = obj.click_rate
        if rate == 0:
            color = 'green'
        elif rate < 20:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            rate
        )
    click_rate_display.short_description = 'Click Rate'

    def compromise_rate_display(self, obj):
        """Display compromise rate with color coding."""
        rate = obj.compromise_rate
        if rate == 0:
            color = 'green'
        elif rate < 20:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            rate
        )
    compromise_rate_display.short_description = 'Compromise Rate'


@admin.register(EmailSimulation)
class EmailSimulationAdmin(admin.ModelAdmin):
    """Admin configuration for EmailSimulation model."""

    list_display = ['employee', 'campaign_name', 'status', 'was_opened', 'was_clicked', 'credentials_entered', 'was_reported', 'sent_at']
    list_filter = ['status', 'was_opened', 'was_clicked', 'credentials_entered', 'was_reported', 'sent_at']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'campaign__name', 'recipient_email']
    ordering = ['-created_at']
    readonly_fields = [
        'tracking_token', 'link_token', 'created_at', 'updated_at',
        'time_to_open', 'time_to_click', 'is_compromised',
        'tracking_pixel_url', 'phishing_link_url'
    ]

    fieldsets = (
        (_('Simulation Details'), {
            'fields': ('campaign', 'employee', 'recipient_email', 'status')
        }),
        (_('Tracking Tokens'), {
            'fields': ('tracking_token', 'link_token', 'tracking_pixel_url', 'phishing_link_url'),
            'classes': ('collapse',)
        }),
        (_('Tracking Flags'), {
            'fields': ('was_opened', 'was_clicked', 'was_reported', 'credentials_entered', 'is_compromised')
        }),
        (_('Timing'), {
            'fields': (
                'sent_at', 'delivered_at', 'first_opened_at', 'clicked_at',
                'reported_at', 'credentials_entered_at', 'time_to_open', 'time_to_click'
            )
        }),
        (_('Technical Details'), {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def campaign_name(self, obj):
        """Display campaign name."""
        return obj.campaign.name
    campaign_name.short_description = 'Campaign'


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    """Admin configuration for TrackingEvent model."""

    list_display = ['event_type', 'employee', 'campaign_name', 'ip_address', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['employee__email', 'campaign__name', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    fieldsets = (
        (_('Event Details'), {
            'fields': ('email_simulation', 'campaign', 'employee', 'event_type', 'event_data')
        }),
        (_('Technical Details'), {
            'fields': ('ip_address', 'user_agent', 'geolocation'),
            'classes': ('collapse',)
        }),
        (_('Timestamp'), {
            'fields': ('created_at',)
        }),
    )

    def campaign_name(self, obj):
        """Display campaign name."""
        return obj.campaign.name
    campaign_name.short_description = 'Campaign'
