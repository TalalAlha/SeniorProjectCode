"""
Email utility functions for PhishAware platform.

All outbound emails are sent via SendGrid SMTP relay using Django's
built-in mail backend. Templates live in apps/core/templates/emails/.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _get_from_email():
    """Return the verified sender address from settings."""
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'PhishAware <noreply@phishaware.com>')


def _send_html_email(subject, template_name, context, recipient_email, from_email=None):
    """
    Core helper: render an HTML template and send with a plain-text fallback.

    Returns True on success, False on failure.
    """
    if from_email is None:
        from_email = _get_from_email()

    # Merge common context variables
    base_context = {
        'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:5173'),
        'support_email': getattr(settings, 'SENDGRID_VERIFIED_SENDER', from_email),
    }
    base_context.update(context)

    try:
        html_body = render_to_string(f'emails/{template_name}', base_context)
        text_body = strip_tags(html_body)

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[recipient_email],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)

        logger.info('Email "%s" sent successfully to %s', subject, recipient_email)
        return True

    except Exception as exc:
        logger.error(
            'Failed to send email "%s" to %s: %s',
            subject, recipient_email, exc, exc_info=True
        )
        return False


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def send_verification_email(user, verification_token):
    """
    Send an email-address verification link to a newly registered user.

    Args:
        user: User model instance (needs .email, .get_full_name(), .first_name)
        verification_token (str): Signed token / UUID for the verification URL.

    Returns:
        bool: True if the email was accepted by SendGrid.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    verification_url = f'{frontend_url}/verify-email/{verification_token}'

    return _send_html_email(
        subject='Verify your PhishAware account',
        template_name='verification.html',
        context={
            'user': user,
            'user_name': user.first_name or user.get_full_name() or user.email,
            'verification_url': verification_url,
        },
        recipient_email=user.email,
    )


def send_employee_invitation(inviting_admin, employee_email, employee_name, company, invitation_token):
    """
    Send a company invitation to a new employee.

    Args:
        inviting_admin: User instance of the admin sending the invite.
        employee_email (str): Recipient email address.
        employee_name (str): Display name for the greeting.
        company: Company model instance (needs .name).
        invitation_token (str): Token used to build the accept-invite URL.

    Returns:
        bool: True if the email was accepted by SendGrid.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    invitation_url = f'{frontend_url}/accept-invitation/{invitation_token}'

    return _send_html_email(
        subject=f"You've been invited to join {company.name} on PhishAware",
        template_name='invitation.html',
        context={
            'employee_name': employee_name or employee_email,
            'company_name': company.name,
            'inviting_admin_name': inviting_admin.get_full_name() or inviting_admin.email,
            'invitation_url': invitation_url,
        },
        recipient_email=employee_email,
    )


def send_simulation_email(recipient_email, recipient_name, subject, html_body, simulation_id=None):
    """
    Send a phishing simulation email directly (plain send, no extra wrapper template).

    The caller is responsible for providing the full HTML body that already
    contains tracking pixels / click-tracking links.

    Args:
        recipient_email (str): Target employee email.
        recipient_name (str): Employee display name.
        subject (str): Spoofed email subject line.
        html_body (str): Full HTML content (may include tracking links).
        simulation_id: Optional ID used only for logging.

    Returns:
        bool: True if the email was accepted by SendGrid.
    """
    from_email = _get_from_email()
    text_body = strip_tags(html_body)

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[recipient_email],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)

        logger.info(
            'Simulation email (id=%s) sent to %s <%s>',
            simulation_id, recipient_name, recipient_email
        )
        return True

    except Exception as exc:
        logger.error(
            'Failed to send simulation email (id=%s) to %s: %s',
            simulation_id, recipient_email, exc, exc_info=True
        )
        return False


def send_password_reset_email(user, reset_token):
    """
    Send a password-reset link to the user.

    Args:
        user: User model instance.
        reset_token (str): Signed token / UUID for the reset URL.

    Returns:
        bool: True if the email was accepted by SendGrid.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    reset_url = f'{frontend_url}/reset-password/{reset_token}'

    return _send_html_email(
        subject='Reset your PhishAware password',
        template_name='password_reset.html',
        context={
            'user': user,
            'user_name': user.first_name or user.get_full_name() or user.email,
            'reset_url': reset_url,
        },
        recipient_email=user.email,
    )
