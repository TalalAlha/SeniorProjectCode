"""
Community App Views
===================
Public-facing API endpoints for awareness portal.
All endpoints allow public access (no authentication required).
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import F, Q
from django.utils import timezone

from .models import (
    ArticleCategory, Article, PublicQuiz,
    PublicQuizQuestion, PublicQuizAttempt, Resource
)
from .serializers import (
    ArticleCategorySerializer, ArticleCategoryDetailSerializer,
    ArticleListSerializer, ArticleDetailSerializer,
    PublicQuizListSerializer, PublicQuizDetailSerializer,
    PublicQuizQuestionSerializer, PublicQuizQuestionWithAnswerSerializer,
    PublicQuizAttemptCreateSerializer, PublicQuizAttemptSubmitSerializer,
    PublicQuizAttemptResultSerializer,
    ResourceListSerializer, ResourceDetailSerializer,
    FeaturedContentSerializer
)


class PublicViewSetMixin:
    """Mixin for public viewsets with common configuration."""

    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    def get_language(self):
        """Get preferred language from request."""
        return self.request.query_params.get('lang', 'en')

    def filter_queryset_by_params(self, queryset, filter_fields):
        """Manually filter queryset by query parameters."""
        for field in filter_fields:
            value = self.request.query_params.get(field)
            if value is not None:
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                queryset = queryset.filter(**{field: value})
        return queryset


# =============================================================================
# Article Category ViewSet
# =============================================================================

class ArticleCategoryViewSet(PublicViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Public API for article categories.

    list: Get all active categories
    retrieve: Get category details with content counts
    """

    queryset = ArticleCategory.objects.filter(is_active=True)
    serializer_class = ArticleCategorySerializer
    lookup_field = 'slug'
    search_fields = ['name', 'name_ar', 'description', 'description_ar']
    ordering_fields = ['display_order', 'name', 'article_count']
    ordering = ['display_order', 'name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticleCategoryDetailSerializer
        return ArticleCategorySerializer

    @action(detail=True, methods=['get'])
    def articles(self, request, slug=None):
        """Get all published articles in this category."""
        category = self.get_object()
        articles = Article.objects.filter(
            category=category,
            status='PUBLISHED',
            is_active=True
        ).order_by('-published_at')

        page = self.paginate_queryset(articles)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def quizzes(self, request, slug=None):
        """Get all published quizzes in this category."""
        category = self.get_object()
        quizzes = PublicQuiz.objects.filter(
            category=category,
            status='PUBLISHED',
            is_active=True
        ).order_by('-created_at')

        page = self.paginate_queryset(quizzes)
        if page is not None:
            serializer = PublicQuizListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PublicQuizListSerializer(quizzes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def resources(self, request, slug=None):
        """Get all active resources in this category."""
        category = self.get_object()
        resources = Resource.objects.filter(
            category=category,
            is_active=True
        ).order_by('display_order', '-created_at')

        page = self.paginate_queryset(resources)
        if page is not None:
            serializer = ResourceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ResourceListSerializer(resources, many=True)
        return Response(serializer.data)


# =============================================================================
# Article ViewSet
# =============================================================================

class ArticleViewSet(PublicViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Public API for awareness articles.

    list: Get published articles with filtering
    retrieve: Get article detail (auto-increments view count)
    """

    queryset = Article.objects.filter(
        status='PUBLISHED',
        is_active=True
    ).select_related('category', 'author')
    serializer_class = ArticleListSerializer
    lookup_field = 'slug'
    search_fields = ['title', 'title_ar', 'excerpt', 'excerpt_ar', 'content', 'content_ar', 'tags']
    ordering_fields = ['published_at', 'view_count', 'reading_time_minutes']
    ordering = ['-published_at']

    def get_queryset(self):
        """Filter by publication date and query parameters."""
        queryset = super().get_queryset()
        # Only show articles that have been published (not future-dated)
        queryset = queryset.filter(
            Q(published_at__isnull=True) | Q(published_at__lte=timezone.now())
        )
        # Apply manual filters
        return self.filter_queryset_by_params(queryset, ['category', 'is_featured'])

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        return ArticleListSerializer

    def retrieve(self, request, *args, **kwargs):
        """Get article and increment view count."""
        instance = self.get_object()

        # Increment view count (thread-safe)
        Article.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)

        # Refresh to get updated count
        instance.refresh_from_db()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured articles."""
        articles = self.get_queryset().filter(is_featured=True)[:6]
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get most recent articles."""
        limit = int(request.query_params.get('limit', 5))
        limit = min(limit, 20)  # Cap at 20
        articles = self.get_queryset()[:limit]
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most viewed articles."""
        limit = int(request.query_params.get('limit', 5))
        limit = min(limit, 20)
        articles = self.get_queryset().order_by('-view_count')[:limit]
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def share(self, request, slug=None):
        """Increment share count for article."""
        instance = self.get_object()
        Article.objects.filter(pk=instance.pk).update(share_count=F('share_count') + 1)
        return Response({'status': 'shared', 'share_count': instance.share_count + 1})

    @action(detail=False, methods=['get'])
    def by_tag(self, request):
        """Get articles by tag."""
        tag = request.query_params.get('tag', '')
        if not tag:
            return Response(
                {'error': 'Tag parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        articles = self.get_queryset().filter(tags__icontains=tag)

        page = self.paginate_queryset(articles)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)


# =============================================================================
# Public Quiz ViewSet
# =============================================================================

class PublicQuizViewSet(PublicViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Public API for awareness quizzes.

    list: Get published quizzes
    retrieve: Get quiz detail with questions
    start_attempt: Start a new quiz attempt
    submit_attempt: Submit quiz answers
    """

    queryset = PublicQuiz.objects.filter(
        status='PUBLISHED',
        is_active=True
    ).select_related('category')
    serializer_class = PublicQuizListSerializer
    lookup_field = 'slug'
    search_fields = ['title', 'title_ar', 'description', 'description_ar']
    ordering_fields = ['created_at', 'total_attempts', 'average_score', 'difficulty']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by query parameters."""
        queryset = super().get_queryset()
        return self.filter_queryset_by_params(queryset, ['category', 'difficulty', 'is_featured'])

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PublicQuizDetailSerializer
        return PublicQuizListSerializer

    @action(detail=True, methods=['get'])
    def questions(self, request, slug=None):
        """Get quiz questions (without correct answers)."""
        quiz = self.get_object()
        questions = quiz.questions.filter(is_active=True).order_by('question_number')

        if quiz.randomize_questions:
            questions = list(questions)
            import random
            random.shuffle(questions)

        serializer = PublicQuizQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start_attempt(self, request, slug=None):
        """
        Start a new quiz attempt.

        Request body:
        {
            "session_id": "optional-session-id",
            "language_preference": "en"  // or "ar"
        }
        """
        quiz = self.get_object()

        # Prepare data
        data = {
            'quiz': quiz.id,
            'session_id': request.data.get('session_id', ''),
            'language_preference': request.data.get('language_preference', 'en')
        }

        serializer = PublicQuizAttemptCreateSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save()

        # Increment total attempts counter
        PublicQuiz.objects.filter(pk=quiz.pk).update(
            total_attempts=F('total_attempts') + 1
        )

        # Return attempt info with questions
        questions = quiz.questions.filter(is_active=True).order_by('question_number')
        if quiz.randomize_questions:
            questions = list(questions)
            import random
            random.shuffle(questions)

        return Response({
            'attempt_id': attempt.id,
            'quiz_id': quiz.id,
            'quiz_title': quiz.title,
            'quiz_title_ar': quiz.title_ar,
            'time_limit_minutes': quiz.time_limit_minutes,
            'passing_score': quiz.passing_score,
            'started_at': attempt.started_at,
            'questions': PublicQuizQuestionSerializer(questions, many=True).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='submit_attempt/(?P<attempt_id>[0-9]+)')
    def submit_attempt(self, request, slug=None, attempt_id=None):
        """
        Submit quiz answers for an attempt.

        Request body:
        {
            "answers": {
                "1": 2,  // question_id: selected_index
                "2": 0,
                "3": 1
            }
        }
        """
        quiz = self.get_object()

        # Get the attempt
        try:
            attempt = PublicQuizAttempt.objects.get(
                id=attempt_id,
                quiz=quiz,
                is_completed=False
            )
        except PublicQuizAttempt.DoesNotExist:
            return Response(
                {'error': 'Invalid or already completed attempt'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate answers
        serializer = PublicQuizAttemptSubmitSerializer(
            data=request.data,
            context={'attempt': attempt}
        )
        serializer.is_valid(raise_exception=True)

        # Submit and get results
        results = attempt.submit(serializer.validated_data['answers'])

        # Build response
        response_data = {
            'attempt_id': attempt.id,
            'score': results['score'],
            'passed': results['passed'],
            'correct_answers': results['correct'],
            'total_questions': results['total'],
            'total_points': results['total_points'],
            'max_points': results['max_points'],
            'passing_score': quiz.passing_score,
            'time_taken': results['time_taken']
        }

        # Include detailed results if quiz allows showing correct answers
        if quiz.show_correct_answers and results['results']:
            # Get questions with explanations
            questions = quiz.questions.filter(is_active=True)
            questions_with_answers = PublicQuizQuestionWithAnswerSerializer(
                questions, many=True
            ).data
            response_data['question_results'] = results['results']
            response_data['questions_with_answers'] = questions_with_answers

        return Response(response_data)

    @action(detail=True, methods=['get'], url_path='attempt/(?P<attempt_id>[0-9]+)')
    def get_attempt(self, request, slug=None, attempt_id=None):
        """Get a specific attempt's results."""
        quiz = self.get_object()

        try:
            attempt = PublicQuizAttempt.objects.get(
                id=attempt_id,
                quiz=quiz,
                is_completed=True
            )
        except PublicQuizAttempt.DoesNotExist:
            return Response(
                {'error': 'Attempt not found or not completed'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PublicQuizAttemptResultSerializer(attempt)
        response_data = serializer.data

        # Include questions with answers if allowed
        if quiz.show_correct_answers:
            questions = quiz.questions.filter(is_active=True)
            response_data['questions_with_answers'] = PublicQuizQuestionWithAnswerSerializer(
                questions, many=True
            ).data
            response_data['user_answers'] = attempt.answers

        return Response(response_data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured quizzes."""
        quizzes = self.get_queryset().filter(is_featured=True)[:6]
        serializer = PublicQuizListSerializer(quizzes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_difficulty(self, request):
        """Get quizzes grouped by difficulty."""
        easy = self.get_queryset().filter(difficulty='EASY')[:5]
        medium = self.get_queryset().filter(difficulty='MEDIUM')[:5]
        hard = self.get_queryset().filter(difficulty='HARD')[:5]

        return Response({
            'easy': PublicQuizListSerializer(easy, many=True).data,
            'medium': PublicQuizListSerializer(medium, many=True).data,
            'hard': PublicQuizListSerializer(hard, many=True).data
        })


# =============================================================================
# Resource ViewSet
# =============================================================================

class ResourceViewSet(PublicViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Public API for downloadable resources.

    list: Get all active resources
    retrieve: Get resource detail (auto-increments view count)
    download: Track download and return resource URL
    """

    queryset = Resource.objects.filter(is_active=True).select_related('category')
    serializer_class = ResourceListSerializer
    lookup_field = 'slug'
    search_fields = ['title', 'title_ar', 'description', 'description_ar', 'source_name']
    ordering_fields = ['display_order', 'created_at', 'download_count', 'view_count']
    ordering = ['display_order', '-created_at']

    def get_queryset(self):
        """Filter by query parameters."""
        queryset = super().get_queryset()
        return self.filter_queryset_by_params(queryset, ['category', 'resource_type', 'language', 'is_featured'])

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ResourceDetailSerializer
        return ResourceListSerializer

    def retrieve(self, request, *args, **kwargs):
        """Get resource and increment view count."""
        instance = self.get_object()

        # Increment view count (thread-safe)
        Resource.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)

        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def download(self, request, slug=None):
        """
        Track download and return resource URL.
        """
        instance = self.get_object()

        # Increment download count (thread-safe)
        Resource.objects.filter(pk=instance.pk).update(
            download_count=F('download_count') + 1
        )

        return Response({
            'status': 'tracked',
            'download_url': instance.file_url or instance.external_url,
            'download_count': instance.download_count + 1
        })

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured resources."""
        resources = self.get_queryset().filter(is_featured=True)[:6]
        serializer = ResourceListSerializer(resources, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get resources grouped by type."""
        resource_type = request.query_params.get('type')

        if resource_type:
            resources = self.get_queryset().filter(resource_type=resource_type.upper())
        else:
            # Return counts by type
            from django.db.models import Count
            type_counts = self.get_queryset().values('resource_type').annotate(
                count=Count('id')
            ).order_by('-count')

            return Response({
                'types': list(type_counts),
                'available_types': [choice[0] for choice in Resource.RESOURCE_TYPE_CHOICES]
            })

        page = self.paginate_queryset(resources)
        if page is not None:
            serializer = ResourceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ResourceListSerializer(resources, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def videos(self, request):
        """Get video resources."""
        videos = self.get_queryset().filter(resource_type='VIDEO')

        page = self.paginate_queryset(videos)
        if page is not None:
            serializer = ResourceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ResourceListSerializer(videos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def downloads(self, request):
        """Get downloadable resources (PDFs, guides, etc.)."""
        downloadable_types = ['PDF', 'GUIDE', 'CHECKLIST', 'INFOGRAPHIC', 'POSTER']
        resources = self.get_queryset().filter(resource_type__in=downloadable_types)

        page = self.paginate_queryset(resources)
        if page is not None:
            serializer = ResourceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ResourceListSerializer(resources, many=True)
        return Response(serializer.data)


# =============================================================================
# Community Portal ViewSet (Homepage/Aggregate Endpoints)
# =============================================================================

class CommunityPortalViewSet(PublicViewSetMixin, viewsets.ViewSet):
    """
    Aggregate endpoints for the community portal homepage.
    """

    @action(detail=False, methods=['get'])
    def homepage(self, request):
        """
        Get all featured content for homepage.
        Returns featured articles, quizzes, resources, and categories.
        """
        featured_articles = Article.objects.filter(
            status='PUBLISHED',
            is_active=True,
            is_featured=True
        ).select_related('category')[:4]

        featured_quizzes = PublicQuiz.objects.filter(
            status='PUBLISHED',
            is_active=True,
            is_featured=True
        ).select_related('category')[:4]

        featured_resources = Resource.objects.filter(
            is_active=True,
            is_featured=True
        ).select_related('category')[:4]

        categories = ArticleCategory.objects.filter(
            is_active=True
        ).order_by('display_order')[:8]

        # Aggregate stats
        stats = {
            'total_articles': Article.objects.filter(
                status='PUBLISHED', is_active=True
            ).count(),
            'total_quizzes': PublicQuiz.objects.filter(
                status='PUBLISHED', is_active=True
            ).count(),
            'total_resources': Resource.objects.filter(is_active=True).count(),
            'total_quiz_attempts': PublicQuizAttempt.objects.filter(
                is_completed=True
            ).count(),
        }

        serializer = FeaturedContentSerializer({
            'featured_articles': featured_articles,
            'featured_quizzes': featured_quizzes,
            'featured_resources': featured_resources,
            'categories': categories,
            'stats': stats
        })

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search across all community content.
        Query params: q (search query), type (article/quiz/resource)
        """
        query = request.query_params.get('q', '').strip()
        content_type = request.query_params.get('type', 'all')

        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = {
            'articles': [],
            'quizzes': [],
            'resources': [],
            'total_count': 0
        }

        # Search articles
        if content_type in ['all', 'article']:
            articles = Article.objects.filter(
                Q(title__icontains=query) |
                Q(title_ar__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(excerpt_ar__icontains=query) |
                Q(tags__icontains=query),
                status='PUBLISHED',
                is_active=True
            )[:10]
            results['articles'] = ArticleListSerializer(articles, many=True).data

        # Search quizzes
        if content_type in ['all', 'quiz']:
            quizzes = PublicQuiz.objects.filter(
                Q(title__icontains=query) |
                Q(title_ar__icontains=query) |
                Q(description__icontains=query) |
                Q(description_ar__icontains=query),
                status='PUBLISHED',
                is_active=True
            )[:10]
            results['quizzes'] = PublicQuizListSerializer(quizzes, many=True).data

        # Search resources
        if content_type in ['all', 'resource']:
            resources = Resource.objects.filter(
                Q(title__icontains=query) |
                Q(title_ar__icontains=query) |
                Q(description__icontains=query) |
                Q(description_ar__icontains=query),
                is_active=True
            )[:10]
            results['resources'] = ResourceListSerializer(resources, many=True).data

        results['total_count'] = (
            len(results['articles']) +
            len(results['quizzes']) +
            len(results['resources'])
        )

        return Response(results)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get community portal statistics."""
        from django.db.models import Avg, Sum

        return Response({
            'content': {
                'total_articles': Article.objects.filter(
                    status='PUBLISHED', is_active=True
                ).count(),
                'total_quizzes': PublicQuiz.objects.filter(
                    status='PUBLISHED', is_active=True
                ).count(),
                'total_resources': Resource.objects.filter(is_active=True).count(),
                'total_categories': ArticleCategory.objects.filter(is_active=True).count(),
            },
            'engagement': {
                'total_article_views': Article.objects.filter(
                    status='PUBLISHED', is_active=True
                ).aggregate(total=Sum('view_count'))['total'] or 0,
                'total_quiz_attempts': PublicQuizAttempt.objects.count(),
                'total_quiz_completions': PublicQuizAttempt.objects.filter(
                    is_completed=True
                ).count(),
                'average_quiz_score': PublicQuizAttempt.objects.filter(
                    is_completed=True
                ).aggregate(avg=Avg('score'))['avg'] or 0,
                'total_resource_downloads': Resource.objects.filter(
                    is_active=True
                ).aggregate(total=Sum('download_count'))['total'] or 0,
            }
        })
