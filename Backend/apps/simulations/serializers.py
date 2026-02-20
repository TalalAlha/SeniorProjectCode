from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    SimulationTemplate,
    SimulationCampaign,
    EmailSimulation,
    TrackingEvent
)

User = get_user_model()


# =============================================================================
# SimulationTemplate Serializers
# =============================================================================

class SimulationTemplateListSerializer(serializers.ModelSerializer):
    """Serializer for SimulationTemplate list view."""

    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    attack_vector_display = serializers.CharField(source='get_attack_vector_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)

    class Meta:
        model = SimulationTemplate
        fields = [
            'id', 'name', 'name_ar', 'description', 'company', 'company_name',
            'created_by', 'created_by_name', 'sender_name', 'sender_email',
            'subject', 'attack_vector', 'attack_vector_display',
            'difficulty', 'difficulty_display', 'is_active', 'is_public',
            'language', 'times_used', 'average_click_rate', 'created_at'
        ]
        read_only_fields = ['id', 'times_used', 'average_click_rate', 'created_at']


class SimulationTemplateDetailSerializer(serializers.ModelSerializer):
    """Serializer for SimulationTemplate detail view with full information."""

    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    attack_vector_display = serializers.CharField(source='get_attack_vector_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)

    class Meta:
        model = SimulationTemplate
        fields = [
            'id', 'name', 'name_ar', 'description', 'description_ar',
            'company', 'company_name', 'created_by', 'created_by_name',
            'sender_name', 'sender_email', 'reply_to_email', 'subject',
            'body_html', 'body_plain', 'attack_vector', 'attack_vector_display',
            'difficulty', 'difficulty_display', 'requires_landing_page',
            'landing_page_title', 'landing_page_message', 'landing_page_message_ar',
            'red_flags', 'is_active', 'is_public', 'language',
            'times_used', 'average_click_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'times_used', 'average_click_rate', 'created_at', 'updated_at']


class SimulationTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a SimulationTemplate."""

    class Meta:
        model = SimulationTemplate
        fields = [
            'name', 'name_ar', 'description', 'description_ar', 'company',
            'sender_name', 'sender_email', 'reply_to_email', 'subject',
            'body_html', 'body_plain', 'attack_vector', 'difficulty',
            'requires_landing_page', 'landing_page_title', 'landing_page_message',
            'landing_page_message_ar', 'red_flags', 'is_active', 'is_public', 'language'
        ]

    def validate_body_html(self, value):
        """Validate that body_html contains required placeholders."""
        if '{TRACKING_PIXEL}' not in value and '{LURE_LINK}' not in value:
            raise serializers.ValidationError(
                "Email body must contain at least {TRACKING_PIXEL} or {LURE_LINK} placeholder "
                "for tracking purposes."
            )
        return value

    def validate_red_flags(self, value):
        """Validate red_flags is a list of strings."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Red flags must be a list.")
        for flag in value:
            if not isinstance(flag, str):
                raise serializers.ValidationError("Each red flag must be a string.")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        requires_landing = attrs.get('requires_landing_page', True)

        if requires_landing:
            if not attrs.get('landing_page_message'):
                raise serializers.ValidationError({
                    'landing_page_message': 'Landing page message is required when landing page is enabled.'
                })

        return attrs

    def create(self, validated_data):
        """Create template and set created_by from request user."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


# =============================================================================
# SimulationCampaign Serializers
# =============================================================================

class EmployeeSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for employee selection in campaigns."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'first_name', 'last_name']
        read_only_fields = ['id', 'email', 'full_name', 'first_name', 'last_name']


class SimulationCampaignListSerializer(serializers.ModelSerializer):
    """Serializer for SimulationCampaign list view."""

    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    open_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    click_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    report_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    target_count = serializers.SerializerMethodField()

    class Meta:
        model = SimulationCampaign
        fields = [
            'id', 'name', 'name_ar', 'company', 'company_name',
            'created_by', 'created_by_name', 'template', 'template_name',
            'status', 'status_display', 'send_date', 'end_date',
            'target_all_employees', 'target_count',
            'total_sent', 'total_opened', 'total_clicked', 'total_reported',
            'open_rate', 'click_rate', 'report_rate',
            'sent_at', 'completed_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'total_sent', 'total_delivered', 'total_opened',
            'total_clicked', 'total_reported', 'total_credentials_entered',
            'sent_at', 'completed_at', 'created_at'
        ]

    def get_target_count(self, obj):
        """Get the number of target employees."""
        if obj.target_all_employees:
            return obj.company.users.filter(role='EMPLOYEE', is_active=True).count()
        return obj.target_employees.count()


class SimulationCampaignDetailSerializer(serializers.ModelSerializer):
    """Serializer for SimulationCampaign detail view with full information."""

    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_details = SimulationTemplateListSerializer(source='template', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_employees_list = EmployeeSimpleSerializer(source='target_employees', many=True, read_only=True)
    open_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    click_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    report_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    compromise_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    target_count = serializers.SerializerMethodField()

    class Meta:
        model = SimulationCampaign
        fields = [
            'id', 'name', 'name_ar', 'description', 'description_ar',
            'company', 'company_name', 'created_by', 'created_by_name',
            'template', 'template_name', 'template_details',
            'status', 'status_display', 'send_date', 'end_date',
            'target_all_employees', 'target_employees_list', 'target_count',
            'track_email_opens', 'track_link_clicks', 'track_credentials',
            'notify_on_click', 'notify_on_credential_entry',
            'total_sent', 'total_delivered', 'total_opened', 'total_clicked',
            'total_reported', 'total_credentials_entered',
            'open_rate', 'click_rate', 'report_rate', 'compromise_rate',
            'sent_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_sent', 'total_delivered', 'total_opened',
            'total_clicked', 'total_reported', 'total_credentials_entered',
            'sent_at', 'completed_at', 'created_at', 'updated_at'
        ]

    def get_target_count(self, obj):
        """Get the number of target employees."""
        if obj.target_all_employees:
            return obj.company.users.filter(role='EMPLOYEE', is_active=True).count()
        return obj.target_employees.count()


class SimulationCampaignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new SimulationCampaign."""

    target_employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of employee user IDs to target"
    )

    class Meta:
        model = SimulationCampaign
        fields = [
            'id', 'name', 'name_ar', 'description', 'description_ar', 'company',
            'template', 'status', 'send_date', 'end_date',
            'target_all_employees', 'target_employee_ids',
            'track_email_opens', 'track_link_clicks', 'track_credentials',
            'notify_on_click', 'notify_on_credential_entry'
        ]
        read_only_fields = ['id']

    def validate_template(self, value):
        """Validate template belongs to the user's company or is public."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            # Template must be public, global (no company), or belong to user's company
            if value.company and value.company != user.company and not value.is_public:
                raise serializers.ValidationError(
                    "Template must be public or belong to your company."
                )
        return value

    def validate_target_employee_ids(self, value):
        """Validate that all employee IDs exist and are employees."""
        if value:
            employees = User.objects.filter(id__in=value, role='EMPLOYEE', is_active=True)
            if employees.count() != len(value):
                raise serializers.ValidationError(
                    "Some employee IDs are invalid or not active employees."
                )
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        target_all = attrs.get('target_all_employees', False)
        target_ids = attrs.get('target_employee_ids', [])

        if not target_all and not target_ids:
            raise serializers.ValidationError({
                'target_employee_ids': 'You must either target all employees or provide specific employee IDs.'
            })

        send_date = attrs.get('send_date')
        end_date = attrs.get('end_date')

        if send_date and end_date:
            if end_date <= send_date:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after send date.'
                })

        if send_date and send_date < timezone.now():
            raise serializers.ValidationError({
                'send_date': 'Send date cannot be in the past.'
            })

        return attrs

    def create(self, validated_data):
        """Create campaign and associate target employees."""
        target_employee_ids = validated_data.pop('target_employee_ids', [])
        validated_data['created_by'] = self.context['request'].user

        campaign = super().create(validated_data)

        # Add target employees
        if target_employee_ids:
            employees = User.objects.filter(id__in=target_employee_ids)
            campaign.target_employees.set(employees)

        return campaign

    def update(self, instance, validated_data):
        """Update campaign and target employees."""
        target_employee_ids = validated_data.pop('target_employee_ids', None)

        # Prevent updating certain fields after campaign is sent
        if instance.status in ['IN_PROGRESS', 'COMPLETED']:
            protected_fields = ['template', 'target_all_employees', 'company']
            for field in protected_fields:
                if field in validated_data:
                    raise serializers.ValidationError({
                        field: f"Cannot modify {field} after campaign has been sent."
                    })

        campaign = super().update(instance, validated_data)

        # Update target employees if provided
        if target_employee_ids is not None:
            employees = User.objects.filter(id__in=target_employee_ids)
            campaign.target_employees.set(employees)

        return campaign


# =============================================================================
# EmailSimulation Serializers
# =============================================================================

class EmailSimulationListSerializer(serializers.ModelSerializer):
    """Serializer for EmailSimulation list view."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_compromised = serializers.BooleanField(read_only=True)

    class Meta:
        model = EmailSimulation
        fields = [
            'id', 'campaign', 'campaign_name', 'employee', 'employee_name',
            'employee_email', 'recipient_email', 'status', 'status_display',
            'was_opened', 'was_clicked', 'was_reported', 'credentials_entered',
            'is_compromised', 'sent_at', 'first_opened_at', 'clicked_at',
            'reported_at', 'created_at'
        ]
        read_only_fields = ['id', 'tracking_token', 'link_token', 'created_at']


class EmailSimulationDetailSerializer(serializers.ModelSerializer):
    """Serializer for EmailSimulation detail view."""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_compromised = serializers.BooleanField(read_only=True)
    time_to_open = serializers.SerializerMethodField()
    time_to_click = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()

    class Meta:
        model = EmailSimulation
        fields = [
            'id', 'campaign', 'campaign_name', 'employee', 'employee_name',
            'employee_email', 'recipient_email', 'status', 'status_display',
            'was_opened', 'was_clicked', 'was_reported', 'credentials_entered',
            'is_compromised', 'sent_at', 'delivered_at', 'first_opened_at',
            'clicked_at', 'reported_at', 'credentials_entered_at',
            'time_to_open', 'time_to_click', 'ip_address', 'user_agent',
            'events', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tracking_token', 'link_token', 'created_at', 'updated_at']

    def get_time_to_open(self, obj):
        """Return time to open in seconds."""
        time_to_open = obj.time_to_open
        if time_to_open:
            return time_to_open.total_seconds()
        return None

    def get_time_to_click(self, obj):
        """Return time to click in seconds."""
        time_to_click = obj.time_to_click
        if time_to_click:
            return time_to_click.total_seconds()
        return None

    def get_events(self, obj):
        """Return list of tracking events for this simulation."""
        events = obj.tracking_events.all().order_by('created_at')
        return TrackingEventListSerializer(events, many=True).data


# =============================================================================
# TrackingEvent Serializers
# =============================================================================

class TrackingEventListSerializer(serializers.ModelSerializer):
    """Serializer for TrackingEvent list view."""

    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)

    class Meta:
        model = TrackingEvent
        fields = [
            'id', 'email_simulation', 'campaign', 'employee', 'employee_name',
            'employee_email', 'event_type', 'event_type_display',
            'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TrackingEventDetailSerializer(serializers.ModelSerializer):
    """Serializer for TrackingEvent detail view."""

    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)

    class Meta:
        model = TrackingEvent
        fields = [
            'id', 'email_simulation', 'campaign', 'campaign_name',
            'employee', 'employee_name', 'employee_email',
            'event_type', 'event_type_display', 'event_data',
            'ip_address', 'user_agent', 'geolocation', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# =============================================================================
# Analytics & Results Serializers
# =============================================================================

class CampaignAnalyticsSerializer(serializers.Serializer):
    """Serializer for campaign analytics endpoint."""

    campaign_id = serializers.IntegerField()
    campaign_name = serializers.CharField()
    status = serializers.CharField()
    template_name = serializers.CharField()
    attack_vector = serializers.CharField()
    difficulty = serializers.CharField()

    # Counts
    total_targeted = serializers.IntegerField()
    total_sent = serializers.IntegerField()
    total_delivered = serializers.IntegerField()
    total_opened = serializers.IntegerField()
    total_clicked = serializers.IntegerField()
    total_reported = serializers.IntegerField()
    total_credentials_entered = serializers.IntegerField()

    # Rates
    delivery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    open_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    click_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    report_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    compromise_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Timing
    avg_time_to_open = serializers.FloatField(allow_null=True)
    avg_time_to_click = serializers.FloatField(allow_null=True)

    # Dates
    send_date = serializers.DateTimeField(allow_null=True)
    sent_at = serializers.DateTimeField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)


class EmployeeSimulationResultSerializer(serializers.Serializer):
    """Serializer for individual employee simulation results."""

    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    employee_email = serializers.EmailField()

    # Status
    email_status = serializers.CharField()
    was_opened = serializers.BooleanField()
    was_clicked = serializers.BooleanField()
    was_reported = serializers.BooleanField()
    credentials_entered = serializers.BooleanField()
    is_compromised = serializers.BooleanField()

    # Timing
    sent_at = serializers.DateTimeField(allow_null=True)
    first_opened_at = serializers.DateTimeField(allow_null=True)
    clicked_at = serializers.DateTimeField(allow_null=True)
    reported_at = serializers.DateTimeField(allow_null=True)
    time_to_open_seconds = serializers.FloatField(allow_null=True)
    time_to_click_seconds = serializers.FloatField(allow_null=True)

    # Risk assessment
    risk_level = serializers.CharField()


class SendCampaignSerializer(serializers.Serializer):
    """Serializer for sending a simulation campaign."""

    send_immediately = serializers.BooleanField(
        default=True,
        help_text="If True, sends immediately. If False, uses campaign's scheduled send_date."
    )

    def validate(self, attrs):
        """Validate campaign can be sent."""
        campaign = self.context.get('campaign')
        if campaign:
            if campaign.status not in ['DRAFT', 'SCHEDULED']:
                raise serializers.ValidationError(
                    f"Campaign cannot be sent. Current status: {campaign.status}"
                )

            if not attrs.get('send_immediately') and not campaign.send_date:
                raise serializers.ValidationError(
                    "Campaign has no scheduled send_date. Either set send_immediately=True "
                    "or update the campaign's send_date first."
                )

        return attrs


class ReportPhishingSerializer(serializers.Serializer):
    """Serializer for employees reporting a phishing email."""

    link_token = serializers.CharField(
        help_text="The unique link token from the phishing email"
    )
    reason = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Optional reason for reporting"
    )
