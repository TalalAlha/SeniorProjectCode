"""
Company Management URLs
=======================
URL routing for company CRUD, user management, and statistics.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CompanyViewSet

app_name = 'companies'

router = DefaultRouter()
router.register(r'', CompanyViewSet, basename='company')

urlpatterns = [
    path('', include(router.urls)),
]

# API Endpoints Summary:
#
# Company CRUD (Super Admin only for create/delete):
# GET    /companies/                         - List all companies (Super Admin sees all, others see own)
# POST   /companies/                         - Create new company (Super Admin only)
# GET    /companies/{id}/                    - Get company details
# PUT    /companies/{id}/                    - Update company (Full update)
# PATCH  /companies/{id}/                    - Update company (Partial update)
# DELETE /companies/{id}/                    - Deactivate company (Super Admin only)
#
# Company Status:
# POST   /companies/{id}/activate/           - Activate company (Super Admin only)
# POST   /companies/{id}/deactivate/         - Deactivate company (Super Admin only)
#
# Company Statistics:
# GET    /companies/{id}/stats/              - Get comprehensive company statistics
# GET    /companies/{id}/activity/           - Get recent company activity log
#
# User Management:
# GET    /companies/{id}/users/              - List users in company
# POST   /companies/{id}/users/add/          - Add single user to company
# PUT    /companies/{id}/users/{user_id}/    - Update user (full update)
# PATCH  /companies/{id}/users/{user_id}/    - Update user (partial update)
# DELETE /companies/{id}/users/{user_id}/remove/  - Remove (deactivate) user
# POST   /companies/{id}/invite_users/       - Bulk invite users via email list
# POST   /companies/{id}/import_csv/         - Bulk import users from CSV file
#
# Utility:
# GET    /companies/my_company/              - Get current user's company details
#
# Query Parameters:
# - GET /companies/?is_active=true           - Filter by active status
# - GET /companies/?industry=TECH            - Filter by industry
# - GET /companies/?search=acme              - Search by name/email
# - GET /companies/{id}/users/?role=EMPLOYEE - Filter users by role
# - GET /companies/{id}/users/?is_active=true - Filter users by active status
# - GET /companies/{id}/users/?search=john   - Search users
# - GET /companies/{id}/activity/?limit=50   - Limit activity results
