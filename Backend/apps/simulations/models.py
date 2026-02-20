from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator
import uuid
import secrets


class SimulationTemplate(models.Model):
    """
    Pre-built phishing email templates for live simulations.

    These templates are reusable across multiple simulation campaigns
    and represent common phishing attack vectors.
    """

    ATTACK_VECTOR_CHOICES = [
        ('LINK_MANIPULATION', _('Malicious Link')),
        ('CREDENTIAL_HARVESTING', _('Fake Login Page')),
        ('ATTACHMENT_MALWARE', _('Malicious Attachment')),
        ('URGENCY_SCAM', _('Urgency/Fear Tactics')),
        ('AUTHORITY_IMPERSONATION', _('Authority Figure Impersonation')),
        ('PRIZE_LOTTERY', _('Prize/Lottery Scam')),
        ('BUSINESS_EMAIL_COMPROMISE', _('Business Email Compromise')),
    ]

    DIFFICULTY_CHOICES = [
        ('EASY', _('Easy - Obvious indicators')),
        ('MEDIUM', _('Medium - Some subtle indicators')),
        ('HARD', _('Hard - Very convincing')),
        ('EXPERT', _('Expert - Nearly identical to legitimate')),
    ]

    # Basic Information
    name = models.CharField(_('template name'), max_length=255)
    name_ar = models.CharField(_('template name (Arabic)'), max_length=255, blank=True)
    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    # Company (null = available to all companies, otherwise company-specific)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='simulation_templates',
        null=True,
        blank=True,
        verbose_name=_('company'),
        help_text=_('Leave empty for global templates available to all companies')
    )

    # Email Content
    sender_name = models.CharField(_('sender name'), max_length=255)
    sender_email = models.EmailField(_('sender email'))
    reply_to_email = models.EmailField(_('reply-to email'), blank=True)
    subject = models.CharField(_('email subject'), max_length=500)
    body_html = models.TextField(_('email body (HTML)'))
    body_plain = models.TextField(_('email body (Plain Text)'), blank=True)

    # Attack Configuration
    attack_vector = models.CharField(
        _('attack vector'),
        max_length=50,
        choices=ATTACK_VECTOR_CHOICES
    )
    difficulty = models.CharField(
        _('difficulty level'),
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='MEDIUM'
    )

    # Tracking Elements
    requires_landing_page = models.BooleanField(
        _('requires landing page'),
        default=True,
        help_text=_('If true, clicked links redirect to educational landing page')
    )
    landing_page_title = models.CharField(
        _('landing page title'),
        max_length=255,
        blank=True
    )
    landing_page_message = models.TextField(
        _('landing page message'),
        blank=True,
        help_text=_('Educational message shown when employee clicks the phishing link')
    )
    landing_page_message_ar = models.TextField(
        _('landing page message (Arabic)'),
        blank=True
    )

    # Red Flags (for educational purposes)
    red_flags = models.JSONField(
        _('phishing red flags'),
        default=list,
        help_text=_('List of indicators that reveal this is a phishing attempt')
    )

    # Metadata
    is_active = models.BooleanField(_('active'), default=True)
    is_public = models.BooleanField(
        _('public template'),
        default=False,
        help_text=_('If true, available to all companies in the platform')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_simulation_templates',
        verbose_name=_('created by')
    )
    language = models.CharField(
        _('language'),
        max_length=2,
        choices=[('en', 'English'), ('ar', 'Arabic')],
        default='en'
    )

    # Usage Statistics
    times_used = models.PositiveIntegerField(_('times used'), default=0)
    average_click_rate = models.DecimalField(
        _('average click rate'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Average percentage of employees who click the link')
    )

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('simulation template')
        verbose_name_plural = _('simulation templates')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['attack_vector', 'difficulty']),
            models.Index(fields=['is_active', 'is_public']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_attack_vector_display()})"


