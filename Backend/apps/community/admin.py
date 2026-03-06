"""
Community App Admin
===================
Admin configuration for public awareness portal content.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    ArticleCategory, Article, PublicQuiz,
    PublicQuizQuestion, PublicQuizAttempt, Resource
)


# =============================================================================
# Inline Admin Classes
# =============================================================================

class PublicQuizQuestionInline(admin.TabularInline):
    """Inline admin for quiz questions."""

    model = PublicQuizQuestion
    extra = 1
    fields = [
        'question_number', 'question_text', 'options',
        'correct_answer_index', 'points', 'is_active'
    ]
    ordering = ['question_number']


# =============================================================================
# Article Category Admin
# =============================================================================

@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    """Admin for article categories."""

    list_display = [
        'name', 'name_ar', 'slug', 'icon', 'display_order',
        'article_count', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'name_ar', 'description', 'description_ar']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'name_ar', 'slug', 'icon')
        }),
        (_('Description'), {
            'fields': ('description', 'description_ar'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('display_order', 'is_active')
        }),
        (_('Statistics'), {
            'fields': ('article_count',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['article_count', 'created_at', 'updated_at']

    actions = ['activate_categories', 'deactivate_categories', 'update_article_counts']

    @admin.action(description=_('Activate selected categories'))
    def activate_categories(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description=_('Deactivate selected categories'))
    def deactivate_categories(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description=_('Update article counts'))
    def update_article_counts(self, request, queryset):
        for category in queryset:
            category.update_article_count()
        self.message_user(request, _('Article counts updated.'))


# =============================================================================
# Article Admin
# =============================================================================

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin for awareness articles."""

    list_display = [
        'title', 'category', 'status', 'is_featured',
        'view_count', 'reading_time_minutes', 'published_at', 'is_active'
    ]
    list_filter = [
        'status', 'is_featured', 'is_active', 'category',
        'published_at', 'created_at'
    ]
    search_fields = [
        'title', 'title_ar', 'excerpt', 'excerpt_ar',
        'content', 'content_ar', 'tags'
    ]
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author', 'category']
    date_hierarchy = 'published_at'
    ordering = ['-created_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'title_ar', 'slug', 'category')
        }),
        (_('Excerpt'), {
            'fields': ('excerpt', 'excerpt_ar')
        }),
        (_('Content'), {
            'fields': ('content', 'content_ar'),
            'classes': ('wide',)
        }),
        (_('Featured Image'), {
            'fields': (
                'featured_image_url', 'featured_image_alt', 'featured_image_alt_ar'
            ),
            'classes': ('collapse',)
        }),
        (_('Author'), {
            'fields': ('author', 'author_name')
        }),
        (_('Categorization'), {
            'fields': ('tags',)
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('Publishing'), {
            'fields': (
                'status', 'is_active', 'is_featured',
                'published_at', 'reading_time_minutes'
            )
        }),
        (_('Statistics'), {
            'fields': ('view_count', 'share_count'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['view_count', 'share_count', 'created_at', 'updated_at']

    actions = [
        'publish_articles', 'unpublish_articles',
        'feature_articles', 'unfeature_articles'
    ]

    @admin.action(description=_('Publish selected articles'))
    def publish_articles(self, request, queryset):
        queryset.update(status='PUBLISHED')

    @admin.action(description=_('Unpublish selected articles (set to draft)'))
    def unpublish_articles(self, request, queryset):
        queryset.update(status='DRAFT')

    @admin.action(description=_('Mark as featured'))
    def feature_articles(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description=_('Remove from featured'))
    def unfeature_articles(self, request, queryset):
        queryset.update(is_featured=False)


# =============================================================================
# Public Quiz Admin
# =============================================================================

@admin.register(PublicQuiz)
class PublicQuizAdmin(admin.ModelAdmin):
    """Admin for public awareness quizzes."""

    list_display = [
        'title', 'category', 'difficulty', 'status', 'is_featured',
        'question_count_display', 'total_attempts', 'average_score_display',
        'pass_rate_display', 'is_active'
    ]
    list_filter = [
        'status', 'difficulty', 'is_featured', 'is_active',
        'category', 'created_at'
    ]
    search_fields = ['title', 'title_ar', 'description', 'description_ar']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['category', 'created_by']
    ordering = ['-created_at']
    inlines = [PublicQuizQuestionInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'title_ar', 'slug', 'category')
        }),
        (_('Description'), {
            'fields': ('description', 'description_ar')
        }),
        (_('Quiz Settings'), {
            'fields': (
                'difficulty', 'time_limit_minutes', 'passing_score',
                'show_correct_answers', 'randomize_questions'
            )
        }),
        (_('Media'), {
            'fields': ('featured_image_url',),
            'classes': ('collapse',)
        }),
        (_('Publishing'), {
            'fields': ('status', 'is_active', 'is_featured', 'created_by')
        }),
        (_('Statistics'), {
            'fields': (
                'total_attempts', 'total_completions',
                'average_score', 'pass_rate'
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'total_attempts', 'total_completions',
        'average_score', 'pass_rate', 'created_at', 'updated_at'
    ]

    actions = [
        'publish_quizzes', 'unpublish_quizzes',
        'feature_quizzes', 'unfeature_quizzes',
        'update_statistics'
    ]

    @admin.display(description=_('Questions'))
    def question_count_display(self, obj):
        return obj.question_count

    @admin.display(description=_('Avg Score'))
    def average_score_display(self, obj):
        if obj.average_score:
            return f"{obj.average_score:.1f}%"
        return "-"

    @admin.display(description=_('Pass Rate'))
    def pass_rate_display(self, obj):
        if obj.pass_rate:
            return f"{obj.pass_rate:.1f}%"
        return "-"

    @admin.action(description=_('Publish selected quizzes'))
    def publish_quizzes(self, request, queryset):
        queryset.update(status='PUBLISHED')

    @admin.action(description=_('Unpublish selected quizzes (set to draft)'))
    def unpublish_quizzes(self, request, queryset):
        queryset.update(status='DRAFT')

    @admin.action(description=_('Mark as featured'))
    def feature_quizzes(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description=_('Remove from featured'))
    def unfeature_quizzes(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description=_('Update statistics'))
    def update_statistics(self, request, queryset):
        for quiz in queryset:
            quiz.update_statistics()
        self.message_user(request, _('Quiz statistics updated.'))


# =============================================================================
# Public Quiz Question Admin
# =============================================================================

@admin.register(PublicQuizQuestion)
class PublicQuizQuestionAdmin(admin.ModelAdmin):
    """Admin for quiz questions (standalone view)."""

    list_display = [
        'quiz', 'question_number', 'question_text_preview',
        'correct_answer_index', 'points', 'is_active'
    ]
    list_filter = ['quiz', 'is_active', 'created_at']
    search_fields = ['question_text', 'question_text_ar', 'explanation']
    raw_id_fields = ['quiz']
    ordering = ['quiz', 'question_number']

    fieldsets = (
        (_('Question'), {
            'fields': ('quiz', 'question_number', 'question_text', 'question_text_ar')
        }),
        (_('Options'), {
            'fields': ('options', 'options_ar', 'correct_answer_index')
        }),
        (_('Explanation'), {
            'fields': ('explanation', 'explanation_ar'),
            'classes': ('collapse',)
        }),
        (_('Media & Settings'), {
            'fields': ('image_url', 'points', 'is_active')
        }),
    )

    @admin.display(description=_('Question'))
    def question_text_preview(self, obj):
        text = obj.question_text[:50]
        if len(obj.question_text) > 50:
            text += "..."
        return text


# =============================================================================
# Public Quiz Attempt Admin
# =============================================================================

@admin.register(PublicQuizAttempt)
class PublicQuizAttemptAdmin(admin.ModelAdmin):
    """Admin for quiz attempts (read-only for analytics)."""

    list_display = [
        'quiz', 'user_display', 'score_display', 'passed',
        'total_questions', 'correct_answers',
        'time_taken_formatted', 'language_preference',
        'started_at', 'is_completed'
    ]
    list_filter = [
        'quiz', 'passed', 'is_completed', 'language_preference',
        'country_code', 'started_at'
    ]
    search_fields = ['session_id', 'user__email']
    raw_id_fields = ['quiz', 'user']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']

    fieldsets = (
        (_('Quiz Information'), {
            'fields': ('quiz', 'user', 'session_id')
        }),
        (_('Results'), {
            'fields': (
                'score', 'passed', 'total_questions', 'correct_answers',
                'total_points', 'max_points'
            )
        }),
        (_('Answers'), {
            'fields': ('answers',),
            'classes': ('collapse',)
        }),
        (_('Timing'), {
            'fields': ('started_at', 'completed_at', 'time_taken_seconds')
        }),
        (_('Metadata'), {
            'fields': (
                'language_preference', 'country_code',
                'user_agent', 'ip_hash'
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'quiz', 'user', 'session_id', 'score', 'passed',
        'total_questions', 'correct_answers', 'total_points', 'max_points',
        'answers', 'started_at', 'completed_at', 'time_taken_seconds',
        'language_preference', 'country_code', 'user_agent', 'ip_hash',
        'is_completed', 'created_at'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description=_('User'))
    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return f"Anonymous ({obj.session_id[:8]}...)" if obj.session_id else "Anonymous"

    @admin.display(description=_('Score'))
    def score_display(self, obj):
        if obj.score is not None:
            color = 'green' if obj.passed else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.score
            )
        return "-"


# =============================================================================
# Resource Admin
# =============================================================================

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin for downloadable resources."""

    list_display = [
        'title', 'resource_type', 'category', 'language',
        'file_size_display', 'download_count', 'view_count',
        'is_featured', 'is_active', 'display_order'
    ]
    list_filter = [
        'resource_type', 'language', 'is_featured', 'is_active',
        'category', 'created_at'
    ]
    search_fields = [
        'title', 'title_ar', 'description', 'description_ar', 'source_name'
    ]
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['category', 'created_by']
    ordering = ['display_order', '-created_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'title_ar', 'slug', 'category', 'resource_type')
        }),
        (_('Description'), {
            'fields': ('description', 'description_ar')
        }),
        (_('URLs'), {
            'fields': ('file_url', 'external_url', 'thumbnail_url')
        }),
        (_('File Metadata'), {
            'fields': ('file_size_bytes', 'file_format'),
            'classes': ('collapse',)
        }),
        (_('Video Metadata'), {
            'fields': ('video_duration_seconds', 'video_platform'),
            'classes': ('collapse',)
        }),
        (_('Source Attribution'), {
            'fields': ('source_name', 'source_url'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': (
                'language', 'is_active', 'is_featured',
                'display_order', 'created_by'
            )
        }),
        (_('Statistics'), {
            'fields': ('download_count', 'view_count'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']

    actions = [
        'activate_resources', 'deactivate_resources',
        'feature_resources', 'unfeature_resources'
    ]

    @admin.display(description=_('File Size'))
    def file_size_display(self, obj):
        return obj.file_size_formatted or "-"

    @admin.action(description=_('Activate selected resources'))
    def activate_resources(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description=_('Deactivate selected resources'))
    def deactivate_resources(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description=_('Mark as featured'))
    def feature_resources(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description=_('Remove from featured'))
    def unfeature_resources(self, request, queryset):
        queryset.update(is_featured=False)
