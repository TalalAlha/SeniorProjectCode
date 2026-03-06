"""
Management command to generate test notifications for all types.

Usage:
    python manage.py test_notifications
    python manage.py test_notifications --employee-email emp@example.com --admin-email admin@example.com
    python manage.py test_notifications --clear-first
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.training.models import TrainingModule, RemediationTraining
from apps.simulations.models import SimulationCampaign
from apps.notifications.services import NotificationService
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = 'Generate test notifications for all types to verify the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--employee-email',
            type=str,
            default=None,
            help='Email of employee account (defaults to first active employee found)',
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default=None,
            help='Email of admin account (defaults to first active company admin found)',
        )
        parser.add_argument(
            '--clear-first',
            action='store_true',
            help='Delete existing notifications for these users before creating test ones',
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ok(self, n, label):
        self.stdout.write(self.style.SUCCESS(f'  [OK] {label} (ID: {n.id})'))

    def _fail(self, label, exc):
        self.stdout.write(self.style.ERROR(f'  [FAIL] {label}: {exc}'))

    def _section(self, title):
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.WARNING(f'  {title}'))
        self.stdout.write('-' * 60)

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('  PHISHAWARE NOTIFICATION SYSTEM TEST'))
        self.stdout.write('=' * 60)

        # ── Resolve users ────────────────────────────────────────────
        if options['employee_email']:
            try:
                employee = User.objects.get(email=options['employee_email'])
            except User.DoesNotExist:
                raise CommandError(f"Employee not found: {options['employee_email']}")
        else:
            employee = User.objects.filter(role='EMPLOYEE', is_active=True).first()
            if not employee:
                raise CommandError('No active employee found. Pass --employee-email.')

        if options['admin_email']:
            try:
                admin = User.objects.get(email=options['admin_email'])
            except User.DoesNotExist:
                raise CommandError(f"Admin not found: {options['admin_email']}")
        else:
            admin = User.objects.filter(role='COMPANY_ADMIN', is_active=True).first()
            if not admin:
                raise CommandError('No active company admin found. Pass --admin-email.')

        self.stdout.write(f'\n  Employee : {employee.email}')
        self.stdout.write(f'  Admin    : {admin.email}')

        # ── Optionally clear ─────────────────────────────────────────
        if options['clear_first']:
            deleted, _ = Notification.objects.filter(user__in=[employee, admin]).delete()
            self.stdout.write(self.style.WARNING(f'\n  Cleared {deleted} existing notifications'))

        # ── Resolve supporting objects ────────────────────────────────
        module = (
            TrainingModule.objects.filter(company__isnull=True, is_active=True).first()
            or TrainingModule.objects.filter(is_active=True).first()
        )
        if not module:
            self.stdout.write(self.style.WARNING(
                '\n  No TrainingModule found - run: python manage.py seed_training'
            ))

        assignment = None
        if module:
            assignment = RemediationTraining.objects.filter(employee=employee).first()
            if not assignment:
                assignment = RemediationTraining.objects.create(
                    employee=employee,
                    company=employee.company,
                    training_module=module,
                    assignment_reason='Test notification',
                    assigned_by=admin,
                    due_date=timezone.now() + timedelta(days=7),
                )
                self.stdout.write(f'  Created test RemediationTraining (ID: {assignment.id})')

        campaign = (
            SimulationCampaign.objects.filter(created_by=admin).first()
            or SimulationCampaign.objects.first()
        )
        if not campaign:
            self.stdout.write(self.style.WARNING(
                '\n  No SimulationCampaign found - some notifications will be skipped'
            ))

        created = 0

        # ==============================================================
        # EMPLOYEE NOTIFICATIONS - TRAINING
        # ==============================================================
        self._section('EMPLOYEE - TRAINING')

        if module and assignment:
            try:
                n = NotificationService.notify_training_assigned(employee, module)
                self._ok(n, '1. Training Assigned'); created += 1
            except Exception as e:
                self._fail('1. Training Assigned', e)

            try:
                n = NotificationService.notify_training_due_soon(employee, assignment, days_left=3)
                self._ok(n, '2. Training Due Soon'); created += 1
            except Exception as e:
                self._fail('2. Training Due Soon', e)

            try:
                n = NotificationService.notify_training_due_tomorrow(employee, assignment)
                self._ok(n, '3. Training Due Tomorrow'); created += 1
            except Exception as e:
                self._fail('3. Training Due Tomorrow', e)

            try:
                n = NotificationService.notify_training_overdue(employee, assignment)
                self._ok(n, '4. Training Overdue'); created += 1
            except Exception as e:
                self._fail('4. Training Overdue', e)

            try:
                n = NotificationService.notify_quiz_passed(employee, module, score=85.0)
                self._ok(n, '5. Quiz Passed'); created += 1
            except Exception as e:
                self._fail('5. Quiz Passed', e)

            try:
                n = NotificationService.notify_quiz_failed(employee, module, score=45.0)
                self._ok(n, '6. Quiz Failed'); created += 1
            except Exception as e:
                self._fail('6. Quiz Failed', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped training notifications (no module/assignment)'))

        # ==============================================================
        # EMPLOYEE NOTIFICATIONS - SIMULATION
        # ==============================================================
        self._section('EMPLOYEE - SIMULATION')

        if campaign:
            try:
                n = NotificationService.notify_simulation_launched(employee, campaign)
                self._ok(n, '7. Simulation Launched'); created += 1
            except Exception as e:
                self._fail('7. Simulation Launched', e)

            try:
                n = NotificationService.notify_simulation_safe(employee, campaign)
                self._ok(n, '8. Simulation Safe'); created += 1
            except Exception as e:
                self._fail('8. Simulation Safe', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped simulation notifications (no campaign)'))

        # ==============================================================
        # EMPLOYEE NOTIFICATIONS - ACCOUNT
        # ==============================================================
        self._section('EMPLOYEE - ACCOUNT')

        try:
            n = NotificationService.notify_welcome(employee)
            self._ok(n, '9. Welcome'); created += 1
        except Exception as e:
            self._fail('9. Welcome', e)

        try:
            n = NotificationService.notify_password_changed(employee)
            self._ok(n, '10. Password Changed'); created += 1
        except Exception as e:
            self._fail('10. Password Changed', e)

        # ==============================================================
        # ADMIN NOTIFICATIONS - EMPLOYEE ACTIONS
        # ==============================================================
        self._section('ADMIN - EMPLOYEE ACTIONS')

        if campaign:
            try:
                n = NotificationService.notify_employee_clicked_phishing(admin, employee, campaign)
                self._ok(n, '11. Employee Clicked Phishing'); created += 1
            except Exception as e:
                self._fail('11. Employee Clicked Phishing', e)

            try:
                n = NotificationService.notify_employee_reported_phishing(admin, employee, campaign)
                self._ok(n, '12. Employee Reported Phishing'); created += 1
            except Exception as e:
                self._fail('12. Employee Reported Phishing', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped click/report notifications (no campaign)'))

        if module:
            try:
                n = NotificationService.notify_training_completed(admin, employee, module)
                self._ok(n, '13. Training Completed (admin)'); created += 1
            except Exception as e:
                self._fail('13. Training Completed (admin)', e)

            try:
                n = NotificationService.notify_employee_failed_quiz(admin, employee, module, score=35.0)
                self._ok(n, '14. Employee Failed Quiz'); created += 1
            except Exception as e:
                self._fail('14. Employee Failed Quiz', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped training-admin notifications (no module)'))

        try:
            n = NotificationService.notify_high_risk_employee(admin, employee, risk_score=85)
            self._ok(n, '15. High Risk Employee'); created += 1
        except Exception as e:
            self._fail('15. High Risk Employee', e)

        # ==============================================================
        # ADMIN NOTIFICATIONS - CAMPAIGN UPDATES
        # ==============================================================
        self._section('ADMIN - CAMPAIGN UPDATES')

        if campaign:
            try:
                n = NotificationService.notify_high_click_rate(admin, campaign, click_rate=65.5)
                self._ok(n, '16. High Click Rate Alert'); created += 1
            except Exception as e:
                self._fail('16. High Click Rate Alert', e)

            try:
                n = NotificationService.notify_simulation_progress(
                    admin, campaign, sent=20, clicked=6, reported=3
                )
                self._ok(n, '17. Simulation Progress'); created += 1
            except Exception as e:
                self._fail('17. Simulation Progress', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped campaign notifications (no campaign)'))

        # ==============================================================
        # ADMIN NOTIFICATIONS - TRAINING MANAGEMENT
        # ==============================================================
        self._section('ADMIN - TRAINING MANAGEMENT')

        try:
            n = NotificationService.notify_training_deadline_approaching(admin, count=5)
            self._ok(n, '18. Training Deadline Approaching'); created += 1
        except Exception as e:
            self._fail('18. Training Deadline Approaching', e)

        try:
            n = NotificationService.notify_overdue_trainings(admin, count=3)
            self._ok(n, '19. Overdue Trainings'); created += 1
        except Exception as e:
            self._fail('19. Overdue Trainings', e)

        # ==============================================================
        # ADMIN NOTIFICATIONS - EMPLOYEE MANAGEMENT
        # ==============================================================
        self._section('ADMIN - EMPLOYEE MANAGEMENT')

        try:
            n = NotificationService.notify_employee_joined(admin, employee)
            self._ok(n, '20. Employee Joined'); created += 1
        except Exception as e:
            self._fail('20. Employee Joined', e)

        try:
            n = NotificationService.notify_invitation_expired(admin, employee_email='pending@example.com')
            self._ok(n, '21. Invitation Expired'); created += 1
        except Exception as e:
            self._fail('21. Invitation Expired', e)

        # ==============================================================
        # EMPLOYEE - TRAINING (NEW)
        # ==============================================================
        self._section('EMPLOYEE - TRAINING (NEW)')

        if module:
            try:
                n = NotificationService.notify_training_completed_employee(employee, module, score=88.0)
                self._ok(n, '22. Training Completed - Employee'); created += 1
            except Exception as e:
                self._fail('22. Training Completed - Employee', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped: no module found'))

        # ==============================================================
        # EMPLOYEE - SIMULATION (NEW)
        # ==============================================================
        self._section('EMPLOYEE - SIMULATION (NEW)')

        if campaign:
            try:
                n = NotificationService.notify_simulation_clicked(employee, campaign)
                self._ok(n, '23. Simulation Clicked - Employee'); created += 1
            except Exception as e:
                self._fail('23. Simulation Clicked - Employee', e)

            try:
                n = NotificationService.notify_simulation_reported(employee, campaign)
                self._ok(n, '24. Simulation Reported - Employee'); created += 1
            except Exception as e:
                self._fail('24. Simulation Reported - Employee', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped: no campaign found'))

        # ==============================================================
        # EMPLOYEE - ACCOUNT (NEW)
        # ==============================================================
        self._section('EMPLOYEE - ACCOUNT (NEW)')

        try:
            n = NotificationService.notify_profile_updated(employee)
            self._ok(n, '25. Profile Updated'); created += 1
        except Exception as e:
            self._fail('25. Profile Updated', e)

        try:
            n = NotificationService.notify_security_score_up(employee, old_score=60, new_score=75)
            self._ok(n, '26. Security Score Up'); created += 1
        except Exception as e:
            self._fail('26. Security Score Up', e)

        try:
            n = NotificationService.notify_security_score_down(employee, old_score=75, new_score=55)
            self._ok(n, '27. Security Score Down'); created += 1
        except Exception as e:
            self._fail('27. Security Score Down', e)

        # ==============================================================
        # ADMIN - EMPLOYEE ACTIONS (NEW)
        # ==============================================================
        self._section('ADMIN - EMPLOYEE ACTIONS (NEW)')

        if campaign:
            try:
                n = NotificationService.notify_multiple_failures(admin, employee_count=10, simulation=campaign)
                self._ok(n, '28. Multiple Failures'); created += 1
            except Exception as e:
                self._fail('28. Multiple Failures', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped: no campaign found'))

        # ==============================================================
        # ADMIN - CAMPAIGN UPDATES (NEW)
        # ==============================================================
        self._section('ADMIN - CAMPAIGN UPDATES (NEW)')

        if campaign:
            try:
                n = NotificationService.notify_campaign_completed(admin, campaign)
                self._ok(n, '29. Campaign Completed'); created += 1
            except Exception as e:
                self._fail('29. Campaign Completed', e)

            try:
                n = NotificationService.notify_low_report_rate(admin, campaign, report_rate=4.5)
                self._ok(n, '30. Low Report Rate'); created += 1
            except Exception as e:
                self._fail('30. Low Report Rate', e)

            try:
                n = NotificationService.notify_simulation_sent(admin, campaign, count=50)
                self._ok(n, '31. Simulation Sent'); created += 1
            except Exception as e:
                self._fail('31. Simulation Sent', e)
        else:
            self.stdout.write(self.style.WARNING('  Skipped: no campaign found'))

        # ==============================================================
        # ADMIN - TRAINING MANAGEMENT (NEW)
        # ==============================================================
        self._section('ADMIN - TRAINING MANAGEMENT (NEW)')

        try:
            n = NotificationService.notify_monthly_report_ready(admin, month='February', year=2026)
            self._ok(n, '32. Monthly Report Ready'); created += 1
        except Exception as e:
            self._fail('32. Monthly Report Ready', e)

        # ==============================================================
        # SUPER ADMIN (NEW)
        # ==============================================================
        self._section('SUPER ADMIN (NEW)')

        try:
            n = NotificationService.notify_new_company(admin, company_name='Acme Corp')
            self._ok(n, '33. New Company'); created += 1
        except Exception as e:
            self._fail('33. New Company', e)

        try:
            n = NotificationService.notify_system_alert(admin, alert_message='Disk usage exceeded 90%')
            self._ok(n, '34. System Alert'); created += 1
        except Exception as e:
            self._fail('34. System Alert', e)

        try:
            n = NotificationService.notify_backup_completed(admin, backup_size='2.4 GB')
            self._ok(n, '35. Backup Completed'); created += 1
        except Exception as e:
            self._fail('35. Backup Completed', e)

        # ==============================================================
        # SUMMARY
        # ==============================================================
        employee_count = Notification.objects.filter(user=employee).count()
        admin_count    = Notification.objects.filter(user=admin).count()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('  SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Created this run   : {created}')
        self.stdout.write(f'  Employee total (DB): {employee_count}')
        self.stdout.write(f'  Admin total (DB)   : {admin_count}')
        self.stdout.write(f'  Grand total (DB)   : {Notification.objects.count()}')
        self.stdout.write('\n  Next steps:')
        self.stdout.write(f'    1. Login as employee  -> {employee.email}')
        self.stdout.write(f'       Bell should show {employee_count} notifications')
        self.stdout.write(f'    2. Login as admin     -> {admin.email}')
        self.stdout.write(f'       Bell should show {admin_count} notifications')
        self.stdout.write(f'    3. Open test page     -> http://localhost:5173/test/notifications\n')
