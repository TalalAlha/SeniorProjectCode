"""
Training App URLs
=================
URL routing for Risk Scoring & Remediation Training.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RiskScoreViewSet,
    TrainingModuleViewSet,
    TrainingQuestionViewSet,
    RemediationTrainingViewSet
)

app_name = 'training'

router = DefaultRouter()
router.register(r'risk-scores', RiskScoreViewSet, basename='risk-score')
router.register(r'modules', TrainingModuleViewSet, basename='training-module')
router.register(r'questions', TrainingQuestionViewSet, basename='training-question')
router.register(r'assignments', RemediationTrainingViewSet, basename='remediation-training')

urlpatterns = [
    path('', include(router.urls)),
]

# API Endpoints Summary:
#
# Risk Scores:
# GET    /risk-scores/                    - List all risk scores (filtered by role)
# GET    /risk-scores/{id}/               - Get risk score detail
# PATCH  /risk-scores/{id}/               - Update risk score (admin only)
# GET    /risk-scores/my_score/           - Get current user's risk score
# GET    /risk-scores/statistics/         - Get company-wide statistics (admin only)
# GET    /risk-scores/{id}/history/       - Get risk score history
# POST   /risk-scores/recalculate/        - Recalculate risk scores (admin only)
#
# Training Modules:
# GET    /modules/                         - List training modules
# POST   /modules/                         - Create training module (admin only)
# GET    /modules/{id}/                    - Get training module detail
# PUT    /modules/{id}/                    - Update training module (admin only)
# DELETE /modules/{id}/                    - Delete training module (admin only)
# GET    /modules/{id}/questions/          - Get module questions
# GET    /modules/categories/              - Get available categories
#
# Training Questions:
# GET    /questions/                       - List questions (admin only)
# POST   /questions/                       - Create question (admin only)
# GET    /questions/{id}/                  - Get question detail (admin only)
# PUT    /questions/{id}/                  - Update question (admin only)
# DELETE /questions/{id}/                  - Delete question (admin only)
#
# Remediation Training Assignments:
# GET    /assignments/                     - List training assignments
# POST   /assignments/                     - Create assignment (admin only)
# GET    /assignments/{id}/                - Get assignment detail
# POST   /assignments/{id}/start/          - Start training
# POST   /assignments/{id}/view_content/   - Mark content as viewed
# GET    /assignments/{id}/quiz/           - Get quiz questions
# POST   /assignments/{id}/submit_quiz/    - Submit quiz answers
# POST   /assignments/bulk_assign/         - Bulk assign training (admin only)
# GET    /assignments/my_trainings/        - Get current user's trainings
# GET    /assignments/pending/             - Get pending trainings
# GET    /assignments/overdue/             - Get overdue trainings (admin only)
