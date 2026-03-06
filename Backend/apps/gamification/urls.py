"""
Gamification URLs
=================
URL routing for badges, points, and leaderboards.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BadgeViewSet, PointsViewSet, LeaderboardViewSet

app_name = 'gamification'

router = DefaultRouter()
router.register(r'badges', BadgeViewSet, basename='badge')
router.register(r'points', PointsViewSet, basename='points')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')

urlpatterns = [
    path('', include(router.urls)),
]

# API Endpoints Summary:
#
# Badges:
# GET    /badges/                    - List available badges
# GET    /badges/{id}/               - Get badge detail
# POST   /badges/                    - Create badge (admin only)
# PUT    /badges/{id}/               - Update badge (admin only)
# DELETE /badges/{id}/               - Delete badge (admin only)
# GET    /badges/my_badges/          - Get current user's earned badges
# GET    /badges/recent/             - Get recently awarded badges
# POST   /badges/{id}/bulk_award/    - Bulk award badge (admin only)
#
# Points:
# GET    /points/                    - List points records (admin sees all)
# GET    /points/{id}/               - Get points detail
# GET    /points/my_summary/         - Get current user's points summary
# GET    /points/my_transactions/    - Get current user's transaction history
# POST   /points/adjust/             - Admin manual adjustment
#
# Leaderboard:
# GET    /leaderboard/               - Get leaderboard (query: period, company, limit)
# GET    /leaderboard/my_position/   - Get current user's leaderboard position
