from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SimulationTemplateViewSet,
    SimulationCampaignViewSet,
    EmailSimulationViewSet,
    track_pixel_view,
    track_link_click_view,
    landing_page_view,
    report_phishing_view,
    credentials_submitted_view
)

app_name = 'simulations'

# Router for ViewSets
router = DefaultRouter()
router.register(r'templates', SimulationTemplateViewSet, basename='template')
router.register(r'campaigns', SimulationCampaignViewSet, basename='campaign')
router.register(r'emails', EmailSimulationViewSet, basename='email-simulation')

urlpatterns = [
    # ViewSet routes (authenticated)
    # Templates: /api/v1/simulations/templates/
    # Campaigns: /api/v1/simulations/campaigns/
    # Email Simulations: /api/v1/simulations/emails/
    path('', include(router.urls)),

    # Tracking endpoints (no authentication - public access via unique tokens)
    # These are embedded in simulation emails and must be publicly accessible

    # Tracking pixel - embedded as <img> in emails to detect opens
    # GET /api/v1/simulations/track/<tracking_token>/
    path(
        'track/<uuid:tracking_token>/',
        track_pixel_view,
        name='tracking-pixel'
    ),

    # Phishing link - the lure link that employees might click
    # GET /api/v1/simulations/link/<link_token>/
    path(
        'link/<str:link_token>/',
        track_link_click_view,
        name='phishing-link'
    ),

    # Landing page - "You've been caught" educational page
    # GET /api/v1/simulations/landing/<link_token>/
    path(
        'landing/<str:link_token>/',
        landing_page_view,
        name='landing-page'
    ),

    # Report phishing - employee reports the email as suspicious (positive action)
    # POST /api/v1/simulations/report/<link_token>/
    path(
        'report/<str:link_token>/',
        report_phishing_view,
        name='report-phishing'
    ),

    # Credentials submitted - logs when employee enters credentials on fake login
    # POST /api/v1/simulations/credentials/<link_token>/
    path(
        'credentials/<str:link_token>/',
        credentials_submitted_view,
        name='credentials-submitted'
    ),
]
