"""
Services for simulation campaign management.

This module provides utility functions for generating email packages
and other simulation-related operations.
"""

import csv
import io
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import SimulationCampaign, EmailSimulation

User = get_user_model()


def generate_email_package(campaign: SimulationCampaign) -> str:
    """
    Generate a CSV file with personalized simulation emails for manual sending.

    This function creates EmailSimulation records for each target employee
    and generates a CSV file containing personalized email content that
    admins can use to send emails manually from their own email accounts.

    Args:
        campaign: The SimulationCampaign instance to generate emails for.

    Returns:
        str: CSV content as a string with columns:
            - employee_email: Target employee's email address
            - employee_name: Target employee's full name
            - subject: Email subject line
            - body_html: Personalized HTML body with tracking URLs

    Workflow:
        1. Gets target employees from campaign
        2. For each employee, creates/gets EmailSimulation record
        3. Replaces placeholders with actual values:
           - {TRACKING_PIXEL} -> <img src="...tracking URL...">
           - {LURE_LINK} -> Unique phishing link URL
           - {EMPLOYEE_NAME} -> Employee's name
           - {EMPLOYEE_FIRST_NAME} -> Employee's first name
           - {EMPLOYEE_EMAIL} -> Employee's email
           - {COMPANY_NAME} -> Company name
        4. Builds CSV with all personalized emails
    """
    # Get base URL from settings or use default
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Get the template
    template = campaign.template

    # Get target employees
    if campaign.target_all_employees:
        target_employees = User.objects.filter(
            company=campaign.company,
            role='EMPLOYEE',
            is_active=True
        )
    else:
        target_employees = campaign.target_employees.all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Write header row
    writer.writerow([
        'employee_email',
        'employee_name',
        'tracking_url',
        'subject',
        'body_html',
        'body_plain',
        'sender_name',
        'sender_email',
        'reply_to'
    ])

    # Process each employee
    for employee in target_employees:
        # Create or get EmailSimulation record
        email_sim, created = EmailSimulation.objects.get_or_create(
            campaign=campaign,
            employee=employee,
            defaults={
                'recipient_email': employee.email,
                'status': 'PENDING'
            }
        )

        # Build tracking URLs
        tracking_pixel_url = f"{base_url}/api/v1/simulations/track/{email_sim.tracking_token}/"
        phishing_link_url = f"{base_url}/api/v1/simulations/link/{email_sim.link_token}/"

        # Create tracking pixel HTML tag
        tracking_pixel_html = (
            f'<img src="{tracking_pixel_url}" width="1" height="1" '
            f'alt="" style="display:none;border:0;height:1px;width:1px;" />'
        )

        # Get employee name
        employee_name = employee.get_full_name() or employee.email.split('@')[0]
        employee_first_name = employee.first_name or employee_name.split()[0] if employee_name else ''

        # Replace placeholders in HTML body — {UPPERCASE} format
        body_html = template.body_html
        body_html = body_html.replace('{TRACKING_PIXEL}', tracking_pixel_html)
        body_html = body_html.replace('{LURE_LINK}', phishing_link_url)
        body_html = body_html.replace('{EMPLOYEE_NAME}', employee_name)
        body_html = body_html.replace('{EMPLOYEE_FIRST_NAME}', employee_first_name)
        body_html = body_html.replace('{EMPLOYEE_EMAIL}', employee.email)
        body_html = body_html.replace('{COMPANY_NAME}', campaign.company.name)
        # Also handle {{lowercase}} variant placeholders
        body_html = body_html.replace('{{tracking_pixel}}', tracking_pixel_html)
        body_html = body_html.replace('{{phishing_link}}', phishing_link_url)
        body_html = body_html.replace('{{employee_name}}', employee_name)
        body_html = body_html.replace('{{employee_first_name}}', employee_first_name)
        body_html = body_html.replace('{{employee_email}}', employee.email)
        body_html = body_html.replace('{{company_name}}', campaign.company.name)

        # Replace placeholders in plain text body — {UPPERCASE} format
        body_plain = template.body_plain or ''
        body_plain = body_plain.replace('{LURE_LINK}', phishing_link_url)
        body_plain = body_plain.replace('{EMPLOYEE_NAME}', employee_name)
        body_plain = body_plain.replace('{EMPLOYEE_FIRST_NAME}', employee_first_name)
        body_plain = body_plain.replace('{EMPLOYEE_EMAIL}', employee.email)
        body_plain = body_plain.replace('{COMPANY_NAME}', campaign.company.name)
        # Also handle {{lowercase}} variant placeholders
        body_plain = body_plain.replace('{{phishing_link}}', phishing_link_url)
        body_plain = body_plain.replace('{{employee_name}}', employee_name)
        body_plain = body_plain.replace('{{employee_first_name}}', employee_first_name)
        body_plain = body_plain.replace('{{employee_email}}', employee.email)
        body_plain = body_plain.replace('{{company_name}}', campaign.company.name)

        # Replace placeholders in subject — {UPPERCASE} format
        subject = template.subject
        subject = subject.replace('{EMPLOYEE_NAME}', employee_name)
        subject = subject.replace('{EMPLOYEE_FIRST_NAME}', employee_first_name)
        subject = subject.replace('{COMPANY_NAME}', campaign.company.name)
        # Also handle {{lowercase}} variant placeholders
        subject = subject.replace('{{employee_name}}', employee_name)
        subject = subject.replace('{{employee_first_name}}', employee_first_name)
        subject = subject.replace('{{company_name}}', campaign.company.name)

        # Write row to CSV
        writer.writerow([
            employee.email,
            employee_name,
            phishing_link_url,
            subject,
            body_html,
            body_plain,
            template.sender_name,
            template.sender_email,
            template.reply_to_email or ''
        ])

    # Get CSV content
    csv_content = output.getvalue()
    output.close()

    return csv_content