class SimulationCampaign(models.Model):
    """
    Live simulation campaign where phishing emails are sent to employee inboxes.

    Unlike quiz campaigns, these send actual emails that employees receive
    and tracks their behavior (opens, clicks, credential entry).
    """

    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('SCHEDULED', _('Scheduled')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('PAUSED', _('Paused')),
        ('CANCELLED', _('Cancelled')),
    ]

    # Basic Information
    name = models.CharField(_('campaign name'), max_length=255)
    name_ar = models.CharField(_('campaign name (Arabic)'), max_length=255, blank=True)
    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    # Relationships
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='simulation_campaigns',
        verbose_name=_('company')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_simulation_campaigns',
        verbose_name=_('created by')
    )

    # Template
    template = models.ForeignKey(
        SimulationTemplate,
        on_delete=models.PROTECT,
        related_name='campaigns',
        verbose_name=_('email template')
    )

    # Campaign Configuration
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    send_date = models.DateTimeField(
        _('scheduled send date'),
        null=True,
        blank=True,
        help_text=_('When to send the simulation emails')
    )
    end_date = models.DateTimeField(
        _('end date'),
        null=True,
        blank=True,
        help_text=_('When to stop tracking and close the simulation')
    )

    # Target Employees
    target_all_employees = models.BooleanField(
        _('target all employees'),
        default=False,
        help_text=_('If true, send to all employees in the company')
    )
    target_employees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='targeted_in_simulations',
        verbose_name=_('target employees'),
        blank=True,
        limit_choices_to={'role': 'EMPLOYEE'}
    )

    # Tracking Configuration
    track_email_opens = models.BooleanField(_('track email opens'), default=True)
    track_link_clicks = models.BooleanField(_('track link clicks'), default=True)
    track_credentials = models.BooleanField(
        _('track credential entry'),
        default=False,
        help_text=_('If true, landing page includes fake login form')
    )

    # Notification Settings
    notify_on_click = models.BooleanField(
        _('notify admin on click'),
        default=False,
        help_text=_('Send notification to admin when employee clicks link')
    )
    notify_on_credential_entry = models.BooleanField(
        _('notify admin on credential entry'),
        default=True
    )

    # Statistics
    total_sent = models.PositiveIntegerField(_('total emails sent'), default=0)
    total_delivered = models.PositiveIntegerField(_('total delivered'), default=0)
    total_opened = models.PositiveIntegerField(_('total opened'), default=0)
    total_clicked = models.PositiveIntegerField(_('total clicked'), default=0)
    total_reported = models.PositiveIntegerField(
        _('total reported'),
        default=0,
        help_text=_('Number of employees who reported the email as phishing')
    )
    total_credentials_entered = models.PositiveIntegerField(
        _('credentials entered'),
        default=0
    )

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)

    class Meta:
        verbose_name = _('simulation campaign')
        verbose_name_plural = _('simulation campaigns')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', 'send_date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    @property
    def _effective_sent_count(self):
        """Get effective sent count, falling back to email simulation count."""
        if self.total_sent > 0:
            return self.total_sent
        # Fallback: count email simulations that aren't pending/failed
        count = self.email_simulations.exclude(status__in=['PENDING', 'FAILED']).count()
        if count > 0:
            return count
        # Last resort: count all email simulations (package was generated)
        return self.email_simulations.count()

    @property
    def open_rate(self):
        """Calculate email open rate percentage."""
        sent = self._effective_sent_count
        if sent == 0:
            return 0
        return (self.total_opened / sent) * 100

    @property
    def click_rate(self):
        """Calculate link click rate percentage."""
        sent = self._effective_sent_count
        if sent == 0:
            return 0
        return (self.total_clicked / sent) * 100

    @property
    def report_rate(self):
        """Calculate report rate percentage (employees who reported it)."""
        sent = self._effective_sent_count
        if sent == 0:
            return 0
        return (self.total_reported / sent) * 100

    @property
    def compromise_rate(self):
        """Calculate compromise rate (clicked or entered credentials)."""
        sent = self._effective_sent_count
        if sent == 0:
            return 0
        compromised = max(self.total_clicked, self.total_credentials_entered)
        return (compromised / sent) * 100

    @property
    def is_active(self):
        """Check if simulation is currently active."""
        return self.status == 'IN_PROGRESS'


