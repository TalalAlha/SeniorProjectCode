from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for PhishAware platform with role-based access control.

    Supports four user roles:
    - SUPER_ADMIN: Platform administrators
    - COMPANY_ADMIN: Company administrators
    - EMPLOYEE: Company employees
    - PUBLIC_USER: Public community users
    """

    ROLE_CHOICES = [
        ('SUPER_ADMIN', _('Super Admin')),
        ('COMPANY_ADMIN', _('Company Admin')),
        ('EMPLOYEE', _('Employee')),
        ('PUBLIC_USER', _('Public User')),
    ]

    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ar', _('Arabic')),
    ]

    # Basic Information
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)

    # Role and Company
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='PUBLIC_USER')
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        verbose_name=_('company')
    )

    # Preferences
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='en'
    )

    # Status fields
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_verified = models.BooleanField(_('verified'), default=False)

    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['company']),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    @property
    def is_super_admin(self):
        """Check if user is a super admin."""
        return self.role == 'SUPER_ADMIN'

    @property
    def is_company_admin(self):
        """Check if user is a company admin."""
        return self.role == 'COMPANY_ADMIN'

    @property
    def is_employee(self):
        """Check if user is an employee."""
        return self.role == 'EMPLOYEE'

    @property
    def is_public_user(self):
        """Check if user is a public user."""
        return self.role == 'PUBLIC_USER'

    @property
    def has_company_access(self):
        """Check if user has access to company features."""
        return self.role in ['COMPANY_ADMIN', 'EMPLOYEE'] and self.company is not None
