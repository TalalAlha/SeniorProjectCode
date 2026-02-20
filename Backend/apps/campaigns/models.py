from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Campaign(models.Model):
    """
    Campaign model for interactive quiz campaigns with AI-generated phishing emails.

    Each campaign is created by a company admin and contains a mix of phishing
    and legitimate emails for employees to identify.
    """

    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('ACTIVE', _('Active')),
        ('SCHEDULED', _('Scheduled')),
        ('COMPLETED', _('Completed')),
        ('ARCHIVED', _('Archived')),
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
        related_name='campaigns',
        verbose_name=_('company')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_campaigns',
        verbose_name=_('created by')
    )

    # Campaign Configuration
    num_emails = models.PositiveIntegerField(
        _('number of emails'),
        validators=[MinValueValidator(5), MaxValueValidator(50)],
        default=10,
        help_text=_('Total number of emails in the quiz (5-50)')
    )
    phishing_ratio = models.DecimalField(
        _('phishing email ratio'),
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0.2), MaxValueValidator(0.8)],
        default=0.5,
        help_text=_('Ratio of phishing emails (0.2-0.8, e.g., 0.5 = 50%)')
    )

    # Status and Dates
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    start_date = models.DateTimeField(_('start date'), null=True, blank=True)
    end_date = models.DateTimeField(_('end date'), null=True, blank=True)

    # Statistics
    total_participants = models.PositiveIntegerField(_('total participants'), default=0)
    completed_participants = models.PositiveIntegerField(_('completed participants'), default=0)
    average_score = models.DecimalField(
        _('average score'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', 'start_date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    @property
    def num_phishing_emails(self):
        """Calculate number of phishing emails based on ratio."""
        return int(self.num_emails * float(self.phishing_ratio))

    @property
    def num_legitimate_emails(self):
        """Calculate number of legitimate emails."""
        return self.num_emails - self.num_phishing_emails

    @property
    def is_active(self):
        """Check if campaign is currently active."""
        from django.utils import timezone
        if self.status != 'ACTIVE':
            return False
        if self.start_date and self.start_date > timezone.now():
            return False
        if self.end_date and self.end_date < timezone.now():
            return False
        return True

    @property
    def completion_rate(self):
        """Calculate campaign completion rate."""
        if self.total_participants == 0:
            return 0
        return (self.completed_participants / self.total_participants) * 100


class Quiz(models.Model):
    """
    Quiz model representing an individual employee's quiz instance.

    Each employee gets their own quiz instance with a randomized set of emails
    from the campaign's email pool.
    """

    STATUS_CHOICES = [
        ('NOT_STARTED', _('Not Started')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
    ]

    # Relationships
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name=_('campaign')
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name=_('employee')
    )

    # Quiz State
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_STARTED'
    )
    current_question_index = models.PositiveIntegerField(
        _('current question index'),
        default=0
    )

    # Timestamps
    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('quiz')
        verbose_name_plural = _('quizzes')
        ordering = ['-created_at']
        unique_together = ['campaign', 'employee']
        indexes = [
            models.Index(fields=['campaign', 'employee']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Quiz: {self.employee.email} - {self.campaign.name}"

    @property
    def time_taken(self):
        """Calculate time taken to complete the quiz."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def total_questions(self):
        """Get total number of questions in this quiz."""
        return self.questions.count()

    @property
    def answered_questions(self):
        """Get number of answered questions."""
        return self.questions.filter(answer__isnull=False).count()

    @property
    def progress_percentage(self):
        """Calculate quiz progress percentage."""
        total = self.total_questions
        if total == 0:
            return 0
        return (self.answered_questions / total) * 100


class QuizResult(models.Model):
    """
    QuizResult model to store the final results of a completed quiz.

    Stores the employee's performance metrics including score, accuracy,
    and time taken.
    """

    # Relationships
    quiz = models.OneToOneField(
        Quiz,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name=_('quiz')
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_results',
        verbose_name=_('employee')
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_('campaign')
    )

    # Score Metrics
    total_questions = models.PositiveIntegerField(_('total questions'))
    correct_answers = models.PositiveIntegerField(_('correct answers'), default=0)
    incorrect_answers = models.PositiveIntegerField(_('incorrect answers'), default=0)
    score = models.DecimalField(
        _('score'),
        max_digits=5,
        decimal_places=2,
        help_text=_('Score as percentage (0-100)')
    )

    # Phishing Detection Metrics
    phishing_emails_identified = models.PositiveIntegerField(
        _('phishing emails correctly identified'),
        default=0
    )
    phishing_emails_missed = models.PositiveIntegerField(
        _('phishing emails missed'),
        default=0
    )
    false_positives = models.PositiveIntegerField(
        _('legitimate emails marked as phishing'),
        default=0
    )

    # Time Metrics
    time_taken_seconds = models.PositiveIntegerField(
    _('time taken (seconds)'),
    null=True,
    blank=True,
    default=0,
    help_text=_('Total time taken to complete the quiz in seconds')
)
    average_time_per_question = models.DecimalField(
    _('average time per question'),
    max_digits=6,
    decimal_places=2,
    null=True,
    blank=True,
    default=0.0,
    help_text=_('Average time per question in seconds')
)

    # Risk Assessment
    risk_level = models.CharField(
        _('risk level'),
        max_length=20,
        choices=[
            ('LOW', _('Low Risk')),
            ('MEDIUM', _('Medium Risk')),
            ('HIGH', _('High Risk')),
            ('CRITICAL', _('Critical Risk')),
        ],
        default='MEDIUM'
    )

    # Timestamps
    completed_at = models.DateTimeField(_('completed at'), auto_now_add=True)

    class Meta:
        verbose_name = _('quiz result')
        verbose_name_plural = _('quiz results')
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['employee', 'campaign']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['score']),
        ]

    def __str__(self):
        return f"Result: {self.employee.email} - {self.campaign.name} - {self.score}%"

    @property
    def accuracy(self):
        """Calculate accuracy percentage."""
        if self.total_questions == 0:
            return 0
        return (self.correct_answers / self.total_questions) * 100

    @property
    def phishing_detection_rate(self):
        """Calculate phishing detection accuracy."""
        total_phishing = self.phishing_emails_identified + self.phishing_emails_missed
        if total_phishing == 0:
            return 0
        return (self.phishing_emails_identified / total_phishing) * 100

    @property
    def passed(self):
        """Check if employee passed the quiz (score >= 70%)."""
        return self.score >= 70
