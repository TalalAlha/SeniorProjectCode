"""
Training App Views
==================
API views for Risk Scoring & Remediation Training.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Avg, Count, F
from django.db import transaction
from datetime import timedelta

from .models import (
    RiskScore,
    RiskScoreHistory,
    TrainingModule,
    TrainingQuestion,
    RemediationTraining,
    TrainingQuizAnswer
)
from .serializers import (
    RiskScoreListSerializer,
    RiskScoreDetailSerializer,
    RiskScoreEmployeeSerializer,
    RiskScoreUpdateSerializer,
    RiskScoreHistorySerializer,
    TrainingModuleListSerializer,
    TrainingModuleDetailSerializer,
    TrainingModuleCreateSerializer,
    TrainingModuleEmployeeSerializer,
    TrainingQuestionSerializer,
    TrainingQuestionDetailSerializer,
    TrainingQuestionCreateSerializer,
    RemediationTrainingListSerializer,
    RemediationTrainingDetailSerializer,
    RemediationTrainingCreateSerializer,
    RemediationTrainingEmployeeSerializer,
    BulkAssignTrainingSerializer,
    SubmitTrainingQuizSerializer,
    CompanyRiskStatisticsSerializer,
)
from apps.core.permissions import (
    IsSuperAdmin,
    IsSuperAdminOrCompanyAdmin,
    HasCompanyAccess,
    IsEmployee
)


# =============================================================================
# RiskScore ViewSet
# =============================================================================

class RiskScoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RiskScore CRUD operations.

    - Super Admins can see all risk scores
    - Company Admins can see their company's risk scores
    - Employees can only see their own risk score
    """

    queryset = RiskScore.objects.select_related('employee', 'company')
    permission_classes = [IsAuthenticated, HasCompanyAccess]
    http_method_names = ['get', 'patch']

    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role."""
        user = self.request.user

        if self.action in ['update', 'partial_update']:
            return RiskScoreUpdateSerializer
        elif user.is_employee and not user.is_company_admin:
            return RiskScoreEmployeeSerializer
        elif self.action == 'retrieve':
            return RiskScoreDetailSerializer
        return RiskScoreListSerializer

    def get_queryset(self):
        """Filter risk scores based on user role."""
        user = self.request.user

        if user.is_super_admin:
            queryset = RiskScore.objects.all()
        elif user.is_company_admin:
            queryset = RiskScore.objects.filter(company=user.company)
        elif user.is_employee:
            queryset = RiskScore.objects.filter(employee=user)
        else:
            queryset = RiskScore.objects.none()

        # Apply filters
        risk_level = self.request.query_params.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)

        requires_remediation = self.request.query_params.get('requires_remediation')
        if requires_remediation is not None:
            queryset = queryset.filter(requires_remediation=requires_remediation.lower() == 'true')

        return queryset.select_related('employee', 'company')

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """
        Manually adjust risk score (admin only).
        Creates history record of the adjustment.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        old_score = instance.score
        old_level = instance.risk_level
        new_score = serializer.validated_data['score']
        reason = serializer.validated_data['adjustment_reason']

        # Update score
        instance.score = new_score
        instance.risk_level = instance.calculate_risk_level()
        instance.save()

        # Create history record
        RiskScoreHistory.objects.create(
            risk_score=instance,
            employee=instance.employee,
            event_type='MANUAL_ADJUSTMENT',
            previous_score=old_score,
            new_score=instance.score,
            previous_risk_level=old_level,
            new_risk_level=instance.risk_level,
            description=f"Manual adjustment by admin: {reason}",
            source_type='ManualAdjustment'
        )

        return Response(RiskScoreDetailSerializer(instance).data)

    @action(detail=False, methods=['get'])
    def my_score(self, request):
        """Get current user's risk score."""
        try:
            risk_score = RiskScore.objects.get(employee=request.user)
            serializer = RiskScoreEmployeeSerializer(risk_score)
            return Response(serializer.data)
        except RiskScore.DoesNotExist:
            return Response(
                {'detail': 'Risk score not found. Complete a quiz or simulation first.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def statistics(self, request):
        """Get company-wide risk statistics."""
        user = request.user

        if user.is_super_admin:
            company_id = request.query_params.get('company')
            if company_id:
                queryset = RiskScore.objects.filter(company_id=company_id)
            else:
                queryset = RiskScore.objects.all()
        else:
            queryset = RiskScore.objects.filter(company=user.company)

        # Calculate statistics
        stats = queryset.aggregate(
            employees_with_scores=Count('id'),
            average_risk_score=Avg('score'),
            low_risk_count=Count('id', filter=Q(risk_level='LOW')),
            medium_risk_count=Count('id', filter=Q(risk_level='MEDIUM')),
            high_risk_count=Count('id', filter=Q(risk_level='HIGH')),
            critical_risk_count=Count('id', filter=Q(risk_level='CRITICAL')),
            total_trainings_assigned=Avg('trainings_assigned'),
            total_trainings_completed=Avg('trainings_completed'),
            total_trainings_passed=Avg('trainings_passed'),
            employees_requiring_remediation=Count('id', filter=Q(requires_remediation=True)),
        )

        # Get average quiz accuracy and simulation click rate
        accuracy_stats = queryset.exclude(total_quiz_questions=0).aggregate(
            average_quiz_accuracy=Avg(
                F('correct_quiz_answers') * 100.0 / F('total_quiz_questions')
            )
        )

        click_stats = queryset.exclude(total_simulations_received=0).aggregate(
            average_simulation_click_rate=Avg(
                F('simulations_clicked') * 100.0 / F('total_simulations_received')
            )
        )

        # Count overdue trainings
        overdue_trainings = RemediationTraining.objects.filter(
            company=user.company if not user.is_super_admin else F('company'),
            status__in=['ASSIGNED', 'IN_PROGRESS'],
            due_date__lt=timezone.now()
        ).count()

        # Get total employees
        from apps.accounts.models import User
        if user.is_super_admin:
            total_employees = User.objects.filter(role='EMPLOYEE').count()
        else:
            total_employees = User.objects.filter(
                role='EMPLOYEE',
                company=user.company
            ).count()

        # Training completion rate
        training_stats = RemediationTraining.objects.filter(
            company=user.company if not user.is_super_admin else F('company')
        ).aggregate(
            total_assigned=Count('id'),
            total_completed=Count('id', filter=Q(status__in=['COMPLETED', 'PASSED'])),
            total_passed=Count('id', filter=Q(status='PASSED'))
        )

        completion_rate = 0
        if training_stats['total_assigned'] and training_stats['total_assigned'] > 0:
            completion_rate = round(
                (training_stats['total_completed'] / training_stats['total_assigned']) * 100, 1
            )

        response_data = {
            'total_employees': total_employees,
            'employees_with_scores': stats['employees_with_scores'] or 0,
            'low_risk_count': stats['low_risk_count'] or 0,
            'medium_risk_count': stats['medium_risk_count'] or 0,
            'high_risk_count': stats['high_risk_count'] or 0,
            'critical_risk_count': stats['critical_risk_count'] or 0,
            'average_risk_score': round(stats['average_risk_score'] or 0, 1),
            'average_quiz_accuracy': round(accuracy_stats['average_quiz_accuracy'] or 0, 1),
            'average_simulation_click_rate': round(click_stats['average_simulation_click_rate'] or 0, 1),
            'total_trainings_assigned': training_stats['total_assigned'] or 0,
            'total_trainings_completed': training_stats['total_completed'] or 0,
            'total_trainings_passed': training_stats['total_passed'] or 0,
            'training_completion_rate': completion_rate,
            'employees_requiring_remediation': stats['employees_requiring_remediation'] or 0,
            'overdue_trainings_count': overdue_trainings,
        }

        return Response(response_data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get risk score history for an employee."""
        risk_score = self.get_object()
        history = RiskScoreHistory.objects.filter(risk_score=risk_score)

        # Paginate
        page = self.paginate_queryset(history)
        if page is not None:
            serializer = RiskScoreHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RiskScoreHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def recalculate(self, request):
        """Recalculate risk scores for specified employees."""
        employee_ids = request.data.get('employee_ids', [])

        if employee_ids:
            queryset = RiskScore.objects.filter(employee_id__in=employee_ids)
        else:
            if request.user.is_super_admin:
                queryset = RiskScore.objects.all()
            else:
                queryset = RiskScore.objects.filter(company=request.user.company)

        count = 0
        for risk_score in queryset:
            old_score = risk_score.score
            risk_score.recalculate_score()
            risk_score.save()
            count += 1

            if risk_score.score != old_score:
                RiskScoreHistory.objects.create(
                    risk_score=risk_score,
                    employee=risk_score.employee,
                    event_type='SCORE_RECALCULATED',
                    previous_score=old_score,
                    new_score=risk_score.score,
                    previous_risk_level=risk_score.calculate_risk_level(),
                    new_risk_level=risk_score.risk_level,
                    description='Automatic recalculation'
                )

        return Response({'recalculated': count})


# =============================================================================
# TrainingModule ViewSet
# =============================================================================

class TrainingModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TrainingModule CRUD operations.

    - Super Admins can see and manage all training modules
    - Company Admins can see global + their company's modules
    - Employees can only see modules assigned to them
    """

    queryset = TrainingModule.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        user = self.request.user

        if self.action in ['create', 'update', 'partial_update']:
            return TrainingModuleCreateSerializer
        elif self.action == 'retrieve':
            if user.is_employee and not user.is_company_admin:
                return TrainingModuleEmployeeSerializer
            return TrainingModuleDetailSerializer
        return TrainingModuleListSerializer

    def get_queryset(self):
        """Filter training modules based on user role."""
        user = self.request.user

        if user.is_super_admin:
            queryset = TrainingModule.objects.all()
        elif user.is_company_admin:
            # Company admins see global + their company's modules
            queryset = TrainingModule.objects.filter(
                Q(company=user.company) | Q(company__isnull=True)
            )
        elif user.is_employee:
            # Employees only see modules they have been assigned
            assigned_module_ids = RemediationTraining.objects.filter(
                employee=user
            ).values_list('training_module_id', flat=True)
            queryset = TrainingModule.objects.filter(id__in=assigned_module_ids)
        else:
            queryset = TrainingModule.objects.none()

        # Apply filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]

    def list(self, request, *args, **kwargs):
        """Return modules with company-scoped stats for non-super-admins."""
        queryset = self.filter_queryset(self.get_queryset())
        user = request.user
        company = getattr(user, 'company', None)

        # For company users, annotate with company-specific assignment stats
        if company and not user.is_super_admin:
            queryset = queryset.annotate(
                company_times_assigned=Count(
                    'assignments',
                    filter=Q(assignments__company=company)
                ),
                company_times_completed=Count(
                    'assignments',
                    filter=Q(assignments__company=company, assignments__status__in=['COMPLETED', 'PASSED', 'FAILED'])
                ),
                company_times_passed=Count(
                    'assignments',
                    filter=Q(assignments__company=company, assignments__status='PASSED')
                ),
            )

        page = self.paginate_queryset(queryset)
        modules = page if page is not None else queryset

        serializer = self.get_serializer(modules, many=True)
        data = serializer.data

        # Override global stats with company-scoped stats
        if company and not user.is_super_admin:
            module_list = list(modules)
            for i, module_data in enumerate(data):
                mod = module_list[i]
                assigned = getattr(mod, 'company_times_assigned', 0)
                completed = getattr(mod, 'company_times_completed', 0)
                passed = getattr(mod, 'company_times_passed', 0)
                module_data['times_assigned'] = assigned
                module_data['times_completed'] = completed
                module_data['times_passed'] = passed
                module_data['completion_rate'] = round((completed / assigned) * 100, 1) if assigned > 0 else 0
                module_data['pass_rate'] = round((passed / completed) * 100, 1) if completed > 0 else 0

        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

    def perform_create(self, serializer):
        """Set created_by on creation."""
        user = self.request.user
        company = serializer.validated_data.get('company')

        if not company and not user.is_super_admin:
            serializer.save(created_by=user, company=user.company)
        else:
            serializer.save(created_by=user)

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get all questions for a training module."""
        module = self.get_object()
        questions = module.questions.filter(is_active=True)

        # For non-admins, hide correct answers
        if request.user.is_employee and not request.user.is_company_admin:
            serializer = TrainingQuestionSerializer(questions, many=True)
        else:
            serializer = TrainingQuestionDetailSerializer(questions, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of available categories."""
        categories = [
            {'value': code, 'label': str(label)}
            for code, label in TrainingModule.CATEGORY_CHOICES
        ]
        return Response(categories)


# =============================================================================
# TrainingQuestion ViewSet
# =============================================================================

class TrainingQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TrainingQuestion CRUD operations.
    Only admins can manage questions.
    """

    queryset = TrainingQuestion.objects.select_related('module')
    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TrainingQuestionCreateSerializer
        return TrainingQuestionDetailSerializer

    def get_queryset(self):
        """Filter questions based on user role."""
        user = self.request.user

        if user.is_super_admin:
            queryset = TrainingQuestion.objects.all()
        else:
            # Company admins see questions for their modules
            queryset = TrainingQuestion.objects.filter(
                Q(module__company=user.company) | Q(module__company__isnull=True)
            )

        # Filter by module
        module_id = self.request.query_params.get('module')
        if module_id:
            queryset = queryset.filter(module_id=module_id)

        return queryset


# =============================================================================
# RemediationTraining ViewSet
# =============================================================================

class RemediationTrainingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RemediationTraining CRUD operations.

    - Super Admins can see all training assignments
    - Company Admins can see their company's training assignments
    - Employees can see their own training assignments
    """

    queryset = RemediationTraining.objects.select_related(
        'employee', 'company', 'training_module', 'assigned_by'
    )
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role."""
        user = self.request.user

        if self.action == 'create':
            return RemediationTrainingCreateSerializer
        elif self.action == 'retrieve':
            if user.is_employee and not user.is_company_admin:
                return RemediationTrainingEmployeeSerializer
            return RemediationTrainingDetailSerializer
        elif user.is_employee and not user.is_company_admin:
            return RemediationTrainingEmployeeSerializer
        return RemediationTrainingListSerializer

    def get_queryset(self):
        """Filter training assignments based on user role."""
        user = self.request.user

        if user.is_super_admin:
            queryset = RemediationTraining.objects.all()
        elif user.is_company_admin:
            queryset = RemediationTraining.objects.filter(company=user.company)
        elif user.is_employee:
            queryset = RemediationTraining.objects.filter(employee=user)
        else:
            queryset = RemediationTraining.objects.none()

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        is_overdue = self.request.query_params.get('is_overdue')
        if is_overdue is not None:
            if is_overdue.lower() == 'true':
                queryset = queryset.filter(
                    status__in=['ASSIGNED', 'IN_PROGRESS'],
                    due_date__lt=timezone.now()
                )

        return queryset.select_related('employee', 'company', 'training_module')

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'destroy', 'bulk_assign']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark training as started."""
        training = self.get_object()

        # Only the assigned employee can start their training
        if training.employee != request.user and not request.user.is_super_admin:
            return Response(
                {'error': 'You can only start your own training'},
                status=status.HTTP_403_FORBIDDEN
            )

        if training.status != 'ASSIGNED':
            return Response(
                {'error': f'Training is already {training.status.lower()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        training.start_training()
        serializer = self.get_serializer(training)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def view_content(self, request, pk=None):
        """Mark training content as viewed."""
        training = self.get_object()

        if training.employee != request.user and not request.user.is_super_admin:
            return Response(
                {'error': 'You can only view your own training'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Auto-start if not started
        if training.status == 'ASSIGNED':
            training.start_training()

        training.mark_content_viewed()

        # Update time spent
        time_spent = request.data.get('time_spent_seconds', 0)
        if time_spent > 0:
            training.time_spent_seconds = F('time_spent_seconds') + time_spent
            training.save(update_fields=['time_spent_seconds'])
            training.refresh_from_db()

        serializer = self.get_serializer(training)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def quiz(self, request, pk=None):
        """Get quiz questions for the training."""
        training = self.get_object()

        if training.employee != request.user and not request.user.is_company_admin:
            return Response(
                {'error': 'You can only access your own training quiz'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not training.content_viewed:
            return Response(
                {'error': 'Please view the training content first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        questions = training.training_module.questions.filter(is_active=True)
        serializer = TrainingQuestionSerializer(questions, many=True)

        return Response({
            'training_id': training.id,
            'module_title': training.training_module.title,
            'passing_score': training.training_module.passing_score,
            'questions': serializer.data
        })

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def submit_quiz(self, request, pk=None):
        """Submit quiz answers for the training."""
        training = self.get_object()

        if training.employee != request.user:
            return Response(
                {'error': 'You can only submit your own training quiz'},
                status=status.HTTP_403_FORBIDDEN
            )

        if training.status in ['PASSED', 'COMPLETED']:
            return Response(
                {'error': 'Training has already been completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not training.content_viewed:
            return Response(
                {'error': 'Please view the training content first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SubmitTrainingQuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = serializer.validated_data['answers']

        # Store risk score before
        try:
            risk_score = RiskScore.objects.get(employee=request.user)
            training.risk_score_before = risk_score.score
        except RiskScore.DoesNotExist:
            risk_score = None

        # Submit quiz and get results
        result = training.submit_quiz(answers)

        # Save individual answers
        for item in result['results']:
            question = TrainingQuestion.objects.get(id=item['question_id'])
            TrainingQuizAnswer.objects.update_or_create(
                remediation_training=training,
                question=question,
                defaults={
                    'selected_answer_index': item['selected'] or 0,
                    'is_correct': item['is_correct']
                }
            )

        # Update training module statistics
        module = training.training_module
        module.times_completed = F('times_completed') + 1
        if result['passed']:
            module.times_passed = F('times_passed') + 1
        module.save(update_fields=['times_completed', 'times_passed'])

        # Update risk score if passed
        if result['passed'] and risk_score:
            old_score = risk_score.score
            risk_score.trainings_completed = F('trainings_completed') + 1
            risk_score.trainings_passed = F('trainings_passed') + 1
            risk_score.last_training_date = timezone.now()
            risk_score.save()
            risk_score.refresh_from_db()

            # Reduce risk score
            new_score = max(0, risk_score.score - module.score_reduction_on_pass)
            risk_score.score = new_score
            risk_score.save()

            training.risk_score_after = new_score
            training.save(update_fields=['risk_score_after'])

            # Create history
            RiskScoreHistory.objects.create(
                risk_score=risk_score,
                employee=request.user,
                event_type='TRAINING_PASSED',
                previous_score=old_score,
                new_score=new_score,
                previous_risk_level=risk_score.calculate_risk_level(),
                new_risk_level=risk_score.risk_level,
                source_type='RemediationTraining',
                source_id=training.id,
                description=f'Passed training: {module.title}'
            )
        elif risk_score:
            risk_score.trainings_completed = F('trainings_completed') + 1
            risk_score.last_training_date = timezone.now()
            risk_score.save()

            RiskScoreHistory.objects.create(
                risk_score=risk_score,
                employee=request.user,
                event_type='TRAINING_FAILED',
                previous_score=risk_score.score,
                new_score=risk_score.score,
                previous_risk_level=risk_score.risk_level,
                new_risk_level=risk_score.risk_level,
                source_type='RemediationTraining',
                source_id=training.id,
                description=f'Failed training: {module.title} (Score: {result["score"]:.1f}%)'
            )

        return Response({
            'training_id': training.id,
            'score': result['score'],
            'passed': result['passed'],
            'correct': result['correct'],
            'total': result['total'],
            'passing_score': module.passing_score,
            'results': result['results'],
            'risk_score_before': training.risk_score_before,
            'risk_score_after': training.risk_score_after
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    @transaction.atomic
    def bulk_assign(self, request):
        """Assign training to multiple employees at once."""
        serializer = BulkAssignTrainingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        employee_ids = data['employee_ids']
        module = TrainingModule.objects.get(id=data['training_module_id'])
        reason = data['assignment_reason']
        due_date = data.get('due_date') or (timezone.now() + timedelta(days=7))

        from apps.accounts.models import User

        # Filter to only employees in admin's company (unless super admin)
        if not request.user.is_super_admin:
            employees = User.objects.filter(
                id__in=employee_ids,
                role='EMPLOYEE',
                company=request.user.company
            )
        else:
            employees = User.objects.filter(id__in=employee_ids, role='EMPLOYEE')

        created = []
        skipped = []

        for employee in employees:
            # Check if already assigned
            exists = RemediationTraining.objects.filter(
                employee=employee,
                training_module=module,
                status__in=['ASSIGNED', 'IN_PROGRESS']
            ).exists()

            if exists:
                skipped.append(employee.email)
                continue

            training = RemediationTraining.objects.create(
                employee=employee,
                company=employee.company,
                training_module=module,
                assignment_reason=reason,
                assigned_by=request.user,
                due_date=due_date
            )

            # Update module stats
            module.times_assigned = F('times_assigned') + 1
            module.save(update_fields=['times_assigned'])

            # Update risk score
            try:
                risk_score = RiskScore.objects.get(employee=employee)
                risk_score.trainings_assigned = F('trainings_assigned') + 1
                risk_score.save(update_fields=['trainings_assigned'])
            except RiskScore.DoesNotExist:
                pass

            created.append(employee.email)

        return Response({
            'assigned': len(created),
            'skipped': len(skipped),
            'created_for': created,
            'skipped_emails': skipped
        })

    @action(detail=False, methods=['get'])
    def my_trainings(self, request):
        """Get current user's training assignments."""
        trainings = RemediationTraining.objects.filter(
            employee=request.user
        ).select_related('training_module')

        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            trainings = trainings.filter(status=status_filter)

        serializer = RemediationTrainingEmployeeSerializer(trainings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending (assigned/in_progress) trainings."""
        user = request.user

        if user.is_employee and not user.is_company_admin:
            queryset = RemediationTraining.objects.filter(
                employee=user,
                status__in=['ASSIGNED', 'IN_PROGRESS']
            )
        elif user.is_company_admin:
            queryset = RemediationTraining.objects.filter(
                company=user.company,
                status__in=['ASSIGNED', 'IN_PROGRESS']
            )
        else:
            queryset = RemediationTraining.objects.filter(
                status__in=['ASSIGNED', 'IN_PROGRESS']
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def overdue(self, request):
        """Get overdue training assignments."""
        user = request.user

        if user.is_super_admin:
            queryset = RemediationTraining.objects.filter(
                status__in=['ASSIGNED', 'IN_PROGRESS'],
                due_date__lt=timezone.now()
            )
        else:
            queryset = RemediationTraining.objects.filter(
                company=user.company,
                status__in=['ASSIGNED', 'IN_PROGRESS'],
                due_date__lt=timezone.now()
            )

        serializer = RemediationTrainingListSerializer(queryset, many=True)
        return Response(serializer.data)
