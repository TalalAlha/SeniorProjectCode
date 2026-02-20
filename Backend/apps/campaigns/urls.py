from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampaignViewSet, QuizViewSet

app_name = 'campaigns'

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'quizzes', QuizViewSet, basename='quiz')

urlpatterns = [
    path('', include(router.urls)),
]
