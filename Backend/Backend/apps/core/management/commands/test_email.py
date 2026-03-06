"""
Management command: test_email

Sends a real email via the configured backend (SendGrid SMTP) to verify
that the email system is working correctly.

Usage:
    python manage.py test_email --to you@example.com
    python manage.py test_email --to you@example.com --type verification
    python manage.py test_email --to you@example.com --type invitation
    python manage.py test_email --to you@example.com --type password_reset
    python manage.py test_email --to you@example.com --type all
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class FakeUser:
    """Minimal user-like object for template rendering."""
    def __init__(self, email, first_name='Test', last_name='User'):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'


class FakeCompany:
    """Minimal company-like object."""
    def __init__(self, name='Acme Corporation'):
        self.name = name


class Command(BaseCommand):
    help = 'Send a test email to verify SendGrid configuration.'

    EMAIL_TYPES = ['verification', 'invitation', 'password_reset', 'all']

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            required=True,
            help='Recipient email address for the test.',
        )
        parser.add_argument(
            '--type',
            default='all',
            choices=self.EMAIL_TYPES,
            help='Which email template to test (default: all).',
        )

    def handle(self, *args, **options):
        from apps.core.emails import (
            send_verification_email,
            send_employee_invitation,
            send_password_reset_email,
        )

        recipient = options['to']
        email_type = options['type']

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== PhishAware Email Test ==='))
        self.stdout.write(f'Backend : {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Host    : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'From    : {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'To      : {recipient}')
        self.stdout.write(f'Type    : {email_type}\n')

        fake_user = FakeUser(email=recipient)
        fake_admin = FakeUser(email='admin@phishaware.com', first_name='Admin', last_name='User')
        fake_company = FakeCompany()
        test_token = 'test-token-abc123xyz'

        results = {}

        if email_type in ('verification', 'all'):
            self.stdout.write('Sending verification email...', ending=' ')
            ok = send_verification_email(fake_user, verification_token=test_token)
            results['verification'] = ok
            self._print_result(ok)

        if email_type in ('invitation', 'all'):
            self.stdout.write('Sending invitation email...', ending=' ')
            ok = send_employee_invitation(
                inviting_admin=fake_admin,
                employee_email=recipient,
                employee_name='Test Employee',
                company=fake_company,
                invitation_token=test_token,
            )
            results['invitation'] = ok
            self._print_result(ok)

        if email_type in ('password_reset', 'all'):
            self.stdout.write('Sending password reset email...', ending=' ')
            ok = send_password_reset_email(fake_user, reset_token=test_token)
            results['password_reset'] = ok
            self._print_result(ok)

        # Summary
        self.stdout.write('')
        passed = sum(results.values())
        total = len(results)

        if passed == total:
            self.stdout.write(self.style.SUCCESS(f'All {total}/{total} emails sent successfully.'))
            self.stdout.write(self.style.SUCCESS(f'Check {recipient} inbox (and spam folder).'))
        else:
            failed = [k for k, v in results.items() if not v]
            self.stdout.write(self.style.ERROR(
                f'{passed}/{total} emails sent. Failed: {", ".join(failed)}'
            ))
            self.stdout.write('Check the Django logs above for error details.')
            raise CommandError('One or more test emails failed to send.')

    def _print_result(self, ok):
        if ok:
            self.stdout.write(self.style.SUCCESS('OK'))
        else:
            self.stdout.write(self.style.ERROR('FAILED'))
