"""
Analytics URLs
==============
URL routing for dashboard, campaign, simulation, risk, training analytics, and exports.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardViewSet,
    CampaignAnalyticsViewSet,
    SimulationAnalyticsViewSet,
    RiskAnalyticsViewSet,
    TrainingAnalyticsViewSet,
    ExportViewSet,
)

app_name = 'analytics'

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'campaigns', CampaignAnalyticsViewSet, basename='campaign-analytics')
router.register(r'simulations', SimulationAnalyticsViewSet, basename='simulation-analytics')
router.register(r'risk', RiskAnalyticsViewSet, basename='risk-analytics')
router.register(r'training', TrainingAnalyticsViewSet, basename='training-analytics')
router.register(r'export', ExportViewSet, basename='export')

urlpatterns = [
    path('', include(router.urls)),
]

# API Endpoints Summary:
#
# Dashboard:
# GET    /analytics/dashboard/overview/         - Overall platform/company statistics
# GET    /analytics/dashboard/trends/           - Time-series trend data for charts
#        Query params: ?period=7d|30d|90d|custom&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&company=ID
#
# Campaign Analytics:
# GET    /analytics/campaigns/                  - List all campaigns with analytics
# GET    /analytics/campaigns/{id}/             - Detailed analytics for specific campaign
#        Query params: ?status=ACTIVE|COMPLETED&company=ID&period=7d|30d|90d|all
#
# Simulation Analytics:
# GET    /analytics/simulations/                - List all simulations with analytics + template comparison
# GET    /analytics/simulations/{id}/           - Detailed analytics for specific simulation
#        Query params: ?status=IN_PROGRESS|COMPLETED&company=ID
#
# Risk Analytics:
# GET    /analytics/risk/distribution/          - Current risk score distribution
# GET    /analytics/risk/trends/                - Risk score trends over time
# GET    /analytics/risk/high_risk_employees/   - List of high-risk employees with details
#        Query params: ?period=7d|30d|90d|custom&company=ID
#
# Training Analytics:
# GET    /analytics/training/                   - Training summary with module stats, effectiveness, pending
# GET    /analytics/training/effectiveness/     - Training effectiveness analysis (risk reduction)
#        Query params: ?company=ID
#
# Data Export:
# POST   /analytics/export/csv/                 - Export data to CSV
#        Body: {
#            "export_type": "campaigns|simulations|risk_scores|training|users",
#            "start_date": "YYYY-MM-DD",  // optional
#            "end_date": "YYYY-MM-DD",    // optional
#            "company_id": 1,             // super admin only
#            "include_pii": true          // include email/names
#        }
#
# Permissions:
# - All endpoints require authentication
# - Super Admin: Access to all companies (can filter by company_id)
# - Company Admin: Access only to their company's data
