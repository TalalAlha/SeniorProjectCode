"""
Community App URLs
==================
Public-facing URLs for the awareness portal.
All endpoints are accessible without authentication.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ArticleCategoryViewSet,
    ArticleViewSet,
    PublicQuizViewSet,
    ResourceViewSet,
    CommunityPortalViewSet,
)

app_name = 'community'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'categories', ArticleCategoryViewSet, basename='category')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'quizzes', PublicQuizViewSet, basename='quiz')
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'portal', CommunityPortalViewSet, basename='portal')

urlpatterns = [
    path('', include(router.urls)),
]

# =============================================================================
# API Endpoint Documentation
# =============================================================================
#
# CATEGORIES
# ----------
# GET  /api/community/categories/                    - List all categories
# GET  /api/community/categories/{slug}/             - Get category details
# GET  /api/community/categories/{slug}/articles/    - Get articles in category
# GET  /api/community/categories/{slug}/quizzes/     - Get quizzes in category
# GET  /api/community/categories/{slug}/resources/   - Get resources in category
#
# ARTICLES
# --------
# GET  /api/community/articles/                      - List published articles
# GET  /api/community/articles/{slug}/               - Get article detail (increments view)
# GET  /api/community/articles/featured/             - Get featured articles
# GET  /api/community/articles/recent/               - Get recent articles
# GET  /api/community/articles/popular/              - Get popular articles
# GET  /api/community/articles/by_tag/?tag=phishing  - Get articles by tag
# POST /api/community/articles/{slug}/share/         - Track share
#
# QUIZZES
# -------
# GET  /api/community/quizzes/                       - List published quizzes
# GET  /api/community/quizzes/{slug}/                - Get quiz detail with questions
# GET  /api/community/quizzes/{slug}/questions/      - Get quiz questions only
# GET  /api/community/quizzes/featured/              - Get featured quizzes
# GET  /api/community/quizzes/by_difficulty/         - Get quizzes by difficulty
# POST /api/community/quizzes/{slug}/start_attempt/  - Start quiz attempt
#      Request: {"session_id": "...", "language_preference": "en"}
#      Response: {attempt_id, questions, time_limit, ...}
# POST /api/community/quizzes/{slug}/submit_attempt/{attempt_id}/
#      Request: {"answers": {"question_id": selected_index, ...}}
#      Response: {score, passed, correct_answers, ...}
# GET  /api/community/quizzes/{slug}/attempt/{attempt_id}/
#      Get completed attempt results
#
# RESOURCES
# ---------
# GET  /api/community/resources/                     - List all resources
# GET  /api/community/resources/{slug}/              - Get resource detail (increments view)
# GET  /api/community/resources/featured/            - Get featured resources
# GET  /api/community/resources/by_type/             - Get resource types with counts
# GET  /api/community/resources/by_type/?type=PDF    - Get resources by type
# GET  /api/community/resources/videos/              - Get video resources
# GET  /api/community/resources/downloads/           - Get downloadable resources
# POST /api/community/resources/{slug}/download/     - Track download
#
# PORTAL (Aggregate)
# ------------------
# GET  /api/community/portal/homepage/               - Get featured content for homepage
# GET  /api/community/portal/search/?q=query         - Search all content
# GET  /api/community/portal/search/?q=query&type=article  - Search specific type
# GET  /api/community/portal/stats/                  - Get portal statistics
#
# =============================================================================
# Query Parameters (common to most list endpoints)
# =============================================================================
#
# Pagination:
#   ?page=1&page_size=10
#
# Filtering:
#   ?category=1                    - Filter by category ID
#   ?is_featured=true              - Filter featured items
#   ?difficulty=EASY               - Filter quizzes by difficulty
#   ?resource_type=PDF             - Filter resources by type
#   ?language=ar                   - Filter by language
#
# Searching:
#   ?search=keyword                - Search in title, description (bilingual)
#
# Ordering:
#   ?ordering=-published_at        - Sort by published date (descending)
#   ?ordering=view_count           - Sort by view count (ascending)
#   ?ordering=-download_count      - Sort by downloads (descending)
#
# Language:
#   ?lang=ar                       - Get Arabic content preference
#
# =============================================================================
