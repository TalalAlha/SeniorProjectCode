from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import EmailTemplate, QuizQuestion
from apps.campaigns.models import Campaign
from .serializers import (
    EmailTemplateSerializer,
    EmailTemplateCreateSerializer,
    AIEmailGenerationRequestSerializer,
    QuizQuestionSerializer
)
from apps.core.permissions import IsSuperAdminOrCompanyAdmin, HasCompanyAccess


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailTemplate CRUD operations.

    Admins can create, update, and delete email templates.
    Employees can only view templates (for learning purposes).
    """

    queryset = EmailTemplate.objects.all()
    permission_classes = [IsAuthenticated, HasCompanyAccess]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return EmailTemplateCreateSerializer
        return EmailTemplateSerializer

    def get_queryset(self):
        """Filter email templates based on user role and company."""
        user = self.request.user

        if user.is_super_admin:
            return EmailTemplate.objects.all()

        # Filter by user's company
        if user.has_company_access:
            return EmailTemplate.objects.filter(campaign__company=user.company)

        return EmailTemplate.objects.none()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSuperAdminOrCompanyAdmin()]
        return [IsAuthenticated(), HasCompanyAccess()]


class AIEmailGenerationView(views.APIView):
    """
    API endpoint for generating phishing and legitimate emails using AI.

    This is a placeholder for AI integration. In production, this would
    connect to your PyTorch LSTM model or external AI service.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminOrCompanyAdmin]

    def post(self, request):
        """Generate emails using AI based on provided parameters."""
        serializer = AIEmailGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        campaign_id = serializer.validated_data['campaign_id']
        num_phishing = serializer.validated_data['num_phishing_emails']
        num_legitimate = serializer.validated_data['num_legitimate_emails']
        language = serializer.validated_data.get('language', 'en')

        # Get campaign
        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            return Response(
                {'error': f'Campaign with id {campaign_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has permission to access this campaign
        if not request.user.is_super_admin and campaign.company != request.user.company:
            return Response(
                {'error': 'You do not have permission to generate emails for this campaign'},
                status=status.HTTP_403_FORBIDDEN
            )

        # TODO: Replace this with actual AI model integration
        # For now, we'll create sample template emails
        generated_emails = {
            'phishing_emails': self._generate_sample_phishing_emails(campaign, num_phishing, language),
            'legitimate_emails': self._generate_sample_legitimate_emails(campaign, num_legitimate, language)
        }

        return Response({
            'message': 'Emails generated successfully',
            'campaign_id': campaign_id,
            'generated_count': {
                'phishing': len(generated_emails['phishing_emails']),
                'legitimate': len(generated_emails['legitimate_emails']),
                'total': len(generated_emails['phishing_emails']) + len(generated_emails['legitimate_emails'])
            },
            'emails': generated_emails
        }, status=status.HTTP_201_CREATED)

    def _generate_sample_phishing_emails(self, campaign, count, language):
        """
        Generate sample phishing emails.

        TODO: Replace with actual AI model integration.
        This should call your PyTorch LSTM model trained on phishing emails.
        """
        phishing_templates = [
            {
                'sender_name': 'IT Support',
                'sender_email': 'it-support@company-security.com',
                'subject': 'Urgent: Password Reset Required',
                'body': 'Dear User,\n\nYour password will expire in 24 hours. Click here to reset: http://fake-link.com\n\nIT Support Team',
                'category': 'CREDENTIAL_HARVESTING',
                'difficulty': 'EASY',
                'red_flags': [
                    'Sense of urgency',
                    'Suspicious sender email domain',
                    'Request for password reset via link',
                    'Generic greeting'
                ],
                'explanation': 'This is a phishing email attempting to steal credentials. Red flags include urgency tactics, suspicious domain, and unsolicited password reset request.'
            },
            {
                'sender_name': 'CEO Office',
                'sender_email': 'ceo@company.co',
                'subject': 'Confidential: Wire Transfer Needed',
                'body': 'I need you to process an urgent wire transfer. Reply immediately with bank account details.\n\nThanks,\nCEO',
                'category': 'BUSINESS_EMAIL_COMPROMISE',
                'difficulty': 'MEDIUM',
                'red_flags': [
                    'Impersonation of authority figure',
                    'Requests for sensitive financial information',
                    'Unusual domain (.co instead of .com)',
                    'Pressure tactics'
                ],
                'explanation': 'Business Email Compromise (BEC) attack impersonating a CEO to request unauthorized financial transactions.'
            }
        ]

        created_emails = []
        for i in range(min(count, len(phishing_templates))):
            template = phishing_templates[i % len(phishing_templates)]

            email = EmailTemplate.objects.create(
                campaign=campaign,
                sender_name=template['sender_name'],
                sender_email=template['sender_email'],
                subject=f"{template['subject']} #{i+1}",
                body=template['body'],
                email_type='PHISHING',
                category=template['category'],
                difficulty=template['difficulty'],
                is_ai_generated=True,
                ai_model_used='LSTM-Phishing-Generator-v1',
                red_flags=template['red_flags'],
                explanation=template['explanation'],
                language=language,
                created_by=self.request.user
            )
            created_emails.append(EmailTemplateSerializer(email).data)

        return created_emails

    def _generate_sample_legitimate_emails(self, campaign, count, language):
        """
        Generate sample legitimate emails.

        TODO: Replace with actual AI model integration.
        """
        legitimate_templates = [
            {
                'sender_name': 'HR Department',
                'sender_email': 'hr@yourcompany.com',
                'subject': 'Employee Benefits Update - Q1 2024',
                'body': 'Dear Team,\n\nWe are pleased to announce updates to our employee benefits package. Please review the attached document.\n\nBest regards,\nHR Team',
                'category': 'LEGITIMATE_BUSINESS',
                'difficulty': 'EASY',
                'explanation': 'This is a legitimate internal communication from the HR department with proper domain and professional tone.'
            },
            {
                'sender_name': 'Project Manager',
                'sender_email': 'pm@yourcompany.com',
                'subject': 'Weekly Team Meeting - Thursday 2PM',
                'body': 'Hi Team,\n\nReminder about our weekly sync meeting this Thursday at 2PM in Conference Room A.\n\nAgenda:\n1. Project updates\n2. Blockers discussion\n\nSee you there!\nProject Manager',
                'category': 'LEGITIMATE_BUSINESS',
                'difficulty': 'EASY',
                'explanation': 'Legitimate internal meeting invitation from a verified company email address.'
            }
        ]

        created_emails = []
        for i in range(min(count, len(legitimate_templates))):
            template = legitimate_templates[i % len(legitimate_templates)]

            email = EmailTemplate.objects.create(
                campaign=campaign,
                sender_name=template['sender_name'],
                sender_email=template['sender_email'],
                subject=f"{template['subject']} #{i+1}",
                body=template['body'],
                email_type='LEGITIMATE',
                category=template['category'],
                difficulty=template['difficulty'],
                is_ai_generated=True,
                ai_model_used='LSTM-Legitimate-Generator-v1',
                explanation=template['explanation'],
                language=language,
                created_by=self.request.user
            )
            created_emails.append(EmailTemplateSerializer(email).data)

        return created_emails
