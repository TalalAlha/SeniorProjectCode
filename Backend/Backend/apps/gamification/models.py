"""
Gamification App Models
=======================
Badges, Points, and Leaderboard system for PhishAware platform.

Models:
- Badge: Badge definitions with criteria
- EmployeeBadge: Tracks badges awarded to employees
- PointsTransaction: Audit trail for points earned/spent
- EmployeePoints: Aggregate points for leaderboard rankings
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class Badge(models.Model):
    """
    Badge definitions with criteria for automatic awarding.

    Badge Types:
    - FIRST_QUIZ_COMPLETED: First quiz taken
    - PERFECT_QUIZ_SCORE: 100% on any quiz
    - PHISH_SLAYER: Reported 5+ phishing emails
    - TRAINING_CHAMPION: Completed all assigned trainings
    - SECURITY_AWARE: LOW risk score maintained for 30 days
    - QUICK_LEARNER: Passed training on first attempt
    """

    BADGE_TYPE_CHOICES = [
        ('FIRST_QUIZ_COMPLETED', _('First Quiz Completed')),
        ('PERFECT_QUIZ_SCORE', _('Perfect Quiz Score')),
        ('PHISH_SLAYER', _('Phish Slayer')),
        ('TRAINING_CHAMPION', _('Training Champion')),
        ('SECURITY_AWARE', _('Security Aware')),
        ('QUICK_LEARNER', _('Quick Learner')),
        ('SIMULATION_SURVIVOR', _('Simulation Survivor')),
        ('STREAK_MASTER', _('Streak Master')),
        ('TOP_REPORTER', _('Top Reporter')),
    ]

    RARITY_CHOICES = [
        ('COMMON', _('Common')),
        ('UNCOMMON', _('Uncommon')),
        ('RARE', _('Rare')),
        ('EPIC', _('Epic')),
        ('LEGENDARY', _('Legendary')),
    ]

    # Basic Information
    name = models.CharField(_('badge name'), max_length=100, unique=True)
    name_ar = models.CharField(_('badge name (Arabic)'), max_length=100, blank=True)

    badge_type = models.CharField(
        _('badge type'),
        max_length=30,
        choices=BADGE_TYPE_CHOICES,
        unique=True
    )

    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    # Visual elements
    icon = models.CharField(
        _('icon'),
        max_length=100,
        help_text=_('Icon identifier or emoji for badge display')
    )
    color = models.CharField(
        _('color'),
        max_length=7,
        default='#FFD700',
        help_text=_('Hex color code for badge display')
    )

    rarity = models.CharField(
        _('rarity'),
        max_length=20,
        choices=RARITY_CHOICES,
        default='COMMON'
    )

    # Points awarded when badge is earned
    points_awarded = models.PositiveIntegerField(
        _('points awarded'),
        default=100,
        validators=[MinValueValidator(0)],
        help_text=_('Points awarded when this badge is earned')
    )

    # Criteria (stored as JSON for flexibility)
    criteria = models.JSONField(
        _('criteria'),
        default=dict,
        blank=True,
        help_text=_('JSON criteria for badge awarding, e.g., {"quizzes_completed": 1}')
    )

    # Metadata
    is_active = models.BooleanField(_('is active'), default=True)
    is_hidden = models.BooleanField(
        _('is hidden'),
        default=False,
        help_text=_('Hidden badges are not shown until earned')
    )

    # Optional company-specific badge
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name=_('company'),
        null=True,
        blank=True,
        help_text=_('Leave empty for global badges')
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('badge')
        verbose_name_plural = _('badges')
        ordering = ['rarity', 'name']
        indexes = [
            models.Index(fields=['badge_type', 'is_active']),
            models.Index(fields=['company', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"


class EmployeeBadge(models.Model):
    """
    Through model tracking badge awards to employees.
    Records when and why a badge was awarded.
    """

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_badges',
        verbose_name=_('employee')
    )

    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='employee_badges',
        verbose_name=_('badge')
    )

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='employee_badges',
        verbose_name=_('company')
    )

    # Award tracking
    awarded_at = models.DateTimeField(_('awarded at'), auto_now_add=True)

    # What triggered this badge award
    source_type = models.CharField(
        _('source type'),
        max_length=50,
        blank=True,
        help_text=_('Model that triggered this award (QuizResult, TrackingEvent, etc.)')
    )
    source_id = models.PositiveIntegerField(
        _('source ID'),
        null=True,
        blank=True
    )

    # Points awarded (denormalized for performance)
    points_awarded = models.PositiveIntegerField(
        _('points awarded'),
        default=0
    )

    # Notification tracking
    is_notified = models.BooleanField(
        _('user notified'),
        default=False,
        help_text=_('Whether user has been notified of this badge')
    )
    notified_at = models.DateTimeField(_('notified at'), null=True, blank=True)

    class Meta:
        verbose_name = _('employee badge')
        verbose_name_plural = _('employee badges')
        ordering = ['-awarded_at']
        unique_together = ['employee', 'badge']
        indexes = [
            models.Index(fields=['employee', '-awarded_at']),
            models.Index(fields=['company', '-awarded_at']),
            models.Index(fields=['badge', '-awarded_at']),
            models.Index(fields=['is_notified']),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.badge.name}"

    def save(self, *args, **kwargs):
        """Auto-set company and points from employee/badge."""
        if not self.company_id and self.employee_id:
            self.company = self.employee.company
        if not self.points_awarded and self.badge_id:
            self.points_awarded = self.badge.points_awarded
        super().save(*args, **kwargs)


class PointsTransaction(models.Model):
    """
    Records all points earned/spent by employees.
    Enables detailed points history and audit trail.
    """

    TRANSACTION_TYPE_CHOICES = [
        # Earning points
        ('QUIZ_COMPLETED', _('Quiz Completed')),
        ('QUIZ_PERFECT_SCORE', _('Quiz Perfect Score')),
        ('PHISHING_REPORTED', _('Phishing Email Reported')),
        ('TRAINING_COMPLETED', _('Training Completed')),
        ('TRAINING_PASSED', _('Training Passed')),
        ('BADGE_EARNED', _('Badge Earned')),
        ('FIRST_ATTEMPT_PASS', _('First Attempt Pass')),
        ('STREAK_BONUS', _('Streak Bonus')),
        # Admin adjustments
        ('ADMIN_ADJUSTMENT', _('Admin Adjustment')),
        ('BONUS', _('Bonus Award')),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_transactions',
        verbose_name=_('employee')
    )

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='points_transactions',
        verbose_name=_('company')
    )

    transaction_type = models.CharField(
        _('transaction type'),
        max_length=30,
        choices=TRANSACTION_TYPE_CHOICES
    )

    points = models.IntegerField(
        _('points'),
        help_text=_('Positive for earned, negative for deductions')
    )

    # Running total after this transaction
    balance_after = models.PositiveIntegerField(
        _('balance after'),
        default=0
    )

    description = models.CharField(
        _('description'),
        max_length=255,
        blank=True
    )
    description_ar = models.CharField(
        _('description (Arabic)'),
        max_length=255,
        blank=True
    )

    # Breakdown metadata (e.g. quiz score, base_points, performance_bonus)
    metadata = models.JSONField(
        _('metadata'),
        default=dict,
        blank=True,
        help_text=_('Stores breakdown details, e.g. {"quiz_score": 80, "base_points": 50, "performance_bonus": 40}')
    )

    # Source tracking
    source_type = models.CharField(
        _('source type'),
        max_length=50,
        blank=True
    )
    source_id = models.PositiveIntegerField(
        _('source ID'),
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('points transaction')
        verbose_name_plural = _('points transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', '-created_at']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        sign = '+' if self.points > 0 else ''
        return f"{self.employee.email}: {sign}{self.points} ({self.transaction_type})"

    def save(self, *args, **kwargs):
        """Auto-set company from employee."""
        if not self.company_id and self.employee_id:
            self.company = self.employee.company
        super().save(*args, **kwargs)


class EmployeePoints(models.Model):
    """
    Aggregate model for employee total points.
    Denormalized for performance on leaderboard queries.
    """

    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gamification_points',
        verbose_name=_('employee')
    )

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='employee_points',
        verbose_name=_('company')
    )

    # Total points (updated on each transaction)
    total_points = models.PositiveIntegerField(
        _('total points'),
        default=0
    )

    # Period-specific points for leaderboard
    weekly_points = models.PositiveIntegerField(
        _('weekly points'),
        default=0,
        help_text=_('Points earned in current week')
    )
    monthly_points = models.PositiveIntegerField(
        _('monthly points'),
        default=0,
        help_text=_('Points earned in current month')
    )

    # Badge count (denormalized)
    badge_count = models.PositiveIntegerField(
        _('badge count'),
        default=0
    )

    # Timestamps for period tracking
    week_start = models.DateField(
        _('week start'),
        null=True,
        blank=True
    )
    month_start = models.DateField(
        _('month start'),
        null=True,
        blank=True
    )

    # Streak tracking
    current_streak_days = models.PositiveIntegerField(
        _('current streak (days)'),
        default=0
    )
    longest_streak_days = models.PositiveIntegerField(
        _('longest streak (days)'),
        default=0
    )
    last_activity_date = models.DateField(
        _('last activity date'),
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('employee points')
        verbose_name_plural = _('employee points')
        ordering = ['-total_points']
        indexes = [
            models.Index(fields=['company', '-total_points']),
            models.Index(fields=['company', '-weekly_points']),
            models.Index(fields=['company', '-monthly_points']),
        ]

    def __str__(self):
        return f"{self.employee.email}: {self.total_points} points"

    def save(self, *args, **kwargs):
        """Auto-set company from employee."""
        if not self.company_id and self.employee_id:
            self.company = self.employee.company
        super().save(*args, **kwargs)
