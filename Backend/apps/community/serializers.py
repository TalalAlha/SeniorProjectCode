"""
Community App Serializers
=========================
Serializers for public-facing awareness portal.
All endpoints are publicly accessible without authentication.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import (
    ArticleCategory, Article, PublicQuiz,
    PublicQuizQuestion, PublicQuizAttempt, Resource
)


# =============================================================================
# Article Category Serializers
# =============================================================================

class ArticleCategorySerializer(serializers.ModelSerializer):
    """Serializer for article categories with article count."""

    class Meta:
        model = ArticleCategory
        fields = [
            'id', 'name', 'name_ar', 'slug', 'description', 'description_ar',
            'icon', 'display_order', 'article_count'
        ]
        read_only_fields = fields


class ArticleCategoryDetailSerializer(ArticleCategorySerializer):
    """Detailed category serializer with related content counts."""

    quiz_count = serializers.SerializerMethodField()
    resource_count = serializers.SerializerMethodField()

    class Meta(ArticleCategorySerializer.Meta):
        fields = ArticleCategorySerializer.Meta.fields + ['quiz_count', 'resource_count']

    def get_quiz_count(self, obj):
        return obj.public_quizzes.filter(status='PUBLISHED', is_active=True).count()

    def get_resource_count(self, obj):
        return obj.resources.filter(is_active=True).count()


# =============================================================================
# Article Serializers
# =============================================================================

class ArticleListSerializer(serializers.ModelSerializer):
    """Minimal serializer for article listings."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ar = serializers.CharField(source='category.name_ar', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    display_author = serializers.ReadOnlyField()
    tags_list = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'title_ar', 'slug', 'excerpt', 'excerpt_ar',
            'category', 'category_name', 'category_name_ar', 'category_slug',
            'featured_image_url', 'featured_image_alt', 'featured_image_alt_ar',
            'display_author', 'published_at', 'reading_time_minutes',
            'view_count', 'is_featured', 'tags_list'
        ]
        read_only_fields = fields


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Full serializer for article detail view."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ar = serializers.CharField(source='category.name_ar', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    display_author = serializers.ReadOnlyField()
    tags_list = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    related_articles = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'title_ar', 'slug', 'excerpt', 'excerpt_ar',
            'content', 'content_ar',
            'category', 'category_name', 'category_name_ar', 'category_slug',
            'tags', 'tags_list',
            'featured_image_url', 'featured_image_alt', 'featured_image_alt_ar',
            'display_author', 'author_name',
            'meta_title', 'meta_description',
            'published_at', 'reading_time_minutes',
            'view_count', 'share_count', 'is_featured', 'is_published',
            'related_articles', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_related_articles(self, obj):
        """Get related articles from same category."""
        if not obj.category:
            return []

        related = Article.objects.filter(
            category=obj.category,
            status='PUBLISHED',
            is_active=True
        ).exclude(pk=obj.pk).order_by('-published_at')[:3]

        return ArticleListSerializer(related, many=True).data


# =============================================================================
# Public Quiz Serializers
# =============================================================================

class PublicQuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer for quiz questions (without correct answer for taking quiz)."""

    class Meta:
        model = PublicQuizQuestion
        fields = [
            'id', 'question_number', 'question_text', 'question_text_ar',
            'options', 'options_ar', 'image_url', 'points'
        ]
        read_only_fields = fields


class PublicQuizQuestionWithAnswerSerializer(PublicQuizQuestionSerializer):
    """Serializer for quiz questions with correct answer (for results)."""

    correct_answer = serializers.ReadOnlyField()

    class Meta(PublicQuizQuestionSerializer.Meta):
        fields = PublicQuizQuestionSerializer.Meta.fields + [
            'correct_answer_index', 'correct_answer', 'explanation', 'explanation_ar'
        ]


class PublicQuizListSerializer(serializers.ModelSerializer):
    """Minimal serializer for quiz listings."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ar = serializers.CharField(source='category.name_ar', read_only=True)
    question_count = serializers.ReadOnlyField()
    completion_rate = serializers.ReadOnlyField()

    class Meta:
        model = PublicQuiz
        fields = [
            'id', 'title', 'title_ar', 'slug', 'description', 'description_ar',
            'difficulty', 'time_limit_minutes', 'passing_score',
            'category', 'category_name', 'category_name_ar',
            'featured_image_url', 'question_count',
            'total_attempts', 'total_completions', 'average_score', 'pass_rate',
            'completion_rate', 'is_featured', 'created_at'
        ]
        read_only_fields = fields


