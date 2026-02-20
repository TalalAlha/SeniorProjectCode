from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
import random
import logging

logger = logging.getLogger(__name__)

from .models import Campaign, Quiz, QuizResult
from apps.assessments.models import EmailTemplate, QuizQuestion
from .serializers import (
    CampaignListSerializer,
    CampaignDetailSerializer,
    CampaignCreateSerializer,
    QuizSerializer,
    QuizQuestionSimpleSerializer,
    QuizQuestionDetailSerializer,
    QuizResultSerializer,
    AnswerQuestionSerializer
)
from apps.core.permissions import (
    IsSuperAdminOrCompanyAdmin,
    HasCompanyAccess,
    IsEmployee
)


class CampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Campaign CRUD operations.

    - Super Admins and Company Admins can create, update, delete campaigns
    - Employees can only view campaigns for their company
    """

    queryset = Campaign.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create' or self.action == 'update':
            return CampaignCreateSerializer
        elif self.action == 'retrieve':
            return CampaignDetailSerializer
        return CampaignListSerializer

    def get_queryset(self):
        """Filter campaigns based on user role."""
        user = self.request.user

        if user.is_super_admin:
            return Campaign.objects.all()

        # Company admins and employees see only their company's campaigns
        if user.has_company_access:
            return Campaign.objects.filter(company=user.company)

        return Campaign.objects.none()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]

    def perform_create(self, serializer):
        """Create campaign and auto-generate AI email templates."""
        campaign = serializer.save()

        try:
            from apps.campaigns.ai_helper import generate_campaign_emails

            templates = generate_campaign_emails(
                campaign=campaign,
                num_phishing=campaign.num_phishing_emails,
                num_legitimate=campaign.num_legitimate_emails,
            )
            logger.info(
                "Generated %d AI email templates for campaign '%s'",
                len(templates), campaign.name,
            )
        except Exception as e:
            logger.error(
                "AI email generation failed for campaign '%s': %s",
                campaign.name, e,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def activate(self, request, pk=None):
        """Activate a campaign and set it to active status."""
        campaign = self.get_object()

        if campaign.status == 'ACTIVE':
            return Response(
                {'error': 'Campaign is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if campaign has enough emails
        total_emails = campaign.email_templates.count()
        if total_emails < campaign.num_emails:
            return Response(
                {'error': f'Campaign needs {campaign.num_emails} emails but only has {total_emails}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.status = 'ACTIVE'
        if not campaign.start_date:
            campaign.start_date = timezone.now()
        campaign.save()

        return Response(
            CampaignDetailSerializer(campaign).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def assign_to_employees(self, request, pk=None):
        """Assign campaign to employees by creating quiz instances."""
        campaign = self.get_object()
        employee_ids = request.data.get('employee_ids', [])

        if not employee_ids:
            return Response(
                {'error': 'employee_ids list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_quizzes = []
        errors = []

        for employee_id in employee_ids:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                employee = User.objects.get(id=employee_id, role='EMPLOYEE', company=campaign.company)

                # Check if quiz already exists
                quiz, created = Quiz.objects.get_or_create(
                    campaign=campaign,
                    employee=employee
                )

                if created:
                    # Generate quiz questions for this employee
                    self._generate_quiz_questions(quiz)
                    created_quizzes.append(QuizSerializer(quiz).data)
                else:
                    errors.append(f"Quiz already exists for employee {employee.email}")

            except Exception as e:
                errors.append(f"Error creating quiz for employee {employee_id}: {str(e)}")

        # Update campaign statistics
        campaign.total_participants = campaign.quizzes.count()
        campaign.save()

        return Response({
            'created_quizzes': created_quizzes,
            'errors': errors,
            'total_created': len(created_quizzes)
        }, status=status.HTTP_201_CREATED)

    def _generate_quiz_questions(self, quiz):
        """Generate randomized questions for a quiz from campaign's email pool."""
        campaign = quiz.campaign

        # Get all email templates for this campaign
        phishing_emails = list(campaign.email_templates.filter(email_type='PHISHING'))
        legitimate_emails = list(campaign.email_templates.filter(email_type='LEGITIMATE'))

        # Randomize selection
        random.shuffle(phishing_emails)
        random.shuffle(legitimate_emails)

        # Select required number of each type
        selected_phishing = phishing_emails[:campaign.num_phishing_emails]
        selected_legitimate = legitimate_emails[:campaign.num_legitimate_emails]

        # Combine and shuffle
        all_emails = selected_phishing + selected_legitimate
        random.shuffle(all_emails)

        # Create quiz questions
        for index, email_template in enumerate(all_emails, start=1):
            QuizQuestion.objects.create(
                quiz=quiz,
                email_template=email_template,
                question_number=index
            )

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, HasCompanyAccess])
    def statistics(self, request, pk=None):
        """Get detailed statistics for a campaign."""
        campaign = self.get_object()

        stats = {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'status': campaign.status,
            'total_participants': campaign.total_participants,
            'completed_participants': campaign.completed_participants,
            'completion_rate': float(campaign.completion_rate),
            'average_score': float(campaign.average_score) if campaign.average_score else None,
            'total_emails': campaign.num_emails,
            'phishing_emails': campaign.num_phishing_emails,
            'legitimate_emails': campaign.num_legitimate_emails,
            'risk_distribution': self._get_risk_distribution(campaign),
            'top_performers': self._get_top_performers(campaign, limit=5),
            'needs_training': self._get_employees_needing_training(campaign)
        }

        return Response(stats, status=status.HTTP_200_OK)

    def _get_risk_distribution(self, campaign):
        """Get distribution of risk levels for campaign results."""
        results = campaign.results.all()
        return {
            'low': results.filter(risk_level='LOW').count(),
            'medium': results.filter(risk_level='MEDIUM').count(),
            'high': results.filter(risk_level='HIGH').count(),
            'critical': results.filter(risk_level='CRITICAL').count()
        }

    def _get_top_performers(self, campaign, limit=5):
        """Get top performing employees in the campaign."""
        results = campaign.results.order_by('-score')[:limit]
        return QuizResultSerializer(results, many=True).data

    def _get_employees_needing_training(self, campaign):
        """Get employees who need additional training (failed or high risk)."""
        results = campaign.results.filter(
            Q(score__lt=70) | Q(risk_level__in=['HIGH', 'CRITICAL'])
        )
        return QuizResultSerializer(results, many=True).data


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Quiz operations.

    Employees can view and take their own quizzes.
    Admins can view all quizzes for their company.
    """

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter quizzes based on user role."""
        user = self.request.user

        if user.is_super_admin:
            return Quiz.objects.all()

        if user.is_company_admin:
            return Quiz.objects.filter(campaign__company=user.company)

        # Employees see only their own quizzes
        return Quiz.objects.filter(employee=user)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def questions(self, request, pk=None):
        """Get all questions for a quiz (without answers)."""
        quiz = self.get_object()

        # Only the assigned employee can view their quiz questions
        if quiz.employee != request.user and not request.user.is_company_admin and not request.user.is_super_admin:
            return Response(
                {'error': 'You do not have permission to view this quiz'},
                status=status.HTTP_403_FORBIDDEN
            )

        questions = quiz.questions.all().order_by('question_number')
        serializer = QuizQuestionSimpleSerializer(questions, many=True)

        # Replace {employee_name} placeholder with the actual employee name
        employee_name = quiz.employee.first_name or quiz.employee.get_full_name() or 'User'
        questions_data = serializer.data
        for q in questions_data:
            if q.get('email_body'):
                q['email_body'] = q['email_body'].replace('{employee_name}', employee_name)

        return Response({
            'quiz_id': quiz.id,
            'campaign_name': quiz.campaign.name,
            'status': quiz.status,
            'total_questions': quiz.total_questions,
            'current_question_index': quiz.current_question_index,
            'questions': questions_data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEmployee])
    def start(self, request, pk=None):
        """Start a quiz (mark as in progress)."""
        quiz = self.get_object()

        # Only the assigned employee can start their quiz
        if quiz.employee != request.user:
            return Response(
                {'error': 'You can only start your own quiz'},
                status=status.HTTP_403_FORBIDDEN
            )

        if quiz.status == 'COMPLETED':
            return Response(
                {'error': 'Quiz has already been completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quiz.status == 'IN_PROGRESS':
            return Response(
                QuizSerializer(quiz).data,
                status=status.HTTP_200_OK
            )

        quiz.status = 'IN_PROGRESS'
        quiz.started_at = timezone.now()
        quiz.save()

        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEmployee])
    def answer_question(self, request, pk=None):
        """Submit an answer to a specific question."""
        quiz = self.get_object()

        # Only the assigned employee can answer their quiz
        if quiz.employee != request.user:
            return Response(
                {'error': 'You can only answer your own quiz questions'},
                status=status.HTTP_403_FORBIDDEN
            )

        if quiz.status == 'COMPLETED':
            return Response(
                {'error': 'Quiz has already been completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get question number from request
        question_number = request.data.get('question_number')
        if not question_number:
            return Response(
                {'error': 'question_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            question = quiz.questions.get(question_number=question_number)
        except QuizQuestion.DoesNotExist:
            return Response(
                {'error': f'Question {question_number} not found in this quiz'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate and save answer
        serializer = AnswerQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question.answer = serializer.validated_data['answer']
        question.confidence_level = serializer.validated_data.get('confidence_level')
        question.time_spent_seconds = serializer.validated_data.get('time_spent_seconds')
        question.answered_at = timezone.now()
        question.check_answer()  # Check if answer is correct
        question.save()

        # Update quiz progress
        quiz.current_question_index = max(quiz.current_question_index, question_number)
        quiz.save()

        return Response({
            'message': 'Answer submitted successfully',
            'question_number': question_number,
            'quiz_progress': quiz.progress_percentage
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEmployee])
    def submit(self, request, pk=None):
        """Submit and finalize the quiz, calculate results."""
        quiz = self.get_object()

        # Only the assigned employee can submit their quiz
        if quiz.employee != request.user:
            return Response(
                {'error': 'You can only submit your own quiz'},
                status=status.HTTP_403_FORBIDDEN
            )

        if quiz.status == 'COMPLETED':
            return Response(
                {'error': 'Quiz has already been completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if all questions are answered
        unanswered = quiz.questions.filter(answer__isnull=True).count()
        if unanswered > 0:
            return Response(
                {'error': f'{unanswered} questions are still unanswered'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate results
        with transaction.atomic():
            result = self._calculate_quiz_result(quiz)
            quiz.status = 'COMPLETED'
            quiz.completed_at = timezone.now()
            quiz.save()

            # Update campaign statistics
            campaign = quiz.campaign
            campaign.completed_participants = campaign.quizzes.filter(status='COMPLETED').count()

            # Recalculate average score
            completed_results = campaign.results.all()
            if completed_results.exists():
                from django.db.models import Avg
                campaign.average_score = completed_results.aggregate(Avg('score'))['score__avg']

            campaign.save()

        return Response({
            'message': 'Quiz submitted successfully',
            'result': QuizResultSerializer(result).data
        }, status=status.HTTP_201_CREATED)

    def _calculate_quiz_result(self, quiz):
        """Calculate and create quiz result."""
        questions = quiz.questions.all()
        total_questions = questions.count()
        correct_answers = questions.filter(is_correct=True).count()
        incorrect_answers = total_questions - correct_answers

        # Calculate score
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # Calculate phishing detection metrics
        phishing_questions = questions.filter(email_template__email_type='PHISHING')
        phishing_identified = phishing_questions.filter(answer='PHISHING', is_correct=True).count()
        phishing_missed = phishing_questions.filter(answer='LEGITIMATE', is_correct=False).count()

        # Calculate false positives (legitimate emails marked as phishing)
        legitimate_questions = questions.filter(email_template__email_type='LEGITIMATE')
        false_positives = legitimate_questions.filter(answer='PHISHING', is_correct=False).count()

        # Calculate time metrics
        total_time = sum(q.time_spent_seconds or 0 for q in questions)
        avg_time = total_time / total_questions if total_questions > 0 else 0

        # Determine risk level
        risk_level = self._determine_risk_level(score, phishing_missed, false_positives)

        # Create result
        result = QuizResult.objects.create(
            quiz=quiz,
            employee=quiz.employee,
            campaign=quiz.campaign,
            total_questions=total_questions,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            score=score,
            phishing_emails_identified=phishing_identified,
            phishing_emails_missed=phishing_missed,
            false_positives=false_positives,
            time_taken_seconds=total_time,
            average_time_per_question=avg_time,
            risk_level=risk_level
        )

        return result

    def _determine_risk_level(self, score, phishing_missed, false_positives):
        """Determine employee risk level based on performance."""
        if score >= 90 and phishing_missed == 0:
            return 'LOW'
        elif score >= 70 and phishing_missed <= 1:
            return 'MEDIUM'
        elif score >= 50 or phishing_missed <= 3:
            return 'HIGH'
        else:
            return 'CRITICAL'

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def result(self, request, pk=None):
        """Get detailed results for a completed quiz."""
        quiz = self.get_object()

        # Only the assigned employee or admins can view results
        if quiz.employee != request.user and not request.user.is_company_admin and not request.user.is_super_admin:
            return Response(
                {'error': 'You do not have permission to view this quiz result'},
                status=status.HTTP_403_FORBIDDEN
            )

        if quiz.status != 'COMPLETED':
            return Response(
                {'error': 'Quiz has not been completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = quiz.result
        except QuizResult.DoesNotExist:
            return Response(
                {'error': 'Result not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get detailed question results
        questions = quiz.questions.all().order_by('question_number')
        question_details = QuizQuestionDetailSerializer(questions, many=True).data

        return Response({
            'result': QuizResultSerializer(result).data,
            'question_details': question_details
        }, status=status.HTTP_200_OK)
