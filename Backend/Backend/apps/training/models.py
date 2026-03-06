"""
Training App Models
===================
Risk Scoring & Remediation Engine for PhishAware platform.

Models:
- RiskScore: Current risk level per employee
- RiskScoreHistory: Track score changes over time
- TrainingModule: Training content library
- TrainingQuestion: Quiz questions for training modules
- RemediationTraining: Assigned training records
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class RiskScore(models.Model):
    """
    Current risk score for each employee.
    Score range: 0-100 (higher = more at risk)

    Risk Levels:
    - LOW: 0-30 (Green - Safe)
    - MEDIUM: 31-60 (Yellow - Needs attention)
    - HIGH: 61-80 (Orange - Requires training)
    - CRITICAL: 81-100 (Red - Immediate action needed)
    """

    RISK_LEVEL_CHOICES = [
        ('LOW', _('Low Risk')),
        ('MEDIUM', _('Medium Risk')),
        ('HIGH', _('High Risk')),
        ('CRITICAL', _('Critical Risk')),
    ]

    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='risk_score',
        verbose_name=_('employee'),
        limit_choices_to={'role': 'EMPLOYEE'}
    )

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='employee_risk_scores',
        verbose_name=_('company')
    )

    # Current score (0-100)
    score = models.IntegerField(
        _('risk score'),
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Risk score from 0 (safest) to 100 (most at risk)')
    )

    risk_level = models.CharField(
        _('risk level'),
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default='MEDIUM'
    )

    # Statistics from quizzes
    total_quizzes_taken = models.PositiveIntegerField(_('total quizzes taken'), default=0)
    total_quiz_questions = models.PositiveIntegerField(_('total quiz questions'), default=0)
    correct_quiz_answers = models.PositiveIntegerField(_('correct quiz answers'), default=0)
    phishing_emails_missed = models.PositiveIntegerField(_('phishing emails missed'), default=0)

    # Statistics from simulations
    total_simulations_received = models.PositiveIntegerField(_('total simulations received'), default=0)
    simulations_opened = models.PositiveIntegerField(_('simulations opened'), default=0)
    simulations_clicked = models.PositiveIntegerField(_('simulations clicked'), default=0)
    simulations_reported = models.PositiveIntegerField(_('simulations reported'), default=0)
    credentials_entered = models.PositiveIntegerField(_('credentials entered'), default=0)

    # Training statistics
    trainings_assigned = models.PositiveIntegerField(_('trainings assigned'), default=0)
    trainings_completed = models.PositiveIntegerField(_('trainings completed'), default=0)
    trainings_passed = models.PositiveIntegerField(_('trainings passed'), default=0)

    # Auto-remediation flag
    requires_remediation = models.BooleanField(
        _('requires remediation'),
        default=False,
        help_text=_('Auto-set when score exceeds threshold')
    )

    last_quiz_date = models.DateTimeField(_('last quiz date'), null=True, blank=True)
    last_simulation_date = models.DateTimeField(_('last simulation date'), null=True, blank=True)
    last_training_date = models.DateTimeField(_('last training date'), null=True, blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('risk score')
        verbose_name_plural = _('risk scores')
        ordering = ['-score', '-updated_at']
        indexes = [
            models.Index(fields=['company', 'risk_level']),
            models.Index(fields=['score']),
            models.Index(fields=['requires_remediation']),
        ]

    def __str__(self):
        return f"{self.employee.email} - Score: {self.score} ({self.risk_level})"

    @property
    def quiz_accuracy(self):
        """Calculate quiz accuracy percentage."""
        if self.total_quiz_questions == 0:
            return None
        return round((self.correct_quiz_answers / self.total_quiz_questions) * 100, 1)

    @property
    def simulation_click_rate(self):
        """Calculate simulation click rate percentage."""
        if self.total_simulations_received == 0:
            return None
        return round((self.simulations_clicked / self.total_simulations_received) * 100, 1)

    @property
    def training_completion_rate(self):
        """Calculate training completion rate percentage."""
        if self.trainings_assigned == 0:
            return None
        return round((self.trainings_completed / self.trainings_assigned) * 100, 1)

    @property
    def training_pass_rate(self):
        """Calculate training pass rate percentage."""
        if self.trainings_completed == 0:
            return None
        return round((self.trainings_passed / self.trainings_completed) * 100, 1)

    def calculate_risk_level(self):
        """Determine risk level based on score."""
        if self.score <= 30:
            return 'LOW'
        elif self.score <= 60:
            return 'MEDIUM'
        elif self.score <= 80:
            return 'HIGH'
        else:
            return 'CRITICAL'

    def recalculate_score(self):
        """
        Recalculate risk score based on all factors.

        Scoring Algorithm:
        - Base score: 50
        - Quiz performance: -20 to +20 based on accuracy
        - Simulation behavior: +30 for clicks, +20 for credentials
        - Reported phishing: -10 per report
        - Training completion: -15 for passed training
        """
        base_score = 50

        # Quiz performance adjustment (-20 to +20)
        if self.total_quiz_questions > 0:
            accuracy = self.correct_quiz_answers / self.total_quiz_questions
            # 100% accuracy = -20, 0% accuracy = +20
            quiz_adjustment = int((0.5 - accuracy) * 40)
        else:
            quiz_adjustment = 0

        # Missed phishing emails penalty (+5 each, max +25)
        phishing_penalty = min(self.phishing_emails_missed * 5, 25)

        # Simulation click penalty (+10 each, max +30)
        if self.total_simulations_received > 0:
            click_rate = self.simulations_clicked / self.total_simulations_received
            simulation_adjustment = int(click_rate * 30)
        else:
            simulation_adjustment = 0

        # Credentials entered penalty (+15 each, max +20)
        credential_penalty = min(self.credentials_entered * 15, 20)

        # Reported phishing bonus (-5 each, max -15)
        report_bonus = min(self.simulations_reported * 5, 15)

        # Training completion bonus (-10 per passed, max -25)
        training_bonus = min(self.trainings_passed * 10, 25)

        # Calculate final score
        new_score = (
            base_score
            + quiz_adjustment
            + phishing_penalty
            + simulation_adjustment
            + credential_penalty
            - report_bonus
            - training_bonus
        )

        # Clamp to 0-100
        self.score = max(0, min(100, new_score))
        self.risk_level = self.calculate_risk_level()

        # Set remediation flag if score > 70
        self.requires_remediation = self.score > 70

        return self.score

    def save(self, *args, **kwargs):
        """Auto-set company from employee if not set."""
        if not self.company_id and self.employee_id:
            self.company = self.employee.company

        # Ensure risk level matches score
        self.risk_level = self.calculate_risk_level()
        self.requires_remediation = self.score > 70

        super().save(*args, **kwargs)


class RiskScoreHistory(models.Model):
    """
    Track all changes to employee risk scores over time.
    Used for trend analysis and reporting.
    """

    EVENT_TYPE_CHOICES = [
        ('QUIZ_COMPLETED', _('Quiz Completed')),
        ('QUIZ_FAILED', _('Quiz Failed')),
        ('SIMULATION_OPENED', _('Simulation Opened')),
        ('SIMULATION_CLICKED', _('Simulation Clicked')),
        ('CREDENTIALS_ENTERED', _('Credentials Entered')),
        ('PHISHING_REPORTED', _('Phishing Reported')),
        ('TRAINING_ASSIGNED', _('Training Assigned')),
        ('TRAINING_COMPLETED', _('Training Completed')),
        ('TRAINING_PASSED', _('Training Passed')),
        ('TRAINING_FAILED', _('Training Failed')),
        ('MANUAL_ADJUSTMENT', _('Manual Adjustment')),
        ('SCORE_RECALCULATED', _('Score Recalculated')),
    ]

    risk_score = models.ForeignKey(
        RiskScore,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('risk score')
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='risk_score_history',
        verbose_name=_('employee')
    )

    event_type = models.CharField(
        _('event type'),
        max_length=30,
        choices=EVENT_TYPE_CHOICES
    )

    # Score change
    previous_score = models.IntegerField(_('previous score'))
    new_score = models.IntegerField(_('new score'))
    score_change = models.IntegerField(_('score change'))

    previous_risk_level = models.CharField(
        _('previous risk level'),
        max_length=20,
        choices=RiskScore.RISK_LEVEL_CHOICES
    )
    new_risk_level = models.CharField(
        _('new risk level'),
        max_length=20,
        choices=RiskScore.RISK_LEVEL_CHOICES
    )

    # Source tracking
    source_type = models.CharField(
        _('source type'),
        max_length=50,
        blank=True,
        help_text=_('Model that triggered this change (e.g., QuizResult, TrackingEvent)')
    )
    source_id = models.PositiveIntegerField(
        _('source ID'),
        null=True,
        blank=True,
        help_text=_('ID of the source object')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Human-readable description of what caused the change')
    )
    description_ar = models.TextField(
        _('description (Arabic)'),
        blank=True
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('risk score history')
        verbose_name_plural = _('risk score histories')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['risk_score', '-created_at']),
            models.Index(fields=['employee', '-created_at']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"{self.employee.email}: {self.previous_score} → {self.new_score} ({self.event_type})"

    def save(self, *args, **kwargs):
        """Auto-calculate score change."""
        self.score_change = self.new_score - self.previous_score
        super().save(*args, **kwargs)


class TrainingModule(models.Model):
    """
    Training content library for remediation.
    Each module contains educational content + post-training quiz.
    """

    CONTENT_TYPE_CHOICES = [
        ('VIDEO', _('Video')),
        ('TEXT', _('Text Article')),
        ('INTERACTIVE', _('Interactive Tutorial')),
        ('PDF', _('PDF Document')),
        ('SLIDES', _('Presentation Slides')),
    ]

    CATEGORY_CHOICES = [
        ('PHISHING_BASICS', _('Phishing Basics')),
        ('EMAIL_SECURITY', _('Email Security')),
        ('LINK_SAFETY', _('Link Safety')),
        ('CREDENTIAL_PROTECTION', _('Credential Protection')),
        ('SOCIAL_ENGINEERING', _('Social Engineering')),
        ('REPORTING_PROCEDURES', _('Reporting Procedures')),
        ('PASSWORD_SECURITY', _('Password Security')),
        ('DATA_PROTECTION', _('Data Protection')),
        ('MOBILE_SECURITY', _('Mobile Security')),
        ('GENERAL_AWARENESS', _('General Security Awareness')),
    ]

    DIFFICULTY_CHOICES = [
        ('BEGINNER', _('Beginner')),
        ('INTERMEDIATE', _('Intermediate')),
        ('ADVANCED', _('Advanced')),
    ]

    # Basic info
    title = models.CharField(_('title'), max_length=255)
    title_ar = models.CharField(_('title (Arabic)'), max_length=255, blank=True)

    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    # Classification
    content_type = models.CharField(
        _('content type'),
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='TEXT'
    )

    category = models.CharField(
        _('category'),
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='GENERAL_AWARENESS'
    )

    difficulty = models.CharField(
        _('difficulty'),
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='BEGINNER'
    )

    # Content
    content_html = models.TextField(
        _('content (HTML)'),
        help_text=_('Training content in HTML format')
    )
    content_html_ar = models.TextField(
        _('content (HTML - Arabic)'),
        blank=True
    )

    video_url = models.URLField(
        _('video URL'),
        blank=True,
        help_text=_('URL for video content (YouTube, Vimeo, etc.)')
    )

    # Estimated duration in minutes
    duration_minutes = models.PositiveIntegerField(
        _('duration (minutes)'),
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(120)]
    )

    # Quiz configuration
    passing_score = models.PositiveIntegerField(
        _('passing score'),
        default=80,
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        help_text=_('Minimum percentage required to pass')
    )

    min_questions_required = models.PositiveIntegerField(
        _('minimum questions required'),
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text=_('Number of questions in post-training quiz')
    )

    # Risk score reduction on completion
    score_reduction_on_pass = models.PositiveIntegerField(
        _('score reduction on pass'),
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(30)],
        help_text=_('Points to reduce from risk score when training is passed')
    )

    # Metadata
    is_active = models.BooleanField(_('is active'), default=True)
    is_mandatory = models.BooleanField(
        _('is mandatory'),
        default=False,
        help_text=_('If true, this training is required for all high-risk employees')
    )

    # Optional company-specific training
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='training_modules',
        verbose_name=_('company'),
        null=True,
        blank=True,
        help_text=_('Leave empty for global training modules')
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_training_modules',
        verbose_name=_('created by'),
        null=True
    )

    # Statistics (denormalized for performance)
    times_assigned = models.PositiveIntegerField(_('times assigned'), default=0)
    times_completed = models.PositiveIntegerField(_('times completed'), default=0)
    times_passed = models.PositiveIntegerField(_('times passed'), default=0)
    average_score = models.DecimalField(
        _('average score'),
        max_digits=5,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('training module')
        verbose_name_plural = _('training modules')
        ordering = ['category', 'difficulty', 'title']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['company', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    @property
    def completion_rate(self):
        """Calculate completion rate percentage."""
        if self.times_assigned == 0:
            return 0
        return round((self.times_completed / self.times_assigned) * 100, 1)

    @property
    def pass_rate(self):
        """Calculate pass rate percentage."""
        if self.times_completed == 0:
            return 0
        return round((self.times_passed / self.times_completed) * 100, 1)

    @property
    def total_questions(self):
        """Get total number of questions for this module."""
        return self.questions.count()


class TrainingQuestion(models.Model):
    """
    Quiz questions for training modules.
    Multiple choice questions to test understanding.
    """

    module = models.ForeignKey(
        TrainingModule,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('training module')
    )

    question_number = models.PositiveIntegerField(
        _('question number'),
        default=1
    )

    question_text = models.TextField(_('question text'))
    question_text_ar = models.TextField(_('question text (Arabic)'), blank=True)

    # Multiple choice options (stored as JSON)
    options = models.JSONField(
        _('options'),
        default=list,
        help_text=_('List of answer options, e.g., ["Option A", "Option B", "Option C", "Option D"]')
    )
    options_ar = models.JSONField(
        _('options (Arabic)'),
        default=list,
        blank=True
    )

    # Correct answer (0-based index into options array)
    correct_answer_index = models.PositiveIntegerField(
        _('correct answer index'),
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text=_('Index of correct answer (0-3)')
    )

    # Explanation shown after answering
    explanation = models.TextField(
        _('explanation'),
        blank=True,
        help_text=_('Explanation shown after answering')
    )
    explanation_ar = models.TextField(_('explanation (Arabic)'), blank=True)

    is_active = models.BooleanField(_('is active'), default=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('training question')
        verbose_name_plural = _('training questions')
        ordering = ['module', 'question_number']
        unique_together = ['module', 'question_number']

    def __str__(self):
        return f"{self.module.title} - Q{self.question_number}"

    @property
    def correct_answer(self):
        """Get the correct answer text."""
        if self.options and 0 <= self.correct_answer_index < len(self.options):
            return self.options[self.correct_answer_index]
        return None


class RemediationTraining(models.Model):
    """
    Assigned training records for employees.
    Tracks assignment, progress, and completion.
    """

    STATUS_CHOICES = [
        ('ASSIGNED', _('Assigned')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('PASSED', _('Passed')),
        ('FAILED', _('Failed')),
        ('EXPIRED', _('Expired')),
    ]

    ASSIGNMENT_REASON_CHOICES = [
        ('AUTO_HIGH_RISK', _('Auto-assigned: High Risk Score')),
        ('AUTO_SIMULATION_FAIL', _('Auto-assigned: Simulation Failure')),
        ('AUTO_QUIZ_FAIL', _('Auto-assigned: Quiz Failure')),
        ('MANUAL_ADMIN', _('Manually Assigned by Admin')),
        ('MANDATORY', _('Mandatory Training')),
        ('REFRESHER', _('Refresher Training')),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='remediation_trainings',
        verbose_name=_('employee'),
        limit_choices_to={'role': 'EMPLOYEE'}
    )

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='remediation_trainings',
        verbose_name=_('company')
    )

    training_module = models.ForeignKey(
        TrainingModule,
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name=_('training module')
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='ASSIGNED'
    )

    assignment_reason = models.CharField(
        _('assignment reason'),
        max_length=30,
        choices=ASSIGNMENT_REASON_CHOICES,
        default='MANUAL_ADMIN'
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_trainings',
        verbose_name=_('assigned by'),
        null=True,
        blank=True,
        help_text=_('Admin who assigned. Null if auto-assigned.')
    )

    # Timing
    assigned_at = models.DateTimeField(_('assigned at'), auto_now_add=True)
    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    due_date = models.DateTimeField(
        _('due date'),
        null=True,
        blank=True,
        help_text=_('Deadline for completion')
    )

    # Quiz results
    quiz_attempts = models.PositiveIntegerField(_('quiz attempts'), default=0)
    quiz_score = models.DecimalField(
        _('quiz score'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    correct_answers = models.PositiveIntegerField(_('correct answers'), default=0)
    total_questions = models.PositiveIntegerField(_('total questions'), default=0)

    # Progress tracking
    content_viewed = models.BooleanField(_('content viewed'), default=False)
    content_viewed_at = models.DateTimeField(_('content viewed at'), null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(_('time spent (seconds)'), default=0)

    # Risk score impact
    risk_score_before = models.IntegerField(
        _('risk score before'),
        null=True,
        blank=True
    )
    risk_score_after = models.IntegerField(
        _('risk score after'),
        null=True,
        blank=True
    )

    # Source tracking (what triggered this assignment)
    source_type = models.CharField(
        _('source type'),
        max_length=50,
        blank=True,
        help_text=_('What triggered this assignment (QuizResult, TrackingEvent, etc.)')
    )
    source_id = models.PositiveIntegerField(
        _('source ID'),
        null=True,
        blank=True
    )

    notes = models.TextField(_('notes'), blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('remediation training')
        verbose_name_plural = _('remediation trainings')
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['training_module', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.training_module.title} ({self.status})"

    @property
    def is_overdue(self):
        """Check if training is past due date."""
        if not self.due_date:
            return False
        if self.status in ['PASSED', 'COMPLETED']:
            return False
        return timezone.now() > self.due_date

    @property
    def passed(self):
        """Check if employee passed the training quiz."""
        if self.quiz_score is None:
            return False
        return self.quiz_score >= self.training_module.passing_score

    @property
    def time_spent_formatted(self):
        """Get formatted time spent."""
        minutes = self.time_spent_seconds // 60
        seconds = self.time_spent_seconds % 60
        return f"{minutes}m {seconds}s"

    def start_training(self):
        """Mark training as started."""
        if self.status == 'ASSIGNED':
            self.status = 'IN_PROGRESS'
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at', 'updated_at'])

    def mark_content_viewed(self):
        """Mark training content as viewed."""
        if not self.content_viewed:
            self.content_viewed = True
            self.content_viewed_at = timezone.now()
            self.save(update_fields=['content_viewed', 'content_viewed_at', 'updated_at'])

    def submit_quiz(self, answers):
        """
        Submit quiz answers and calculate score.

        Args:
            answers: dict mapping question_id to selected_answer_index

        Returns:
            dict with score, passed, and question results
        """
        from django.db.models import F

        questions = self.training_module.questions.filter(is_active=True)
        total = questions.count()
        correct = 0
        results = []

        for question in questions:
            selected = answers.get(str(question.id))
            is_correct = selected == question.correct_answer_index
            if is_correct:
                correct += 1
            results.append({
                'question_id': question.id,
                'selected': selected,
                'correct_answer': question.correct_answer_index,
                'is_correct': is_correct,
                'explanation': question.explanation
            })

        # Calculate score
        score = (correct / total * 100) if total > 0 else 0
        passed = score >= self.training_module.passing_score

        # Update record
        self.quiz_attempts = F('quiz_attempts') + 1
        self.quiz_score = score
        self.correct_answers = correct
        self.total_questions = total
        self.completed_at = timezone.now()
        self.status = 'PASSED' if passed else 'FAILED'
        self.save()

        # Refresh to get actual quiz_attempts value
        self.refresh_from_db()

        return {
            'score': score,
            'passed': passed,
            'correct': correct,
            'total': total,
            'results': results
        }

    def save(self, *args, **kwargs):
        """Auto-set company from employee."""
        if not self.company_id and self.employee_id:
            self.company = self.employee.company
        super().save(*args, **kwargs)


class TrainingQuizAnswer(models.Model):
    """
    Records individual question answers during training quiz.
    """

    remediation_training = models.ForeignKey(
        RemediationTraining,
        on_delete=models.CASCADE,
        related_name='quiz_answers',
        verbose_name=_('remediation training')
    )

    question = models.ForeignKey(
        TrainingQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('question')
    )

    selected_answer_index = models.PositiveIntegerField(
        _('selected answer index'),
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )

    is_correct = models.BooleanField(_('is correct'))

    answered_at = models.DateTimeField(_('answered at'), auto_now_add=True)
    time_spent_seconds = models.PositiveIntegerField(_('time spent (seconds)'), default=0)

    class Meta:
        verbose_name = _('training quiz answer')
        verbose_name_plural = _('training quiz answers')
        ordering = ['remediation_training', 'question__question_number']
        unique_together = ['remediation_training', 'question']

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{self.remediation_training.employee.email} - Q{self.question.question_number} {status}"

    def save(self, *args, **kwargs):
        """Auto-check if answer is correct."""
        self.is_correct = self.selected_answer_index == self.question.correct_answer_index
        super().save(*args, **kwargs)
