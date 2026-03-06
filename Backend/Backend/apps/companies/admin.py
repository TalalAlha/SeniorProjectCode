from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin configuration for Company model."""

    list_display = ['name', 'industry', 'company_size', 'country', 'city', 'is_active', 'created_at']
    list_filter = ['industry', 'company_size', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'name_ar', 'email', 'phone', 'city', 'country']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'total_users', 'total_employees', 'total_admins']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'name_ar', 'description', 'description_ar')
        }),
        (_('Contact Information'), {
            'fields': ('email', 'phone', 'website')
        }),
        (_('Location'), {
            'fields': ('country', 'city', 'address')
        }),
        (_('Company Details'), {
            'fields': ('industry', 'company_size')
        }),
        (_('Subscription'), {
            'fields': ('is_active', 'subscription_start_date', 'subscription_end_date')
        }),
        (_('Statistics'), {
            'fields': ('total_users', 'total_employees', 'total_admins'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation."""
        if obj:  # Editing an existing object
            return self.readonly_fields
        return ['created_at', 'updated_at', 'total_users', 'total_employees', 'total_admins']
