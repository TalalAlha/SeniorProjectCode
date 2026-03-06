from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        # Employee - Training
        ('TRAINING_ASSIGNED', 'Training Assigned'),
        ('TRAINING_DUE_SOON', 'Training Due Soon'),
        ('TRAINING_DUE_TOMORROW', 'Training Due Tomorrow'),
        ('TRAINING_OVERDUE', 'Training Overdue'),
        ('TRAINING_COMPLETED_EMPLOYEE', 'Training Completed - You'),
        ('QUIZ_FAILED', 'Quiz Failed'),
        ('QUIZ_PASSED', 'Quiz Passed'),

        # Employee - Simulation
        ('SIMULATION_CLICKED', 'You Clicked Phishing Link'),
        ('SIMULATION_REPORTED', 'You Reported Phishing'),
        ('SIMULATION_LAUNCHED', 'New Simulation Campaign'),
        ('SIMULATION_SAFE', 'Simulation Expired - You Were Safe'),

        # Employee - Account
        ('WELCOME', 'Welcome to PhishAware'),
        ('PROFILE_UPDATED', 'Profile Updated'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        ('SECURITY_SCORE_UP', 'Security Score Improved'),
        ('SECURITY_SCORE_DOWN', 'Security Score Decreased'),

        # Admin - Employee Actions
        ('EMPLOYEE_CLICKED', 'Employee Clicked Phishing'),
        ('EMPLOYEE_REPORTED', 'Employee Reported Phishing'),
        ('TRAINING_COMPLETED', 'Training Completed'),
        ('EMPLOYEE_FAILED_QUIZ', 'Employee Failed Training'),
        ('MULTIPLE_FAILURES', 'Multiple Employees Failed'),
        ('HIGH_RISK_EMPLOYEE', 'Employee Marked High Risk'),

        # Admin - Campaign Updates
        ('CAMPAIGN_COMPLETED', 'Campaign Completed'),
        ('SIMULATION_PROGRESS', 'Simulation Progress Update'),
        ('HIGH_CLICK_RATE', 'High Click Rate Alert'),
        ('LOW_REPORT_RATE', 'Low Report Rate Warning'),
        ('SIMULATION_SENT', 'Simulation Emails Sent'),

        # Admin - Training Management
        ('TRAINING_DEADLINE_APPROACHING', 'Training Deadlines Approaching'),
        ('OVERDUE_TRAININGS', 'Overdue Trainings Alert'),
        ('MONTHLY_REPORT_READY', 'Monthly Report Ready'),

        # Admin - Employee Management
        ('EMPLOYEE_JOINED', 'New Employee Joined'),
        ('INVITATION_EXPIRED', 'Employee Invitation Expired'),

        # Legacy (kept for backward compatibility)
        ('HIGH_RISK_ALERT', 'High Risk Employee'),

        # Super Admin
        ('NEW_COMPANY', 'New Company Registered'),
        ('SYSTEM_ALERT', 'System Alert'),
        ('BACKUP_COMPLETED', 'Backup Completed'),
    ]

    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')

    # Optional link to related object
    link = models.CharField(max_length=500, blank=True, null=True)

    # State
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"