class PublicQuizDetailSerializer(serializers.ModelSerializer):
    """Full serializer for quiz detail (includes questions without answers)."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ar = serializers.CharField(source='category.name_ar', read_only=True)
    questions = PublicQuizQuestionSerializer(many=True, read_only=True)
    question_count = serializers.ReadOnlyField()
    completion_rate = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()

    class Meta:
        model = PublicQuiz
        fields = [
            'id', 'title', 'title_ar', 'slug', 'description', 'description_ar',
            'difficulty', 'time_limit_minutes', 'passing_score',
            'show_correct_answers', 'randomize_questions',
            'category', 'category_name', 'category_name_ar',
            'featured_image_url', 'questions', 'question_count',
            'total_attempts', 'total_completions', 'average_score', 'pass_rate',
            'completion_rate', 'is_featured', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        """Optionally randomize questions."""
        data = super().to_representation(instance)
        if instance.randomize_questions:
            import random
            questions = data.get('questions', [])
            random.shuffle(questions)
            data['questions'] = questions
        return data


# =============================================================================
# Quiz Attempt Serializers
# =============================================================================

class PublicQuizAttemptCreateSerializer(serializers.ModelSerializer):
    """Serializer for starting a quiz attempt."""

    class Meta:
        model = PublicQuizAttempt
        fields = ['id', 'quiz', 'session_id', 'language_preference', 'started_at']
        read_only_fields = ['id', 'started_at']

    def create(self, validated_data):
        """Create attempt with optional metadata."""
        request = self.context.get('request')
        if request:
            # Extract metadata from request
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]

            # Create privacy-preserving IP hash
            ip = self._get_client_ip(request)
            if ip:
                import hashlib
                validated_data['ip_hash'] = hashlib.sha256(ip.encode()).hexdigest()[:64]

        return super().create(validated_data)

    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class PublicQuizAttemptSubmitSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers."""

    answers = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=5),
        help_text='Map of question_id to selected answer index'
    )

    def validate_answers(self, value):
        """Validate that answers correspond to actual questions."""
        attempt = self.context.get('attempt')
        if not attempt:
            raise serializers.ValidationError("Quiz attempt not found.")

        quiz = attempt.quiz
        question_ids = set(
            str(q.id) for q in quiz.questions.filter(is_active=True)
        )

        # Check for invalid question IDs
        submitted_ids = set(value.keys())
        invalid_ids = submitted_ids - question_ids

        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid question IDs: {', '.join(invalid_ids)}"
            )

        return value


class PublicQuizAttemptResultSerializer(serializers.ModelSerializer):
    """Serializer for quiz attempt results."""

    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    quiz_title_ar = serializers.CharField(source='quiz.title_ar', read_only=True)
    time_taken_formatted = serializers.ReadOnlyField()
    passing_score = serializers.IntegerField(source='quiz.passing_score', read_only=True)

    class Meta:
        model = PublicQuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'quiz_title_ar',
            'score', 'total_questions', 'correct_answers',
            'total_points', 'max_points', 'passed', 'passing_score',
            'started_at', 'completed_at', 'time_taken_seconds', 'time_taken_formatted',
            'language_preference'
        ]
        read_only_fields = fields


# =============================================================================
# Resource Serializers
# =============================================================================

class ResourceListSerializer(serializers.ModelSerializer):
    """Minimal serializer for resource listings."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ar = serializers.CharField(source='category.name_ar', read_only=True)
    file_size_formatted = serializers.ReadOnlyField()
    video_duration_formatted = serializers.ReadOnlyField()
    primary_url = serializers.ReadOnlyField()
    resource_type_display = serializers.CharField(
        source='get_resource_type_display', read_only=True
    )

    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'title_ar', 'slug', 'description', 'description_ar',
            'resource_type', 'resource_type_display',
            'category', 'category_name', 'category_name_ar',
            'thumbnail_url', 'primary_url',
            'file_size_bytes', 'file_size_formatted', 'file_format',
            'video_duration_seconds', 'video_duration_formatted', 'video_platform',
            'source_name', 'language',
            'download_count', 'view_count', 'is_featured', 'display_order'
        ]
        read_only_fields = fields


class ResourceDetailSerializer(serializers.ModelSerializer):
    """Full serializer for resource detail view."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ar = serializers.CharField(source='category.name_ar', read_only=True)
    file_size_formatted = serializers.ReadOnlyField()
    video_duration_formatted = serializers.ReadOnlyField()
    primary_url = serializers.ReadOnlyField()
    resource_type_display = serializers.CharField(
        source='get_resource_type_display', read_only=True
    )
    related_resources = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'title_ar', 'slug', 'description', 'description_ar',
            'resource_type', 'resource_type_display',
            'category', 'category_name', 'category_name_ar',
            'file_url', 'external_url', 'primary_url', 'thumbnail_url',
            'file_size_bytes', 'file_size_formatted', 'file_format',
            'video_duration_seconds', 'video_duration_formatted', 'video_platform',
            'source_name', 'source_url', 'language',
            'download_count', 'view_count', 'is_featured', 'display_order',
            'related_resources', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_related_resources(self, obj):
        """Get related resources from same category or type."""
        filters = {'is_active': True}

        if obj.category:
            filters['category'] = obj.category
        else:
            filters['resource_type'] = obj.resource_type

        related = Resource.objects.filter(**filters).exclude(pk=obj.pk)[:4]
        return ResourceListSerializer(related, many=True).data


# =============================================================================
# Combined/Search Serializers
# =============================================================================

class CommunitySearchResultSerializer(serializers.Serializer):
    """Serializer for combined search results across community content."""

    articles = ArticleListSerializer(many=True)
    quizzes = PublicQuizListSerializer(many=True)
    resources = ResourceListSerializer(many=True)
    total_count = serializers.IntegerField()


class FeaturedContentSerializer(serializers.Serializer):
    """Serializer for featured content on homepage."""

    featured_articles = ArticleListSerializer(many=True)
    featured_quizzes = PublicQuizListSerializer(many=True)
    featured_resources = ResourceListSerializer(many=True)
    categories = ArticleCategorySerializer(many=True)
    stats = serializers.DictField()
