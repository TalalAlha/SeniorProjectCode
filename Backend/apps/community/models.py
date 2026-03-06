"""
Community App Models
====================
Public-facing awareness portal for PhishAware platform.
Educational content accessible without authentication.

Models:
- ArticleCategory: Organize articles by topic
- Article: Blog-style awareness content
- PublicQuiz: Simple quizzes for public awareness
- PublicQuizQuestion: Questions for public quizzes
- PublicQuizAttempt: Track anonymous quiz attempts
- Resource: Downloadable resources and links
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ArticleCategory(models.Model):
    """
    Categories for organizing awareness articles.
    Examples: Phishing Basics, Email Security, Mobile Security, etc.
    """

    name = models.CharField(_('category name'), max_length=100)
    name_ar = models.CharField(_('category name (Arabic)'), max_length=100, blank=True)

    slug = models.SlugField(
        _('slug'),
        max_length=120,
        unique=True,
        help_text=_('URL-friendly identifier (auto-generated from name)')
    )

    description = models.TextField(_('description'), blank=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    icon = models.CharField(
        _('icon'),
        max_length=50,
        blank=True,
        help_text=_('Icon class name (e.g., "shield", "mail", "smartphone")')
    )

    display_order = models.PositiveIntegerField(
        _('display order'),
        default=0,
        help_text=_('Lower numbers appear first')
    )

    is_active = models.BooleanField(_('is active'), default=True)

    # Statistics (denormalized for performance)
    article_count = models.PositiveIntegerField(_('article count'), default=0)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('article category')
        verbose_name_plural = _('article categories')
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while ArticleCategory.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def update_article_count(self):
        """Update the denormalized article count."""
        self.article_count = self.articles.filter(
            status='PUBLISHED',
            is_active=True
        ).count()
        self.save(update_fields=['article_count', 'updated_at'])


class Article(models.Model):
    """
    Blog-style awareness articles for public education.
    Bilingual content with SEO-friendly URLs.
    """

    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('REVIEW', _('Under Review')),
        ('PUBLISHED', _('Published')),
        ('ARCHIVED', _('Archived')),
    ]

    # Basic Information
    title = models.CharField(_('title'), max_length=255)
    title_ar = models.CharField(_('title (Arabic)'), max_length=255, blank=True)

    slug = models.SlugField(
        _('slug'),
        max_length=280,
        unique=True,
        help_text=_('URL-friendly identifier (auto-generated from title)')
    )

    excerpt = models.TextField(
        _('excerpt'),
        max_length=500,
        help_text=_('Short summary for article listings (max 500 chars)')
    )
    excerpt_ar = models.TextField(
        _('excerpt (Arabic)'),
        max_length=500,
        blank=True
    )

    # Content
    content = models.TextField(
        _('content'),
        help_text=_('Full article content (HTML or Markdown)')
    )
    content_ar = models.TextField(_('content (Arabic)'), blank=True)

    # Categorization
    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        related_name='articles',
        verbose_name=_('category'),
        null=True,
        blank=True
    )

    tags = models.CharField(
        _('tags'),
        max_length=500,
        blank=True,
        help_text=_('Comma-separated tags for search (e.g., "phishing,email,security")')
    )

    # Featured Image
    featured_image_url = models.URLField(
        _('featured image URL'),
        blank=True,
        help_text=_('URL of the featured image')
    )
    featured_image_alt = models.CharField(
        _('image alt text'),
        max_length=255,
        blank=True,
        help_text=_('Alternative text for accessibility')
    )
    featured_image_alt_ar = models.CharField(
        _('image alt text (Arabic)'),
        max_length=255,
        blank=True
    )

    # Status and Publishing
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    is_active = models.BooleanField(_('is active'), default=True)
    is_featured = models.BooleanField(
        _('is featured'),
        default=False,
        help_text=_('Featured articles appear prominently on the portal')
    )

    # Dates
    published_at = models.DateTimeField(
        _('published at'),
        null=True,
        blank=True,
        help_text=_('Date when article was/will be published')
    )

    # Author (optional - can be staff or anonymous)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='authored_articles',
        verbose_name=_('author'),
        null=True,
        blank=True
    )
    author_name = models.CharField(
        _('author name'),
        max_length=100,
        blank=True,
        help_text=_('Display name (uses user name if author is set)')
    )

    # SEO
    meta_title = models.CharField(
        _('meta title'),
        max_length=70,
        blank=True,
        help_text=_('SEO title (max 70 chars)')
    )
    meta_description = models.CharField(
        _('meta description'),
        max_length=160,
        blank=True,
        help_text=_('SEO description (max 160 chars)')
    )

    # Statistics
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    share_count = models.PositiveIntegerField(_('share count'), default=0)

    # Estimated reading time (in minutes)
    reading_time_minutes = models.PositiveIntegerField(
        _('reading time (minutes)'),
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(60)]
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('article')
        verbose_name_plural = _('articles')
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active', '-published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured', 'status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Auto-generate slug and set published_at."""
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Auto-set published_at when publishing
        if self.status == 'PUBLISHED' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def is_published(self):
        """Check if article is currently published."""
        if self.status != 'PUBLISHED' or not self.is_active:
            return False
        if self.published_at and self.published_at > timezone.now():
            return False
        return True

    @property
    def display_author(self):
        """Get author display name."""
        if self.author_name:
            return self.author_name
        if self.author:
            return self.author.get_full_name() or self.author.email
        return _('PhishAware Team')

    @property
    def tags_list(self):
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def increment_view_count(self):
        """Increment view count (use F() for thread safety)."""
        from django.db.models import F
        Article.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)


