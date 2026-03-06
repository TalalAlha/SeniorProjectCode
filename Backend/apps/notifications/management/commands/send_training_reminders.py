from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.training.models import RemediationTraining
from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Send training deadline reminders to employees and summary alerts to admins'

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # ── Due in 3 days ────────────────────────────────────────────────────
        three_days_ahead = now + timedelta(days=3)
        due_soon = RemediationTraining.objects.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS'],
            due_date__date=three_days_ahead.date(),
        ).select_related('employee', 'training_module')

        for assignment in due_soon:
            try:
                NotificationService.notify_training_due_soon(
                    employee=assignment.employee,
                    training_assignment=assignment,
                    days_left=3,
                )
                self.stdout.write(f'3-day reminder → {assignment.employee.email}')
            except Exception as exc:
                self.stderr.write(f'Failed 3-day reminder for {assignment.employee.email}: {exc}')

        # ── Due tomorrow ─────────────────────────────────────────────────────
        tomorrow = now + timedelta(days=1)
        due_tomorrow = RemediationTraining.objects.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS'],
            due_date__date=tomorrow.date(),
        ).select_related('employee', 'training_module')

        for assignment in due_tomorrow:
            try:
                NotificationService.notify_training_due_tomorrow(
                    employee=assignment.employee,
                    training_assignment=assignment,
                )
                self.stdout.write(f'Tomorrow reminder → {assignment.employee.email}')
            except Exception as exc:
                self.stderr.write(f'Failed tomorrow reminder for {assignment.employee.email}: {exc}')

        # ── Overdue ──────────────────────────────────────────────────────────
        overdue = RemediationTraining.objects.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS'],
            due_date__lt=now,
        ).select_related('employee', 'training_module')

        for assignment in overdue:
            try:
                NotificationService.notify_training_overdue(
                    employee=assignment.employee,
                    training_assignment=assignment,
                )
                self.stdout.write(f'Overdue alert → {assignment.employee.email}')
            except Exception as exc:
                self.stderr.write(f'Failed overdue alert for {assignment.employee.email}: {exc}')

        # ── Admin summary alerts ──────────────────────────────────────────────
        from apps.accounts.models import User

        approaching_count = due_soon.count() + due_tomorrow.count()
        overdue_count = overdue.count()

        # Group by company so each admin only gets counts for their company
        companies_seen = set()
        all_assignments = list(due_soon) + list(due_tomorrow) + list(overdue)
        company_due_counts = {}
        company_overdue_counts = {}

        for assignment in list(due_soon) + list(due_tomorrow):
            cid = assignment.company_id if hasattr(assignment, 'company_id') else (
                assignment.employee.company_id if assignment.employee else None
            )
            if cid:
                company_due_counts[cid] = company_due_counts.get(cid, 0) + 1

        for assignment in overdue:
            cid = assignment.company_id if hasattr(assignment, 'company_id') else (
                assignment.employee.company_id if assignment.employee else None
            )
            if cid:
                company_overdue_counts[cid] = company_overdue_counts.get(cid, 0) + 1

        admins = User.objects.filter(role='COMPANY_ADMIN', is_active=True).select_related('company')

        for admin in admins:
            cid = admin.company_id
            due_for_company = company_due_counts.get(cid, 0)
            overdue_for_company = company_overdue_counts.get(cid, 0)

            try:
                if due_for_company > 0:
                    NotificationService.notify_training_deadline_approaching(
                        admin=admin,
                        count=due_for_company,
                    )
                if overdue_for_company > 0:
                    NotificationService.notify_overdue_trainings(
                        admin=admin,
                        count=overdue_for_company,
                    )
            except Exception as exc:
                self.stderr.write(f'Failed admin summary for {admin.email}: {exc}')

        self.stdout.write(self.style.SUCCESS(
            f'Done — approaching: {approaching_count}, overdue: {overdue_count}'
        ))