def generate_email_package_json(campaign: SimulationCampaign) -> list:
    """
    Generate a list of personalized simulation emails as JSON-serializable dicts.

    Similar to generate_email_package but returns a list of dictionaries
    instead of CSV content, useful for API responses.

    Args:
        campaign: The SimulationCampaign instance to generate emails for.

    Returns:
        list: List of dictionaries, each containing:
            - employee_email
            - employee_name
            - subject
            - body_html
            - body_plain
            - sender_name
            - sender_email
            - reply_to
            - tracking_token
            - link_token
    """
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    template = campaign.template

    # Get target employees
    if campaign.target_all_employees:
        target_employees = User.objects.filter(
            company=campaign.company,
            role='EMPLOYEE',
            is_active=True
        )
    else:
        target_employees = campaign.target_employees.all()

    emails = []

    for employee in target_employees:
        # Create or get EmailSimulation record
        email_sim, created = EmailSimulation.objects.get_or_create(
            campaign=campaign,
            employee=employee,
            defaults={
                'recipient_email': employee.email,
                'status': 'PENDING'
            }
        )

        # Build tracking URLs
        tracking_pixel_url = f"{base_url}/api/v1/simulations/track/{email_sim.tracking_token}/"
        phishing_link_url = f"{base_url}/api/v1/simulations/link/{email_sim.link_token}/"

        # Create tracking pixel HTML
        tracking_pixel_html = (
            f'<img src="{tracking_pixel_url}" width="1" height="1" '
            f'alt="" style="display:none;border:0;height:1px;width:1px;" />'
        )

        # Get employee name
        employee_name = employee.get_full_name() or employee.email.split('@')[0]
        employee_first_name = employee.first_name or employee_name.split()[0] if employee_name else ''

        # Replace placeholders in HTML body — {UPPERCASE} format
        body_html = template.body_html
        body_html = body_html.replace('{TRACKING_PIXEL}', tracking_pixel_html)
        body_html = body_html.replace('{LURE_LINK}', phishing_link_url)
        body_html = body_html.replace('{EMPLOYEE_NAME}', employee_name)
        body_html = body_html.replace('{EMPLOYEE_FIRST_NAME}', employee_first_name)
        body_html = body_html.replace('{EMPLOYEE_EMAIL}', employee.email)
        body_html = body_html.replace('{COMPANY_NAME}', campaign.company.name)
        # Also handle {{lowercase}} variant placeholders
        body_html = body_html.replace('{{tracking_pixel}}', tracking_pixel_html)
        body_html = body_html.replace('{{phishing_link}}', phishing_link_url)
        body_html = body_html.replace('{{employee_name}}', employee_name)
        body_html = body_html.replace('{{employee_first_name}}', employee_first_name)
        body_html = body_html.replace('{{employee_email}}', employee.email)
        body_html = body_html.replace('{{company_name}}', campaign.company.name)

        # Replace placeholders in plain text — {UPPERCASE} format
        body_plain = template.body_plain or ''
        body_plain = body_plain.replace('{LURE_LINK}', phishing_link_url)
        body_plain = body_plain.replace('{EMPLOYEE_NAME}', employee_name)
        body_plain = body_plain.replace('{EMPLOYEE_FIRST_NAME}', employee_first_name)
        body_plain = body_plain.replace('{EMPLOYEE_EMAIL}', employee.email)
        body_plain = body_plain.replace('{COMPANY_NAME}', campaign.company.name)
        # Also handle {{lowercase}} variant placeholders
        body_plain = body_plain.replace('{{phishing_link}}', phishing_link_url)
        body_plain = body_plain.replace('{{employee_name}}', employee_name)
        body_plain = body_plain.replace('{{employee_first_name}}', employee_first_name)
        body_plain = body_plain.replace('{{employee_email}}', employee.email)
        body_plain = body_plain.replace('{{company_name}}', campaign.company.name)

        # Replace placeholders in subject — {UPPERCASE} format
        subject = template.subject
        subject = subject.replace('{EMPLOYEE_NAME}', employee_name)
        subject = subject.replace('{EMPLOYEE_FIRST_NAME}', employee_first_name)
        subject = subject.replace('{COMPANY_NAME}', campaign.company.name)
        # Also handle {{lowercase}} variant placeholders
        subject = subject.replace('{{employee_name}}', employee_name)
        subject = subject.replace('{{employee_first_name}}', employee_first_name)
        subject = subject.replace('{{company_name}}', campaign.company.name)

        emails.append({
            'employee_email': employee.email,
            'employee_name': employee_name,
            'subject': subject,
            'body_html': body_html,
            'body_plain': body_plain,
            'sender_name': template.sender_name,
            'sender_email': template.sender_email,
            'reply_to': template.reply_to_email or '',
            'tracking_token': str(email_sim.tracking_token),
            'link_token': email_sim.link_token
        })

    return emails


