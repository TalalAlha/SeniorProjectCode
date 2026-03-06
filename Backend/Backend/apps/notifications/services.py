from .models import Notification


class NotificationService:
    """Service layer for creating notifications."""

    @staticmethod
    def create_notification(user, notification_type, title, message, priority='MEDIUM', link=None):
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            link=link,
        )

    # =========================================================================
    # EMPLOYEE NOTIFICATIONS - TRAINING
    # =========================================================================

    @staticmethod
    def notify_training_assigned(employee, training_module):
        return NotificationService.create_notification(
            user=employee,
            notification_type='TRAINING_ASSIGNED',
            title='New Training Assigned',
            message=f'You have been assigned: {training_module.title}',
            priority='MEDIUM',
            link='/employee/training',
        )

    @staticmethod
    def notify_training_due_soon(employee, training_assignment, days_left):
        return NotificationService.create_notification(
            user=employee,
            notification_type='TRAINING_DUE_SOON',
            title='Training Due Soon',
            message=f'{training_assignment.training_module.title} is due in {days_left} days',
            priority='MEDIUM',
            link='/employee/training',
        )

    @staticmethod
    def notify_training_due_tomorrow(employee, training_assignment):
        return NotificationService.create_notification(
            user=employee,
            notification_type='TRAINING_DUE_TOMORROW',
            title='Training Due Tomorrow!',
            message=f'{training_assignment.training_module.title} is due tomorrow',
            priority='HIGH',
            link='/employee/training',
        )

    @staticmethod
    def notify_training_overdue(employee, training_assignment):
        return NotificationService.create_notification(
            user=employee,
            notification_type='TRAINING_OVERDUE',
            title='Training Overdue',
            message=f'{training_assignment.training_module.title} is overdue. Please complete ASAP.',
            priority='URGENT',
            link='/employee/training',
        )

    @staticmethod
    def notify_quiz_passed(employee, training_module, score):
        return NotificationService.create_notification(
            user=employee,
            notification_type='QUIZ_PASSED',
            title='Quiz Passed!',
            message=f'Congratulations! You scored {score:.1f}% on {training_module.title}',
            priority='LOW',
            link='/employee/training',
        )

    @staticmethod
    def notify_quiz_failed(employee, training_module, score):
        return NotificationService.create_notification(
            user=employee,
            notification_type='QUIZ_FAILED',
            title='Quiz Failed',
            message=f'You scored {score:.1f}% on {training_module.title}. Retry available.',
            priority='MEDIUM',
            link='/employee/training',
        )

    # =========================================================================
    # EMPLOYEE NOTIFICATIONS - SIMULATION
    # =========================================================================

    @staticmethod
    def notify_simulation_launched(employee, simulation):
        return NotificationService.create_notification(
            user=employee,
            notification_type='SIMULATION_LAUNCHED',
            title='New Security Awareness Test',
            message='A new security test has been launched. Stay alert for suspicious emails!',
            priority='LOW',
            link='/employee/dashboard',
        )

    @staticmethod
    def notify_simulation_safe(employee, simulation):
        return NotificationService.create_notification(
            user=employee,
            notification_type='SIMULATION_SAFE',
            title='Great Job!',
            message=f'You successfully avoided the phishing attempt in "{simulation.name}"',
            priority='LOW',
            link='/employee/dashboard',
        )

    # =========================================================================
    # EMPLOYEE NOTIFICATIONS - ACCOUNT
    # =========================================================================

    @staticmethod
    def notify_welcome(employee):
        return NotificationService.create_notification(
            user=employee,
            notification_type='WELCOME',
            title='Welcome to PhishAware!',
            message='Your account has been created. Start your security awareness journey!',
            priority='LOW',
            link='/employee/dashboard',
        )

    @staticmethod
    def notify_password_changed(user):
        return NotificationService.create_notification(
            user=user,
            notification_type='PASSWORD_CHANGED',
            title='Password Changed',
            message="Your password was successfully changed. If this wasn't you, contact support immediately.",
            priority='HIGH',
            link='/employee/profile',
        )

    # =========================================================================
    # ADMIN NOTIFICATIONS - EMPLOYEE ACTIONS
    # =========================================================================

    @staticmethod
    def notify_employee_clicked_phishing(admin, employee, simulation):
        return NotificationService.create_notification(
            user=admin,
            notification_type='EMPLOYEE_CLICKED',
            title='Employee Clicked Phishing Link',
            message=f'{employee.get_full_name() or employee.email} clicked phishing link in "{simulation.name}"',
            priority='HIGH',
            link=f'/company/simulations/{simulation.id}/analytics',
        )

    @staticmethod
    def notify_employee_reported_phishing(admin, employee, simulation):
        return NotificationService.create_notification(
            user=admin,
            notification_type='EMPLOYEE_REPORTED',
            title='Employee Reported Phishing',
            message=f'{employee.get_full_name() or employee.email} correctly reported phishing in "{simulation.name}"',
            priority='LOW',
            link=f'/company/simulations/{simulation.id}/analytics',
        )

    @staticmethod
    def notify_training_completed(admin, employee, training_module):
        return NotificationService.create_notification(
            user=admin,
            notification_type='TRAINING_COMPLETED',
            title='Training Completed',
            message=f'{employee.get_full_name() or employee.email} completed training: {training_module.title}',
            priority='LOW',
            link='/company/training',
        )

    @staticmethod
    def notify_employee_failed_quiz(admin, employee, training_module, score):
        return NotificationService.create_notification(
            user=admin,
            notification_type='EMPLOYEE_FAILED_QUIZ',
            title='Employee Failed Training',
            message=f'{employee.get_full_name() or employee.email} scored {score:.1f}% on {training_module.title}',
            priority='MEDIUM',
            link='/company/analytics',
        )

    @staticmethod
    def notify_high_risk_employee(admin, employee, risk_score):
        return NotificationService.create_notification(
            user=admin,
            notification_type='HIGH_RISK_EMPLOYEE',
            title='High Risk Employee Detected',
            message=f'{employee.get_full_name() or employee.email} has a risk score of {risk_score}%',
            priority='HIGH',
            link='/company/analytics',
        )

    # =========================================================================
    # ADMIN NOTIFICATIONS - CAMPAIGN UPDATES
    # =========================================================================

    @staticmethod
    def notify_campaign_completed(admin, campaign):
        return NotificationService.create_notification(
            user=admin,
            notification_type='CAMPAIGN_COMPLETED',
            title='Campaign Completed',
            message=f'Campaign "{campaign.name}" has been completed. View results.',
            priority='MEDIUM',
            link=f'/company/simulations/{campaign.id}/analytics',
        )

    @staticmethod
    def notify_high_click_rate(admin, simulation, click_rate):
        return NotificationService.create_notification(
            user=admin,
            notification_type='HIGH_CLICK_RATE',
            title='High Click Rate Alert',
            message=f'"{simulation.name}" has a {click_rate}% click rate. Review security training.',
            priority='HIGH',
            link=f'/company/simulations/{simulation.id}/analytics',
        )

    @staticmethod
    def notify_simulation_progress(admin, simulation, sent, clicked, reported):
        return NotificationService.create_notification(
            user=admin,
            notification_type='SIMULATION_PROGRESS',
            title='Simulation Update',
            message=f'"{simulation.name}": {sent} sent, {clicked} clicked, {reported} reported',
            priority='LOW',
            link=f'/company/simulations/{simulation.id}/analytics',
        )

    # =========================================================================
    # ADMIN NOTIFICATIONS - TRAINING MANAGEMENT
    # =========================================================================

    @staticmethod
    def notify_training_deadline_approaching(admin, count):
        return NotificationService.create_notification(
            user=admin,
            notification_type='TRAINING_DEADLINE_APPROACHING',
            title='Training Deadlines Approaching',
            message=f'{count} employees have training due within 3 days',
            priority='MEDIUM',
            link='/company/training',
        )

    @staticmethod
    def notify_overdue_trainings(admin, count):
        return NotificationService.create_notification(
            user=admin,
            notification_type='OVERDUE_TRAININGS',
            title='Overdue Trainings',
            message=f'{count} employees have overdue training assignments',
            priority='HIGH',
            link='/company/training',
        )

    # =========================================================================
    # ADMIN NOTIFICATIONS - EMPLOYEE MANAGEMENT
    # =========================================================================

    @staticmethod
    def notify_employee_joined(admin, employee):
        return NotificationService.create_notification(
            user=admin,
            notification_type='EMPLOYEE_JOINED',
            title='New Employee Joined',
            message=f'{employee.get_full_name() or employee.email} has accepted the invitation',
            priority='LOW',
            link='/company/employees',
        )

    @staticmethod
    def notify_invitation_expired(admin, employee_email):
        return NotificationService.create_notification(
            user=admin,
            notification_type='INVITATION_EXPIRED',
            title='Invitation Expired',
            message=f'Employee invitation for {employee_email} has expired without being accepted',
            priority='LOW',
            link='/company/employees',
        )

    # =========================================================================
    # EMPLOYEE NOTIFICATIONS - TRAINING (NEW)
    # =========================================================================

    @staticmethod
    def notify_training_completed_employee(employee, training_module, score):
        return NotificationService.create_notification(
            user=employee,
            notification_type='TRAINING_COMPLETED_EMPLOYEE',
            title='Training Completed!',
            message=f'You completed "{training_module.title}" with a score of {score:.1f}%',
            priority='LOW',
            link='/employee/training',
        )

    # =========================================================================
    # EMPLOYEE NOTIFICATIONS - SIMULATION (NEW)
    # =========================================================================

    @staticmethod
    def notify_simulation_clicked(employee, simulation):
        return NotificationService.create_notification(
            user=employee,
            notification_type='SIMULATION_CLICKED',
            title='You Clicked a Phishing Link',
            message=f'This was a security test. Review the red flags in "{simulation.name}" to stay safe.',
            priority='MEDIUM',
            link='/employee/training',
        )

    @staticmethod
    def notify_simulation_reported(employee, simulation):
        return NotificationService.create_notification(
            user=employee,
            notification_type='SIMULATION_REPORTED',
            title='Great Job Reporting!',
            message=f'You correctly identified and reported the phishing attempt in "{simulation.name}"',
            priority='LOW',
            link='/employee/dashboard',
        )

    # =========================================================================
    # EMPLOYEE NOTIFICATIONS - ACCOUNT (NEW)
    # =========================================================================

    @staticmethod
    def notify_profile_updated(user):
        return NotificationService.create_notification(
            user=user,
            notification_type='PROFILE_UPDATED',
            title='Profile Updated',
            message='Your profile information has been successfully updated.',
            priority='LOW',
            link='/employee/profile',
        )

    @staticmethod
    def notify_security_score_up(employee, old_score, new_score):
        improvement = round(new_score - old_score, 1)
        return NotificationService.create_notification(
            user=employee,
            notification_type='SECURITY_SCORE_UP',
            title='Security Score Improved!',
            message=f'Your security score increased by {improvement}% and is now {new_score}%',
            priority='LOW',
            link='/employee/dashboard',
        )

    @staticmethod
    def notify_security_score_down(employee, old_score, new_score):
        decrease = round(old_score - new_score, 1)
        return NotificationService.create_notification(
            user=employee,
            notification_type='SECURITY_SCORE_DOWN',
            title='Security Score Decreased',
            message=f'Your security score decreased by {decrease}% and is now {new_score}%. Review your training.',
            priority='MEDIUM',
            link='/employee/training',
        )

    # =========================================================================
    # ADMIN NOTIFICATIONS - EMPLOYEE ACTIONS (NEW)
    # =========================================================================

    @staticmethod
    def notify_multiple_failures(admin, employee_count, simulation):
        return NotificationService.create_notification(
            user=admin,
            notification_type='MULTIPLE_FAILURES',
            title='Multiple Employees Clicked Phishing',
            message=f'{employee_count} employees have clicked the phishing link in "{simulation.name}". Consider additional training.',
            priority='HIGH',
            link=f'/company/simulations/{simulation.id}/analytics',
        )

    # =========================================================================
    # ADMIN NOTIFICATIONS - CAMPAIGN UPDATES (NEW)
    # =========================================================================

    @staticmethod
    def notify_low_report_rate(admin, simulation, report_rate):
        return NotificationService.create_notification(
            user=admin,
            notification_type='LOW_REPORT_RATE',
            title='Low Report Rate Warning',
            message=f'Only {report_rate}% of employees reported the phishing email in "{simulation.name}". Employees may need guidance on reporting.',
            priority='MEDIUM',
            link=f'/company/simulations/{simulation.id}/analytics',
        )

    @staticmethod
    def notify_simulation_sent(admin, simulation, count):
        return NotificationService.create_notification(
            user=admin,
            notification_type='SIMULATION_SENT',
            title='Simulation Emails Sent',
            message=f'Successfully sent {count} simulation emails for "{simulation.name}"',
            priority='LOW',
            link=f'/company/simulations/{simulation.id}/analytics',
        )

    # =========================================================================
    # ADMIN NOTIFICATIONS - TRAINING MANAGEMENT (NEW)
    # =========================================================================

    @staticmethod
    def notify_monthly_report_ready(admin, month, year):
        return NotificationService.create_notification(
            user=admin,
            notification_type='MONTHLY_REPORT_READY',
            title='Monthly Report Ready',
            message=f'Training completion report for {month} {year} is now available',
            priority='LOW',
            link='/company/analytics',
        )

    # =========================================================================
    # SUPER ADMIN NOTIFICATIONS (NEW)
    # =========================================================================

    @staticmethod
    def notify_new_company(super_admin, company_name):
        return NotificationService.create_notification(
            user=super_admin,
            notification_type='NEW_COMPANY',
            title='New Company Registered',
            message=f'New company "{company_name}" has registered on the platform',
            priority='LOW',
            link='/superadmin/companies',
        )

    @staticmethod
    def notify_system_alert(super_admin, alert_message):
        return NotificationService.create_notification(
            user=super_admin,
            notification_type='SYSTEM_ALERT',
            title='System Alert',
            message=alert_message,
            priority='HIGH',
            link='/superadmin/system',
        )

    @staticmethod
    def notify_backup_completed(super_admin, backup_size):
        return NotificationService.create_notification(
            user=super_admin,
            notification_type='BACKUP_COMPLETED',
            title='Backup Completed',
            message=f'Database backup completed successfully ({backup_size})',
            priority='LOW',
            link='/superadmin/backups',
        )
