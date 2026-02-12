from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator


class Company(models.Model):
    """
    Company model for organizations using the PhishAware platform.

    Each company can have multiple users (admins and employees) and
    run phishing awareness campaigns for their employees.
    """

    INDUSTRY_CHOICES = [
        ('TECH', _('Technology')),
        ('FINANCE', _('Finance & Banking')),
        ('HEALTHCARE', _('Healthcare')),
        ('EDUCATION', _('Education')),
        ('RETAIL', _('Retail & E-commerce')),
        ('MANUFACTURING', _('Manufacturing')),
        ('GOVERNMENT', _('Government')),
        ('TELECOM', _('Telecommunications')),
        ('ENERGY', _('Energy & Utilities')),
        ('OTHER', _('Other')),
    ]

    COMPANY_SIZE_CHOICES = [
        ('1-10', _('1-10 employees')),
        ('11-50', _('11-50 employees')),
        ('51-200', _('51-200 employees')),
        ('201-500', _('201-500 employees')),
        ('501-1000', _('501-1000 employees')),
        ('1001+', _('1001+ employees')),
    ]

    # Basic Information
    name = models.CharField(_('company name'), max_length=255, unique=True)
    name_ar = models.CharField(_('company name (Arabic)'), max_length=255, blank=True)
    description = models.TextField(_('description'), blank=True)
    description_ar = models.TextField(_('description (Arabic)'), blank=True)

    # Contact Information
    email = models.EmailField(_('company email'))
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    website = models.URLField(_('website'), validators=[URLValidator()], blank=True)

    # Location
    country = models.CharField(_('country'), max_length=100)
    city = models.CharField(_('city'), max_length=100)
    address = models.TextField(_('address'), blank=True)

    # Company Details
    industry = models.CharField(_('industry'), max_length=50, choices=INDUSTRY_CHOICES)
    company_size = models.CharField(_('company size'), max_length=20, choices=COMPANY_SIZE_CHOICES)

    # Subscription & Status
    is_active = models.BooleanField(_('active'), default=True)
    subscription_start_date = models.DateField(_('subscription start date'), null=True, blank=True)
    subscription_end_date = models.DateField(_('subscription end date'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_subscription_active(self):
        """Check if company subscription is currently active."""
        from django.utils import timezone
        if not self.subscription_end_date:
            return False
        return self.subscription_end_date >= timezone.now().date()

    @property
    def total_users(self):
        """Get total number of users in the company."""
        return self.users.count()

    @property
    def total_employees(self):
        """Get total number of employees in the company."""
        return self.users.filter(role='EMPLOYEE').count()

    @property
    def total_admins(self):
        """Get total number of company admins."""
        return self.users.filter(role='COMPANY_ADMIN').count()