def mark_campaign_emails_sent(campaign: SimulationCampaign) -> int:
    """
    Mark all pending EmailSimulation records for a campaign as sent.

    Used after admin confirms they've manually sent the emails.
    Also updates each targeted employee's RiskScore.total_simulations_received.

    Args:
        campaign: The SimulationCampaign to update.

    Returns:
        int: Number of records updated.
    """
    from django.utils import timezone
    from django.db.models import F

    # Get the pending simulations before bulk update so we can update RiskScores
    pending_employee_ids = list(
        EmailSimulation.objects.filter(
            campaign=campaign,
            status='PENDING'
        ).values_list('employee_id', flat=True)
    )

    updated = EmailSimulation.objects.filter(
        campaign=campaign,
        status='PENDING'
    ).update(
        status='SENT',
        sent_at=timezone.now()
    )

    # Update campaign statistics
    campaign.total_sent = campaign.email_simulations.filter(status='SENT').count()
    campaign.status = 'IN_PROGRESS'
    campaign.sent_at = timezone.now()
    campaign.save()

    # Update each employee's RiskScore.total_simulations_received
    if pending_employee_ids:
        try:
            from apps.training.models import RiskScore

            for emp_id in pending_employee_ids:
                try:
                    employee = User.objects.get(id=emp_id)
                    if employee.role != 'EMPLOYEE':
                        continue

                    risk_score, created = RiskScore.objects.get_or_create(
                        employee=employee,
                        defaults={
                            'company': employee.company,
                            'score': 50,
                            'risk_level': 'MEDIUM'
                        }
                    )
                    risk_score.total_simulations_received = F('total_simulations_received') + 1
                    risk_score.last_simulation_date = timezone.now()
                    risk_score.save(update_fields=['total_simulations_received', 'last_simulation_date'])
                except User.DoesNotExist:
                    continue
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('Error updating risk scores on mark_sent')

    return updated


def get_campaign_summary(campaign: SimulationCampaign) -> dict:
    """
    Get a summary of campaign statistics.

    Args:
        campaign: The SimulationCampaign to summarize.

    Returns:
        dict: Summary statistics including:
            - total_targeted
            - total_simulations
            - pending_count
            - sent_count
            - opened_count
            - clicked_count
            - reported_count
            - rates (open, click, report, compromise)
    """
    simulations = campaign.email_simulations.all()

    # Count by status
    pending_count = simulations.filter(status='PENDING').count()
    sent_count = simulations.filter(status='SENT').count()

    # Count by behavior
    opened_count = simulations.filter(was_opened=True).count()
    clicked_count = simulations.filter(was_clicked=True).count()
    reported_count = simulations.filter(was_reported=True).count()
    credentials_count = simulations.filter(credentials_entered=True).count()

    total = simulations.count()

    return {
        'campaign_id': campaign.id,
        'campaign_name': campaign.name,
        'status': campaign.status,
        'total_targeted': total,
        'pending_count': pending_count,
        'sent_count': sent_count,
        'opened_count': opened_count,
        'clicked_count': clicked_count,
        'reported_count': reported_count,
        'credentials_entered_count': credentials_count,
        'open_rate': round((opened_count / total * 100), 2) if total > 0 else 0,
        'click_rate': round((clicked_count / total * 100), 2) if total > 0 else 0,
        'report_rate': round((reported_count / total * 100), 2) if total > 0 else 0,
        'compromise_rate': round((max(clicked_count, credentials_count) / total * 100), 2) if total > 0 else 0,
    }
