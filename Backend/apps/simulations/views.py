from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.db.models import Q, Avg, F
from django.db import transaction
from django.urls import reverse
from django.conf import settings

from .models import (
    SimulationTemplate,
    SimulationCampaign,
    EmailSimulation,
    TrackingEvent
)
from .serializers import (
    SimulationTemplateListSerializer,
    SimulationTemplateDetailSerializer,
    SimulationTemplateCreateSerializer,
    SimulationCampaignListSerializer,
    SimulationCampaignDetailSerializer,
    SimulationCampaignCreateSerializer,
    EmailSimulationListSerializer,
    EmailSimulationDetailSerializer,
    TrackingEventListSerializer,
    CampaignAnalyticsSerializer,
    EmployeeSimulationResultSerializer,
    SendCampaignSerializer,
    ReportPhishingSerializer
)
from apps.core.permissions import (
    IsSuperAdmin,
    IsSuperAdminOrCompanyAdmin,
    HasCompanyAccess,
    IsSameCompany
)

# 1x1 transparent PNG pixel (68 bytes)
TRACKING_PIXEL = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
    0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
    0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
    0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
    0x42, 0x60, 0x82
])


# =============================================================================
# SimulationTemplate ViewSet
# =============================================================================

class SimulationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SimulationTemplate CRUD operations.

    - Super Admins can see all templates
    - Company Admins can see their company's templates + public templates
    - Only Super Admins and Company Admins can create/update/delete
    """

    queryset = SimulationTemplate.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return SimulationTemplateCreateSerializer
        elif self.action == 'retrieve':
            return SimulationTemplateDetailSerializer
        return SimulationTemplateListSerializer

    def get_queryset(self):
        """Filter templates based on user role."""
        user = self.request.user

        if user.is_super_admin:
            return SimulationTemplate.objects.all()

        # Company admins and employees see:
        # - Templates belonging to their company
        # - Public templates (is_public=True)
        # - Global templates (company=None)
        if user.has_company_access:
            return SimulationTemplate.objects.filter(
                Q(company=user.company) |
                Q(is_public=True) |
                Q(company__isnull=True)
            ).filter(is_active=True)

        return SimulationTemplate.objects.none()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]

    def perform_create(self, serializer):
        """Set created_by and company on creation."""
        user = self.request.user
        company = serializer.validated_data.get('company')

        # If company not provided and user is not super admin, use user's company
        if not company and not user.is_super_admin:
            serializer.save(created_by=user, company=user.company)
        else:
            serializer.save(created_by=user)

    def update(self, request, *args, **kwargs):
        """Prevent updating templates that are used in campaigns."""
        instance = self.get_object()

        # Check if template is used in any campaigns
        if instance.campaigns.exists():
            return Response(
                {'error': 'Cannot modify template that is used in existing campaigns.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Prevent deleting templates that are used in campaigns."""
        instance = self.get_object()

        # Check if template is used in any campaigns
        if instance.campaigns.exists():
            return Response(
                {'error': 'Cannot delete template that is used in existing campaigns.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, HasCompanyAccess])
    def by_attack_vector(self, request):
        """Get templates grouped by attack vector."""
        queryset = self.get_queryset()
        attack_vectors = {}

        for vector_code, vector_name in SimulationTemplate.ATTACK_VECTOR_CHOICES:
            templates = queryset.filter(attack_vector=vector_code)
            attack_vectors[vector_code] = {
                'name': str(vector_name),
                'count': templates.count(),
                'templates': SimulationTemplateListSerializer(templates, many=True).data
            }

        return Response(attack_vectors, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, HasCompanyAccess])
    def by_difficulty(self, request):
        """Get templates grouped by difficulty level."""
        queryset = self.get_queryset()
        difficulties = {}

        for diff_code, diff_name in SimulationTemplate.DIFFICULTY_CHOICES:
            templates = queryset.filter(difficulty=diff_code)
            difficulties[diff_code] = {
                'name': str(diff_name),
                'count': templates.count(),
                'templates': SimulationTemplateListSerializer(templates, many=True).data
            }

        return Response(difficulties, status=status.HTTP_200_OK)


# =============================================================================
# SimulationCampaign ViewSet
# =============================================================================

class SimulationCampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SimulationCampaign CRUD operations.

    - Super Admins can see all campaigns
    - Company Admins can see their company's campaigns
    - Custom actions for sending emails, viewing analytics, and results
    """

    queryset = SimulationCampaign.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return SimulationCampaignCreateSerializer
        elif self.action == 'retrieve':
            return SimulationCampaignDetailSerializer
        return SimulationCampaignListSerializer

    def get_queryset(self):
        """Filter campaigns based on user role."""
        user = self.request.user

        if user.is_super_admin:
            return SimulationCampaign.objects.all()

        # Company admins and employees see only their company's campaigns
        if user.has_company_access:
            return SimulationCampaign.objects.filter(company=user.company)

        return SimulationCampaign.objects.none()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'send']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]

    def perform_create(self, serializer):
        """Set created_by and company on creation."""
        user = self.request.user
        company = serializer.validated_data.get('company')

        # If company not provided and user is not super admin, use user's company
        if not company and not user.is_super_admin:
            serializer.save(created_by=user, company=user.company)
        else:
            serializer.save(created_by=user)

    def update(self, request, *args, **kwargs):
        """Prevent updating campaigns that are not in DRAFT status."""
        instance = self.get_object()

        if instance.status not in ['DRAFT', 'SCHEDULED']:
            return Response(
                {'error': f'Cannot modify campaign with status: {instance.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a simulation campaign regardless of status."""
        return super().destroy(request, *args, **kwargs)

    # -------------------------------------------------------------------------
    # Custom Actions
    # -------------------------------------------------------------------------

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def send(self, request, pk=None):
        """
        Send simulation emails to target employees.

        Creates EmailSimulation records for each target employee and
        triggers the email sending process.
        """
        campaign = self.get_object()

        # Validate using serializer
        serializer = SendCampaignSerializer(
            data=request.data,
            context={'campaign': campaign, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        send_immediately = serializer.validated_data.get('send_immediately', True)

        # Get target employees
        if campaign.target_all_employees:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            target_employees = User.objects.filter(
                company=campaign.company,
                role='EMPLOYEE',
                is_active=True
            )
        else:
            target_employees = campaign.target_employees.all()

        if not target_employees.exists():
            return Response(
                {'error': 'No target employees found for this campaign.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create EmailSimulation records and send emails
        with transaction.atomic():
            created_simulations = []
            errors = []

            for employee in target_employees:
                try:
                    # Check if simulation already exists
                    if EmailSimulation.objects.filter(campaign=campaign, employee=employee).exists():
                        errors.append(f"Simulation already exists for {employee.email}")
                        continue

                    # Create EmailSimulation record
                    email_sim = EmailSimulation.objects.create(
                        campaign=campaign,
                        employee=employee,
                        recipient_email=employee.email,
                        status='PENDING'
                    )
                    created_simulations.append(email_sim)

                except Exception as e:
                    errors.append(f"Error creating simulation for {employee.email}: {str(e)}")

            # Update campaign statistics
            campaign.total_sent = len(created_simulations)

            if send_immediately:
                # Send emails now
                sent_count = 0
                for email_sim in created_simulations:
                    try:
                        self._send_simulation_email(email_sim)
                        sent_count += 1
                    except Exception as e:
                        email_sim.status = 'FAILED'
                        email_sim.save()
                        errors.append(f"Failed to send to {email_sim.recipient_email}: {str(e)}")

                campaign.status = 'IN_PROGRESS'
                campaign.sent_at = timezone.now()
            else:
                campaign.status = 'SCHEDULED'

            campaign.save()

        return Response({
            'message': f'Campaign {"sent" if send_immediately else "scheduled"} successfully',
            'total_targeted': target_employees.count(),
            'simulations_created': len(created_simulations),
            'emails_sent': sent_count if send_immediately else 0,
            'errors': errors
        }, status=status.HTTP_200_OK)

    def _send_simulation_email(self, email_simulation):
        """
        Send a single simulation email to an employee.

        Replaces placeholders with unique tracking URLs and sends the email.
        """
        from django.core.mail import EmailMultiAlternatives
        from django.template import Template, Context

        campaign = email_simulation.campaign
        template = campaign.template

        # Build tracking URLs
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        tracking_pixel_url = f"{base_url}/api/v1/simulations/track/{email_simulation.tracking_token}/"
        phishing_link_url = f"{base_url}/api/v1/simulations/link/{email_simulation.link_token}/"

        # Create tracking pixel HTML
        tracking_pixel_html = f'<img src="{tracking_pixel_url}" width="1" height="1" alt="" style="display:none;" />'

        # Replace placeholders in email body
        body_html = template.body_html
        body_html = body_html.replace('{TRACKING_PIXEL}', tracking_pixel_html)
        body_html = body_html.replace('{LURE_LINK}', phishing_link_url)
        body_html = body_html.replace('{EMPLOYEE_NAME}', email_simulation.employee.get_full_name())
        body_html = body_html.replace('{EMPLOYEE_EMAIL}', email_simulation.employee.email)

        # Plain text version
        body_plain = template.body_plain or ''
        body_plain = body_plain.replace('{LURE_LINK}', phishing_link_url)
        body_plain = body_plain.replace('{EMPLOYEE_NAME}', email_simulation.employee.get_full_name())
        body_plain = body_plain.replace('{EMPLOYEE_EMAIL}', email_simulation.employee.email)

        # Create and send email
        email = EmailMultiAlternatives(
            subject=template.subject,
            body=body_plain,
            from_email=f"{template.sender_name} <{template.sender_email}>",
            to=[email_simulation.recipient_email],
            reply_to=[template.reply_to_email] if template.reply_to_email else None
        )
        email.attach_alternative(body_html, "text/html")
        email.send(fail_silently=False)

        # Update simulation status
        email_simulation.status = 'SENT'
        email_simulation.sent_at = timezone.now()
        email_simulation.save()

        # Create tracking event
        TrackingEvent.objects.create(
            email_simulation=email_simulation,
            campaign=campaign,
            employee=email_simulation.employee,
            event_type='EMAIL_SENT'
        )

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, HasCompanyAccess])
    def analytics(self, request, pk=None):
        """
        Get detailed analytics for a simulation campaign.

        Returns aggregated statistics including rates, timing metrics, etc.
        """
        campaign = self.get_object()

        # Calculate target count
        if campaign.target_all_employees:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            total_targeted = User.objects.filter(
                company=campaign.company,
                role='EMPLOYEE',
                is_active=True
            ).count()
        else:
            total_targeted = campaign.target_employees.count()

        # Calculate timing metrics
        simulations = campaign.email_simulations.all()

        # Average time to open (for those who opened)
        opened_sims = simulations.filter(was_opened=True, sent_at__isnull=False, first_opened_at__isnull=False)
        avg_time_to_open = None
        if opened_sims.exists():
            time_diffs = [(s.first_opened_at - s.sent_at).total_seconds() for s in opened_sims]
            avg_time_to_open = sum(time_diffs) / len(time_diffs)

        # Average time to click (for those who clicked)
        clicked_sims = simulations.filter(was_clicked=True, sent_at__isnull=False, clicked_at__isnull=False)
        avg_time_to_click = None
        if clicked_sims.exists():
            time_diffs = [(s.clicked_at - s.sent_at).total_seconds() for s in clicked_sims]
            avg_time_to_click = sum(time_diffs) / len(time_diffs)

        # Calculate delivery rate
        delivery_rate = 0
        if campaign.total_sent > 0:
            delivery_rate = (campaign.total_delivered / campaign.total_sent) * 100

        analytics_data = {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'status': campaign.status,
            'template_name': campaign.template.name,
            'attack_vector': campaign.template.get_attack_vector_display(),
            'difficulty': campaign.template.get_difficulty_display(),

            # Counts
            'total_targeted': total_targeted,
            'total_sent': campaign.total_sent,
            'total_delivered': campaign.total_delivered,
            'total_opened': campaign.total_opened,
            'total_clicked': campaign.total_clicked,
            'total_reported': campaign.total_reported,
            'total_credentials_entered': campaign.total_credentials_entered,

            # Rates
            'delivery_rate': round(delivery_rate, 2),
            'open_rate': round(campaign.open_rate, 2),
            'click_rate': round(campaign.click_rate, 2),
            'report_rate': round(campaign.report_rate, 2),
            'compromise_rate': round(campaign.compromise_rate, 2),

            # Timing
            'avg_time_to_open': avg_time_to_open,
            'avg_time_to_click': avg_time_to_click,

            # Dates
            'send_date': campaign.send_date,
            'sent_at': campaign.sent_at,
            'completed_at': campaign.completed_at
        }

        serializer = CampaignAnalyticsSerializer(analytics_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, HasCompanyAccess])
    def results(self, request, pk=None):
        """
        Get individual employee results for a simulation campaign.

        Returns a list of all EmailSimulation records with employee details.
        """
        campaign = self.get_object()
        simulations = campaign.email_simulations.all().select_related('employee')

        results = []
        for sim in simulations:
            # Determine risk level based on behavior
            risk_level = 'LOW'
            if sim.credentials_entered:
                risk_level = 'CRITICAL'
            elif sim.was_clicked:
                risk_level = 'HIGH'
            elif sim.was_opened and not sim.was_reported:
                risk_level = 'MEDIUM'
            elif sim.was_reported:
                risk_level = 'LOW'

            # Calculate time metrics
            time_to_open = None
            time_to_click = None
            if sim.sent_at and sim.first_opened_at:
                time_to_open = (sim.first_opened_at - sim.sent_at).total_seconds()
            if sim.sent_at and sim.clicked_at:
                time_to_click = (sim.clicked_at - sim.sent_at).total_seconds()

            results.append({
                'employee_id': sim.employee.id,
                'employee_name': sim.employee.get_full_name(),
                'employee_email': sim.employee.email,
                'email_status': sim.status,
                'was_opened': sim.was_opened,
                'was_clicked': sim.was_clicked,
                'was_reported': sim.was_reported,
                'credentials_entered': sim.credentials_entered,
                'is_compromised': sim.is_compromised,
                'sent_at': sim.sent_at,
                'first_opened_at': sim.first_opened_at,
                'clicked_at': sim.clicked_at,
                'reported_at': sim.reported_at,
                'time_to_open_seconds': time_to_open,
                'time_to_click_seconds': time_to_click,
                'risk_level': risk_level
            })

        serializer = EmployeeSimulationResultSerializer(results, many=True)
        return Response({
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'total_results': len(results),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, HasCompanyAccess])
    def events(self, request, pk=None):
        """
        Get all tracking events for a campaign.

        Returns a paginated list of TrackingEvent records.
        """
        campaign = self.get_object()
        events = campaign.tracking_events.all().order_by('-created_at')

        # Filter by event type if provided
        event_type = request.query_params.get('event_type')
        if event_type:
            events = events.filter(event_type=event_type)

        # Paginate
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = TrackingEventListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TrackingEventListSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def complete(self, request, pk=None):
        """
        Mark a campaign as completed.

        Stops tracking and calculates final statistics.
        """
        campaign = self.get_object()

        if campaign.status not in ['IN_PROGRESS', 'SCHEDULED']:
            return Response(
                {'error': f'Cannot complete campaign with status: {campaign.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update template usage statistics
        template = campaign.template
        template.times_used = template.campaigns.filter(status='COMPLETED').count() + 1

        # Calculate and update average click rate for template
        completed_campaigns = template.campaigns.filter(status='COMPLETED')
        if completed_campaigns.exists():
            total_click_rate = sum(c.click_rate for c in completed_campaigns) + campaign.click_rate
            template.average_click_rate = total_click_rate / (completed_campaigns.count() + 1)
        else:
            template.average_click_rate = campaign.click_rate

        template.save()

        # Update campaign status
        campaign.status = 'COMPLETED'
        campaign.completed_at = timezone.now()
        campaign.save()

        return Response(
            SimulationCampaignDetailSerializer(campaign).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def pause(self, request, pk=None):
        """Pause an in-progress campaign."""
        campaign = self.get_object()

        if campaign.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Can only pause campaigns that are in progress.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.status = 'PAUSED'
        campaign.save()

        return Response(
            SimulationCampaignDetailSerializer(campaign).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def resume(self, request, pk=None):
        """Resume a paused campaign."""
        campaign = self.get_object()

        if campaign.status != 'PAUSED':
            return Response(
                {'error': 'Can only resume campaigns that are paused.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.status = 'IN_PROGRESS'
        campaign.save()

        return Response(
            SimulationCampaignDetailSerializer(campaign).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def generate_package(self, request, pk=None):
        """
        Generate downloadable CSV package with personalized simulation emails.

        This creates EmailSimulation records for each target employee and
        generates a CSV file that admins can use to send emails manually
        from their own email accounts (Gmail, Outlook, etc.).

        The CSV contains:
        - employee_email: Target employee's email address
        - employee_name: Target employee's full name
        - subject: Email subject line
        - body_html: Personalized HTML body with embedded tracking URLs
        - body_plain: Plain text version
        - sender_name: Suggested sender name
        - sender_email: Suggested sender email
        - reply_to: Suggested reply-to address

        Returns:
            CSV file download
        """
        from .services import generate_email_package

        campaign = self.get_object()

        # Validate campaign status
        if campaign.status not in ['DRAFT', 'SCHEDULED', 'IN_PROGRESS']:
            return Response(
                {'error': 'Can only generate package for active campaigns.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if campaign has target employees
        if campaign.target_all_employees:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            target_count = User.objects.filter(
                company=campaign.company,
                role='EMPLOYEE',
                is_active=True
            ).count()
        else:
            target_count = campaign.target_employees.count()

        if target_count == 0:
            return Response(
                {'error': 'No target employees found for this campaign.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate CSV content
        csv_content = generate_email_package(campaign)

        # Update campaign status to SCHEDULED
        campaign.status = 'SCHEDULED'
        campaign.save()

        # Return CSV file download
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="simulation_campaign_{campaign.id}_emails.csv"'

        return response

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def preview_package(self, request, pk=None):
        """
        Preview the email package without creating EmailSimulation records.

        Returns JSON with personalized emails for review before generating
        the actual package.
        """
        from .services import generate_email_package_json

        campaign = self.get_object()

        # Validate campaign status
        if campaign.status not in ['DRAFT', 'SCHEDULED']:
            return Response(
                {'error': 'Can only preview package for DRAFT or SCHEDULED campaigns.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate email list as JSON
        emails = generate_email_package_json(campaign)

        return Response({
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'template_name': campaign.template.name,
            'total_emails': len(emails),
            'emails': emails
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdminOrCompanyAdmin])
    def mark_sent(self, request, pk=None):
        """
        Mark all pending emails as sent after admin confirms manual sending.

        Call this endpoint after the admin has manually sent all the emails
        from the downloaded CSV package.
        """
        from .services import mark_campaign_emails_sent

        campaign = self.get_object()

        # Validate campaign has been scheduled (package generated)
        if campaign.status not in ['SCHEDULED', 'DRAFT']:
            return Response(
                {'error': 'Campaign must be in SCHEDULED or DRAFT status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if there are any pending simulations
        pending_count = campaign.email_simulations.filter(status='PENDING').count()

        if pending_count == 0:
            return Response(
                {'error': 'No pending email simulations found. Generate a package first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark all as sent
        updated_count = mark_campaign_emails_sent(campaign)

        return Response({
            'message': f'Successfully marked {updated_count} emails as sent.',
            'campaign_id': campaign.id,
            'campaign_status': campaign.status,
            'emails_marked_sent': updated_count
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, HasCompanyAccess])
    def summary(self, request, pk=None):
        """
        Get a quick summary of campaign statistics.
        """
        from .services import get_campaign_summary

        campaign = self.get_object()
        summary = get_campaign_summary(campaign)

        return Response(summary, status=status.HTTP_200_OK)


# =============================================================================
# EmailSimulation ViewSet (Read-Only)
# =============================================================================

class EmailSimulationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing EmailSimulation records.

    Read-only access to individual simulation results.
    """

    queryset = EmailSimulation.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return EmailSimulationDetailSerializer
        return EmailSimulationListSerializer

    def get_queryset(self):
        """Filter simulations based on user role."""
        user = self.request.user

        if user.is_super_admin:
            return EmailSimulation.objects.all()

        if user.has_company_access:
            return EmailSimulation.objects.filter(campaign__company=user.company)

        return EmailSimulation.objects.none()


# =============================================================================
# Tracking Views (Function-Based, No Authentication)
# =============================================================================

def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['GET'])
@permission_classes([AllowAny])
def track_pixel_view(request, tracking_token):
    """
    Serve 1x1 transparent tracking pixel and log EMAIL_OPENED event.

    This endpoint is embedded in simulation emails as an image.
    When the email is opened, the image loads and triggers this view.
    """
    try:
        email_sim = EmailSimulation.objects.select_related(
            'campaign', 'employee'
        ).get(tracking_token=tracking_token)
    except EmailSimulation.DoesNotExist:
        # Return pixel anyway to avoid revealing that the token is invalid
        return HttpResponse(TRACKING_PIXEL, content_type='image/png')

    # Check if campaign is still active
    if email_sim.campaign.status not in ['IN_PROGRESS', 'SCHEDULED']:
        return HttpResponse(TRACKING_PIXEL, content_type='image/png')

    # Check if tracking is enabled
    if not email_sim.campaign.track_email_opens:
        return HttpResponse(TRACKING_PIXEL, content_type='image/png')

    # Log the tracking event
    TrackingEvent.objects.create(
        email_simulation=email_sim,
        campaign=email_sim.campaign,
        employee=email_sim.employee,
        event_type='EMAIL_OPENED',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # Set cache headers to prevent caching
    response = HttpResponse(TRACKING_PIXEL, content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def track_link_click_view(request, link_token):
    """
    Log LINK_CLICKED event and redirect to landing page.

    This endpoint is the phishing link embedded in simulation emails.
    When clicked, it logs the event and redirects to educational content.
    """
    try:
        email_sim = EmailSimulation.objects.select_related(
            'campaign', 'campaign__template', 'employee'
        ).get(link_token=link_token)
    except EmailSimulation.DoesNotExist:
        # Redirect to a generic error page
        return HttpResponseRedirect('/simulation-error/')

    # Check if campaign is still active
    if email_sim.campaign.status not in ['IN_PROGRESS', 'SCHEDULED']:
        return HttpResponseRedirect('/simulation-expired/')

    # Check if tracking is enabled
    if email_sim.campaign.track_link_clicks:
        # Log the tracking event
        TrackingEvent.objects.create(
            email_simulation=email_sim,
            campaign=email_sim.campaign,
            employee=email_sim.employee,
            event_type='LINK_CLICKED',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    # Redirect to landing page
    landing_url = reverse('simulations:landing-page', kwargs={'link_token': link_token})
    return HttpResponseRedirect(landing_url)


@api_view(['GET'])
@permission_classes([AllowAny])
def landing_page_view(request, link_token):
    """
    Display "You've been caught" educational landing page.

    Shows the employee what red flags they should have noticed
    and provides educational content about phishing.

    Supports language toggle via ?lang=en or ?lang=ar query parameter.
    """
    try:
        email_sim = EmailSimulation.objects.select_related(
            'campaign', 'campaign__template', 'campaign__company', 'employee'
        ).get(link_token=link_token)
    except EmailSimulation.DoesNotExist:
        return render(request, 'simulations/error.html', {
            'message': 'This simulation link is invalid or has expired.'
        })

    template = email_sim.campaign.template
    campaign = email_sim.campaign

    # Log landing page view event
    TrackingEvent.objects.create(
        email_simulation=email_sim,
        campaign=campaign,
        employee=email_sim.employee,
        event_type='LANDING_PAGE_VIEWED',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # Determine language - check query param first, then employee preference
    lang_param = request.GET.get('lang')
    if lang_param in ['en', 'ar']:
        language = lang_param
    elif hasattr(email_sim.employee, 'preferred_language'):
        language = email_sim.employee.preferred_language
    else:
        language = 'en'

    # Get appropriate content based on language
    if language == 'ar' and template.landing_page_message_ar:
        message = template.landing_page_message_ar
        title = template.landing_page_title or 'تنبيه أمني!'
    else:
        message = template.landing_page_message or 'This was a phishing simulation test.'
        title = template.landing_page_title or 'Security Alert!'

    # Get employee name, fallback to email prefix if empty
    employee_name = email_sim.employee.get_full_name()
    if not employee_name or employee_name.strip() == '':
        employee_name = email_sim.employee.email.split('@')[0].title()

    context = {
        'title': title,
        'message': message,
        'red_flags': template.red_flags or [],
        'attack_vector': template.get_attack_vector_display(),
        'difficulty': template.get_difficulty_display(),
        'employee_name': employee_name,
        'employee_email': email_sim.employee.email,
        'company_name': campaign.company.name,
        'campaign_name': campaign.name,
        'email_subject': template.subject,
        'link_token': link_token,
        'language': language,
        'requires_landing_page': template.requires_landing_page
    }

    return render(request, 'simulations/landing_page.html', context)


@api_view(['POST'])
@permission_classes([AllowAny])
def report_phishing_view(request, link_token):
    """
    Handle employee reporting a phishing email.

    This is a positive action - the employee correctly identified
    the email as suspicious and reported it.
    """
    try:
        email_sim = EmailSimulation.objects.select_related(
            'campaign', 'employee'
        ).get(link_token=link_token)
    except EmailSimulation.DoesNotExist:
        return Response(
            {'error': 'Invalid simulation link.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if already reported
    if email_sim.was_reported:
        return Response(
            {'message': 'You have already reported this email. Thank you!'},
            status=status.HTTP_200_OK
        )

    # Get optional reason from request
    reason = request.data.get('reason', '')

    # Log the tracking event
    TrackingEvent.objects.create(
        email_simulation=email_sim,
        campaign=email_sim.campaign,
        employee=email_sim.employee,
        event_type='EMAIL_REPORTED',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        event_data={'reason': reason} if reason else {}
    )

    return Response({
        'message': 'Thank you for reporting this suspicious email! '
                   'This was a security awareness simulation. '
                   'Your vigilance helps keep our organization safe.',
        'was_simulation': True
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def credentials_submitted_view(request, link_token):
    """
    Handle fake credential submission from landing page.

    If track_credentials is enabled, this logs when employees
    enter credentials into the fake login form.

    NOTE: Credentials are NEVER stored - only the fact that
    they were entered is logged for training purposes.
    """
    try:
        email_sim = EmailSimulation.objects.select_related(
            'campaign', 'employee'
        ).get(link_token=link_token)
    except EmailSimulation.DoesNotExist:
        return Response(
            {'error': 'Invalid simulation link.'},
            status=status.HTTP_404_NOT_FOUND
        )

    campaign = email_sim.campaign

    # Check if credential tracking is enabled
    if not campaign.track_credentials:
        return Response(
            {'message': 'Credential tracking is not enabled for this campaign.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Log the tracking event (DO NOT store actual credentials!)
    TrackingEvent.objects.create(
        email_simulation=email_sim,
        campaign=campaign,
        employee=email_sim.employee,
        event_type='CREDENTIALS_ENTERED',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        event_data={
            'username_field_filled': bool(request.data.get('username')),
            'password_field_filled': bool(request.data.get('password')),
            # Never log actual credential values!
        }
    )

    # Notify admin if enabled
    if campaign.notify_on_credential_entry:
        # TODO: Implement admin notification (email/webhook)
        pass

    return Response({
        'message': 'This was a phishing simulation. '
                   'Your credentials were NOT captured or stored. '
                   'Please review the security training materials.',
        'was_simulation': True
    }, status=status.HTTP_200_OK)
