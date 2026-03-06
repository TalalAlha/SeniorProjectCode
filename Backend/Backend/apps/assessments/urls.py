from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailTemplateViewSet, AIEmailGenerationView

app_name = 'assessments'

router = DefaultRouter()
router.register(r'email-templates', EmailTemplateViewSet, basename='emailtemplate')

urlpatterns = [
    path('', include(router.urls)),
    path('ai/generate-emails/', AIEmailGenerationView.as_view(), name='ai-generate-emails'),
]
