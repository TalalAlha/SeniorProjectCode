"""
URL configuration for phishaware_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation with Swagger/ReDoc
schema_view = get_schema_view(
    openapi.Info(
        title="PhishAware API",
        default_version='v1',
        description="PhishAware - AI-Powered Phishing Simulation and Awareness Platform API",
        terms_of_service="https://www.phishaware.com/terms/",
        contact=openapi.Contact(email="support@phishaware.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API Endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/employees/', include('apps.accounts.urls_employees')),
    path('api/v1/companies/', include('apps.companies.urls')),
    path('api/v1/campaigns/', include('apps.campaigns.urls')),
    path('api/v1/assessments/', include('apps.assessments.urls')),
    path('api/v1/simulations/', include('apps.simulations.urls')),
    path('api/v1/training/', include('apps.training.urls')),
    path('api/v1/gamification/', include('apps.gamification.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),

    # Public Community Portal (no authentication required)
    path('api/v1/community/', include('apps.community.urls')),

    # Notifications
    path('api/v1/notifications/', include('apps.notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