class PublicQuiz(models.Model):
    """
    Simple awareness quizzes accessible to the public without login.
    """

    DIFFICULTY_CHOICES = [
        ('EASY', _('Easy')),
        ('MEDIUM', _('Medium')),
        ('HARD', _('Hard')),
    ]

    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('PUBLISHED', _('Published')),
        ('ARCHIVED', _('Archived')),
    ]

    # Basic Information
    title = models.CharField(_('title'), max_length=255)
    title_ar = models.CharField(_('title (Arabic)'), max_length=255, blank=True)

    slug = models.SlugField(
        _('slug'),
        max_length=280,
        unique=True,
        help_text=_('URL-friendly identifier')
    )

    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    # Quiz Configuration
    difficulty = models.CharField(
        _('difficulty'),
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='MEDIUM'
    )

    time_limit_minutes = models.PositiveIntegerField(
        _('time limit (minutes)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text=_('Optional time limit. Leave empty for unlimited.')
    )

    passing_score = models.PositiveIntegerField(
        _('passing score'),
        default=70,
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        help_text=_('Minimum percentage to pass (50-100)')
    )

    show_correct_answers = models.BooleanField(
        _('show correct answers'),
        default=True,
        help_text=_('Show correct answers after quiz completion')
    )

    randomize_questions = models.BooleanField(
        _('randomize questions'),
        default=False,
        help_text=_('Randomize question order for each attempt')
    )

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    is_active = models.BooleanField(_('is active'), default=True)
    is_featured = models.BooleanField(
        _('is featured'),
        default=False,
        help_text=_('Featured quizzes appear prominently on the portal')
    )

    # Optional category link
    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        related_name='public_quizzes',
        verbose_name=_('category'),
        null=True,
        blank=True
    )

    # Featured image
    featured_image_url = models.URLField(
        _('featured image URL'),
        blank=True
    )

    # Statistics (denormalized)
    total_attempts = models.PositiveIntegerField(_('total attempts'), default=0)
    total_completions = models.PositiveIntegerField(_('total completions'), default=0)
    average_score = models.DecimalField(
        _('average score'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    pass_rate = models.DecimalField(
        _('pass rate'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Percentage of completions that passed')
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_public_quizzes',
        verbose_name=_('created by'),
        null=True
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('public quiz')
        verbose_name_plural = _('public quizzes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Auto-generate slug from title."""
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while PublicQuiz.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        """Check if quiz is published and active."""
        return self.status == 'PUBLISHED' and self.is_active

    @property
    def question_count(self):
        """Get total number of active questions."""
        return self.questions.filter(is_active=True).count()

    @property
    def completion_rate(self):
        """Calculate completion rate."""
        if self.total_attempts == 0:
            return 0
        return round((self.total_completions / self.total_attempts) * 100, 1)

    def update_statistics(self):
        """Recalculate quiz statistics from attempts."""
        completions = self.attempts.filter(is_completed=True)
        total_completions = completions.count()

        if total_completions > 0:
            from django.db.models import Avg
            avg_score = completions.aggregate(avg=Avg('score'))['avg']
            passed = completions.filter(passed=True).count()

            self.total_completions = total_completions
            self.average_score = avg_score
            self.pass_rate = (passed / total_completions) * 100
        else:
            self.total_completions = 0
            self.average_score = None
            self.pass_rate = None

        self.total_attempts = self.attempts.count()
        self.save(update_fields=[
            'total_attempts', 'total_completions',
            'average_score', 'pass_rate', 'updated_at'
        ])


class PublicQuizQuestion(models.Model):
    """
    Questions for public awareness quizzes.
    Multiple choice with explanation support.
    """

    quiz = models.ForeignKey(
        PublicQuiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('quiz')
    )

    question_number = models.PositiveIntegerField(
        _('question number'),
        default=1
    )

    question_text = models.TextField(_('question text'))
    question_text_ar = models.TextField(_('question text (Arabic)'), blank=True)

    # Multiple choice options (stored as JSON array)
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

    # Correct answer index (0-based)
    correct_answer_index = models.PositiveIntegerField(
        _('correct answer index'),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text=_('Index of correct answer (0-based)')
    )

    # Explanation shown after answering
    explanation = models.TextField(
        _('explanation'),
        blank=True,
        help_text=_('Explanation shown after answering (supports Markdown)')
    )
    explanation_ar = models.TextField(_('explanation (Arabic)'), blank=True)

    # Optional image for visual questions
    image_url = models.URLField(
        _('image URL'),
        blank=True,
        help_text=_('Optional image to accompany the question')
    )

    # Points for this question (for weighted scoring)
    points = models.PositiveIntegerField(
        _('points'),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_('Points awarded for correct answer')
    )

    is_active = models.BooleanField(_('is active'), default=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('public quiz question')
        verbose_name_plural = _('public quiz questions')
        ordering = ['quiz', 'question_number']
        unique_together = ['quiz', 'question_number']
        indexes = [
            models.Index(fields=['quiz', 'is_active']),
        ]

    def __str__(self):
        return f"{self.quiz.title} - Q{self.question_number}"

    @property
    def correct_answer(self):
        """Get the correct answer text."""
        if self.options and 0 <= self.correct_answer_index < len(self.options):
            return self.options[self.correct_answer_index]
        return None


class PublicQuizAttempt(models.Model):
    """
    Track anonymous quiz attempts.
    Stores results without requiring authentication.
    """

    quiz = models.ForeignKey(
        PublicQuiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('quiz')
    )

    # Anonymous tracking (optional)
    session_id = models.CharField(
        _('session ID'),
        max_length=100,
        blank=True,
        help_text=_('Browser session ID for anonymous tracking')
    )

    # Optional user link (if logged in)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='public_quiz_attempts',
        verbose_name=_('user'),
        null=True,
        blank=True
    )

    # Results
    score = models.DecimalField(
        _('score'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Score as percentage (0-100)')
    )
    total_questions = models.PositiveIntegerField(_('total questions'), default=0)
    correct_answers = models.PositiveIntegerField(_('correct answers'), default=0)
    total_points = models.PositiveIntegerField(
        _('total points'),
        default=0,
        help_text=_('Total points earned')
    )
    max_points = models.PositiveIntegerField(
        _('max points'),
        default=0,
        help_text=_('Maximum possible points')
    )

    passed = models.BooleanField(_('passed'), default=False)
    is_completed = models.BooleanField(_('is completed'), default=False)

    # Answers (stored as JSON: {question_id: selected_index})
    answers = models.JSONField(
        _('answers'),
        default=dict,
        help_text=_('Map of question_id to selected answer index')
    )

    # Timing
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(
        _('time taken (seconds)'),
        null=True,
        blank=True
    )

    # Anonymous user metadata (optional, for analytics)
    user_agent = models.CharField(_('user agent'), max_length=500, blank=True)
    ip_hash = models.CharField(
        _('IP hash'),
        max_length=64,
        blank=True,
        help_text=_('Hashed IP for duplicate detection (privacy-preserving)')
    )
    country_code = models.CharField(
        _('country code'),
        max_length=2,
        blank=True,
        help_text=_('ISO country code (e.g., SA, AE, EG)')
    )
    language_preference = models.CharField(
        _('language preference'),
        max_length=5,
        default='en',
        help_text=_('User language preference (en/ar)')
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('public quiz attempt')
        verbose_name_plural = _('public quiz attempts')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['quiz', 'is_completed']),
            models.Index(fields=['session_id']),
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['-started_at']),
        ]

    def __str__(self):
        identifier = self.user.email if self.user else f"Anonymous ({self.session_id[:8]}...)"
        return f"{self.quiz.title} - {identifier} - {self.score}%"

    @property
    def time_taken_formatted(self):
        """Get formatted time taken."""
        if not self.time_taken_seconds:
            return None
        minutes = self.time_taken_seconds // 60
        seconds = self.time_taken_seconds % 60
        return f"{minutes}m {seconds}s"

    def submit(self, answers_dict):
        """
        Submit quiz answers and calculate results.

        Args:
            answers_dict: dict mapping question_id (str) to selected_index (int)

        Returns:
            dict with score, passed, and detailed results
        """
        questions = self.quiz.questions.filter(is_active=True)
        total_questions = questions.count()
        correct = 0
        total_points = 0
        max_points = 0
        results = []

        for question in questions:
            max_points += question.points
            selected = answers_dict.get(str(question.id))
            is_correct = selected == question.correct_answer_index

            if is_correct:
                correct += 1
                total_points += question.points

            results.append({
                'question_id': question.id,
                'question_number': question.question_number,
                'selected': selected,
                'correct_answer': question.correct_answer_index,
                'is_correct': is_correct,
                'explanation': question.explanation if self.quiz.show_correct_answers else None,
                'points_earned': question.points if is_correct else 0
            })

        # Calculate score
        score = (correct / total_questions * 100) if total_questions > 0 else 0
        passed = score >= self.quiz.passing_score

        # Update attempt record
        self.answers = answers_dict
        self.total_questions = total_questions
        self.correct_answers = correct
        self.total_points = total_points
        self.max_points = max_points
        self.score = score
        self.passed = passed
        self.is_completed = True
        self.completed_at = timezone.now()

        if self.started_at:
            self.time_taken_seconds = int((self.completed_at - self.started_at).total_seconds())

        self.save()

        # Update quiz statistics
        self.quiz.update_statistics()

        return {
            'score': score,
            'passed': passed,
            'correct': correct,
            'total': total_questions,
            'total_points': total_points,
            'max_points': max_points,
            'results': results if self.quiz.show_correct_answers else None,
            'time_taken': self.time_taken_formatted
        }


class Resource(models.Model):
    """
    Downloadable resources and external links for public education.
    PDFs, infographics, video links, external resources.
    """

    RESOURCE_TYPE_CHOICES = [
        ('PDF', _('PDF Document')),
        ('INFOGRAPHIC', _('Infographic')),
        ('VIDEO', _('Video')),
        ('GUIDE', _('Guide/Handbook')),
        ('CHECKLIST', _('Checklist')),
        ('POSTER', _('Poster')),
        ('EXTERNAL_LINK', _('External Link')),
        ('TOOL', _('Tool/Application')),
    ]

    # Basic Information
    title = models.CharField(_('title'), max_length=255)
    title_ar = models.CharField(_('title (Arabic)'), max_length=255, blank=True)

    slug = models.SlugField(
        _('slug'),
        max_length=280,
        unique=True
    )

    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    # Resource Type and Category
    resource_type = models.CharField(
        _('resource type'),
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default='PDF'
    )

    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        related_name='resources',
        verbose_name=_('category'),
        null=True,
        blank=True
    )

    # URLs
    file_url = models.URLField(
        _('file URL'),
        blank=True,
        help_text=_('URL to download the resource (for PDFs, images, etc.)')
    )
    external_url = models.URLField(
        _('external URL'),
        blank=True,
        help_text=_('External link (for videos, websites, tools)')
    )

    # Thumbnail/Preview
    thumbnail_url = models.URLField(
        _('thumbnail URL'),
        blank=True,
        help_text=_('Preview image URL')
    )

    # File metadata
    file_size_bytes = models.PositiveIntegerField(
        _('file size (bytes)'),
        null=True,
        blank=True
    )
    file_format = models.CharField(
        _('file format'),
        max_length=20,
        blank=True,
        help_text=_('e.g., PDF, PNG, MP4')
    )

    # Video-specific fields
    video_duration_seconds = models.PositiveIntegerField(
        _('video duration (seconds)'),
        null=True,
        blank=True
    )
    video_platform = models.CharField(
        _('video platform'),
        max_length=50,
        blank=True,
        help_text=_('e.g., YouTube, Vimeo')
    )

    # Source attribution
    source_name = models.CharField(
        _('source name'),
        max_length=200,
        blank=True,
        help_text=_('Original source or creator')
    )
    source_url = models.URLField(
        _('source URL'),
        blank=True,
        help_text=_('Link to original source')
    )

    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    is_featured = models.BooleanField(
        _('is featured'),
        default=False,
        help_text=_('Featured resources appear prominently')
    )

    # Language
    language = models.CharField(
        _('language'),
        max_length=10,
        default='en',
        choices=[
            ('en', _('English')),
            ('ar', _('Arabic')),
            ('both', _('Bilingual')),
        ]
    )

    # Statistics
    download_count = models.PositiveIntegerField(_('download count'), default=0)
    view_count = models.PositiveIntegerField(_('view count'), default=0)

    # Display order
    display_order = models.PositiveIntegerField(
        _('display order'),
        default=0
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_resources',
        verbose_name=_('created by'),
        null=True
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('resource')
        verbose_name_plural = _('resources')
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['resource_type', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"

    def save(self, *args, **kwargs):
        """Auto-generate slug from title."""
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Resource.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def file_size_formatted(self):
        """Get human-readable file size."""
        if not self.file_size_bytes:
            return None
        size = self.file_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def video_duration_formatted(self):
        """Get formatted video duration."""
        if not self.video_duration_seconds:
            return None
        minutes = self.video_duration_seconds // 60
        seconds = self.video_duration_seconds % 60
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s"

    @property
    def primary_url(self):
        """Get the primary URL for this resource."""
        return self.file_url or self.external_url

    def increment_download_count(self):
        """Increment download count (thread-safe)."""
        from django.db.models import F
        Resource.objects.filter(pk=self.pk).update(download_count=F('download_count') + 1)

    def increment_view_count(self):
        """Increment view count (thread-safe)."""
        from django.db.models import F
        Resource.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)