class EmailSimulation(models.Model):
    """
    Individual phishing email sent to a specific employee.

    Each employee gets a unique instance with unique tracking tokens
    to monitor their specific behavior.
    """

    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('SENT', _('Sent')),
        ('DELIVERED', _('Delivered')),
        ('BOUNCED', _('Bounced')),
        ('FAILED', _('Failed')),
    ]

    # Relationships
    campaign = models.ForeignKey(
        SimulationCampaign,
        on_delete=models.CASCADE,
        related_name='email_simulations',
        verbose_name=_('campaign')
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_simulations',
        verbose_name=_('employee')
    )

    # Tracking Tokens (UUID for security)
    tracking_token = models.UUIDField(
        _('tracking token'),
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text=_('Unique token for tracking this specific email')
    )
    link_token = models.CharField(
        _('link token'),
        max_length=64,
        unique=True,
        editable=False,
        help_text=_('Unique token for the phishing link')
    )

    # Email Details
    recipient_email = models.EmailField(_('recipient email'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Tracking Flags
    was_opened = models.BooleanField(_('email opened'), default=False)
    was_clicked = models.BooleanField(_('link clicked'), default=False)
    was_reported = models.BooleanField(
        _('reported as phishing'),
        default=False,
        help_text=_('Employee reported this email as phishing (good!)')
    )
    credentials_entered = models.BooleanField(
        _('credentials entered'),
        default=False
    )

    # Timing Metrics
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    first_opened_at = models.DateTimeField(_('first opened at'), null=True, blank=True)
    clicked_at = models.DateTimeField(_('clicked at'), null=True, blank=True)
    reported_at = models.DateTimeField(_('reported at'), null=True, blank=True)
    credentials_entered_at = models.DateTimeField(_('credentials entered at'), null=True, blank=True)

    # Additional Data
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True,
        help_text=_('IP address from which the link was clicked')
    )
    user_agent = models.TextField(
        _('user agent'),
        blank=True,
        help_text=_('Browser/device information when link was clicked')
    )

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('email simulation')
        verbose_name_plural = _('email simulations')
        ordering = ['-created_at']
        unique_together = ['campaign', 'employee']
        indexes = [
            models.Index(fields=['campaign', 'employee']),
            models.Index(fields=['tracking_token']),
            models.Index(fields=['link_token']),
            models.Index(fields=['was_clicked', 'credentials_entered']),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.campaign.name}"

    def save(self, *args, **kwargs):
        """Generate unique link token on creation."""
        if not self.link_token:
            self.link_token = secrets.token_urlsafe(32)
        if not self.recipient_email:
            self.recipient_email = self.employee.email
        super().save(*args, **kwargs)

    @property
    def time_to_open(self):
        """Calculate time from sent to first open."""
        if self.sent_at and self.first_opened_at:
            return self.first_opened_at - self.sent_at
        return None

    @property
    def time_to_click(self):
        """Calculate time from sent to click."""
        if self.sent_at and self.clicked_at:
            return self.clicked_at - self.sent_at
        return None

    @property
    def is_compromised(self):
        """Check if employee was compromised (clicked or entered credentials)."""
        return self.was_clicked or self.credentials_entered

    @property
    def tracking_pixel_url(self):
        """Generate tracking pixel URL for email opens."""
        from django.urls import reverse
        return reverse('simulations:tracking-pixel', kwargs={'token': str(self.tracking_token)})

    @property
    def phishing_link_url(self):
        """Generate unique phishing link URL."""
        from django.urls import reverse
        return reverse('simulations:phishing-link', kwargs={'token': self.link_token})


class TrackingEvent(models.Model):
    """
    Event log for tracking employee interactions with simulation emails.

    Records all actions: opens, clicks, credential entries, reports, etc.
    """

    EVENT_TYPE_CHOICES = [
        ('EMAIL_SENT', _('Email Sent')),
        ('EMAIL_DELIVERED', _('Email Delivered')),
        ('EMAIL_BOUNCED', _('Email Bounced')),
        ('EMAIL_OPENED', _('Email Opened')),
        ('LINK_CLICKED', _('Link Clicked')),
        ('CREDENTIALS_ENTERED', _('Credentials Entered')),
        ('EMAIL_REPORTED', _('Email Reported as Phishing')),
        ('LANDING_PAGE_VIEWED', _('Landing Page Viewed')),
    ]

    # Relationships
    email_simulation = models.ForeignKey(
        EmailSimulation,
        on_delete=models.CASCADE,
        related_name='tracking_events',
        verbose_name=_('email simulation')
    )
    campaign = models.ForeignKey(
        SimulationCampaign,
        on_delete=models.CASCADE,
        related_name='tracking_events',
        verbose_name=_('campaign')
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simulation_events',
        verbose_name=_('employee')
    )

    # Event Details
    event_type = models.CharField(
        _('event type'),
        max_length=30,
        choices=EVENT_TYPE_CHOICES
    )
    event_data = models.JSONField(
        _('event data'),
        default=dict,
        blank=True,
        help_text=_('Additional data about the event (e.g., form data, click location)')
    )

    # Technical Details
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    geolocation = models.JSONField(
        _('geolocation'),
        default=dict,
        blank=True,
        help_text=_('Geolocation data from IP address')
    )

    # Timestamp
    created_at = models.DateTimeField(_('timestamp'), auto_now_add=True)

    class Meta:
        verbose_name = _('tracking event')
        verbose_name_plural = _('tracking events')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email_simulation', 'event_type']),
            models.Index(fields=['campaign', 'event_type']),
            models.Index(fields=['employee', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.employee.email} - {self.created_at}"

    def save(self, *args, **kwargs):
        """Update related EmailSimulation and Campaign statistics on save."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self._update_simulation_stats()
            self._update_campaign_stats()

    def _update_simulation_stats(self):
        """Update EmailSimulation tracking flags based on event type."""
        sim = self.email_simulation
        updated = False

        # If we're receiving tracking events, the email must have been sent.
        # Mark it as SENT if still PENDING (handles manual sending workflow).
        if sim.status == 'PENDING' and self.event_type in (
            'EMAIL_OPENED', 'LINK_CLICKED', 'CREDENTIALS_ENTERED', 'EMAIL_REPORTED'
        ):
            sim.status = 'SENT'
            if not sim.sent_at:
                sim.sent_at = self.created_at
            updated = True

        if self.event_type == 'EMAIL_OPENED' and not sim.was_opened:
            sim.was_opened = True
            sim.first_opened_at = self.created_at
            updated = True

        elif self.event_type == 'LINK_CLICKED' and not sim.was_clicked:
            sim.was_clicked = True
            sim.clicked_at = self.created_at
            sim.ip_address = self.ip_address
            sim.user_agent = self.user_agent
            updated = True

        elif self.event_type == 'CREDENTIALS_ENTERED' and not sim.credentials_entered:
            sim.credentials_entered = True
            sim.credentials_entered_at = self.created_at
            updated = True

        elif self.event_type == 'EMAIL_REPORTED' and not sim.was_reported:
            sim.was_reported = True
            sim.reported_at = self.created_at
            updated = True

        if updated:
            sim.save()

    def _update_campaign_stats(self):
        """Update SimulationCampaign aggregate statistics."""
        campaign = self.campaign

        # Always recount total_sent from actual EmailSimulation statuses
        campaign.total_sent = campaign.email_simulations.exclude(
            status__in=['PENDING', 'FAILED']
        ).count()

        if self.event_type == 'EMAIL_OPENED':
            campaign.total_opened = campaign.email_simulations.filter(was_opened=True).count()

        elif self.event_type == 'LINK_CLICKED':
            campaign.total_clicked = campaign.email_simulations.filter(was_clicked=True).count()

        elif self.event_type == 'CREDENTIALS_ENTERED':
            campaign.total_credentials_entered = campaign.email_simulations.filter(credentials_entered=True).count()

        elif self.event_type == 'EMAIL_REPORTED':
            campaign.total_reported = campaign.email_simulations.filter(was_reported=True).count()

        # Update campaign status to IN_PROGRESS if still in DRAFT/SCHEDULED
        if campaign.status in ('DRAFT', 'SCHEDULED') and campaign.total_sent > 0:
            campaign.status = 'IN_PROGRESS'
            if not campaign.sent_at:
                campaign.sent_at = self.created_at

        campaign.save()
