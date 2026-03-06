from django.core.management.base import BaseCommand
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
import inspect


class Command(BaseCommand):
    help = 'Audit notification system - show what is implemented and what is missing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('NOTIFICATION SYSTEM AUDIT'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        # Get all notification types from model
        notification_types = dict(Notification.NOTIFICATION_TYPES)

        # Get all service methods
        service_methods = [
            method for method in dir(NotificationService)
            if method.startswith('notify_') and callable(getattr(NotificationService, method))
        ]

        # Categorize notification types
        categories = {
            'EMPLOYEE - TRAINING': [
                'TRAINING_ASSIGNED',
                'TRAINING_DUE_SOON',
                'TRAINING_DUE_TOMORROW',
                'TRAINING_OVERDUE',
                'TRAINING_COMPLETED_EMPLOYEE',
                'QUIZ_FAILED',
                'QUIZ_PASSED',
            ],
            'EMPLOYEE - SIMULATION': [
                'SIMULATION_CLICKED',
                'SIMULATION_REPORTED',
                'SIMULATION_LAUNCHED',
                'SIMULATION_SAFE',
            ],
            'EMPLOYEE - ACCOUNT': [
                'WELCOME',
                'PROFILE_UPDATED',
                'PASSWORD_CHANGED',
                'SECURITY_SCORE_UP',
                'SECURITY_SCORE_DOWN',
            ],
            'ADMIN - EMPLOYEE ACTIONS': [
                'EMPLOYEE_CLICKED',
                'EMPLOYEE_REPORTED',
                'TRAINING_COMPLETED',
                'EMPLOYEE_FAILED_QUIZ',
                'MULTIPLE_FAILURES',
                'HIGH_RISK_EMPLOYEE',
            ],
            'ADMIN - CAMPAIGN UPDATES': [
                'CAMPAIGN_COMPLETED',
                'SIMULATION_PROGRESS',
                'HIGH_CLICK_RATE',
                'LOW_REPORT_RATE',
                'SIMULATION_SENT',
            ],
            'ADMIN - TRAINING MANAGEMENT': [
                'TRAINING_DEADLINE_APPROACHING',
                'OVERDUE_TRAININGS',
                'MONTHLY_REPORT_READY',
            ],
            'ADMIN - EMPLOYEE MANAGEMENT': [
                'EMPLOYEE_JOINED',
                'INVITATION_EXPIRED',
            ],
            'SUPER ADMIN': [
                'NEW_COMPANY',
                'SYSTEM_ALERT',
                'BACKUP_COMPLETED',
            ],
        }

        # Map notification types to expected service method names
        type_to_method_map = {
            'TRAINING_ASSIGNED': 'notify_training_assigned',
            'TRAINING_DUE_SOON': 'notify_training_due_soon',
            'TRAINING_DUE_TOMORROW': 'notify_training_due_tomorrow',
            'TRAINING_OVERDUE': 'notify_training_overdue',
            'TRAINING_COMPLETED_EMPLOYEE': 'notify_training_completed_employee',
            'QUIZ_FAILED': 'notify_quiz_failed',
            'QUIZ_PASSED': 'notify_quiz_passed',
            'SIMULATION_CLICKED': 'notify_simulation_clicked',
            'SIMULATION_REPORTED': 'notify_simulation_reported',
            'SIMULATION_LAUNCHED': 'notify_simulation_launched',
            'SIMULATION_SAFE': 'notify_simulation_safe',
            'WELCOME': 'notify_welcome',
            'PROFILE_UPDATED': 'notify_profile_updated',
            'PASSWORD_CHANGED': 'notify_password_changed',
            'SECURITY_SCORE_UP': 'notify_security_score_up',
            'SECURITY_SCORE_DOWN': 'notify_security_score_down',
            'EMPLOYEE_CLICKED': 'notify_employee_clicked_phishing',
            'EMPLOYEE_REPORTED': 'notify_employee_reported_phishing',
            'TRAINING_COMPLETED': 'notify_training_completed',
            'EMPLOYEE_FAILED_QUIZ': 'notify_employee_failed_quiz',
            'MULTIPLE_FAILURES': 'notify_multiple_failures',
            'HIGH_RISK_EMPLOYEE': 'notify_high_risk_employee',
            'CAMPAIGN_COMPLETED': 'notify_campaign_completed',
            'SIMULATION_PROGRESS': 'notify_simulation_progress',
            'HIGH_CLICK_RATE': 'notify_high_click_rate',
            'LOW_REPORT_RATE': 'notify_low_report_rate',
            'SIMULATION_SENT': 'notify_simulation_sent',
            'TRAINING_DEADLINE_APPROACHING': 'notify_training_deadline_approaching',
            'OVERDUE_TRAININGS': 'notify_overdue_trainings',
            'MONTHLY_REPORT_READY': 'notify_monthly_report_ready',
            'EMPLOYEE_JOINED': 'notify_employee_joined',
            'INVITATION_EXPIRED': 'notify_invitation_expired',
            'NEW_COMPANY': 'notify_new_company',
            'SYSTEM_ALERT': 'notify_system_alert',
            'BACKUP_COMPLETED': 'notify_backup_completed',
        }

        # Track statistics
        categorized_types = set(t for types in categories.values() for t in types)
        total_types = len(categorized_types)
        implemented_count = 0
        missing_count = 0

        # Print each category
        for category, types in categories.items():
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.WARNING(category))
            self.stdout.write('=' * 80)

            for notif_type in types:
                if notif_type not in notification_types:
                    self.stdout.write(
                        self.style.ERROR(f'  [NOT IN MODEL] {notif_type}')
                    )
                    continue

                label = notification_types[notif_type]
                expected_method = type_to_method_map.get(notif_type)

                # Check if service method exists
                has_service = expected_method in service_methods if expected_method else False

                # Check if any notifications of this type exist in DB
                count_in_db = Notification.objects.filter(notification_type=notif_type).count()

                if has_service:
                    implemented_count += 1
                    status_icon = '[OK]'
                    status_color = self.style.SUCCESS
                else:
                    missing_count += 1
                    status_icon = '[XX]'
                    status_color = self.style.ERROR

                # Format output
                line = f"{status_icon} {notif_type:<35} {label:<40}"

                if has_service:
                    line += f" -> {expected_method}"
                else:
                    line += f" -> MISSING: {expected_method or 'unknown'}"

                if count_in_db > 0:
                    line += f" (DB: {count_in_db})"

                self.stdout.write(status_color(line))

        # Legacy types (in model but not categorized)
        legacy_types = set(notification_types.keys()) - categorized_types
        if legacy_types:
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.WARNING('LEGACY / UNCATEGORIZED'))
            self.stdout.write('=' * 80)
            for notif_type in sorted(legacy_types):
                label = notification_types[notif_type]
                count_in_db = Notification.objects.filter(notification_type=notif_type).count()
                db_suffix = f' (DB: {count_in_db})' if count_in_db > 0 else ''
                self.stdout.write(
                    self.style.WARNING(f'  [??] {notif_type:<35} {label}{db_suffix}')
                )

        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('=' * 80 + '\n')

        self.stdout.write(f"Total notification types (categorized): {total_types}")
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Implemented: {implemented_count} ({implemented_count / total_types * 100:.1f}%)"
        ))
        self.stdout.write(self.style.ERROR(
            f"[XX] Missing:     {missing_count} ({missing_count / total_types * 100:.1f}%)"
        ))

        # List all service methods for reference
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('ALL EXISTING SERVICE METHODS:'))
        self.stdout.write('=' * 80 + '\n')
        for method in sorted(service_methods):
            self.stdout.write(f"  + {method}")

        # List missing methods that need implementation
        if missing_count > 0:
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.WARNING('MISSING SERVICE METHODS TO IMPLEMENT:'))
            self.stdout.write('=' * 80 + '\n')

            seen = set()
            missing_methods = []
            for notif_type, method_name in type_to_method_map.items():
                if method_name not in service_methods and method_name not in seen:
                    seen.add(method_name)
                    missing_methods.append(method_name)

            for method in sorted(missing_methods):
                self.stdout.write(self.style.ERROR(f"  - {method}"))

        # Check for triggers
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.WARNING('TRIGGER LOCATIONS TO VERIFY:'))
        self.stdout.write('=' * 80 + '\n')

        triggers = {
            'Training assigned': 'training/views.py -> bulk_assign_training',
            'Quiz submitted': 'training/views.py -> submit_quiz',
            'Phishing clicked': 'simulations/views.py -> track_link_click_view',
            'Phishing reported': 'simulations/views.py -> report_phishing_view',
            'Invitation accepted': 'accounts/views.py -> AcceptInvitationView',
            'Password changed': 'accounts/views.py -> ChangePasswordView',
            'Training reminders': 'notifications/management/commands/send_training_reminders.py',
            'High click rate': 'simulations/views.py -> track_link_click_view (auto-check)',
        }

        for trigger, location in triggers.items():
            self.stdout.write(f"  [>] {trigger:<25} -> {location}")

        # Database statistics
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('DATABASE STATISTICS:'))
        self.stdout.write('=' * 80 + '\n')

        total_notifs = Notification.objects.count()
        unread_notifs = Notification.objects.filter(is_read=False).count()

        self.stdout.write(f"Total notifications in database: {total_notifs}")
        self.stdout.write(f"Unread notifications:           {unread_notifs}")

        # Top notification types by count
        from django.db.models import Count
        top_types = (
            Notification.objects
            .values('notification_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        if top_types:
            self.stdout.write('\nTop 10 notification types by count:')
            for i, item in enumerate(top_types, 1):
                notif_type = item['notification_type']
                count = item['count']
                label = notification_types.get(notif_type, 'Unknown')
                self.stdout.write(f"   {i:>2}. {notif_type:<35} {label:<40} ({count})")

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('Audit complete!'))
        self.stdout.write('=' * 80 + '\n')
